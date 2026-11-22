"""Scenario 语义校验：把“数据结构正确”升级为“规则上可执行”。

校验项（失败一律抛 ``InvalidActionError`` / ``UnsupportedRuleError``，不静默降级）：
- rules_version 与当前 Ruleset 一致；
- origin / decision_type / goal 合法；
- 初始手牌/Joker 全部是合法稳定 ID、不重复、不超过容量；
- 盲注/资源/目标分在规则范围内；
- **Boss 效果**：任何非空 effect 都拒绝（子集未实现 Boss 效果，见 Ruleset.excluded）；
- extensions 只允许 ``free_joker_choice``，且 real_capture/real_counterfactual 场景不得使用；
- real_capture 场景必须有 metadata.capture_id；
- 未知字段拒绝（防止拼写错误被静默忽略）。
"""
from __future__ import annotations

from typing import Iterable

from bench.cards import card_from_stable_id
from bench.errors import BAD_REQUEST, NOT_ALLOWED, UnsupportedRuleError, InvalidActionError
from bench.jokers import CATALOG_BY_ID
from bench.rules_version import SHOP_EXTENSION, VANILLA_SUBSET_V1, Ruleset

from .schema import (
    SCENARIO_SCHEMA_VERSION,
    Scenario,
    VALID_DECISION_TYPES,
    VALID_GOAL_TYPES,
    VALID_ORIGINS,
)

_ALLOWED_TOP_LEVEL = {
    "scenario_schema_version", "scenario_id", "rules_version", "seed", "origin",
    "decision_type", "goal", "initial_state", "constraints", "extensions",
    "boss_blind", "metadata",
}
_ALLOWED_ACTIONS = {"play", "discard", "choose_joker"}


