"""状态初始化与状态推进：Ante 1 子集规则的唯一权威实现。

设计原则：
- **纯函数式转移**：``new_game`` / ``play`` / ``discard`` / ``choose_joker`` 都不修改
  入参，先 ``deepcopy`` 再改，最后返回新状态；日志/轨迹由 ``evaluation.trace`` 记录，
  规则层不做文件 IO。
- **规则常量集中在** ``bench.rules_version``：目标分 300/450/600、4 手/4 弃、8 张手牌、
  5 个 Joker 槽位都从 ``Ruleset`` 取，不在本模块散落魔法数字。
- **随机性只来自** ``GameState.rng_state``：洗牌与商店抽样都先还原、再写回；相同
  state + 相同动作 ⇒ 相同结果。
- **显式失败**：非法动作抛 ``InvalidActionError``，不静默忽略；Boss 效果等排除机制
  不会被偷偷跳过（见 ``boss_effect`` 字段与场景校验）。

未验证/子集边界（不得弱化）：
- 跨盲注手牌处理：本实现把上一盲注剩余手牌放入弃牌堆、从抽牌堆补满（必要时洗回弃牌堆）；
  vanilla 的精确行为未实测（``Ruleset.unverified``）。
- Boss Blind 仅按目标分建模；Ante 1 的真实 Boss 效果均未实现。
- 商店默认关闭；``shop_enabled=True`` 是 benchmark 扩展（免费 3 选 1），不是 vanilla。
"""
from __future__ import annotations

import copy
import random
from typing import Sequence

from .actions import Action
from .cards import cards_by_ids, remaining_deck, standard_deck
from .errors import (
    BAD_REQUEST,
    DUPLICATE_CARD,
    EPISODE_DONE,
    INVALID_STATE,
    NO_RESOURCE,
    NOT_ALLOWED,
    UNKNOWN_CARD,
    InvalidActionError,
)
from .jokers import JOKER_CATALOG, CATALOG_BY_ID
from .model import Card, GameState, Joker
from .rules_version import VANILLA_SUBSET_V1, Ruleset
from .rng import encode_state, restore_rng
from .scoring import ScoreResult, score_hand


def _check_state(state: GameState) -> None:
    """状态不变量自检（防御性，不应由 Agent 输入触发）。"""
    if state.deck_total != 52:
        raise InvalidActionError(
            INVALID_STATE,
            f"card conservation violated: hand+deck+discard={state.deck_total}, expected 52",
            {"total": state.deck_total},
        )
    if len(state.jokers) > state.joker_slots:
        raise InvalidActionError(INVALID_STATE, "jokers exceed slots")


def _draw(state: GameState, count: int) -> list[Card]:
    """原地补牌：先抽抽牌堆；抽空后把弃牌堆洗回；返回抽到的牌。

    Args:
        state: 将被修改的状态（调用方保证这是副本）。
        count: 期望抽牌数；牌堆不足时可能少抽。

    Returns:
        按抽取顺序的牌列表。

    副作用：修改 ``state.deck`` / ``discard_pile`` / ``rng_state``。仅当抽牌堆为空且
    弃牌堆非空时消耗随机数（洗牌），因此同 seed 的牌序可复现。
    """
    drawn: list[Card] = []
    while count > 0:
        if not state.deck:
            if not state.discard_pile:
                break
            rng = restore_rng(state.rng_state)
            state.deck = list(state.discard_pile)
            state.discard_pile.clear()
            rng.shuffle(state.deck)
            state.rng_state = encode_state(rng)
        take = min(count, len(state.deck))
        drawn.extend(state.deck[:take])
        del state.deck[:take]
        count -= take
    return drawn


def _refill(state: GameState) -> None:
    """把手牌补到 ``hand_size``（不改变手牌顺序，抽到的牌追加在尾部）。"""
    missing = state.hand_size - len(state.hand)
    if missing > 0:
        state.hand.extend(_draw(state, missing))


def _blind_spec(ruleset: Ruleset, blind_idx: int):
    return ruleset.blind(blind_idx)


