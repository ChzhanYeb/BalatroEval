"""BalatroEval 规则子集 v1 的类型化领域模型。

职责：定义不可变 ``Card`` / ``Joker`` 值对象与可变但**按值传递**的 ``GameState``，
并提供 JSON 序列化辅助函数。

不变量：
- ``Card`` 是标准 52 张牌中的一张（无增强/蜡封/版本），以 ``(suit, rank)`` 与稳定
  ``card_id`` 为身份；``rank=1`` 表示 A，仅用于顺子排序，计分筹码另有口径。
- ``Joker`` 是 vanilla 具名 Joker 的**规则参数**（不是可变的游戏对象）；8 个目录条目
  在 ``bench/jokers.py`` 中集中定义。
- ``GameState`` 是可变 dataclass，但所有状态转移函数都遵守“先在副本上改、再返回副本”，
  调用方持有的旧状态不会被就地修改。
- 随机性只来自 ``rng_state``（完整 ``random.Random.getstate()`` 的 JSON 编码）。
  禁止使用全局随机源、时间或哈希随机化。

与旧 L0 模型的差异（见 docs/implementation/rules-implementation.md）：
- 增加 ``blind_kind`` / ``boss_effect`` / ``joker_slots`` / ``ante`` 字段；
- ``Joker`` 增加 ``condition`` / ``rarity``，支持 vanilla 触发条件；
- 旧的 3 槽位硬编码与自定义 ``HAND_MULT`` 已删除（规则表在 ``rules_version`` 与
  ``hand_eval``）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .rules_version import REROLL_BASE_COST, STARTING_MONEY, VANILLA_SUBSET_V1

SUIT_NAMES = ("spades", "hearts", "diamonds", "clubs")
SUIT_CODES = ("s", "h", "d", "c")
RANK_NAMES = {1: "A", 11: "J", 12: "Q", 13: "K"}

Phase = Literal["play", "shop", "done"]
BlindKind = Literal["small", "big", "boss"]
Outcome = Literal["win", "loss"]
JokerKind = Literal["add_chips", "add_mult", "mul_mult"]
JokerCondition = Literal["always", "contains_pair", "contains_three", "cards_le_3"]


@dataclass(frozen=True, slots=True, order=True)
class Card:
    """一张无修饰的标准扑克牌（不可变值对象）。

    Args:
        suit: 0..3，依次为黑桃/红心/方块/梅花（与 ``SUIT_CODES`` 下标对齐）。
        rank: 1..13；1=A、11/12/13=J/Q/K、2..10 为点数本身。

    Raises:
        ValueError: suit/rank 越界。
    """

    suit: int
    rank: int

    def __post_init__(self) -> None:
        if self.suit not in range(4):
            raise ValueError(f"suit must be 0..3, got {self.suit}")
        if self.rank not in range(1, 14):
            raise ValueError(f"rank must be 1..13, got {self.rank}")

    @property
    def card_id(self) -> str:
        """稳定卡牌 ID（如 ``c7h``：rank=7、suit=hearts）。标准牌组内唯一。"""
        return f"c{self.rank}{SUIT_CODES[self.suit]}"

    @property
    def label(self) -> str:
        """人类可读短标签（如 ``7h``、``10s``）；仅展示用，不作身份判断。"""
        rank = RANK_NAMES.get(self.rank, str(self.rank))
        return f"{rank}{SUIT_CODES[self.suit]}"

    @property
    def rank_label(self) -> str:
        """点数标签：A/J/Q/K/2..10。"""
        return RANK_NAMES.get(self.rank, str(self.rank))

    @property
    def suit_name(self) -> str:
        """花色英文名（spades/hearts/diamonds/clubs）。"""
        return SUIT_NAMES[self.suit]

    @property
    def chips(self) -> int:
        """单牌 rank chips：A=11、J/Q/K=10、其余=点数；与 vanilla 口径一致。"""
        if self.rank == 1:
            return 11
        if self.rank >= 11:
            return 10
        return self.rank

    def to_dict(self) -> dict:
        """导出 JSON dict：``id`` / ``suit`` / ``rank`` / ``label``。"""
        return {"id": self.card_id, "suit": self.suit, "rank": self.rank, "label": self.label}

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        """从 ``to_dict`` 产物还原；接受 id 或 (suit, rank)。"""
        if "id" in data:
            return card_from_id(str(data["id"]))
        return cls(suit=int(data["suit"]), rank=int(data["rank"]))


def card_from_id(card_id: str) -> Card:
    """把稳定卡牌 ID（如 ``c7h``）解析成 ``Card``。

    Raises:
        ValueError: 格式非法（必须以 c 开头、两位 rank 或一位、合法花色码）。

    说明：rank 支持 ``c10s`` 这类两位数字；解析顺序为“去掉首尾后取中间数字 + 末位花色”。
    """
    if not isinstance(card_id, str) or len(card_id) < 3 or card_id[0] != "c":
        raise ValueError(f"invalid card id: {card_id!r}")
    suit_code, rank_text = card_id[-1], card_id[1:-1]
    if suit_code not in SUIT_CODES:
        raise ValueError(f"invalid card id suit: {card_id!r}")
    if not rank_text.isdigit():
        raise ValueError(f"invalid card id rank: {card_id!r}")
    rank = int(rank_text)
    if rank not in range(1, 14):
        raise ValueError(f"invalid card id rank: {card_id!r}")
    return Card(suit=SUIT_CODES.index(suit_code), rank=rank)


@dataclass(frozen=True, slots=True)
class Joker:
    """一个具名 vanilla Joker 的规则参数（不可变）。

    Args:
        jid: 稳定 ID（如 ``jolly_joker``）。
        name: 展示名（如 ``Jolly Joker``）。
        kind: 效果类型，``add_chips`` / ``add_mult`` / ``mul_mult``。
        value: add_* 为整数增量；``mul_mult`` 为**百分之一**整数（200 表示 ×2、300 表示 ×3）。
        condition: 触发条件，见 ``JokerCondition``；``always`` 表示恒定生效。
        rarity: ``Common`` / ``Uncommon`` / ``Rare`` / ``Legendary``。
        buy_price: 商店基础价（仅声明，子集不实现金钱，不参与规则计算）。

    Raises:
        ValueError: kind/condition 非法，或 value 与其单位不匹配。
    """

    jid: str
    name: str
    kind: JokerKind
    value: int
    condition: JokerCondition = "always"
    rarity: str = ""
    buy_price: int = 0

    def __post_init__(self) -> None:
        if self.kind not in ("add_chips", "add_mult", "mul_mult"):
            raise ValueError(f"unsupported joker kind: {self.kind}")
        if self.condition not in ("always", "contains_pair", "contains_three", "cards_le_3"):
            raise ValueError(f"unsupported joker condition: {self.condition}")
        if self.kind == "mul_mult":
            if self.value <= 0:
                raise ValueError("mul_mult value must be positive hundredths, e.g. 200 for x2")
        elif self.value < 0:
            raise ValueError("additive joker value must be nonnegative in this subset")

    @property
    def multiplier(self):
        """``mul_mult`` 的精确倍率（Fraction）；非乘法效果调用会抛 ValueError。"""
        if self.kind != "mul_mult":
            raise ValueError("multiplier is only defined for mul_mult jokers")
        from fractions import Fraction

        return Fraction(self.value, 100)

    def to_dict(self) -> dict:
        """导出 JSON dict（含 units 字段说明 value 单位，避免下游误读）。"""
        return {
            "jid": self.jid,
            "name": self.name,
            "kind": self.kind,
            "value": self.value,
            "value_unit": "hundredths_of_mult" if self.kind == "mul_mult" else "chips_or_mult",
            "condition": self.condition,
            "rarity": self.rarity,
            "buy_price": self.buy_price,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Joker":
        """从 ``to_dict`` 产物还原（忽略 value_unit 等展示字段）。"""
        return cls(
            jid=str(data["jid"]),
            name=str(data.get("name", data["jid"])),
            kind=data["kind"],
            value=int(data["value"]),
            condition=data.get("condition", "always"),
            rarity=str(data.get("rarity", "")),
            buy_price=int(data.get("buy_price", 0)),
        )


@dataclass
class GameState:
    """Ante 1 子集一局的完整状态。

    字段分三组：
    - 规则身份：``rules_version`` / ``ante`` / ``blind_idx`` / ``blind_kind`` /
      ``target`` / ``joker_slots``；
    - 资源与进度：``total_score`` / ``hands_left`` / ``discards_left`` / ``steps`` /
      ``phase`` / ``outcome``；
    - 经济（v2）：``money`` / ``reroll_cost`` / ``last_payout``；
    - 牌与 Joker：``hand`` / ``deck`` / ``discard_pile`` / ``jokers`` / ``shop_options``；
    - 随机性：``seed`` / ``rng_state``。

    经济语义：
    - ``money`` 只由「盲注结算」增加（奖励 + 剩余手数 + 未用弃牌 + 利息），只由「商店」
      减少（买入 / reroll）；出牌与弃牌都不花钱。
    - ``reroll_cost`` 只在当前商店内累加，进入下一盲注时重置为基准价。
    - ``last_payout`` 是最近一次结算的明细（奖励/手数/弃牌/利息/合计/结算后金额），
      用于 observation 与 trace 对账；进入下一盲注时清空。

    可变性：本类不做防御性拷贝；``bench.engine`` 的状态转移在 deepcopy 副本上完成。
    直接就地修改会跳过校验与转移语义，属于未受支持用法。

    Raises:
        ValueError: 结构不合法（blind_idx/资源/槽位/phase/outcome 等）。
    """

    # --- 规则身份 ---
    rules_version: str = VANILLA_SUBSET_V1.rules_version
    ante: int = 1
    blind_idx: int = 0
    blind_kind: BlindKind = "small"
    boss_effect: str | None = None
    target: int = 300
    joker_slots: int = 5
    hand_size: int = 8
    shop_enabled: bool = False
    # --- 进度 ---
    total_score: int = 0
    hands_left: int = 4
    discards_left: int = 4
    steps: int = 0
    phase: Phase = "play"
    outcome: Outcome | None = None
    # --- 经济（v2）---
    money: int = STARTING_MONEY
    reroll_cost: int = REROLL_BASE_COST
    last_payout: dict | None = None
    # --- 牌与 Joker ---
    hand: list[Card] = field(default_factory=list)
    deck: list[Card] = field(default_factory=list)
    discard_pile: list[Card] = field(default_factory=list)
    jokers: list[Joker] = field(default_factory=list)
    shop_options: list[Joker] = field(default_factory=list)
    # --- 随机性 ---
    seed: int = 0
    rng_state: str = ""

    def __post_init__(self) -> None:
        if self.blind_idx not in range(3):
            raise ValueError("blind_idx must be 0..2")
        if self.blind_kind not in ("small", "big", "boss"):
            raise ValueError(f"invalid blind_kind: {self.blind_kind!r}")
        if self.target <= 0:
            raise ValueError("target must be positive")
        if self.joker_slots < 0:
            raise ValueError("joker_slots cannot be negative")
        if self.hand_size < 0:
            raise ValueError("hand_size cannot be negative")
        if len(self.jokers) > self.joker_slots:
            raise ValueError("jokers exceed joker_slots")
        if self.hands_left < 0 or self.discards_left < 0:
            raise ValueError("hands_left and discards_left cannot be negative")
        if self.phase not in ("play", "shop", "done"):
            raise ValueError(f"invalid phase: {self.phase!r}")
        if self.outcome not in (None, "win", "loss"):
            raise ValueError(f"invalid outcome: {self.outcome!r}")
        if self.total_score < 0:
            raise ValueError("total_score cannot be negative")
        if self.money < 0:
            raise ValueError("money cannot be negative")
        if self.reroll_cost < 0:
            raise ValueError("reroll_cost cannot be negative")
        if self.last_payout is not None and not isinstance(self.last_payout, dict):
            raise ValueError("last_payout must be a dict or None")

    @property
    def deck_total(self) -> int:
        """手牌 + 抽牌堆 + 弃牌堆的总张数（标准牌组应恒为 52）。"""
        return len(self.hand) + len(self.deck) + len(self.discard_pile)


def card_to_dict(card: Card) -> dict:
    """兼容旧日志消费者：等价于 ``card.to_dict()``。"""
    return card.to_dict()


def joker_to_dict(joker: Joker) -> dict:
    """兼容旧日志消费者：等价于 ``joker.to_dict()``。"""
    return joker.to_dict()


def state_summary(state: GameState) -> dict:
    """导出紧凑状态摘要（供 trace / 旧日志消费者使用）。

    设计取舍：``hand`` / ``jokers`` / ``shop_options`` 给完整内容（决策对象），
    ``deck`` / ``discard_pile`` 只给计数以控制体积；完整牌序用
    ``bench.serialize.state_to_dict``。
    """
    return {
        "rules_version": state.rules_version,
        "ante": state.ante,
        "blind_idx": state.blind_idx,
        "blind_kind": state.blind_kind,
        "boss_effect": state.boss_effect,
        "target": state.target,
        "total_score": state.total_score,
        "hand": [card.to_dict() for card in state.hand],
        "deck_count": len(state.deck),
        "discard_pile_count": len(state.discard_pile),
        "jokers": [joker.to_dict() for joker in state.jokers],
        "joker_slots": state.joker_slots,
        "hands_left": state.hands_left,
        "discards_left": state.discards_left,
        "money": state.money,
        "phase": state.phase,
        "outcome": state.outcome,
        "steps": state.steps,
        "seed": state.seed,
    }
