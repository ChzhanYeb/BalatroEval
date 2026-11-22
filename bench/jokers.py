"""8 个具名 vanilla Joker（Ante 1 子集）的规则目录与条件判定。

数值与条件来源（只取事实数值，描述自写）：
- ``docs/balatro/content.md`` §1.5 与各 Joker 单页；``docs/balatro/rules.md`` §4.6；
- 条件语义：``Contains`` = 手牌结构上包含某牌型（见 ``bench.hand_eval.CONTAINS_POLICY``）。

8 个 Joker（6 Common + 2 Rare）：

====================  ==========  ==========================  ==========================
Joker                 稀有度       效果                         触发条件
====================  ==========  ==========================  ==========================
Joker                 Common       +4 Mult                     恒定
Jolly Joker           Common       +8 Mult                     含对子
Zany Joker            Common       +12 Mult                    含三条
Sly Joker             Common       +50 Chips                   含对子
Wily Joker            Common       +100 Chips                  含三条
Half Joker            Common       +20 Mult                    打出的牌 ≤ 3 张
The Duo               Rare         ×2 Mult                     含对子
The Trio              Rare         ×3 Mult                     含三条
====================  ==========  ==========================  ==========================

边界（不得弱化）：
- 这 8 个 Joker 的**数值**来自二手 Wiki 事实页；触发顺序/与计分牌的交互**未经真游戏
  实测**，因此规则状态是 ``IMPLEMENTED`` 而非 ``VERIFIED``。
- 其余 142 个 Joker 明确排除（见 ``Ruleset.excluded``）；不得因为“结构相似”就宣称覆盖。
- 旧的合成夹具（``jc_*``/``jm_*``/``jx_*``）已移出生产目录，只保留在
  ``tests/fixtures.py``，避免被误当作原版 Joker 进入场景。
"""
from __future__ import annotations

from typing import Final

from .hand_eval import HandAnalysis, HandType
from .model import Joker

# 8 个具名 Joker 的权威目录。顺序不代表规则优先级（计分顺序由槽位顺序决定）。
VANILLA_JOKERS: Final[tuple[Joker, ...]] = (
    Joker("joker", "Joker", "add_mult", 4, "always", "Common", 2),
    Joker("jolly_joker", "Jolly Joker", "add_mult", 8, "contains_pair", "Common", 3),
    Joker("zany_joker", "Zany Joker", "add_mult", 12, "contains_three", "Common", 4),
    Joker("sly_joker", "Sly Joker", "add_chips", 50, "contains_pair", "Common", 3),
    Joker("wily_joker", "Wily Joker", "add_chips", 100, "contains_three", "Common", 4),
    Joker("half_joker", "Half Joker", "add_mult", 20, "cards_le_3", "Common", 5),
    Joker("the_duo", "The Duo", "mul_mult", 200, "contains_pair", "Rare", 8),
    Joker("the_trio", "The Trio", "mul_mult", 300, "contains_three", "Rare", 8),
)

JOKER_CATALOG: Final[tuple[Joker, ...]] = VANILLA_JOKERS
CATALOG_BY_ID: Final[dict[str, Joker]] = {j.jid: j for j in VANILLA_JOKERS}


def get_joker(jid: str) -> Joker:
    """按稳定 ID 取 Joker。

    Raises:
        KeyError: ID 不在 8 个具名目录中（调用方应转成 UNKNOWN_CARD/BAD_REQUEST）。
    """
    return CATALOG_BY_ID[jid]


def condition_met(joker: Joker, analysis: HandAnalysis, played_card_count: int) -> bool:
    """判断 Joker 的触发条件是否满足。

    Args:
        joker: 目录中的 Joker。
        analysis: 本次出牌的 ``HandAnalysis``（含 contains 集合）。
        played_card_count: 玩家选择的牌数（1–5），用于 ``cards_le_3``。

    Returns:
        True 表示本次出牌触发该 Joker。

    确定性：纯函数。
    """
    condition = joker.condition
    if condition == "always":
        return True
    if condition == "contains_pair":
        return HandType.PAIR in analysis.contains
    if condition == "contains_three":
        return HandType.THREE_KIND in analysis.contains
    if condition == "cards_le_3":
        return played_card_count <= 3
    raise ValueError(f"unsupported joker condition: {condition!r}")