def _start_blind(state: GameState, blind_idx: int, ruleset: Ruleset) -> None:
    """进入指定盲注：重置资源/分数/目标，并把上一盲注手牌换成一新手牌。

    顺序：先把当前手牌放入弃牌堆 → 重置资源与目标 → 补满手牌。这样弃牌堆里包含
    “上一盲注未打出的牌”，牌堆不足时会在洗回时参与下一次抽取（确定性行为）。
    """
    spec = _blind_spec(ruleset, blind_idx)
    state.blind_idx = blind_idx
    state.blind_kind = spec.kind
    state.boss_effect = spec.effect
    state.target = spec.target
    state.total_score = 0
    state.hands_left = ruleset.hands_per_blind
    state.discards_left = ruleset.discards_per_blind
    state.shop_options = []
    state.phase = "play"
    state.outcome = None
    if state.hand:
        state.discard_pile.extend(state.hand)
        state.hand = []
    _refill(state)


def new_game(
    seed: int,
    *,
    ruleset: Ruleset = VANILLA_SUBSET_V1,
    hand_ids: Sequence[str] | None = None,
    joker_ids: Sequence[str] = (),
    deck_order: Sequence[str] | None = None,
) -> GameState:
    """构造一局初始状态（Ante 1 Small Blind，phase=play）。

    Args:
        seed: 随机种子；决定洗牌顺序与商店抽样（本项目内可复现，不承诺与真游戏同局面）。
        ruleset: 规则集；默认 ``VANILLA_SUBSET_V1``。
        hand_ids: 可选，指定初始手牌（稳定 ID，按给定顺序）。用于决策点场景；
            缺省时从洗好的 52 张牌顶部发 ``hand_size`` 张。
        joker_ids: 可选，初始拥有的 Joker（稳定 ID，按槽位顺序）。
        deck_order: 可选，显式指定抽牌堆顺序（仅用于回放/测试；必须与 hand 互补且
            合计 52 张）。通常不需要。

    Returns:
        GameState。

    Raises:
        InvalidActionError: hand/joker/deck 参数非法（未知 ID、重复、超过槽位/张数）。

    确定性：相同参数恒返回相同状态（含 rng_state）。
    """
    if not isinstance(seed, int):
        raise InvalidActionError(BAD_REQUEST, "seed must be an integer")
    if ruleset.rules_version != VANILLA_SUBSET_V1.rules_version:
        raise InvalidActionError(
            BAD_REQUEST,
            f"unsupported ruleset version: {ruleset.rules_version!r}",
            {"supported": VANILLA_SUBSET_V1.rules_version},
        )
    rng = random.Random(seed)
    jokers: list[Joker] = []
    for jid in joker_ids:
        try:
            jokers.append(CATALOG_BY_ID[jid])
        except KeyError as exc:
            raise InvalidActionError(UNKNOWN_CARD, f"unknown joker id: {jid!r}",
                                     {"joker_id": jid}) from exc
    if len(jokers) > ruleset.joker_slots:
        raise InvalidActionError(BAD_REQUEST, "too many starting jokers",
                                 {"count": len(jokers), "slots": ruleset.joker_slots})

    if hand_ids is None:
        deck = standard_deck()
        rng.shuffle(deck)
        hand, deck = deck[: ruleset.hand_size], deck[ruleset.hand_size:]
    else:
        hand_list = list(hand_ids)
        hand = cards_by_ids(standard_deck(), hand_list)
        if len(hand) > ruleset.hand_size:
            raise InvalidActionError(BAD_REQUEST, "hand exceeds hand_size",
                                     {"count": len(hand)})
        deck = remaining_deck(c.card_id for c in hand)
        if deck_order is not None:
            deck = cards_by_ids(standard_deck(), list(deck_order))
            if {c.card_id for c in deck} & {c.card_id for c in hand}:
                raise InvalidActionError(BAD_REQUEST, "deck_order overlaps hand")
            if len(deck) + len(hand) != 52:
                raise InvalidActionError(BAD_REQUEST, "hand+deck must total 52")
        else:
            rng.shuffle(deck)

    state = GameState(
        rules_version=ruleset.rules_version,
        ante=ruleset.ante,
        blind_idx=0,
        blind_kind=ruleset.blind(0).kind,
        boss_effect=ruleset.blind(0).effect,
        target=ruleset.blind(0).target,
        joker_slots=ruleset.joker_slots,
        hand_size=ruleset.hand_size,
        shop_enabled=ruleset.shop_enabled,
        total_score=0,
        hands_left=ruleset.hands_per_blind,
        discards_left=ruleset.discards_per_blind,
        steps=0,
        phase="play",
        outcome=None,
        hand=hand,
        deck=deck,
        discard_pile=[],
        jokers=jokers,
        shop_options=[],
        seed=seed,
        rng_state=encode_state(rng),
    )
    _check_state(state)
    return state


