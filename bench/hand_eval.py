"""牌型识别、计分牌筛选与牌型包含（contains）关系。

规则来源：``docs/balatro/rules.md`` §4–§5；本模块只实现 **Ante 1 子集**用到的部分：
12 种牌型（9 常规 + 3 隐藏）的识别、等级 1 的基础 Chips×Mult、参与计分的牌筛选，
以及 Joker 条件所需的 contains 关系。

三个概念必须区分（对应任务书 §2.C/§2.D）：
1. **玩家选择的牌**（played cards）：1–5 张，由动作给出；
2. **参与牌型的牌**（hands that count）：决定牌型与基础分，例如四条带 kicker 时
   kicker 不参与牌型；
3. **参与计分的牌**（scoring cards）：真正贡献 rank chips 的牌。本子集无卡牌增强/
   版本/蜡封，也没有 Splash/Four Fingers 等改变筛选的 Joker，因此 2 与 3 在本子集内
   相同；分开建模是为了给后续扩展留接口，且便于测试“不计分牌”的边界。

未验证项（不得写成事实）：
- 最终取整方式（本模块返回的 ``final_score`` 由 ``bench.scoring`` 用 floor 候选口径）；
- 四条/五条是否“包含”对子/三条（``CONTAINS_POLICY`` 采用结构超集口径）。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

from .errors import BAD_REQUEST, DUPLICATE_CARD, InvalidActionError
from .model import Card
from .rules_version import HAND_BASE_SCORE


class HandType(str, Enum):
    """12 种牌型；字符串值进入日志与 trace，保持稳定。"""

    HIGH_CARD = "high_card"
    PAIR = "pair"
    TWO_PAIR = "two_pair"
    THREE_KIND = "three_kind"
    STRAIGHT = "straight"
    FLUSH = "flush"
    FULL_HOUSE = "full_house"
    FOUR_KIND = "four_kind"
    STRAIGHT_FLUSH = "straight_flush"
    FIVE_KIND = "five_kind"
    FLUSH_HOUSE = "flush_house"
    FLUSH_FIVE = "flush_five"

    @property
    def display_name(self) -> str:
        """人类可读英文名（用于 observation/render）。"""
        return _DISPLAY[self]


_DISPLAY = {
    HandType.HIGH_CARD: "High Card",
    HandType.PAIR: "Pair",
    HandType.TWO_PAIR: "Two Pair",
    HandType.THREE_KIND: "Three of a Kind",
    HandType.STRAIGHT: "Straight",
    HandType.FLUSH: "Flush",
    HandType.FULL_HOUSE: "Full House",
    HandType.FOUR_KIND: "Four of a Kind",
    HandType.STRAIGHT_FLUSH: "Straight Flush",
    HandType.FIVE_KIND: "Five of a Kind",
    HandType.FLUSH_HOUSE: "Flush House",
    HandType.FLUSH_FIVE: "Flush Five",
}

# contains 口径：结构超集（structural superset）。
# - 三条含对子；葫芦含三条/对子/两对；四条含对子/三条/四条但不含两对；
# - 五条含对子/三条/四条/五条，但不含葫芦（葫芦要求两个不同点数）；
# - 同花顺含顺子与同花；同花葫芦/同花五条同理。
# 该口径与 rules.md 引用的 Wiki 表述一致的部分已标注 ✅；4K/5K 与 Pair/Three 的
# 边界在一手资料中未明示，标 ⏳（见 Ruleset.unverified）。
CONTAINS_POLICY = "structural_superset_v1"


@dataclass(frozen=True, slots=True)
class HandAnalysis:
    """一次出牌的完整牌型分析结果（不可变，可作为缓存键的输入）。

    Attributes:
        hand_type: 识别出的最高牌型。
        base_chips: 该牌型等级 1 的基础 Chips。
        base_mult: 该牌型等级 1 的基础 Mult。
        scoring_indices: 参与计分的牌在输入序列中的下标（升序）。
        scoring_cards: 参与计分的牌（按输入顺序）。
        contains: 该手牌结构上包含的全部牌型（供 Joker 条件使用）。
        is_royal_flush: 是否为 Royal Flush（仅展示层区分，机制等同同花顺）。
    """

    hand_type: HandType
    base_chips: int
    base_mult: int
    scoring_indices: tuple[int, ...]
    scoring_cards: tuple[Card, ...]
    contains: frozenset[HandType]
    is_royal_flush: bool

    def to_dict(self) -> dict:
        """导出 JSON 友好 dict（不含 Card 对象本身，含稳定 ID）。"""
        return {
            "hand_type": self.hand_type.value,
            "hand_type_name": self.hand_type.display_name,
            "base_chips": self.base_chips,
            "base_mult": self.base_mult,
            "scoring_indices": list(self.scoring_indices),
            "scoring_card_ids": [c.card_id for c in self.scoring_cards],
            "contains": sorted(t.value for t in self.contains),
            "is_royal_flush": self.is_royal_flush,
            "contains_policy": CONTAINS_POLICY,
        }


def _rank_counts(cards: Sequence[Card]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for card in cards:
        counts[card.rank] = counts.get(card.rank, 0) + 1
    return counts


def is_straight_ranks(ranks: Iterable[int]) -> bool:
    """判断 5 个互不相同的点数是否构成顺子（A 可高可低，不可同时）。

    Args:
        ranks: 点数集合（1=A，11/12/13=J/Q/K）。

    Returns:
        是否为顺子；不足/超过 5 个不同点数恒为 False。
    """
    unique = set(ranks)
    if len(unique) != 5:
        return False
    if unique == {1, 2, 3, 4, 5}:  # wheel：A-2-3-4-5
        return True
    if unique == {1, 10, 11, 12, 13}:  # Broadway：10-J-Q-K-A
        return True
    ordered = sorted(unique)
    return ordered[-1] - ordered[0] == 4 and all(
        ordered[i] + 1 == ordered[i + 1] for i in range(4)
    )


def classify_hand(cards: Sequence[Card]) -> HandType:
    """识别 1–5 张牌的牌型（按 vanilla 牌型基础分从高到低短路）。

    Args:
        cards: 玩家选择的牌，1–5 张；顺序不影响判定。

    Returns:
        HandType。

    Raises:
        InvalidActionError: 张数不在 1..5（BAD_REQUEST）。重复物理牌不在这里拒绝
            （隐藏牌型分析需要）；计分入口 ``evaluate_hand`` 会拒绝。

    优先级（= 基础分从高到低）：
        同花五条 > 同花葫芦 > 五条 > 同花顺 > 四条 > 葫芦 > 同花 > 顺子 >
        三条 > 两对 > 对子 > 高牌

    注意：Royal Flush 不单独成为牌型（只由 ``is_royal_flush`` 标记），与其机制等同
    同花顺的规则一致。
    """
    _validate_selection(cards)
    rank_counts = _rank_counts(cards)
    counts = sorted(rank_counts.values(), reverse=True)
    n = len(cards)
    is_flush = n == 5 and len({c.suit for c in cards}) == 1
    is_straight = n == 5 and is_straight_ranks(rank_counts)

    if n == 5 and counts == [5]:
        return HandType.FLUSH_FIVE if is_flush else HandType.FIVE_KIND
    if n == 5 and is_flush and counts == [3, 2]:
        return HandType.FLUSH_HOUSE
    if is_flush and is_straight:
        return HandType.STRAIGHT_FLUSH
    if counts[0] == 4:
        return HandType.FOUR_KIND
    if n == 5 and counts == [3, 2]:
        return HandType.FULL_HOUSE
    if is_flush:
        return HandType.FLUSH
    if is_straight:
        return HandType.STRAIGHT
    if counts[0] == 3:
        return HandType.THREE_KIND
    if counts.count(2) >= 2:
        return HandType.TWO_PAIR
    if counts[0] == 2:
        return HandType.PAIR
    return HandType.HIGH_CARD


def _validate_selection(cards: Sequence[Card]) -> None:
    """校验张数（1–5）。

    注意：这里**不**拒绝重复物理牌，因为 ``classify_hand`` 也用于离线分析“隐藏牌型”
    （五条/同花葫芦/同花五条，标准 52 张牌组不可达，需要构造重复点数/花色的测试牌）。
    真正执行计分的 ``evaluate_hand`` 会拒绝重复 ``card_id``。
    """
    if not 1 <= len(cards) <= 5:
        raise InvalidActionError(
            BAD_REQUEST, f"a played hand must contain 1..5 cards, got {len(cards)}",
            {"cards": len(cards)},
        )


def scoring_card_indices(cards: Sequence[Card], hand_type: HandType) -> tuple[int, ...]:
    """返回参与计分的牌下标（升序）。

    规则（rules.md §4.2）：高牌只计点数最高的 1 张；对子 2 张；两对 4 张；三条 3 张；
    顺子/同花/葫芦/同花顺 5 张；四条 4 张；隐藏牌型 5 张。未参与牌型的 kicker 不贡献
    rank chips。

    Args:
        cards: 已选择的牌（1–5 张）。
        hand_type: ``classify_hand`` 的结果（避免重复判定）。

    Returns:
        下标元组，按输入顺序升序。
    """
    rank_counts = _rank_counts(cards)
    n = len(cards)
    if hand_type is HandType.HIGH_CARD:
        # 高牌按“点数大小”比较：A 最大（rank=1 需映射成 14）。
        best = max(range(n), key=lambda i: (14 if cards[i].rank == 1 else cards[i].rank, -i))
        return (best,)
    if hand_type is HandType.PAIR:
        rank = next(r for r, c in rank_counts.items() if c == 2)
        return tuple(i for i, card in enumerate(cards) if card.rank == rank)
    if hand_type is HandType.TWO_PAIR:
        ranks = {r for r, c in rank_counts.items() if c == 2}
        return tuple(i for i, card in enumerate(cards) if card.rank in ranks)
    if hand_type is HandType.THREE_KIND:
        rank = next(r for r, c in rank_counts.items() if c == 3)
        return tuple(i for i, card in enumerate(cards) if card.rank == rank)
    if hand_type is HandType.FOUR_KIND:
        rank = next(r for r, c in rank_counts.items() if c == 4)
        return tuple(i for i, card in enumerate(cards) if card.rank == rank)
    if hand_type is HandType.FIVE_KIND:
        return tuple(range(n))
    # 顺子、同花、葫芦、同花顺、同花葫芦、同花五条：5 张全部参与。
    return tuple(range(n))


def hand_contains_types(cards: Sequence[Card]) -> frozenset[HandType]:
    """计算手牌结构上包含的牌型集合（Joker 条件使用，见 ``CONTAINS_POLICY``）。

    Args:
        cards: 打出的牌（1–5 张）。

    Returns:
        frozenset[HandType]；恒含 ``HIGH_CARD``。

    注意：这里基于**打出的全部牌**，不是仅计分牌。四条带 kicker 时 kicker 不影响
    结构包含关系（例如 [8,8,8,8,4] 仍包含对子/三条/四条）。
    """
    if not cards:
        return frozenset()
    rank_counts = _rank_counts(cards)
    counts = list(rank_counts.values())
    max_count = max(counts)
    contains: set[HandType] = {HandType.HIGH_CARD}
    if max_count >= 2:
        contains.add(HandType.PAIR)
    if max_count >= 3:
        contains.add(HandType.THREE_KIND)
    if max_count >= 4:
        contains.add(HandType.FOUR_KIND)
    if max_count >= 5:
        contains.add(HandType.FIVE_KIND)
    if sum(1 for c in counts if c >= 2) >= 2:
        contains.add(HandType.TWO_PAIR)
    n = len(cards)
    if n == 5:
        is_straight = is_straight_ranks(rank_counts)
        is_flush = len({c.suit for c in cards}) == 1
        if is_straight:
            contains.add(HandType.STRAIGHT)
        if is_flush:
            contains.add(HandType.FLUSH)
        if is_straight and is_flush:
            contains.add(HandType.STRAIGHT_FLUSH)
        if counts == [3, 2]:
            contains.add(HandType.FULL_HOUSE)
            if is_flush:
                contains.add(HandType.FLUSH_HOUSE)
        if max_count == 5 and is_flush:
            contains.add(HandType.FLUSH_FIVE)
    return frozenset(contains)


def evaluate_hand(cards: Sequence[Card]) -> HandAnalysis:
    """识别牌型并给出基础分、计分牌与 contains 集合。

    Args:
        cards: 1–5 张（物理牌必须唯一；重复 ID 抛 DUPLICATE_CARD）。

    Returns:
        HandAnalysis。

    Raises:
        InvalidActionError: 张数越界或同一张物理牌重复。

    确定性：纯函数；相同输入恒返回相等结果，不读全局状态、不修改入参。
    """
    if len({c.card_id for c in cards}) != len(cards):
        raise InvalidActionError(DUPLICATE_CARD, "played hand contains duplicate card ids")
    hand_type = classify_hand(cards)
    indices = scoring_card_indices(cards, hand_type)
    base = HAND_BASE_SCORE[hand_type.value]
    ranks = {c.rank for c in cards}
    return HandAnalysis(
        hand_type=hand_type,
        base_chips=base[0],
        base_mult=base[1],
        scoring_indices=indices,
        scoring_cards=tuple(cards[i] for i in indices),
        contains=hand_contains_types(cards),
        is_royal_flush=hand_type is HandType.STRAIGHT_FLUSH and ranks == {1, 10, 11, 12, 13},
    )