def validate_scenario(scenario: Scenario, ruleset: Ruleset = VANILLA_SUBSET_V1,
                      *, raw: dict | None = None) -> None:
    """校验一个 Scenario；通过返回 None，失败抛异常。

    Args:
        scenario: 已解析的场景。
        ruleset: 目标规则集（默认 Ante 1 子集）。
        raw: 可选原始 dict，用于拒绝未知顶层字段。

    Raises:
        InvalidActionError: 字段值非法（BAD_REQUEST）或动作种类不被允许（NOT_ALLOWED）。
        UnsupportedRuleError: 请求了未实现的规则（Boss 效果、未知扩展）。
    """
    if raw is not None:
        unknown = sorted(set(raw) - _ALLOWED_TOP_LEVEL)
        if unknown:
            raise InvalidActionError(BAD_REQUEST, f"unknown scenario fields: {unknown}",
                                     {"unknown": unknown})
    if scenario.scenario_schema_version != SCENARIO_SCHEMA_VERSION:
        raise InvalidActionError(BAD_REQUEST, "scenario schema version mismatch")
    if not scenario.scenario_id or len(scenario.scenario_id) > 120:
        raise InvalidActionError(BAD_REQUEST, "scenario_id must be 1..120 chars")
    if scenario.rules_version != ruleset.rules_version:
        raise InvalidActionError(
            BAD_REQUEST,
            f"scenario rules_version {scenario.rules_version!r} != engine {ruleset.rules_version!r}",
            {"scenario": scenario.rules_version, "engine": ruleset.rules_version},
        )
    if scenario.origin not in VALID_ORIGINS:
        raise InvalidActionError(BAD_REQUEST, f"invalid origin: {scenario.origin!r}")
    if scenario.decision_type not in VALID_DECISION_TYPES:
        raise InvalidActionError(BAD_REQUEST, f"invalid decision_type: {scenario.decision_type!r}")
    if scenario.goal.type not in VALID_GOAL_TYPES:
        raise InvalidActionError(BAD_REQUEST, f"invalid goal.type: {scenario.goal.type!r}")
    if scenario.goal.type == "reach_score" and (scenario.goal.target is None or scenario.goal.target <= 0):
        raise InvalidActionError(BAD_REQUEST, "goal.target must be positive for reach_score")

    # 扩展
    unknown_ext = [name for name in scenario.extensions if name != SHOP_EXTENSION]
    if unknown_ext:
        raise UnsupportedRuleError(f"unsupported scenario extensions: {unknown_ext}",
                                   {"extensions": unknown_ext})
    if scenario.extensions and scenario.origin != "synthetic_dev":
        raise UnsupportedRuleError(
            "benchmark extensions are only allowed for synthetic_dev scenarios",
            {"origin": scenario.origin, "extensions": list(scenario.extensions)},
        )

    # 动作种类约束
    allowed = scenario.constraints.allowed_action_kinds
    if scenario.decision_type == "play":
        allowed = allowed or ("play",)
        if set(allowed) != {"play"}:
            raise InvalidActionError(NOT_ALLOWED, "play decision scenarios must allow only 'play'")
    elif scenario.decision_type == "discard":
        allowed = allowed or ("discard",)
        if set(allowed) != {"discard"}:
            raise InvalidActionError(NOT_ALLOWED, "discard decision scenarios must allow only 'discard'")
    if allowed is not None:
        bad = sorted(set(allowed) - _ALLOWED_ACTIONS)
        if bad:
            raise InvalidActionError(BAD_REQUEST, f"invalid allowed_action_kinds: {bad}")
        if "choose_joker" in allowed and SHOP_EXTENSION not in scenario.extensions:
            raise InvalidActionError(NOT_ALLOWED, "choose_joker requires the free_joker_choice extension")

    if scenario.constraints.max_steps is not None and scenario.constraints.max_steps <= 0:
        raise InvalidActionError(BAD_REQUEST, "constraints.max_steps must be positive")

    # 初始状态
    initial = scenario.initial_state
    if initial.hand_ids is not None:
        if len(initial.hand_ids) > ruleset.hand_size:
            raise InvalidActionError(BAD_REQUEST, "hand exceeds hand_size",
                                     {"hand": len(initial.hand_ids), "limit": ruleset.hand_size})
        _validate_card_ids(initial.hand_ids, "hand_ids")
    _validate_joker_ids(initial.joker_ids, ruleset)
    blind_idx = 0 if initial.blind_idx is None else initial.blind_idx
    if blind_idx not in (0, 1, 2):
        raise InvalidActionError(BAD_REQUEST, "initial_state.blind_idx must be 0..2")
    if initial.total_score is not None and initial.total_score < 0:
        raise InvalidActionError(BAD_REQUEST, "initial_state.total_score cannot be negative")
    if initial.target is not None and initial.target <= 0:
        raise InvalidActionError(BAD_REQUEST, "initial_state.target must be positive")
    if initial.hands_left is not None and not 0 <= initial.hands_left <= ruleset.hands_per_blind:
        raise InvalidActionError(BAD_REQUEST, "initial_state.hands_left out of range")
    if initial.discards_left is not None and not 0 <= initial.discards_left <= ruleset.discards_per_blind:
        raise InvalidActionError(BAD_REQUEST, "initial_state.discards_left out of range")

    # Boss：Ante 1 的 Boss 一定存在效果；子集未实现 → 场景必须显式声明 effect=None，
    # 且不得请求任何具名效果。
    boss = scenario.boss_blind
    if boss is not None:
        if not isinstance(boss, dict):
            raise InvalidActionError(BAD_REQUEST, "boss_blind must be an object or null")
        effect = boss.get("effect")
        if effect not in (None, "none"):
            raise UnsupportedRuleError(
                f"boss effect {effect!r} is not implemented in this ruleset",
                {"boss_blind": boss},
            )
    if blind_idx == 2 and boss is None:
        raise InvalidActionError(
            BAD_REQUEST,
            "boss blind scenarios must declare boss_blind with effect=null (effects are excluded)",
        )
    # 场景起点不应已经通过当前盲注。
    if initial.total_score is not None:
        target = initial.target if initial.target is not None else ruleset.blind(blind_idx).target
        if initial.total_score >= target:
            raise InvalidActionError(BAD_REQUEST, "initial total_score already clears the blind")

    if scenario.origin == "real_capture" and not scenario.metadata.get("capture_id"):
        raise InvalidActionError(BAD_REQUEST, "real_capture scenarios require metadata.capture_id")


def validate_scenarios(scenarios: Iterable[Scenario], ruleset: Ruleset = VANILLA_SUBSET_V1) -> None:
    """批量校验；任一失败即抛出（fail fast）。"""
    seen: set[str] = set()
    for scenario in scenarios:
        validate_scenario(scenario, ruleset)
        if scenario.scenario_id in seen:
            raise InvalidActionError(BAD_REQUEST, f"duplicate scenario_id: {scenario.scenario_id}")
        seen.add(scenario.scenario_id)


def _validate_card_ids(card_ids: Iterable[str], field: str) -> None:
    ids = list(card_ids)
    if len(set(ids)) != len(ids):
        raise InvalidActionError(BAD_REQUEST, f"{field} contains duplicate card ids")
    for cid in ids:
        card_from_stable_id(cid)  # 未知 ID 会抛 UNKNOWN_CARD


def _validate_joker_ids(joker_ids: Iterable[str], ruleset: Ruleset) -> None:
    ids = list(joker_ids)
    if len(ids) > ruleset.joker_slots:
        raise InvalidActionError(BAD_REQUEST, "starting jokers exceed joker slots")
    if len(set(ids)) != len(ids):
        raise InvalidActionError(BAD_REQUEST, "duplicate starting jokers")
    for jid in ids:
        if jid not in CATALOG_BY_ID:
            raise InvalidActionError(BAD_REQUEST, f"unknown joker id: {jid!r}",
                                     {"joker_id": jid})
