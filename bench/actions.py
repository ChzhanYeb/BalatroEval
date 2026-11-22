"""合法动作枚举与动作值对象。

动作种类（v2 经济子集）：
- ``play``：打出 1–5 张手牌（消耗 1 次 hand）；
- ``discard``：弃掉 1–5 张手牌（消耗 1 次 discard，随后补牌）；
- ``choose_joker``：**仅 shop 阶段**（Small/Big 之后）。``joker_index=i`` 表示花
  money 买下第 i 个报价；``joker_index=None`` 表示**离开商店**、进入下一盲注；
- ``sell_joker``：**仅 shop 阶段**。卖出第 ``joker_index`` 个已拥有的 Joker，返还半价
  （最低 $1），腾出槽位；
- ``reroll_shop``：**仅 shop 阶段**。花 ``reroll_cost`` 换一批报价，价格 +$1；
- ``advance``：保留给未来“显式阶段推进”使用；当前环境不需要（自动推进）。

不变量：
- 出牌/弃牌的候选数只取决于手牌张数：8 张时 ``C(8,1..5)=218``；
- 枚举顺序固定（先张数、后组合字典序），Oracle 穷举与测试依赖该顺序；
- 动作身份以稳定卡牌 ID 为准；手牌下标只作当次快照；
- ``Action.code`` 使用**排序后的 ID**（canonical），修复旧实现“选择顺序不同 → code
  不同”的问题；回放与去重一律用 code。
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Literal, Sequence

from .errors import BAD_REQUEST, InvalidActionError
from .model import Card, GameState
from .rules_version import joker_price

ActionKind = Literal["play", "discard", "choose_joker", "sell_joker", "reroll_shop", "advance"]

_ACTION_KINDS = ("play", "discard", "choose_joker", "sell_joker", "reroll_shop", "advance")


@dataclass(frozen=True, slots=True)
class Action:
    """一个可回放的动作。

    Args:
        kind: ``play`` / ``discard`` / ``choose_joker`` / ``sell_joker`` /
            ``reroll_shop`` / ``advance``。
        card_ids: 出牌/弃牌的稳定卡牌 ID 元组（选择顺序保留展示，code 会排序）。
        hand_indices_snapshot: 动作发生时的 0 基手牌下标快照（仅展示/审计）。
        joker_index: ``choose_joker`` 的报价下标（None = 离开商店）；``sell_joker``
            的被卖 Joker 槽位下标。

    Raises:
        InvalidActionError: kind 非法，card_ids/张数不合法，或缺少所需下标。
    """

    kind: ActionKind
    card_ids: tuple[str, ...] = ()
    hand_indices_snapshot: tuple[int, ...] = ()
    joker_index: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in _ACTION_KINDS:
            raise InvalidActionError(BAD_REQUEST, f"invalid action kind: {self.kind!r}")
        if self.kind in ("play", "discard"):
            if not 1 <= len(self.card_ids) <= 5:
                raise InvalidActionError(
                    BAD_REQUEST, "card action must select 1..5 cards",
                    {"count": len(self.card_ids)},
                )
            if len(set(self.card_ids)) != len(self.card_ids):
                raise InvalidActionError(BAD_REQUEST, "card action contains duplicate ids")
        elif self.card_ids:
            raise InvalidActionError(BAD_REQUEST, f"{self.kind} action cannot carry card ids")
        if self.kind == "sell_joker" and self.joker_index is None:
            raise InvalidActionError(BAD_REQUEST, "sell_joker requires joker_index")
        if self.kind in ("choose_joker", "sell_joker") and self.joker_index is not None:
            if self.joker_index < 0:
                raise InvalidActionError(BAD_REQUEST, "joker_index must be >= 0")

    @property
    def code(self) -> str:
        """canonical 动作编码：``play:c1s,c2h``（ID 排序，去重键稳定）。"""
        if self.kind in ("play", "discard"):
            return f"{self.kind}:" + ",".join(sorted(self.card_ids))
        if self.kind == "choose_joker":
            return "choose_joker:" + ("leave" if self.joker_index is None else f"buy:{self.joker_index}")
        if self.kind == "sell_joker":
            return f"sell_joker:{self.joker_index}"
        if self.kind == "reroll_shop":
            return "reroll_shop"
        return "advance"

    def to_dict(self) -> dict:
        """导出 JSON dict（``card_ids`` 保留选择顺序，另给 ``canonical_code``）。"""
        return {
            "kind": self.kind,
            "card_ids": list(self.card_ids),
            "hand_indices_snapshot": list(self.hand_indices_snapshot),
            "joker_index": self.joker_index,
            "code": self.code,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Action":
        """从工具层/轨迹层的 dict 还原动作。

        Raises:
            InvalidActionError: 缺字段/类型错。
        """
        if not isinstance(data, dict):
            raise InvalidActionError(BAD_REQUEST, "action must be an object")
        kind = data.get("kind")
        if kind in ("play", "discard"):
            ids = data.get("card_ids")
            if not isinstance(ids, (list, tuple)):
                raise InvalidActionError(BAD_REQUEST, "card_ids must be a list")
            return cls(kind=kind, card_ids=tuple(str(cid) for cid in ids))
        if kind in ("choose_joker", "sell_joker"):
            index = data.get("joker_index", data.get("index"))
            if index is not None and (isinstance(index, bool) or not isinstance(index, int)):
                raise InvalidActionError(BAD_REQUEST, "joker_index must be an integer or null")
            return cls(kind=kind, joker_index=index)
        if kind in ("reroll_shop", "advance"):
            return cls(kind=kind)
        raise InvalidActionError(BAD_REQUEST, f"unknown action kind: {kind!r}")



def _index_combinations(hand: Sequence[Card], max_cards: int) -> list[tuple[int, ...]]:
    """枚举 1..max_cards 张手牌下标组合，按稳定 ID 集合去重，顺序固定。"""
    result: list[tuple[int, ...]] = []
    seen: set[tuple[str, ...]] = set()
    for size in range(1, min(max_cards, len(hand)) + 1):
        for indices in combinations(range(len(hand)), size):
            key = tuple(sorted(hand[i].card_id for i in indices))
            if key not in seen:
                seen.add(key)
                result.append(indices)
    return result


def legal_plays(hand: Sequence[Card], max_cards: int = 5) -> list[tuple[int, ...]]:
    """返回当前手牌的全部合法出牌下标组合（1–5 张）。

    Args:
        hand: 当前手牌；空手牌返回 ``[]``。
        max_cards: 单次最多牌数（规则常量 5）。

    Returns:
        下标元组列表；8 张手牌时恰为 218。
    """
    return _index_combinations(hand, max_cards)


def legal_discards(hand: Sequence[Card], discards_left: int, max_cards: int = 5) -> list[tuple[int, ...]]:
    """返回当前可用的弃牌组合；``discards_left<=0`` 时返回 ``[]``。"""
    if discards_left <= 0:
        return []
    return _index_combinations(hand, max_cards)


def encode_card_action(kind: str, hand: Sequence[Card], indices: Iterable[int]) -> Action:
    """把“动作种类 + 手牌下标”编码为 ``Action``（含稳定 ID 与下标快照）。

    Raises:
        InvalidActionError: kind/张数/重复下标非法；下标越界（BAD_REQUEST）。
    """
    if kind not in ("play", "discard"):
        raise InvalidActionError(BAD_REQUEST, "kind must be 'play' or 'discard'")
    idxs = tuple(indices)
    if not 1 <= len(idxs) <= 5 or len(set(idxs)) != len(idxs):
        raise InvalidActionError(BAD_REQUEST, "action must select 1..5 distinct indices")
    if any(i < 0 or i >= len(hand) for i in idxs):
        raise InvalidActionError(BAD_REQUEST, "hand index out of range", {"indices": list(idxs)})
    return Action(kind=kind, card_ids=tuple(hand[i].card_id for i in idxs), hand_indices_snapshot=idxs)


def shop_actions(state: GameState) -> list[Action]:
    """枚举 shop 阶段全部合法动作（只看规则，不看场景约束）。

    顺序固定：可买的报价（下标升序）→ 可卖的 Joker（槽位升序）→ reroll → 离开。
    「可买」= 有空格位 且 ``money >= price``；「可 reroll」= ``money >= reroll_cost``。
    买不起的报价**不进入**合法动作集（调用方强买会拿到 ``NO_RESOURCE``）。

    Args:
        state: 必须 ``phase == 'shop'``；其它阶段返回 ``[]``。

    Returns:
        动作列表；「离开商店」恒为最后一项（``choose_joker:leave``）。
    """
    if state.phase != "shop":
        return []
    actions: list[Action] = []
    has_free_slot = len(state.jokers) < state.joker_slots
    if has_free_slot:
        for index, offer in enumerate(state.shop_options):
            if state.money >= joker_price(offer):
                actions.append(Action("choose_joker", joker_index=index))
    for index in range(len(state.jokers)):
        actions.append(Action("sell_joker", joker_index=index))
    if state.money >= state.reroll_cost:
        actions.append(Action("reroll_shop"))
    actions.append(Action("choose_joker", joker_index=None))  # 离开商店
    return actions


def legal_actions(state: GameState, max_play_cards: int = 5, max_discard_cards: int = 5) -> list[Action]:
    """按游戏规则枚举当前状态的全部合法动作（不读场景约束）。

    Args:
        state: 当前状态。
        max_play_cards / max_discard_cards: 规则常量。

    Returns:
        ``play`` 与 ``discard`` 动作列表（按枚举顺序）；phase 不是 play 时返回
        shop 阶段动作（见 ``shop_actions``）或空列表（done）。
    """
    if state.phase == "done":
        return []
    if state.phase == "shop":
        return shop_actions(state)
    actions: list[Action] = []
    for indices in legal_plays(state.hand, max_play_cards):
        actions.append(encode_card_action("play", state.hand, indices))
    for indices in legal_discards(state.hand, state.discards_left, max_discard_cards):
        actions.append(encode_card_action("discard", state.hand, indices))
    return actions
