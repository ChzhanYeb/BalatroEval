"""局部参照（Oracle）策略：O1 精确 / O2 近似 / O3 贪心。

保证范围（必须与结论一起引用）：
- **O1 ``best_play``**：只对**当前手牌的出牌动作**做精确 argmax（8 张手牌 218 个候选），
  是“眼前最优”，不做全局规划、不评估弃牌；
- **O2 ``discard_ev``**：Monte Carlo 估计“弃牌后下一手 O1 分数”的均值/最小/最大，
  抽样模型与引擎真实发牌**不一致**（不读 rng_state、把 deck+discard 混池），因此是
  approximate，不是精确期望值；
- **O3 ``greedy_episode``**：O1 贪心 + 商店「能买就买第一个 / 否则离开」的参照轨迹，
  不是最优解或上界（经济决策也不做前瞻）。

与评测层的接口：
- ``score_action(state, action)`` 对 ``play`` 返回精确 ``ScoreResult``；对 ``discard`` 返回
  None（弃牌价值需 O2 近似），评测层据此把 play 决策点与 discard 决策点分开计算
  Regret（避免把“正确弃牌”记成最大 regret 的旧问题，见 methodology P0-3）。

确定性：O1 纯函数；O2 用 state 派生的确定性 seed；O3 仅通过 engine 转移（engine 确定性）。
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import combinations
from statistics import mean
from typing import Sequence

from .actions import Action, legal_discards, legal_plays
from .cards import cards_by_ids
from .engine import apply_action
from .engine import play as engine_play
from .errors import BAD_REQUEST, INVALID_STATE, InvalidActionError
from .model import Card, GameState
from .rules_version import joker_price
from .scoring import ScoreResult, score_hand

ORACLE_PRECISION_EXACT_LOCAL = "exact_local_play_argmax"


@dataclass(frozen=True, slots=True)
class BestPlay:
    """O1 单步结果：最优出牌组合、分数、完整计分结果与候选数。"""

    card_ids: tuple[str, ...]
    indices: tuple[int, ...]
    score: int
    result: ScoreResult
    candidates_evaluated: int
    precision: str = ORACLE_PRECISION_EXACT_LOCAL


def best_play(state: GameState) -> BestPlay:
    """对当前手牌的全部合法出牌组合做精确 argmax（不评估弃牌/未来）。

    Args:
        state: 必须 ``phase == 'play'``。

    Returns:
        BestPlay；同分时保留枚举顺序中的第一个（严格 ``>`` 比较）。

    Raises:
        InvalidActionError: phase 不是 play（INVALID_STATE）或没有合法动作（BAD_REQUEST）。

    确定性：纯函数，不推进状态、不写日志。
    """
    if state.phase != "play":
        raise InvalidActionError(INVALID_STATE, "O1 best_play only applies in phase='play'")
    candidates = legal_plays(state.hand)
    if not candidates:
        raise InvalidActionError(BAD_REQUEST, "no legal play actions")
    best: BestPlay | None = None
    for indices in candidates:
        cards = [state.hand[i] for i in indices]
        result = score_hand(cards, state.jokers)
        candidate = BestPlay(
            card_ids=tuple(card.card_id for card in cards),
            indices=indices,
            score=result.final_score,
            result=result,
            candidates_evaluated=len(candidates),
        )
        if best is None or candidate.score > best.score:
            best = candidate
    assert best is not None  # candidates 非空，循环至少执行一次
    return best


def score_action(state: GameState, action: Action) -> ScoreResult | None:
    """精确评估一个动作的“本步收益”。

    - ``play``：返回精确 ``ScoreResult``（与 engine 使用同一 ``score_hand``）；
    - ``discard`` / 商店动作（``choose_joker`` / ``sell_joker`` / ``reroll_shop``）：
      返回 None（弃牌价值只能用 O2 近似，商店价值是跨期资源决策，不属于单步计分，
      评测层应分别处理）。

    Raises:
        InvalidActionError: 出牌的卡牌不在当前手牌中/重复（UNKNOWN_CARD/DUPLICATE_CARD）。
    """
    if action.kind != "play":
        return None
    cards = cards_by_ids(state.hand, action.card_ids)
    return score_hand(cards, state.jokers)


@dataclass(frozen=True, slots=True)
class DiscardEV:
    """O2 对单个弃牌子集的抽样结果（近似）。"""

    card_ids: tuple[str, ...]
    indices: tuple[int, ...]
    mean: float
    min: int
    max: int
    samples: int
    precision: str = "approximate_monte_carlo"


def discard_ev(state: GameState, K: int = 50, seed: int | None = None) -> list[DiscardEV]:
    """用 Monte Carlo 估计每个弃牌子集后“下一手 O1 分数”的 EV。

    近似声明（引用时必须保留）：
    - 每个 replicate 用 state 派生的独立 ``random.Random``，不读取/推进引擎 rng_state；
    - 未看见牌池 = deck + discard_pile 混池抽样，不建模“先抽抽牌堆、空了才洗回”；
    - 本次弃掉的牌不在抽样池中（真实引擎里它们会进弃牌堆，可能在后续洗回时被抽到）。

    Args:
        state: 必须 phase='play'。
        K: 每个子集的抽样次数（>=1）。
        seed: None 时用 ``state.seed ^ blind_idx*1009 ^ steps`` 派生，保证同状态可复现。

    Returns:
        按 ``legal_discards`` 顺序的 DiscardEV 列表；无弃牌次数时返回 []。

    Raises:
        InvalidActionError: phase 不是 play 或 K < 1。
    """
    if state.phase != "play":
        raise InvalidActionError(INVALID_STATE, "O2 discard_ev only applies in phase='play'")
    if K < 1:
        raise InvalidActionError(BAD_REQUEST, "K must be >= 1")
    actions = legal_discards(state.hand, state.discards_left)
    if not actions:
        return []
    unseen = list(state.deck) + list(state.discard_pile)
    if seed is None:
        seed = state.seed ^ (state.blind_idx * 1009) ^ state.steps
    output: list[DiscardEV] = []
    for action_idx, indices in enumerate(actions):
        discarded = {state.hand[i].card_id for i in indices}
        kept = [card for card in state.hand if card.card_id not in discarded]
        kept_ids = {card.card_id for card in kept}
        candidate_pool = [card for card in unseen if card.card_id not in kept_ids]
        n_draw = min(len(indices), len(candidate_pool))
        samples: list[int] = []
        for replicate in range(K):
            rng = random.Random(seed + action_idx * 1_000_003 + replicate * 97_409)
            draw = rng.sample(candidate_pool, n_draw) if n_draw else []
            next_hand = kept + draw
            best_score = max(
                score_hand([next_hand[i] for i in combo], state.jokers).final_score
                for combo in _combos_for_hand(next_hand)
            )
            samples.append(best_score)
        output.append(DiscardEV(
            card_ids=tuple(state.hand[i].card_id for i in indices),
            indices=indices, mean=mean(samples), min=min(samples), max=max(samples),
            samples=K,
        ))
    return output


def _combos_for_hand(hand: Sequence[Card]) -> list[tuple[int, ...]]:
    """枚举 1..5 张下标组合（允许手牌 >5；不按稳定 ID 去重）。"""
    return [combo for size in range(1, min(5, len(hand)) + 1)
            for combo in combinations(range(len(hand)), size)]


@dataclass(frozen=True, slots=True)
class EpisodeReference:
    """O3 近似对局摘要（含最终金钱）。"""

    outcome: str | None
    score_by_blind: tuple[int, ...]
    total_scored: int
    steps: int
    final_money: int = 0
    precision: str = "approximate_greedy_not_global_optimum"


def greedy_shop_action(state: GameState) -> Action:
    """O3 的商店策略：能买得起第一个报价就买，否则离开（不 reroll、不卖）。

    这条策略**不是**经济最优解，只用于给出一致、可复现的参照轨迹：
    它不看利息、不比较两个报价的收益，也不为后续盲注存钱。

    Args:
        state: 必须 ``phase == 'shop'``。

    Returns:
        ``choose_joker`` 动作（买下标 0..n 或 ``None`` 离开）。
    """
    has_free_slot = len(state.jokers) < state.joker_slots
    if has_free_slot:
        for index, offer in enumerate(state.shop_options):
            if any(j.jid == offer.jid for j in state.jokers):
                continue
            if state.money >= joker_price(offer):
                return Action("choose_joker", joker_index=index)
    return Action("choose_joker", joker_index=None)


def greedy_episode(state: GameState, max_steps: int = 200) -> EpisodeReference:
    """用 O1 贪心打完整局（商店：能买就买第一个，否则离开），返回近似摘要。

    这是参照轨迹，不是最优策略；不评估弃牌、不搜索、不做经济优化。

    Raises:
        RuntimeError: 超过 max_steps（状态机不前进，暴露 bug）。
    """
    current = state
    scores: list[int] = []
    total_scored = 0
    for _ in range(max_steps):
        if current.phase == "done":
            return EpisodeReference(current.outcome, tuple(scores), total_scored,
                                    current.steps, current.money)
        if current.phase == "shop":
            current = apply_action(current, greedy_shop_action(current))[0]
            continue
        best = best_play(current)
        index = current.blind_idx
        current, result = engine_play(current, best.card_ids)
        total_scored += result.final_score
        while len(scores) <= index:
            scores.append(0)
        if index < len(scores):
            scores[index] += result.final_score
    raise RuntimeError(f"episode exceeded max_steps={max_steps}; probable transition bug")
