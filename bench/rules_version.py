"""规则版本与规则子集声明：本仓库**唯一**的机器可读规则范围来源。

规则版本 ``vanilla_1.0.1o_subset_v1`` 的定义：

- 目标游戏版本：Vanilla Balatro **1.0.1o**（Steam）。
- 目标配置：**Red Deck + White Stake + Ante 1**。
- 已实现：9 种常规牌型 + 3 种隐藏牌型的识别；等级 1 的牌型基础 Chips×Mult；
  计分牌筛选；8 个具名 vanilla Joker 及其条件；Ante 1 三盲注目标 300/450/600；
  Red Deck 的 4 手/4 弃；手牌上限 8；5 个 Joker 槽位；出牌/弃牌/补牌/洗回；
  Small/Big/Boss 三盲注推进与胜负判定。
- 明确排除：金钱/利息/商店经济、Boss 效果、消耗品、Voucher、补充包、卡牌增强/
  蜡封/版本、多牌组/多赌注、Tag/跳盲、Endless、手牌等级 >1、重触发、
  以及依赖上述机制的 Joker。
- 未验证：所有“与真游戏一致”的主张。当前没有一份 A2（单步分数）实测行，
  因此 ``verification_status`` 恒为 ``NOT_VERIFIED``，``alignment_level`` 恒为 ``L0``。

重要边界：
1. 规则实现完成 ≠ 与 vanilla 对齐验证完成。修改 ``implemented`` 只表示代码路径存在；
   修改 ``verification_status`` 必须等 ``docs/engine-fidelity.md`` A 表签核。
2. 本模块**不**从 ``scenarios/RULES_VERSION`` 读取配置；文件是给人看的镜像，
   测试会断言两者一致（防止文档与代码漂移）。
3. 规则常量是规则定义的一部分；改动必须升 ``rules_version`` 并同步测试与文档。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Final


# 牌型基础分表（等级 1）。键与 bench.hand_eval.HandType 的字符串值一致。
HAND_BASE_SCORE: Final[dict[str, tuple[int, int]]] = {
    "high_card": (5, 1),
    "pair": (10, 2),
    "two_pair": (20, 2),
    "three_kind": (30, 3),
    "straight": (30, 4),
    "flush": (35, 4),
    "full_house": (40, 4),
    "four_kind": (60, 7),
    "straight_flush": (100, 8),
    "five_kind": (120, 12),
    "flush_house": (140, 14),
    "flush_five": (160, 16),
}


@dataclass(frozen=True, slots=True)
class BlindSpec:
    """Ante 1 的一个盲注定义。

    Attributes:
        index: 0/1/2，分别对应 Small/Big/Boss。
        kind: ``small`` / ``big`` / ``boss``。
        name: 展示名。
        base_score: Ante 1 基础分（300）。
        multiplier: 目标分倍率（1 / 3/2 / 2）。
        reward_money: 现金奖励；本子集不实现金钱，仅作规则声明与未来扩展占位。
        effect: Boss 效果名；子集只允许 ``None``（效果未实现）。
    """

    index: int
    kind: str
    name: str
    base_score: int
    multiplier: Fraction
    reward_money: int = 0
    effect: str | None = None

    @property
    def target(self) -> int:
        """该盲注的目标分 = base_score × multiplier（向下取整，当前三档均为整数）。"""
        return int(self.base_score * self.multiplier)

    def to_dict(self) -> dict:
        """导出为 JSON 友好 dict（target 一并给出，便于数据消费者直接读取）。"""
        return {
            "index": self.index,
            "kind": self.kind,
            "name": self.name,
            "base_score": self.base_score,
            "multiplier": f"{self.multiplier.numerator}/{self.multiplier.denominator}",
            "target": self.target,
            "reward_money": self.reward_money,
            "effect": self.effect,
        }


ANTE1_BLINDS: Final[tuple[BlindSpec, ...]] = (
    BlindSpec(index=0, kind="small", name="Small Blind", base_score=300,
              multiplier=Fraction(1, 1), reward_money=3),
    BlindSpec(index=1, kind="big", name="Big Blind", base_score=300,
              multiplier=Fraction(3, 2), reward_money=4),
    BlindSpec(index=2, kind="boss", name="Boss Blind", base_score=300,
              multiplier=Fraction(2, 1), reward_money=5),
)


@dataclass(frozen=True, slots=True)
class Ruleset:
    """一个完整规则子集的不可变声明（环境初始化时注入，禁止全局可变状态）。"""

    rules_version: str
    target_game_version: str
    deck: str
    stake: str
    ante: int
    max_ante: int
    hands_per_blind: int
    discards_per_blind: int
    hand_size: int
    joker_slots: int
    blinds: tuple[BlindSpec, ...]
    shop_enabled: bool
    max_play_cards: int
    max_discard_cards: int
    implemented: tuple[str, ...]
    unverified: tuple[str, ...]
    excluded: tuple[str, ...]
    fidelity_status: str
    alignment_level: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.ante > self.max_ante:
            raise ValueError("ante must be <= max_ante")
        if len(self.blinds) != 3:
            raise ValueError("ruleset must define exactly three blinds for Ante 1")
        if [b.index for b in self.blinds] != [0, 1, 2]:
            raise ValueError("blind indexes must be 0,1,2")
        if self.max_play_cards > self.hand_size:
            raise ValueError("max_play_cards cannot exceed hand_size")
        if self.fidelity_status not in ("NOT_VERIFIED", "PARTIALLY_VERIFIED", "VERIFIED"):
            raise ValueError("invalid fidelity_status")

    def blind(self, index: int) -> BlindSpec:
        """按 blind_idx 取盲注定义；越界抛 IndexError。"""
        return self.blinds[index]

    def to_dict(self) -> dict:
        """导出为 JSON 可序列化 dict（供 CLI、manifest、规则文件校验使用）。"""
        return {
            "rules_version": self.rules_version,
            "target_game_version": self.target_game_version,
            "deck": self.deck,
            "stake": self.stake,
            "ante": self.ante,
            "max_ante": self.max_ante,
            "hands_per_blind": self.hands_per_blind,
            "discards_per_blind": self.discards_per_blind,
            "hand_size": self.hand_size,
            "joker_slots": self.joker_slots,
            "max_play_cards": self.max_play_cards,
            "max_discard_cards": self.max_discard_cards,
            "shop_enabled": self.shop_enabled,
            "blinds": [b.to_dict() for b in self.blinds],
            "hand_base_score": {k: {"chips": v[0], "mult": v[1]}
                                for k, v in HAND_BASE_SCORE.items()},
            "implemented": list(self.implemented),
            "unverified": list(self.unverified),
            "excluded": list(self.excluded),
            "fidelity_status": self.fidelity_status,
            "alignment_level": self.alignment_level,
            "notes": list(self.notes),
        }

    def signature(self) -> str:
        """规则声明内容的 sha256（前 16 位十六进制），用于 manifest 与结果头。"""
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# 规则子集 v1 的权威实例。环境、Oracle、场景加载器都从这里取常量，不得各自复制。
VANILLA_SUBSET_V1: Final[Ruleset] = Ruleset(
    rules_version="vanilla_1.0.1o_subset_v1",
    target_game_version="1.0.1o",
    deck="red",
    stake="white",
    ante=1,
    max_ante=1,
    hands_per_blind=4,
    discards_per_blind=4,  # base 3 + Red Deck +1
    hand_size=8,
    joker_slots=5,
    blinds=ANTE1_BLINDS,
    shop_enabled=False,  # vanilla 商店依赖金钱（excluded）；见 SHOP_EXTENSION
    max_play_cards=5,
    max_discard_cards=5,
    implemented=(
        "deck_standard_52",
        "deck_red_plus1_discard",
        "stake_white",
        "hand_size_8",
        "hands_4_per_blind",
        "discards_4_per_blind",
        "joker_slots_5",
        "ante1_blinds_small300_big450_boss600",
        "play_1_to_5_cards",
        "discard_1_to_5_cards",
        "draw_and_reshuffle_discard_pile",
        "hand_types_9_regular",
        "hand_types_3_secret",
        "hand_base_chips_mult_level1",
        "scoring_card_filtering",
        "jokers_8_named_vanilla",
        "joker_conditions_contains_pair_contains_three_cards_le_3",
        "blind_progression_and_win_loss",
        "deterministic_rng_state",
        "snapshot_restore",
    ),
    unverified=(
        "final_score_rounding_floor_candidate",
        "contains_relation_for_four_kind_and_five_kind",
        "cross_blind_hand_redraw_policy",
        "boss_blind_effect_absent",
        "hand_level_greater_than_1",
        "real_game_single_step_score_equality_A2",
    ),
    excluded=(
        "money",
        "interest",
        "shop_economy",
        "boss_effects",
        "consumables_tarot_planet_spectral",
        "vouchers",
        "booster_packs",
        "card_enhancements",
        "card_seals",
        "card_editions",
        "multi_deck",
        "multi_stake",
        "tags_and_blind_skip",
        "endless_mode",
        "hand_levels_gt1",
        "retriggers",
        "blueprint_brainstorm",
        "joker_editions",
        "negative_joker_slots",
        "held_in_hand_card_effects",
        "stone_gold_glass_steel_lucky_cards",
    ),
    fidelity_status="NOT_VERIFIED",
    alignment_level="L0",
    notes=(
        "Implemented != verified. A2 (real-game single-step score equality) has 0 measured rows.",
        "Boss Blind is modeled as a score-only blind: every Ante 1 boss effect is NOT implemented; "
        "scenarios requesting a boss effect must be rejected by the scenario validator.",
        "Shop extension (free 3-choose-1 joker) is a benchmark scaffold, disabled by default; "
        "it is not vanilla and must never be cited as alignment evidence.",
        "Score rounding: floor(chips*mult) at the end is a candidate convention; the wiki does not "
        "state it explicitly, so it stays UNVERIFIED.",
        "Contains relation: structural superset policy; 4K/5K vs Pair/Three is UNVERIFIED.",
    ),
)


# 商店扩展：仅供 benchmark 在“没有金钱”的约束下仍能构造 build 差异。
# 它不是 vanilla 规则，默认关闭；启用时必须通过 Scenario.extensions 显式声明。
SHOP_EXTENSION: Final[str] = "free_joker_choice"


def ruleset_for(extension_names: tuple[str, ...] | list[str] | None = None) -> Ruleset:
    """按场景声明的扩展返回规则集副本（仅 ``free_joker_choice`` 受支持）。

    Args:
        extension_names: 场景 ``extensions`` 列表；None/空表示严格子集。

    Returns:
        Ruleset；若含未支持扩展抛 ValueError（场景校验阶段应给出 BAD_REQUEST）。

    Raises:
        ValueError: 出现未支持的扩展名。
    """
    names = tuple(extension_names or ())
    unknown = [n for n in names if n != SHOP_EXTENSION]
    if unknown:
        raise ValueError(f"unsupported ruleset extensions: {unknown}")
    if SHOP_EXTENSION in names:
        return replace(VANILLA_SUBSET_V1, shop_enabled=True)
    return VANILLA_SUBSET_V1