def _create_shop_options(state: GameState, count: int = 3) -> None:
    """生成 count 个互不重复的商店候选（排除已拥有）；修改 rng_state。"""
    owned = {j.jid for j in state.jokers}
    available = [j for j in JOKER_CATALOG if j.jid not in owned]
    rng = restore_rng(state.rng_state)
    selected = rng.sample(available, min(count, len(available))) if available else []
    state.shop_options = list(selected)
    state.rng_state = encode_state(rng)


def _after_play(state: GameState, ruleset: Ruleset) -> None:
    """出牌后的阶段结算：达标 → 过盲注/胜利；否则手牌耗尽 → 失败。"""
    if state.total_score >= state.target:
        if state.blind_idx >= 2:
            state.phase = "done"
            state.outcome = "win"
            state.shop_options = []
            return
        if ruleset.shop_enabled:
            state.phase = "shop"
            _create_shop_options(state)
            return
        _start_blind(state, state.blind_idx + 1, ruleset)
        return
    if state.hands_left == 0:
        state.phase = "done"
        state.outcome = "loss"
        state.shop_options = []


def play(state: GameState, card_ids: Sequence[str]) -> tuple[GameState, ScoreResult]:
    """打出一组牌：计分 → 扣手数 → 补牌 → 打出的牌入弃牌堆 → 阶段结算。

    Args:
        state: 变更前状态（不会被修改）。
        card_ids: 1–5 个稳定卡牌 ID，必须都在当前手牌中且不重复。

    Returns:
        (新状态, ScoreResult)。

    Raises:
        InvalidActionError: phase 不是 play（INVALID_STATE）、已结束（EPISODE_DONE）、
            张数越界/重复（BAD_REQUEST/DUPLICATE_CARD）、未知 ID（UNKNOWN_CARD）、
            无出牌次数（NO_RESOURCE）。

    确定性：给定相同 state 与 card_ids，结果唯一。
    """
    if state.phase == "done":
        raise InvalidActionError(EPISODE_DONE, "episode is already finished")
    if state.phase != "play":
        raise InvalidActionError(INVALID_STATE, f"play requires phase='play', got {state.phase!r}")
    if state.hands_left <= 0:
        raise InvalidActionError(NO_RESOURCE, "no hands remaining")
    ids = list(card_ids)
    if not 1 <= len(ids) <= 5:
        raise InvalidActionError(BAD_REQUEST, "play action must select 1..5 cards",
                                 {"count": len(ids)})
    if len(set(ids)) != len(ids):
        raise InvalidActionError(DUPLICATE_CARD, "play action contains duplicate card ids")
    selected = cards_by_ids(state.hand, ids)

    after = copy.deepcopy(state)
    result = score_hand(selected, after.jokers)

    after.total_score += result.final_score
    after.hands_left -= 1
    after.steps += 1
    selected_ids = set(ids)
    after.hand = [card for card in after.hand if card.card_id not in selected_ids]
    _refill(after)
    after.discard_pile.extend(selected)
    _after_play(after, _ruleset_like(after))
    _check_state(after)
    return after, result


def _ruleset_like(state: GameState) -> Ruleset:
    """从状态重建规则集（用于转移函数保持无全局依赖）。

    只覆盖状态里携带的开关（shop_enabled）；常量表仍来自规则定义，避免状态被篡改。
    """
    from dataclasses import replace

    return replace(VANILLA_SUBSET_V1, shop_enabled=state.shop_enabled)


