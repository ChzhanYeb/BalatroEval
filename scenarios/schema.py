"""Scenario（评测场景）数据模型：固定初始局面 + 目标 + 约束 + 元数据。

Scenario 是评测的最小单位，对应两种用法：
1. **完整 Ante 1 episode**：只给 seed/初始 Joker，环境按规则发牌；
2. **固定决策点**：给 hand_ids + 资源/分数，限制动作种类（play 或 discard），用于
   Local Regret / Action Optimality 等单步指标。

设计边界：
- 场景数据只描述**初始状态与约束**，不包含 oracle 结果（oracle 由评测层现场计算，
  避免把答案写进数据）；
- 场景必须声明 ``rules_version``；规则不匹配时校验失败（不允许静默降级）；
- 场景显式声明使用哪些 benchmark 扩展（如 ``free_joker_choice``），未声明的扩展
  一律不启用。

Schema 版本：``SCENARIO_SCHEMA_VERSION = 1``（字段变更必须升版本并更新
docs/implementation/data-schema.md）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bench.errors import BAD_REQUEST, InvalidActionError
from bench.rules_version import VANILLA_SUBSET_V1

SCENARIO_SCHEMA_VERSION = 1
VALID_DECISION_TYPES = ("episode", "play", "discard")
VALID_GOAL_TYPES = ("clear_ante1", "maximize_score", "reach_score")
VALID_ORIGINS = ("synthetic_dev", "real_capture", "real_counterfactual")


@dataclass(frozen=True, slots=True)
class Goal:
    """场景目标。

    Attributes:
        type: ``clear_ante1``（清完 Ante 1 三盲注）/ ``maximize_score``（尽量高分）/
            ``reach_score``（达到 target）。
        target: ``reach_score`` 必填；其余可选，用于记录期望分。
    """

    type: str = "clear_ante1"
    target: int | None = None

    def to_dict(self) -> dict:
        return {"type": self.type, "target": self.target}


@dataclass(frozen=True, slots=True)
class InitialState:
    """初始状态覆盖项；None 表示按规则默认。

    Attributes:
        hand_ids: 固定手牌（稳定 ID，按顺序）；None 表示按 seed 发牌。
        joker_ids: 初始 Joker（稳定 ID，按槽位顺序）。
        blind_idx: 0/1/2；None 表示 0（Small）。
        total_score: 当前盲注已得分。
        hands_left / discards_left: 资源覆盖；None 表示规则默认。
        target: 目标分覆盖；None 表示按盲注定义。
    """

    hand_ids: tuple[str, ...] | None = None
    joker_ids: tuple[str, ...] = ()
    blind_idx: int | None = None
    total_score: int | None = None
    hands_left: int | None = None
    discards_left: int | None = None
    target: int | None = None

    def to_dict(self) -> dict:
        return {
            "hand_ids": list(self.hand_ids) if self.hand_ids is not None else None,
            "joker_ids": list(self.joker_ids),
            "blind_idx": self.blind_idx,
            "total_score": self.total_score,
            "hands_left": self.hands_left,
            "discards_left": self.discards_left,
            "target": self.target,
        }


@dataclass(frozen=True, slots=True)
class Constraints:
    """场景约束。

    Attributes:
        max_steps: episode 步数上限；None 表示不限。
        allowed_action_kinds: 允许的动作种类；None 表示不限制。decision_type=play 时
            默认 ``("play",)``，decision_type=discard 时默认 ``("discard",)``。
    """

    max_steps: int | None = None
    allowed_action_kinds: tuple[str, ...] | None = None

    def to_dict(self) -> dict:
        return {
            "max_steps": self.max_steps,
            "allowed_action_kinds": list(self.allowed_action_kinds)
            if self.allowed_action_kinds is not None else None,
        }


@dataclass(frozen=True, slots=True)
class Scenario:
    """一个评测场景（不可变）。

    Attributes:
        scenario_id: 稳定 ID（建议 ``<origin>-<配置>-<seed>``）。
        rules_version: 必须与当前 Ruleset 一致。
        seed: 随机种子。
        origin: 来源（synthetic_dev / real_capture / real_counterfactual）。
        decision_type: episode / play / discard。
        goal: 目标。
        initial_state: 初始状态覆盖。
        constraints: 约束。
        extensions: benchmark 扩展名列表（如 free_joker_choice）。
        boss_blind: Boss 盲注声明；``effect`` 非空表示请求未实现的效果（会被拒）。
        metadata: 描述/标签/捕获 ID 等自由字段（只读展示，不参与规则）。
    """

    scenario_id: str
    rules_version: str = VANILLA_SUBSET_V1.rules_version
    seed: int = 0
    origin: str = "synthetic_dev"
    decision_type: str = "episode"
    goal: Goal = field(default_factory=Goal)
    initial_state: InitialState = field(default_factory=InitialState)
    constraints: Constraints = field(default_factory=Constraints)
    extensions: tuple[str, ...] = ()
    boss_blind: dict | None = None
    metadata: dict = field(default_factory=dict)
    scenario_schema_version: int = SCENARIO_SCHEMA_VERSION

    def to_dict(self) -> dict:
        """导出 JSON 友好 dict（用于落盘与哈希）。"""
        return {
            "scenario_schema_version": self.scenario_schema_version,
            "scenario_id": self.scenario_id,
            "rules_version": self.rules_version,
            "seed": self.seed,
            "origin": self.origin,
            "decision_type": self.decision_type,
            "goal": self.goal.to_dict(),
            "initial_state": self.initial_state.to_dict(),
            "constraints": self.constraints.to_dict(),
            "extensions": list(self.extensions),
            "boss_blind": self.boss_blind,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Scenario":
        """从 JSON dict 构造（只做结构解析；语义校验见 ``scenarios.validator``）。

        Raises:
            InvalidActionError: 缺字段/类型错误（BAD_REQUEST）。
        """
        if not isinstance(data, dict):
            raise InvalidActionError(BAD_REQUEST, "scenario must be a JSON object")
        version = data.get("scenario_schema_version", SCENARIO_SCHEMA_VERSION)
        if version != SCENARIO_SCHEMA_VERSION:
            raise InvalidActionError(
                BAD_REQUEST, f"unsupported scenario_schema_version: {version!r}",
                {"supported": SCENARIO_SCHEMA_VERSION},
            )
        try:
            goal_raw = data.get("goal") or {}
            init_raw = data.get("initial_state") or {}
            cons_raw = data.get("constraints") or {}
            goal = Goal(type=str(goal_raw.get("type", "clear_ante1")),
                        target=_opt_int(goal_raw.get("target")))
            initial = InitialState(
                hand_ids=_opt_tuple(init_raw.get("hand_ids")),
                joker_ids=tuple(init_raw.get("joker_ids") or ()),
                blind_idx=_opt_int(init_raw.get("blind_idx")),
                total_score=_opt_int(init_raw.get("total_score")),
                hands_left=_opt_int(init_raw.get("hands_left")),
                discards_left=_opt_int(init_raw.get("discards_left")),
                target=_opt_int(init_raw.get("target")),
            )
            allowed = cons_raw.get("allowed_action_kinds")
            constraints = Constraints(
                max_steps=_opt_int(cons_raw.get("max_steps")),
                allowed_action_kinds=tuple(allowed) if allowed is not None else None,
            )
            return cls(
                scenario_id=str(data["scenario_id"]),
                rules_version=str(data.get("rules_version", VANILLA_SUBSET_V1.rules_version)),
                seed=int(data.get("seed", 0)),
                origin=str(data.get("origin", "synthetic_dev")),
                decision_type=str(data.get("decision_type", "episode")),
                goal=goal,
                initial_state=initial,
                constraints=constraints,
                extensions=tuple(data.get("extensions") or ()),
                boss_blind=data.get("boss_blind"),
                metadata=dict(data.get("metadata") or {}),
                scenario_schema_version=version,
            )
        except KeyError as exc:
            raise InvalidActionError(BAD_REQUEST, f"scenario missing required field: {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise InvalidActionError(BAD_REQUEST, f"invalid scenario field: {exc}") from exc


def _opt_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidActionError(BAD_REQUEST, f"expected integer or null, got {type(value).__name__}")
    return value


def _opt_tuple(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or not all(isinstance(x, str) for x in value):
        raise InvalidActionError(BAD_REQUEST, "hand_ids must be a list of strings")
    return tuple(value)
