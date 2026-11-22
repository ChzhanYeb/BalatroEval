"""状态初始化与状态推进：Ante 1 子集规则的唯一权威实现。

设计原则：
- **纯函数式转移**：``new_game`` / ``play`` / ``discard`` / ``choose_joker`` /
  ``sell_joker`` / ``reroll_shop`` 都不修改入参，先 ``deepcopy`` 再改，最后返回新状态；
  日志/轨迹由 ``evaluation.trace`` 记录，规则层不做文件 IO。
- **规则常量集中在** ``bench.rules_version``：目标分 300/450/600、4 手/4 弃、8 张手牌、
  5 个 Joker 槽位、起始 $4、奖励 $3/$4/$5、利息每 $5 上限 $5、商店价目表都从
  ``Ruleset`` 取，不在本模块散落魔法数字。
- **随机性只来自** ``GameState.rng_state``：洗牌与商店抽样都先还原、再写回；相同
  state + 相同动作 ⇒ 相同结果。
- **显式失败**：非法动作抛 ``InvalidActionError``，不静默忽略；Boss 效果等排除机制
  不会被偷偷跳过（见 ``boss_effect`` 字段与场景校验）。

经济（v2）：
- 盲注通关时一次性结算「奖励 + 剩余手数 + 未用弃牌 + 利息」写入 ``money``；
- Small/Big 之后进商店，可买入 / 卖出 / reroll / 离开；Boss 通关即 ``win``，不进商店；
- 金钱**跨盲注保留**（这正是长线资源分配的唯一载体），手数/弃牌仍每盲注重置。

未验证/子集边界（不得弱化）：
- 跨盲注手牌处理：本实现把上一盲注剩余手牌放入弃牌堆、从抽牌堆补满（必要时洗回弃牌堆）；
  vanilla 的精确行为未实测（``Ruleset.unverified``）。
- Boss Blind 仅按目标分建模；Ante 1 的真实 Boss 效果均未实现。
- 利息按**入账前**金额计算；商店价格按稀有度取固定中值、候选均匀抽样；这些口径
  均列入 ``Ruleset.unverified``，不得当作已对齐事实。
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
from .rules_version import VANILLA_SUBSET_V1, Ruleset, joker_price, sell_value
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

    **不改动 money**：金钱是跨盲注资源（这正是经济层存在的意义）。只把
    ``last_payout``（上一盲注的结算明细）清空、把 ``reroll_cost`` 重置为基准价。
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
    state.last_payout = None
    state.reroll_cost = ruleset.reroll_base_cost
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
        money=ruleset.starting_money,
        reroll_cost=ruleset.reroll_base_cost,
        last_payout=None,
        seed=seed,
        rng_state=encode_state(rng),
    )
    _check_state(state)
    return state


def _blind_payout(state: GameState, ruleset: Ruleset) -> dict:
    """结算一次通关奖励并写入 ``state.money``，返回明细。

    口径（v2，整数、无随机）::

        blind_reward = BlindSpec.reward_money        # Small 3 / Big 4 / Boss 5
        hand_bonus   = hands_left   * hand_bonus     # 每剩 1 手 +$1
        discard_bonus= discards_left* discard_bonus  # 每未用 1 弃牌 +$1
        interest     = min(money // 5, 5)            # 用**入账前**的 money 计算
        total        = blind_reward + hand_bonus + discard_bonus + interest

    边界：利息用入账前的金额（原版顺序未实测，见 ``Ruleset.unverified``）；
    本函数只改 ``state.money``，不改分数与阶段。

    Args:
        state: 将被修改的状态（调用方保证是副本）。
        ruleset: 规则集（提供奖励/利息常量）。

    Returns:
        明细 dict：``blind_reward`` / ``hand_bonus`` / ``discard_bonus`` / ``interest`` /
        ``total`` / ``money_before`` / ``money_after``。
    """
    spec = ruleset.blind(state.blind_idx)
    money_before = state.money
    blind_reward = spec.reward_money
    hand_bonus = state.hands_left * ruleset.hand_bonus
    discard_bonus = state.discards_left * ruleset.discard_bonus
    interest = min(money_before // ruleset.interest_per, ruleset.interest_cap)
    total = blind_reward + hand_bonus + discard_bonus + interest
    state.money = money_before + total
    return {
        "blind_kind": spec.kind,
        "blind_reward": blind_reward,
        "hand_bonus": hand_bonus,
        "discard_bonus": discard_bonus,
        "interest": interest,
        "total": total,
        "money_before": money_before,
        "money_after": state.money,
    }


def draw_shop_offers(state: GameState, ruleset: Ruleset) -> None:
    """抽一批商店报价（原地修改 ``state.shop_options``；消耗 ``rng_state``）。

    规则（v2）：候选池 = 8 个具名 Joker 中**尚未拥有**的那些；用 ``rng.sample``
    **均匀**抽 ``ruleset.shop_offer_count`` 个。原版是带稀有度权重的卡池，本子集
    不建模权重（见 ``Ruleset.unverified: shop_offer_pool_uniform_no_rarity_weights``）。

    Args:
        state: 将被修改的状态（调用方保证是副本）。
        ruleset: 规则集（提供报价数量）。
    """
    owned = {j.jid for j in state.jokers}
    available = [j for j in JOKER_CATALOG if j.jid not in owned]
    rng = restore_rng(state.rng_state)
    count = min(ruleset.shop_offer_count, len(available))
    state.shop_options = list(rng.sample(available, count)) if count else []
    state.rng_state = encode_state(rng)


def open_shop(state: GameState, ruleset: Ruleset) -> None:
    """打开商店：``phase='shop'``、重置 reroll 价、抽一批报价。

    只在 Small/Big 通关后调用（Boss 通关即 ``win``，不再进商店）。卖掉的 Joker
    会回到候选池，因此可能在后续 reroll 中再次出现（本子集不维护淘汰池）。
    """
    state.phase = "shop"
    state.reroll_cost = ruleset.reroll_base_cost
    draw_shop_offers(state, ruleset)


def _after_play(state: GameState, ruleset: Ruleset) -> None:
    """出牌后的阶段结算：达标 → 结算金钱 → 商店/下一盲注/胜利；否则手牌耗尽 → 失败。"""
    if state.total_score >= state.target:
        state.last_payout = _blind_payout(state, ruleset)
        if state.blind_idx >= 2:
            state.phase = "done"
            state.outcome = "win"
            state.shop_options = []
            return
        if ruleset.shop_enabled:
            open_shop(state, ruleset)
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
    """商店动作：买入第 index 个报价（None = 离开商店，进入下一盲注）。

    Args:
        state: 必须处于 phase='shop'。
        index: 报价下标，或 None 表示离开商店。

    Returns:
        新状态。买入后**仍停在 shop 阶段**（还能继续买/卖/reroll，最后显式离开）；
        离开后进入下一盲注的 play 阶段。

    Raises:
        InvalidActionError: 商店未启用（NOT_ALLOWED）、阶段不符（INVALID_STATE）、
            下标越界（BAD_REQUEST）、槽位已满或钱不够（NO_RESOURCE）、重复拥有
            （NOT_ALLOWED）。
    """
    if not state.shop_enabled:
        raise InvalidActionError(NOT_ALLOWED, "shop is disabled in this ruleset")
    if state.phase != "shop":
        raise InvalidActionError(INVALID_STATE, f"choose_joker requires phase='shop', got {state.phase!r}")
    after = copy.deepcopy(state)
    if index is None:
        after.steps += 1
        _start_blind(after, after.blind_idx + 1, _ruleset_like(after))
        _check_state(after)
        return after
    if not 0 <= index < len(after.shop_options):
        raise InvalidActionError(BAD_REQUEST, "shop option index out of range",
                                 {"index": index, "options": len(after.shop_options)})
    chosen = after.shop_options[index]
    price = joker_price(chosen)
    if len(after.jokers) >= after.joker_slots:
        raise InvalidActionError(NO_RESOURCE, "all Joker slots are occupied",
                                 {"slots": after.joker_slots})
    if any(j.jid == chosen.jid for j in after.jokers):
        raise InvalidActionError(NOT_ALLOWED, "duplicate Joker ownership is not allowed")
    if after.money < price:
        raise InvalidActionError(NO_RESOURCE, "not enough money to buy this Joker",
                                 {"money": after.money, "price": price, "joker_id": chosen.jid})
    after.money -= price
    after.jokers.append(chosen)
    del after.shop_options[index]
    after.steps += 1
    _check_state(after)
    return after


def sell_joker(state: GameState, index: int) -> GameState:
    """卖出第 index 个已拥有的 Joker：返还 ``max(1, price // 2)``，腾出槽位。

    Args:
        state: 必须处于 phase='shop'（原版也只在商店界面能卖）。
        index: Joker 槽位下标（0 基，按槽位顺序）。

    Returns:
        新状态（phase 仍为 shop）。

    Raises:
        InvalidActionError: 阶段不符（INVALID_STATE）、下标越界（BAD_REQUEST）。
    """
    if state.phase != "shop":
        raise InvalidActionError(INVALID_STATE, f"sell_joker requires phase='shop', got {state.phase!r}")
    if not 0 <= index < len(state.jokers):
        raise InvalidActionError(BAD_REQUEST, "joker slot index out of range",
                                 {"index": index, "jokers": len(state.jokers)})
    after = copy.deepcopy(state)
    sold = after.jokers.pop(index)
    after.money += sell_value(sold)
    after.steps += 1
    _check_state(after)
    return after


def reroll_shop(state: GameState) -> GameState:
    """花 ``reroll_cost`` 换一批商店报价；同一商店内每次 reroll 价格 +$1。

    Args:
        state: 必须处于 phase='shop'。

    Returns:
        新状态（phase 仍为 shop，``reroll_cost`` 已涨价）。

    Raises:
        InvalidActionError: 阶段不符（INVALID_STATE）、钱不够（NO_RESOURCE）。
    """
    if state.phase != "shop":
        raise InvalidActionError(INVALID_STATE, f"reroll_shop requires phase='shop', got {state.phase!r}")
    if state.money < state.reroll_cost:
        raise InvalidActionError(NO_RESOURCE, "not enough money to reroll",
                                 {"money": state.money, "reroll_cost": state.reroll_cost})
    after = copy.deepcopy(state)
    after.money -= after.reroll_cost
    after.reroll_cost += _ruleset_like(after).reroll_increment
    draw_shop_offers(after, _ruleset_like(after))
    after.steps += 1
    _check_state(after)
    return after


def apply_action(state: GameState, action: Action) -> tuple[GameState, ScoreResult | None]:
    """统一动作入口：把 ``Action`` 分派到 play/discard/choose_joker/sell_joker/reroll_shop。

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
    if action.kind == "sell_joker":
        if action.joker_index is None:  # 防御性：Action 构造已拒绝 None
            raise InvalidActionError(BAD_REQUEST, "sell_joker requires joker_index")
        return sell_joker(state, action.joker_index), None
    if action.kind == "reroll_shop":
        return reroll_shop(state), None
    raise InvalidActionError(BAD_REQUEST, f"unsupported action kind: {action.kind!r}")
