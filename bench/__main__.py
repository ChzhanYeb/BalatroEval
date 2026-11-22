"""规则引擎命令行：python -m bench {rules,demo,verify,ev}。

子命令语义：
- ``rules``：打印机器可读的规则声明（版本/已实现/未验证/排除项/盲注表）；
- ``demo``：用 O1 贪心跑一局 Ante 1 样例（不写文件，stdout 输出 JSON）；
- ``verify``：用独立暴力枚举交叉检查 O1（只证明两条搜索路径一致，不证明与真游戏一致）；
- ``ev``：对初始手牌估计每个弃牌子集的 EV（近似，K 默认 50）。

退出行为：业务异常以 traceback + 退出码 1 结束；参数错误 argparse 退出码 2。
"""
from __future__ import annotations

import argparse
import json
import random
from itertools import combinations

from .cards import standard_deck
from .engine import new_game, play, choose_joker
from .oracle import best_play, discard_ev, greedy_episode
from .rules_version import VANILLA_SUBSET_V1
from .scoring import score_hand


def verify_oracle(samples: int = 10, seed: int = 20261112) -> dict:
    """独立暴力核验 O1：随机 8 张手牌上穷举 1..5 张取最大分。

    与 ``oracle.best_play`` 的区别：这里用独立的 ``combinations`` 循环，未经
    ``actions.legal_plays``；但两边最终都调用 ``scoring.score_hand``，因此本检查只证明
    “搜索路径一致”，不证明计分规则符合真游戏（A2 仍是 0 行）。
    """
    rng = random.Random(seed)
    deck = standard_deck()
    checks = []
    for i in range(samples):
        hand = rng.sample(deck, 8)
        state = new_game(
            seed + i,
            hand_ids=[c.card_id for c in hand],
            deck_order=[c.card_id for c in deck if c not in hand],
        )
        result = best_play(state)
        brute_force = max(
            score_hand([hand[j] for j in indices], state.jokers).final_score
            for size in range(1, 6)
            for indices in combinations(range(len(hand)), size)
        )
        checks.append({
            "case": i + 1, "oracle": result.score, "brute_force": brute_force,
            "match": result.score == brute_force,
            "candidates": result.candidates_evaluated,
        })
    return {"seed": seed, "samples": samples,
            "passed": all(c["match"] for c in checks), "checks": checks}


def run_demo(seed: int, max_steps: int) -> dict:
    """用 O1 贪心跑一局 Ante 1 样例，返回可 JSON 序列化的摘要。"""
    reference = greedy_episode(new_game(seed), max_steps=max_steps)
    # 再跑一遍以记录逐步历史（greedy_episode 只返回摘要）。
    current = new_game(seed)
    history = []
    for _ in range(max_steps):
        if current.phase == "done":
            break
        if current.phase == "shop":
            current = choose_joker(current, 0 if current.shop_options else None)
            history.append({"action": "choose_joker", "blind_idx": current.blind_idx})
            continue
        best = best_play(current)
        current, result = play(current, best.card_ids)
        history.append({
            "action": "play", "cards": list(best.card_ids),
            "hand_type": result.hand_type.value, "score": result.final_score,
            "total_score": current.total_score, "blind_idx": current.blind_idx,
            "phase": current.phase,
        })
    return {
        "seed": seed, "rules_version": current.rules_version,
        "outcome": reference.outcome, "phase": current.phase,
        "blind_idx": current.blind_idx, "blind_scores": reference.score_by_blind,
        "total_scored": reference.total_scored, "steps": current.steps,
        "history": history,
    }


def main() -> None:
    """解析参数并分派子命令。"""
    parser = argparse.ArgumentParser(prog="python -m bench",
                                     description="BalatroEval vanilla-subset rules engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rules", help="print the machine-readable ruleset declaration")
    p_demo = sub.add_parser("demo", help="run an O1-greedy Ante 1 sample episode")
    p_demo.add_argument("--seed", type=int, default=20261112)
    p_demo.add_argument("--max-steps", type=int, default=100)
    p_verify = sub.add_parser("verify", help="cross-check O1 against independent brute force")
    p_verify.add_argument("--samples", type=int, default=10)
    p_verify.add_argument("--seed", type=int, default=20261112)
    p_ev = sub.add_parser("ev", help="estimate discard EV for the initial hand")
    p_ev.add_argument("--seed", type=int, default=20261112)
    p_ev.add_argument("-k", type=int, default=50)
    args = parser.parse_args()

    if args.cmd == "rules":
        result: dict = VANILLA_SUBSET_V1.to_dict()
        result["signature"] = VANILLA_SUBSET_V1.signature()
    elif args.cmd == "demo":
        result = run_demo(args.seed, args.max_steps)
    elif args.cmd == "verify":
        result = verify_oracle(args.samples, args.seed)
    else:
        state = new_game(args.seed)
        ev = discard_ev(state, K=args.k)
        result = {"seed": args.seed, "K": args.k, "actions": [
            {"cards": list(item.card_ids), "indices": list(item.indices),
             "mean": item.mean, "min": item.min, "max": item.max, "samples": item.samples}
            for item in ev
        ]}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
