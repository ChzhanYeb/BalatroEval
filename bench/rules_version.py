"""规则版本与规则子集声明：本仓库**唯一**的机器可读规则范围来源。

规则版本 ``vanilla_1.0.1o_subset_v2`` 的定义（v1 = 无经济版，v2 = 加经济版）：

- 目标游戏版本：Vanilla Balatro **1.0.1o**（Steam）。
- 目标配置：**Red Deck + White Stake + Ante 1**。
- 已实现（计分与流程）：9 种常规牌型 + 3 种隐藏牌型的识别；等级 1 的牌型基础
  Chips×Mult；计分牌筛选；8 个具名 vanilla Joker 及其条件；Ante 1 三盲注目标
  300/450/600；Red Deck 的 4 手/4 弃；手牌上限 8；5 个 Joker 槽位；出牌/弃牌/补牌/
  洗回；Small/Big/Boss 三盲注推进与胜负判定。
- 已实现（经济，v2 新增）：起始金钱 **$4**；通关奖励 Small **$3** / Big **$4** /
  Boss **$5**；每剩 1 手 **+$1**、每未用 1 弃牌 **+$1**；利息**每 $5 得 $1、上限
  $5**（按结算前持有金额计算）；Small/Big 通关后进入**商店**：2 个 Joker 报价、
  按稀有度固定价（Common $5 / Rare $9）、可**买入 / 卖出（返还半价）/ reroll /
  离开**。
- 明确排除：Boss 效果、消耗品、Voucher、补充包、卡牌增强/蜡封/版本、多牌组/
  多赌注、Tag/跳盲、Endless、手牌等级 >1、重触发、Blueprint/Brainstorm、
  Joker 版本、负片槽、手牌内效果、特殊牌，以及依赖上述机制的 Joker。
- 未验证：所有“与真游戏一致”的主张。当前没有一份 A2（单步分数）实测行，
  因此 ``verification_status`` 恒为 ``NOT_VERIFIED``，``alignment_level`` 恒为 ``L0``。

经济口径的三条边界（引用时必须保留）：
1. **价格是固定的**：按稀有度取 vanilla 价格区间的中值（Common $5、Rare $9），
   不使用原版的 $4–6 / $6–8 / $8–10 浮动与稀有度权重；商店候选是**均匀抽样**，
   不是原版权重 70/25/5。
2. **利息按结算前金额算**：先把「奖励 + 剩余手数 + 未用弃牌 + 利息」一次性入账，
   其中利息用入账前的 ``money`` 计算。原版结算顺序未实测（``unverified``）。
3. **商店只在 Small/Big 之后开**：Boss 通关即 ``win``，不再进商店；卖掉的 Joker
   可能在下一次 reroll 里重新出现（本子集不维护“已淘汰卡池”）。

重要边界：
1. 规则实现完成 ≠ 与 vanilla 对齐验证完成。修改 ``implemented`` 只表示代码路径存在；
   修改 ``verification_status`` 必须等 ``docs/quality/engine-fidelity.md`` A 表签核。
2. 本模块**不**从 ``scenarios/RULES_VERSION`` 读取配置；文件是给人看的镜像，
   测试会断言两者一致（防止文档与代码漂移）。
3. 规则常量是规则定义的一部分；改动必须升 ``rules_version`` 并同步测试与文档。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
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


# --- 经济常量（v2）-----------------------------------------------------------
# 全部是整数常量：结算可完全判定，不依赖随机数；唯一随机的地方是商店候选抽样
# （由 GameState.rng_state 决定，同 seed 可复现）。
STARTING_MONEY: Final[int] = 4          # Red Deck 起始金钱
HAND_BONUS: Final[int] = 1              # 每剩余 1 手 +$1
DISCARD_BONUS: Final[int] = 1           # 每未用 1 弃牌 +$1
INTEREST_PER: Final[int] = 5            # 每 $5 得 $1 利息
INTEREST_CAP: Final[int] = 5            # 利息上限 $5
SHOP_OFFER_COUNT: Final[int] = 2        # 商店 Joker 报价数（vanilla 2 个卡位）
REROLL_BASE_COST: Final[int] = 5        # 同一商店内第一次 reroll 价格
REROLL_INCREMENT: Final[int] = 1        # 每次 reroll 后涨价
SELL_REFUND_DIVISOR: Final[int] = 2     # 卖出返还 = 原价 // 2（最低 $1）

# 固定价：取 vanilla 价格区间的中值。**不是**原版的浮动定价。
JOKER_PRICE_BY_RARITY: Final[dict[str, int]] = {
    "Common": 5,
    "Uncommon": 7,
    "Rare": 9,
    "Legendary": 10,
}

# v2 起商店是基础规则，旧的非 vanilla 免费扩展退役。
RETIRED_EXTENSIONS: Final[tuple[str, ...]] = ("free_joker_choice",)


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
    starting_money: int
    hand_bonus: int
    discard_bonus: int
    interest_per: int
    interest_cap: int
    shop_offer_count: int
    reroll_base_cost: int
    reroll_increment: int
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
        if self.starting_money < 0:
            raise ValueError("starting_money cannot be negative")
        if self.interest_per <= 0:
            raise ValueError("interest_per must be positive")
        if self.shop_offer_count < 1:
            raise ValueError("shop_offer_count must be >= 1")
        if self.reroll_base_cost < 0 or self.reroll_increment < 0:
            raise ValueError("reroll costs cannot be negative")

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
            "starting_money": self.starting_money,
            "hand_bonus": self.hand_bonus,
            "discard_bonus": self.discard_bonus,
            "interest_per": self.interest_per,
            "interest_cap": self.interest_cap,
            "shop_offer_count": self.shop_offer_count,
            "reroll_base_cost": self.reroll_base_cost,
            "reroll_increment": self.reroll_increment,
            "joker_price_by_rarity": dict(JOKER_PRICE_BY_RARITY),
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


# 规则子集 v2 的权威实例（v1 只作历史；v2 = v1 + 金钱/利息/商店经济）。
# 环境、Oracle、场景加载器都从这里取常量，不得各自复制。
VANILLA_SUBSET_V1: Final[Ruleset] = Ruleset(
    rules_version="vanilla_1.0.1o_subset_v2",
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
    shop_enabled=True,  # v2：商店是基础规则（Small/Big 之后，花真钱）
    max_play_cards=5,
    max_discard_cards=5,
    starting_money=STARTING_MONEY,
    hand_bonus=HAND_BONUS,
    discard_bonus=DISCARD_BONUS,
    interest_per=INTEREST_PER,
    interest_cap=INTEREST_CAP,
    shop_offer_count=SHOP_OFFER_COUNT,
    reroll_base_cost=REROLL_BASE_COST,
    reroll_increment=REROLL_INCREMENT,
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
        # --- v2 经济 ---
        "money_start_4",
        "blind_reward_money_3_4_5",
        "hand_bonus_1_per_hand",
        "discard_bonus_1_per_unused_discard",
        "interest_1_per_5_cap_5",
        "shop_after_small_and_big",
        "shop_2_offers_fixed_price_by_rarity",
        "shop_buy_sell_reroll_leave",
    ),
    unverified=(
        "final_score_rounding_floor_candidate",
        "contains_relation_for_four_kind_and_five_kind",
        "cross_blind_hand_redraw_policy",
        "boss_blind_effect_absent",
        "hand_level_greater_than_1",
        "real_game_single_step_score_equality_A2",
        # --- v2 经济口径未实测 ---
        "interest_ordering_before_payout",
        "joker_price_fixed_mid_of_vanilla_range",
        "shop_offer_pool_uniform_no_rarity_weights",
        "shop_rng_not_vanilla",
        "sold_joker_may_reappear_after_reroll",
    ),
    excluded=(
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
        "Economy (v2): payout = blind reward + $1 per remaining hand + $1 per unused discard + "
        "interest (money//5, cap 5). Interest is computed on money BEFORE this payout; the vanilla "
        "ordering is UNVERIFIED.",
        "Shop (v2): 2 offers, fixed price by rarity (Common $5 / Rare $9), buy/sell(floor half)/"
        "reroll(base $5, +$1)/leave. Offers are a uniform sample of the 8-joker catalog, NOT the "
        "vanilla weight table; reroll draws advance the seeded rng, not the vanilla rng.",
        "Score rounding: floor(chips*mult) at the end is a candidate convention; the wiki does not "
        "state it explicitly, so it stays UNVERIFIED.",
        "Contains relation: structural superset policy; 4K/5K vs Pair/Three is UNVERIFIED.",
    ),
)


def joker_price(joker: Joker | str) -> int:
    """按稀有度返回 Joker 的固定买价（v2 定价表；未知稀有度抛 ValueError）。

    Args:
        joker: ``model.Joker`` 实例或其稀有度字符串（如 ``"Common"``）。

    Returns:
        整数美元价格。

    Raises:
        ValueError: 稀有度不在 ``JOKER_PRICE_BY_RARITY`` 中。
    """
    rarity = joker if isinstance(joker, str) else getattr(joker, "rarity", "")
    try:
        return JOKER_PRICE_BY_RARITY[rarity]
    except KeyError as exc:
        raise ValueError(f"no price defined for joker rarity: {rarity!r}") from exc


def sell_value(joker: Joker) -> int:
    """卖出返还：买价的 ``1/2`` 向下取整，最低 $1。"""
    return max(1, joker_price(joker) // SELL_REFUND_DIVISOR)


def interest_for(money: int, ruleset: "Ruleset | None" = None) -> int:
    """按持有金额算利息：``min(money // interest_per, interest_cap)``。

    Args:
        money: 结算前持有的金钱（非负）。
        ruleset: 规则集；None 用 ``VANILLA_SUBSET_V1``。

    Returns:
        本次结算的利息（整数美元）。
    """
    rules = ruleset or VANILLA_SUBSET_V1
    return min(max(0, money) // rules.interest_per, rules.interest_cap)


def ruleset_for(extension_names: tuple[str, ...] | list[str] | None = None) -> Ruleset:
    """按场景声明的扩展返回规则集。

    v2 起**不再有** benchmark 扩展：``free_joker_choice``（免费三选一）已退役，
    由付费商店取代。任何扩展名都视为不支持。

    Args:
        extension_names: 场景 ``extensions`` 列表；None/空表示标准子集。

    Returns:
        ``VANILLA_SUBSET_V1``。

    Raises:
        ValueError: 声明了任何扩展（含已退役的 ``free_joker_choice``）。
    """
    names = tuple(extension_names or ())
    if names:
        retired = [n for n in names if n in RETIRED_EXTENSIONS]
        hint = " (retired in v2: the paid shop replaced the free choice)" if retired else ""
        raise ValueError(f"unsupported ruleset extensions: {list(names)}{hint}")
    return VANILLA_SUBSET_V1

