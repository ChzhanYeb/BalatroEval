"""BalatroEval v1 自定义子集规则的类型化领域模型。

职责：定义不可变的 Card / Joker（小丑牌）值对象与可变的单局状态 GameState，
并提供供日志层（bench.logging）复用的 dict 导出辅助函数。

边界／不变量：
- 这里描述的是自定义子集（custom subset），不是原版（not vanilla）复刻：
  卡牌没有增强、版本、蜡封等属性，计分口径见 bench.scoring 的公式说明。
- Card / Joker 为 frozen+slots 值对象，构造期由 __post_init__ 校验不变量。
- GameState 是可变对象；一次 state transition 由 bench.engine 在 deepcopy 副本上
  完成，调用方持有的旧状态不会被原地改写。
- rng_state 保存完整随机数状态而非 seed，原因见 GameState 类说明。

维护提示：改字段、校验或导出键之前先读 tests/test_w2_rules.py 与
bench/logging.py（state_summary 的消费者），并同步 bench/engine.py 的构造点。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SUIT_NAMES = ("spades", "hearts", "diamonds", "clubs")
SUIT_CODES = ("s", "h", "d", "c")
RANK_NAMES = {1: "A", 11: "J", 12: "Q", 13: "K"}
Phase = Literal["play", "shop", "done"]
JokerKind = Literal["add_chips", "add_mult", "mul_mult"]


@dataclass(frozen=True, slots=True, order=True)
class Card:
    """一张无修饰的标准扑克牌（不可变值对象，可哈希、可排序）。

    编码约定：suit 0..3 依次为黑桃／红心／方块／梅花，与 SUIT_CODES 下标对齐；
    rank 1..13 中 1 表示 A、11/12/13 表示 J/Q/K、2..10 为点数本身。
    rank 是「排序与牌型判断」用的序数（A 记 1，以便组成 A-2-3-4-5 顺子），
    而 chips 是「计分」用的筹码值（A 记 11），两套口径不可混用。

    card_id 是稳定卡牌 ID（形如 c7h），在标准 52 张牌组与整个 episode 内唯一，
    用于动作回放、候选动作去重与日志身份；label 只是给人看的短标签（如 7h），
    不参与任何身份比较。

    构造期不变量：suit 必须 0..3，rank 必须 1..13，越界抛 ValueError；
    frozen=True 保证实例创建后不可再赋值。
    """

    # suit：0 黑桃、1 红心、2 方块、3 梅花，数值只用于编码与排序。
    suit: int
    # rank：1=A、2..10 为点数、11=J、12=Q、13=K，用于牌型判断与排序。
    rank: int

    def __post_init__(self) -> None:
        if self.suit not in range(4):
            raise ValueError(f"suit must be 0..3, got {self.suit}")
        if self.rank not in range(1, 14):
            raise ValueError(f"rank must be 1..13, got {self.rank}")

    @property
    def card_id(self) -> str:
        """稳定卡牌 ID：形如 c{rank}{suit_code}（黑桃 A 为 c1s）。

        标准牌组内唯一、跨 episode 不变；动作记录、回放与去重都以它为准。
        返回：纯 ASCII 字符串。副作用：无。
        """
        return f"c{self.rank}{SUIT_CODES[self.suit]}"

    @property
    def label(self) -> str:
        """人类可读的短标签，如 As、10h、Ks；仅用于展示与日志阅读。

        返回：由 RANK_NAMES 与 SUIT_CODES 拼出的字符串。
        注意：展示层不要用 label 做身份判断——稳定身份应使用 card_id。
        副作用：无。
        """
        rank = RANK_NAMES.get(self.rank, str(self.rank))
        return f"{rank}{SUIT_CODES[self.suit]}"

    @property
    def chips(self) -> int:
        """该牌按自定义子集公式贡献的筹码（单牌 rank chips）。

        规则：A 记 11、J／Q／K 记 10、其余取点数本身（与原版单牌筹码口径一致）。
        返回：非负整数。副作用：无。
        注意：这里只算单牌筹码；原版（vanilla）按牌型等级给出的 hand base chips
        在本子集中被显式省略（见 bench.scoring 模块说明），因此总分不可与原版直接比较。
        """
        if self.rank == 1:
            return 11
        if self.rank >= 11:
            return 10
        return self.rank


@dataclass(frozen=True, slots=True)
class Joker:
    """一枚合成夹具 Joker（fixture），不是原版具名 Joker。

    字段：jid 为稳定 Joker ID（如 jx_mul_mult_150）；kind 决定效果类别；
    value 的语义随 kind 变化——add_chips 为筹码增量、add_mult 为倍率增量、
    mul_mult 为「百分之一」整数（150 表示 x1.5，100 表示 x1.0）；name 仅展示用。

    构造期不变量：kind 必须是三种之一；mul_mult 的 value 必须为正的百分之一；
    加法类效果的 value 不得为负（v1 子集只支持非负加法效果）。违反时抛
    ValueError，错误消息文本属于对外契约，勿改。

    fidelity 提醒：这些是合成夹具（synthetic fixtures），只模拟无条件瞬时效果；
    不得据此宣称原版分数保真度。
    """

    jid: str
    kind: JokerKind
    # value：chips、可加 mult，或百分之一整数倍的 x-mult（150 == x1.5）。
    value: int
    name: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ("add_chips", "add_mult", "mul_mult"):
            raise ValueError(f"unsupported joker kind: {self.kind}")
        if self.kind == "mul_mult" and self.value <= 0:
            raise ValueError("mul_mult value must be positive hundredths, e.g. 150 for x1.5")
        if self.kind != "mul_mult" and self.value < 0:
            raise ValueError("this v1 subset only supports nonnegative additive effects")


@dataclass
class GameState:
    """一局游戏从开局到结束的完整可变状态。

    可变性约定：本类不做防御性拷贝；bench.engine 的 play／discard／choose_joker
    先在 deepcopy 副本上推进再返回，因此调用方持有的旧状态保持不变。绕过 engine
    直接就地修改会跳过日志与 phase 结算，属于未受支持用法。

    关键字段：phase 为 play（出牌／弃牌）→ shop（商店，三关之间购买 Joker）→
    done（win／loss 终局）；rng_state 存 random.Random.getstate() 的完整 JSON 编码，
    而不是 seed——牌堆洗牌与 shop 抽样已经消费了随机流，仅凭 seed 无法复现
    「当前」随机数状态；seed 仍保留，用于统计分组与 oracle 派生采样种子。
    discard_pile 为弃牌堆，抽牌堆耗尽时由 engine 洗回 deck；shop_options 为当前
    商店候选；outcome 与 steps 为终局标记与已执行动作数。

    构造期不变量（__post_init__）：blind_idx 0..2；target>0；Joker 不超过 3 个；
    hands_left／discards_left 非负；违反抛 ValueError。
    """

    blind_idx: int  # 0..2，依次对应 bench.engine.TARGETS 的三个盲注
    target: int  # 当前盲注目标分
    total_score: int  # 当前盲注累计分，进入下一盲注时归零
    hand: list[Card]  # 手牌，列表顺序即展示顺序，动作下标快照基于它
    deck: list[Card]  # 抽牌堆，队首（下标 0）为下一张要抽的牌
    jokers: list[Joker]  # 已拥有 Joker，槽位顺序决定计分顺序（顺序敏感）
    hands_left: int  # 本盲注剩余出牌次数
    discards_left: int  # 本盲注剩余弃牌次数
    phase: Phase  # play / shop / done
    rng_state: str  # 完整 getstate() 的 JSON 文本，不是 seed，见类 docstring
    seed: int  # 开局种子，仅用于记录；复现当前随机流请用 rng_state
    # 弃牌堆：已打出的牌与主动弃掉的牌，抽牌堆耗尽时由 engine 洗回 deck。
    discard_pile: list[Card] = field(default_factory=list)
    # 当前商店候选 Joker；离开 shop 阶段时清空。
    shop_options: list[Joker] = field(default_factory=list)
    outcome: Literal["win", "loss"] | None = None  # 终局结果，未结束为 None
    steps: int = 0  # 已执行的动作数，用于日志与 oracle 采样种子的派生

    def __post_init__(self) -> None:
        if self.blind_idx not in range(3):
            raise ValueError("blind_idx must be 0..2")
        if self.target <= 0:
            raise ValueError("target must be positive")
        if len(self.jokers) > 3:
            raise ValueError("at most 3 jokers are allowed")
        if self.hands_left < 0 or self.discards_left < 0:
            raise ValueError("hands_left and discards_left cannot be negative")


def card_to_dict(card: Card) -> dict[str, int | str]:
    """把一张牌导出为 JSON 友好的 dict（id／suit／rank）。

    同时给出稳定卡牌 ID 与数值编码，便于日志审计与人工排查；派生值
    （label／chips）不落库，避免编码规则调整后日志与代码失同步。
    返回：可 json.dumps 的 dict。异常：无。副作用：无。
    """
    return {"id": card.card_id, "suit": card.suit, "rank": card.rank}


def joker_to_dict(joker: Joker) -> dict[str, int | str]:
    """把一枚 Joker 导出为 JSON 友好的 dict（jid／kind／value／name）。

    消费方必须按 kind 解释 value：mul_mult 的 150 表示 x1.5，不能当作
    倍率数值直接运算。返回：可 json.dumps 的 dict。异常／副作用：无。
    """
    return {"jid": joker.jid, "kind": joker.kind, "value": joker.value, "name": joker.name}


def state_summary(state: GameState) -> dict:
    """导出写日志用的状态摘要（bench.logging 写入 state_before／state_after）。

    设计取舍：hand／jokers／shop_options 给完整内容（它们是决策对象），
    deck／discard_pile 只给计数以控制 JSONL 体积；需要核对具体牌序时，
    应结合动作流与 rng_state 做回放，而不是依赖摘要本身。
    返回：可 JSON 序列化的 dict，其键集合即日志 schema（schema_version=1）。
    异常：无。副作用：无，不修改 state；新增 GameState 字段时要同步这里。
    """
    return {
        "blind_idx": state.blind_idx,
        "target": state.target,
        "total_score": state.total_score,
        "hand": [card_to_dict(c) for c in state.hand],
        "deck_count": len(state.deck),
        "discard_pile_count": len(state.discard_pile),
        "jokers": [joker_to_dict(j) for j in state.jokers],
        "hands_left": state.hands_left,
        "discards_left": state.discards_left,
        "phase": state.phase,
        "seed": state.seed,
        "rng_state": state.rng_state,
        "shop_options": [joker_to_dict(j) for j in state.shop_options],
        "outcome": state.outcome,
        "steps": state.steps,
    }