def discard(state: GameState, card_ids: Sequence[str]) -> GameState:
    """弃掉一组牌并补满手牌：消耗 1 次 discard，不改变分数与阶段。

    Args:
        state: 变更前状态（不会被修改）。
        card_ids: 1–5 个稳定卡牌 ID。

    Returns:
        新状态。

    Raises:
        InvalidActionError: phase 非 play、无弃牌次数（NO_RESOURCE）、参数非法。
    """
    if state.phase == "done":
        raise InvalidActionError(EPISODE_DONE, "episode is already finished")
    if state.phase != "play":
        raise InvalidActionError(INVALID_STATE, f"discard requires phase='play', got {state.phase!r}")
    if state.discards_left <= 0:
        raise InvalidActionError(NO_RESOURCE, "no discards remaining")
    ids = list(card_ids)
    if not 1 <= len(ids) <= 5:
        raise InvalidActionError(BAD_REQUEST, "discard action must select 1..5 cards",
                                 {"count": len(ids)})
    if len(set(ids)) != len(ids):
        raise InvalidActionError(DUPLICATE_CARD, "discard action contains duplicate card ids")
    selected = cards_by_ids(state.hand, ids)

    after = copy.deepcopy(state)
    after.discards_left -= 1
    after.steps += 1
    selected_ids = set(ids)
    after.hand = [card for card in after.hand if card.card_id not in selected_ids]
    _refill(after)
    after.discard_pile.extend(selected)
    _check_state(after)
    return after


def choose_joker(state: GameState, index: int | None) -> GameState:
    """商店扩展动作：选择第 index 个候选（None=跳过）并进入下一盲注。

    Args:
        state: 必须处于 phase='shop'（仅当 ``shop_enabled``）。
        index: 候选下标，或 None 表示跳过。

    Returns:
        新状态（下一盲注 play 阶段）。

    Raises:
        InvalidActionError: 商店未启用（NOT_ALLOWED）、阶段不符（INVALID_STATE）、
            下标越界（BAD_REQUEST）、槽位已满（NO_RESOURCE）、重复拥有（NOT_ALLOWED）。
    """
    if not state.shop_enabled:
        raise InvalidActionError(NOT_ALLOWED, "shop is disabled in this ruleset",
                                 {"extension": "free_joker_choice"})
    if state.phase != "shop":
        raise InvalidActionError(INVALID_STATE, f"choose_joker requires phase='shop', got {state.phase!r}")
    after = copy.deepcopy(state)
    if index is not None:
        if not 0 <= index < len(after.shop_options):
            raise InvalidActionError(BAD_REQUEST, "shop option index out of range",
                                     {"index": index, "options": len(after.shop_options)})
        chosen = after.shop_options[index]
        if len(after.jokers) >= after.joker_slots:
            raise InvalidActionError(NO_RESOURCE, "all Joker slots are occupied")
        if any(j.jid == chosen.jid for j in after.jokers):
            raise InvalidActionError(NOT_ALLOWED, "duplicate Joker ownership is not allowed")
        after.jokers.append(chosen)
    after.steps += 1
    _start_blind(after, after.blind_idx + 1, _ruleset_like(after))
    _check_state(after)
    return after


def apply_action(state: GameState, action: Action) -> tuple[GameState, ScoreResult | None]:
    """统一动作入口：把 ``Action`` 分派到 play/discard/choose_joker。

    Returns:
        (新状态, ScoreResult 或 None)。

    Raises:
        InvalidActionError: 动作种类与阶段不符等（见各转移函数）。
    """
    if action.kind == "play":
        after, result = play(state, action.card_ids)
        return after, result
    if action.kind == "discard":
        return discard(state, action.card_ids), None
    if action.kind == "choose_joker":
        return choose_joker(state, action.joker_index), None
    raise InvalidActionError(BAD_REQUEST, f"unsupported action kind: {action.kind!r}")
