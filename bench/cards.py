"""标准牌组构造与稳定卡牌 ID 查找。

职责：
- 生成确定顺序的 52 张标准牌（4 花色 × 13 点数）；
- 缓存 ``card_id -> Card`` 映射；
- 按稳定 ID 从手牌/牌堆取牌（动作回放基础）；
- 为场景初始化构造“扣除手牌后的剩余牌堆”。

不变量：
- 本模块不含随机性；洗牌只发生在 ``bench.engine`` 且只使用 ``state.rng_state``。
- 标准牌组内 ``card_id`` 唯一；重复 ID 会被 ``cards_by_ids`` 显式拒绝。
- 所有函数是纯函数，不修改入参。
"""
from __future__ import annotations

from typing import Iterable, Sequence

from .errors import DUPLICATE_CARD, UNKNOWN_CARD, InvalidActionError
from .model import Card, card_from_id

# 52 张标准牌：外层花色 0..3，内层点数 1..13，顺序固定。
STANDARD_DECK_ORDER: tuple[Card, ...] = tuple(
    Card(suit=suit, rank=rank) for suit in range(4) for rank in range(1, 14)
)
CARD_BY_ID: dict[str, Card] = {card.card_id: card for card in STANDARD_DECK_ORDER}


def standard_deck() -> list[Card]:
    """返回 52 张互不相同标准牌的新列表（顺序固定：花色优先、点数升序）。

    Returns:
        list[Card]，长度 52；调用方可安全 shuffle（Card 不可变）。
    """
    return list(STANDARD_DECK_ORDER)


def card_from_stable_id(card_id: str) -> Card:
    """按稳定 ID 取标准牌；未知 ID 抛 ``InvalidActionError(UNKNOWN_CARD)``。

    Args:
        card_id: 形如 ``c1s``（黑桃 A）、``c10h``（红心 10）、``c13c``（梅花 K）。

    Raises:
        InvalidActionError: 格式非法或不在标准 52 张内。
    """
    try:
        return CARD_BY_ID[card_id]
    except KeyError as exc:
        try:
            card = card_from_id(card_id)
        except ValueError:
            raise InvalidActionError(UNKNOWN_CARD, f"unknown card id: {card_id!r}",
                                     {"card_id": card_id}) from exc
        raise InvalidActionError(
            UNKNOWN_CARD, f"card id is not part of the standard 52-card deck: {card_id!r}",
            {"card_id": card_id},
        ) from exc


def cards_by_ids(cards: Sequence[Card], card_ids: Iterable[str]) -> list[Card]:
    """按稳定 ID 从查找池中取牌，保持请求顺序。

    Args:
        cards: 查找池（通常是当前手牌）。
        card_ids: 稳定卡牌 ID 序列。

    Returns:
        与请求等长、同序的 Card 列表。

    Raises:
        InvalidActionError: 含未知 ID（UNKNOWN_CARD）或重复 ID（DUPLICATE_CARD）。

    为什么拒绝未知/重复：动作回放要求“一个动作恰好对应一组确定的牌”；静默忽略未知 ID
    会让日志与回放对不上，重复 ID 会让同一张牌被计分两次。
    """
    wanted = list(card_ids)
    by_id = {card.card_id: card for card in cards}
    missing = sorted({cid for cid in wanted if cid not in by_id})
    if missing:
        raise InvalidActionError(UNKNOWN_CARD, f"unknown card ids: {missing}", {"card_ids": missing})
    if len(set(wanted)) != len(wanted):
        raise InvalidActionError(DUPLICATE_CARD, "action contains duplicate stable card ids",
                                 {"card_ids": wanted})
    return [by_id[cid] for cid in wanted]


def combo_ids(cards: Sequence[Card]) -> tuple[str, ...]:
    """把一组牌规范化为“字典序排序后的稳定 ID 元组”（等价动作比较键）。"""
    return tuple(sorted(card.card_id for card in cards))


def remaining_deck(excluded_ids: Iterable[str]) -> list[Card]:
    """返回标准 52 张中排除指定 ID 后的剩余牌（保持 ``STANDARD_DECK_ORDER``）。

    Args:
        excluded_ids: 已分配给手牌/弃牌堆的卡牌 ID。

    Returns:
        剩余 Card 列表；若 excluded 含非标准 ID 则抛 ``InvalidActionError``。

    Raises:
        InvalidActionError: 未知 ID 或重复 ID。
    """
    excluded = list(excluded_ids)
    if len(set(excluded)) != len(excluded):
        raise InvalidActionError(DUPLICATE_CARD, "duplicate ids in excluded set",
                                 {"card_ids": excluded})
    for cid in excluded:
        if cid not in CARD_BY_ID:
            raise InvalidActionError(UNKNOWN_CARD, f"unknown card id: {cid!r}", {"card_id": cid})
    excluded_set = set(excluded)
    return [card for card in STANDARD_DECK_ORDER if card.card_id not in excluded_set]
