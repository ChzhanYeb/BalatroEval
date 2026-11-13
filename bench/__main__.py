"""命令行入口：python -m bench {demo,verify,ev}。

三个子命令的语义与退出行为：
- demo：用 O1 贪心跑一局样例对局，把逐步 history 与终局摘要打印为 JSON，并把每一步
  写成 append-only JSONL 日志（默认 data/episode.jsonl，重复运行会继续追加）；
- verify：用独立实现的暴力枚举交叉检查 O1，只证明「两条搜索路径对同一 score_hand
  口径给出相同最大分」，**不能证明计分规则符合原版 Balatro**；
- ev：估计初始手牌上每个弃牌子集的期望值（EV），默认 K=50。

退出行为（如实说明）：main 没有统一的 try/except；可预期的业务错误以未捕获异常
冒泡（打印 traceback，退出码 1），参数错误由 argparse 以退出码 2 终止。成功时只把
缩进后的 JSON 打到 stdout。
"""
from __future__ import annotations
import argparse
from itertools import combinations
import json
from pathlib import Path
import random

from .actions import legal_plays
from .engine import new_game, play, discard, choose_joker
from .oracle import best_play, discard_ev, greedy_episode
from .model import Card
from .scoring import score_hand


def verify_oracle(samples: int = 10, seed: int = 20261112) -> dict:
    """独立地暴力核验 O1：对每个随机 8 张手牌直接枚举 1..5 张组合取最大分。

    为什么说「独立」：这里用 range(1, 6) + combinations 重新写一遍枚举，不经过
    oracle.best_play → actions.legal_plays 的循环结构，避免同一个枚举 bug 被两条路径
    同时复制。但两边最终都调用 scoring.score_hand，所以本检查只能证明「两条搜索路径
    一致」，**不能证明计分规则本身正确，更不证明符合原版 Balatro**。
    参数：samples 为手牌样本数；seed 固定，结果可复现。
    checks[].candidates 每例应恒为 218（8 张手牌的 C(8,1..5)），可作枚举完整性的旁证。
    返回：可直接 json.dumps 的 dict（seed / samples / passed / checks）。
    注意：为了让状态满足 best_play 的前置条件，这里覆盖了 state.hand 却保留了
    new_game 发好的 deck，二者可能出现重复物理牌，破坏「52 张唯一牌堆」不变量；
    因为只对 hand 计分、不抽牌，检查结果不受影响，但不要把这个构造复用成完整对局。
    副作用：不写日志、不读写文件。
    """
    rng = random.Random(seed)
    deck = [Card(suit=s, rank=r) for s in range(4) for r in range(1, 14)]
    checks = []
    for i in range(samples):
        hand = rng.sample(deck, 8)
        # 复用 new_game 只是要一个合法的 GameState 外壳；hand 与 jokers 随后被覆盖。
        state = new_game(seed + i)
        state.hand = hand
        state.jokers = []
        result = best_play(state)
        brute_force = max(
            score_hand([hand[j] for j in indices], state.jokers).final_score
            for size in range(1, 6) for indices in combinations(range(len(hand)), size)
        )
        checks.append({"case": i + 1, "oracle": result.score, "brute_force": brute_force,
                       "match": result.score == brute_force, "candidates": result.candidates_evaluated})
    return {"seed": seed, "samples": samples, "passed": all(x["match"] for x in checks), "checks": checks}


def run_demo(seed: int, max_steps: int, log_path: str | None) -> dict:
    """用 O1 贪心跑一局样例对局，返回可直接 json.dumps 的摘要。

    顶层字段：seed、phase、outcome、blind_idx、total_score_in_current_blind、
    hands_left、discards_left、steps、history、log_path。
    history 每步一条：
    - play -> {action, cards, hand_type, score_delta, total_score, blind_idx, phase}；
    - shop -> {action: "choose_joker", picked, blind_idx}。
    注意：total_score 在每个盲注结束后归零，所以顶层键叫
    total_score_in_current_blind，不要把它误读成整局累计分。
    参数：log_path 为 None 时不写日志；否则每一步都追加一条 JSONL。
    副作用：写日志文件（append-only）；不修改传入的标量参数。
    """
    state = new_game(seed)
    history = []
    for _ in range(max_steps):
        if state.phase == "done":
            break
        if state.phase == "shop":
            # 先完成转移再取 jokers[-1]/blind_idx：记录的是「刚选中的 Joker」与
            # 「进入后的盲注索引」，而不是商店选项列表本身。
            state = choose_joker(state, 0, log_path=log_path)
            history.append({"action": "choose_joker", "picked": state.jokers[-1].jid,
                            "blind_idx": state.blind_idx})
            continue
        best = best_play(state)
        state, result = play(state, best.card_ids, log_path=log_path)
        # history 记录的是本次转移之后的状态（分数、盲注、阶段），不是转移前快照。
        history.append({"action": "play", "cards": list(best.card_ids), "hand_type": result.hand_type.value,
                        "score_delta": result.final_score, "total_score": state.total_score,
                        "blind_idx": state.blind_idx, "phase": state.phase})
    return {"seed": seed, "phase": state.phase, "outcome": state.outcome, "blind_idx": state.blind_idx,
            "total_score_in_current_blind": state.total_score, "hands_left": state.hands_left,
            "discards_left": state.discards_left, "steps": state.steps, "history": history,
            "log_path": log_path}


def main() -> None:
    """解析参数并分派 demo/verify/ev；成功时把结果 JSON 打到 stdout。

    退出行为：不捕获子命令异常（错误以 traceback + 退出码 1 结束），也不把结果写成
    文件；只有 demo 会按 --log 写日志。
    """
    # 固定 prog，避免以模块方式调用时 usage 里显示成 __main__.py。
    parser = argparse.ArgumentParser(prog="python -m bench", description="BalatroEval custom ruleset v1")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_demo = sub.add_parser("demo", help="run an O1-greedy sample episode")
    # 默认 seed 20261112 是项目约定的固定值：与 spec_revision 日期 2026-11-12 的写法
    # 一致（文档未单列出处），tests/ 与 data/ 下 local 产物都用它；改它会让样例失效。
    p_demo.add_argument("--seed", type=int, default=20261112)
    p_demo.add_argument("--max-steps", type=int, default=50)
    p_demo.add_argument("--log", default="data/episode.jsonl")
    p_verify = sub.add_parser("verify", help="cross-check O1 against an independent brute-force max")
    p_verify.add_argument("--samples", type=int, default=10)
    p_verify.add_argument("--seed", type=int, default=20261112)
    p_ev = sub.add_parser("ev", help="estimate discard EV for the initial hand")
    p_ev.add_argument("--seed", type=int, default=20261112)
    p_ev.add_argument("-k", type=int, default=50)
    args = parser.parse_args()

    if args.cmd == "demo":
        result = run_demo(args.seed, args.max_steps, args.log)
    elif args.cmd == "verify":
        result = verify_oracle(args.samples, args.seed)
    else:
        # dest="cmd" 是 required=True，所以走到这里只可能是 ev。
        state = new_game(args.seed)
        # O2 的抽样 seed 由 discard_ev 内部从 state 派生，这里不额外传入 --seed。
        ev = discard_ev(state, K=args.k)
        result = {"seed": args.seed, "K": args.k, "actions": [
            {"cards": list(x.card_ids), "indices": list(x.indices), "mean": x.mean, "min": x.min,
             "max": x.max, "samples": x.samples} for x in ev
        ]}
    # ensure_ascii=False 保留中文可读；indent=2 便于人工核对与 diff。
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
