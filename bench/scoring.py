"""等级 1 的 vanilla 计分：基础 Chips×Mult → 计分牌 rank chips → Joker 槽位顺序。

计分公式（``docs/balatro/rules.md`` §4，和 ``docs/balatro/engine-gap.md`` §2）：

    chips = 牌型基础 Chips + Σ(参与计分牌的 rank chips) + Σ(+Chips 效果)
    mult  = 牌型基础 Mult  × Π(×Mult 效果) + Σ(+Mult 效果)   # 按槽位顺序逐项应用
    score = floor(chips × mult)                              # 末尾一次取整（候选口径）

顺序细节：
1. 牌型基础分先进入累加器（trace 第一条）；
2. 只对 ``HandAnalysis.scoring_cards`` 加 rank chips（高牌只加 1 张等）；
3. 按 Joker 槽位从左到右逐项应用 ``+Chips`` / ``+Mult`` / ``×Mult``；条件不满足时
   记录一条 ``triggered=False`` 的 trace 但不改变分数；
4. 全部中间值用 ``Fraction`` 保留，最后只 floor 一次。

未验证（⏳，不得写成已验证）：
- Wiki 未明写最终取整方式与中间小数处理；本节采用 ``floor`` 一次作为**候选口径**；
- Joker 触发时机与计分牌筛选的交互未做真游戏实测（A2 0 行）。
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import floor
from typing import Sequence

from .hand_eval import HandAnalysis, HandType, evaluate_hand
from .jokers import condition_met
from .model import Card, Joker


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """一次出牌的完整计分结果（不可变）。

    Attributes:
        analysis: 牌型分析（牌型、基础分、计分牌、contains）。
        chips: 最终 Chips（整数；本子集所有 +Chips 均为整数）。
        mult: 最终 Mult（``Fraction``，保留精确小数）。
        final_score: ``floor(chips × mult)``。
        trace: 计分过程事件元组（每条为 JSON 友好 dict）。
        scoring_card_ids: 参与计分的稳定卡牌 ID（按输入顺序）。
    """

    analysis: HandAnalysis
    chips: int
    mult: Fraction
    final_score: int
    trace: tuple[dict, ...]
    scoring_card_ids: tuple[str, ...]

    @property
    def hand_type(self) -> HandType:
        """便捷访问牌型（兼容旧调用方 ``result.hand_type``）。"""
        return self.analysis.hand_type

    def to_dict(self) -> dict:
        """导出 JSON 友好 dict；倍率同时给精确分数字符串与浮点展示值。

        ``mult`` 字段形如 ``"9/2"``，下游要数值请用 ``mult_float`` 或自行解析，
        不要直接 ``float("9/2")``。
        """
        return {
            "hand_type": self.analysis.hand_type.value,
            "hand_type_name": self.analysis.hand_type.display_name,
            "base_chips": self.analysis.base_chips,
            "base_mult": self.analysis.base_mult,
            "scoring_card_ids": list(self.scoring_card_ids),
            "chips": self.chips,
            "mult": f"{self.mult.numerator}/{self.mult.denominator}",
            "mult_float": float(self.mult),
            "final_score": self.final_score,
            "trace": list(self.trace),
            "analysis": self.analysis.to_dict(),
        }


def _apply_effect(chips: int, mult: Fraction, joker: Joker) -> tuple[int, Fraction]:
    """应用单个 Joker 效果；返回新的 ``(chips, mult)``。

    Raises:
        ValueError: 未支持的效果类型（防御性；目录校验已拦截）。
    """
    if joker.kind == "add_chips":
        return chips + joker.value, mult
    if joker.kind == "add_mult":
        return chips, mult + joker.value
    if joker.kind == "mul_mult":
        return chips, mult * joker.multiplier
    raise ValueError(f"unsupported joker kind: {joker.kind!r}")


def score_hand(cards: Sequence[Card], jokers: Sequence[Joker] = ()) -> ScoreResult:
    """计算一次出牌的得分并返回完整中间过程。

    Args:
        cards: 本次打出的 1–5 张牌（稳定 ID 必须唯一；顺序保留玩家选择顺序）。
        jokers: 按槽位顺序排列的 Joker 序列（左→右）。

    Returns:
        ScoreResult；``final_score`` 为本子集的取整后得分。

    Raises:
        InvalidActionError: 牌数越界或重复牌（来自 ``evaluate_hand``）。
        ValueError: 出现未注册的 Joker 效果（防御性，不应由合法输入触发）。

    确定性：纯函数；不修改入参、不读全局状态、不消耗随机数。
    """
    analysis = evaluate_hand(cards)
    trace: list[dict] = [
        {
            "phase": "hand_base",
            "hand_type": analysis.hand_type.value,
            "hand_type_name": analysis.hand_type.display_name,
            "base_chips": analysis.base_chips,
            "base_mult": analysis.base_mult,
            "is_royal_flush": analysis.is_royal_flush,
        }
    ]

    chips = analysis.base_chips
    mult = Fraction(analysis.base_mult, 1)

    card_chips = sum(card.chips for card in analysis.scoring_cards)
    chips += card_chips
    trace.append({
        "phase": "scoring_cards",
        "card_ids": [c.card_id for c in analysis.scoring_cards],
        "cards_chips": card_chips,
        "chips_after": chips,
        "mult_after": f"{mult.numerator}/{mult.denominator}",
    })

    for slot, joker in enumerate(jokers):
        triggered = condition_met(joker, analysis, played_card_count=len(cards))
        before_chips, before_mult = chips, mult
        if triggered:
            chips, mult = _apply_effect(chips, mult, joker)
        trace.append({
            "phase": "joker",
            "slot": slot,
            "joker_id": joker.jid,
            "joker_name": joker.name,
            "kind": joker.kind,
            "value": joker.value,
            "condition": joker.condition,
            "triggered": triggered,
            "chips_before": before_chips,
            "chips_after": chips,
            "mult_before": f"{before_mult.numerator}/{before_mult.denominator}",
            "mult_after": f"{mult.numerator}/{mult.denominator}",
        })

    final_score = floor(Fraction(chips, 1) * mult)
    trace.append({
        "phase": "final_score",
        "expression": "floor(chips * mult)",
        "chips": chips,
        "mult": f"{mult.numerator}/{mult.denominator}",
        "final_score": final_score,
        "rounding_status": "CANDIDATE_FLOOR_UNVERIFIED",
    })
    return ScoreResult(
        analysis=analysis,
        chips=chips,
        mult=mult,
        final_score=final_score,
        trace=tuple(trace),
        scoring_card_ids=tuple(c.card_id for c in analysis.scoring_cards),
    )
