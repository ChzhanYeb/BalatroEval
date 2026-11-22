"""Scenario 加载：JSON/JSONL → ``Scenario`` → ``Environment.ResetSpec``。

支持格式：
- 单个 JSON 对象（``scenarios/dev/*.json``）；
- JSONL（每行一个 scenario，适合大规模场景集）；
- 目录（按文件名排序读取其中 ``*.json``）。

加载时立即做语义校验，保证 runner 拿到的场景一定可执行；校验失败抛
``InvalidActionError``/``UnsupportedRuleError``，错误信息带字段名。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

from bench.environment import ResetSpec
from bench.errors import BAD_REQUEST, InvalidActionError
from bench.rules_version import VANILLA_SUBSET_V1, Ruleset, ruleset_for

from .schema import Scenario
from .validator import validate_scenario


def scenario_from_dict(data: dict, ruleset: Ruleset = VANILLA_SUBSET_V1) -> Scenario:
    """解析 + 校验单个 scenario dict。

    Raises:
        InvalidActionError / UnsupportedRuleError: 见 ``validator.validate_scenario``。
    """
    scenario = Scenario.from_dict(data)
    validate_scenario(scenario, ruleset, raw=data)
    return scenario


def load_scenario(path: str | Path, ruleset: Ruleset = VANILLA_SUBSET_V1) -> Scenario:
    """读取单个 JSON 场景文件并校验。"""
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidActionError(BAD_REQUEST, f"invalid JSON in {path}: {exc}") from exc
    return scenario_from_dict(data, ruleset)


def iter_scenarios(path: str | Path, ruleset: Ruleset = VANILLA_SUBSET_V1) -> Iterator[Scenario]:
    """遍历一个 scenario 来源（JSON / JSONL / 目录）。"""
    target = Path(path)
    if target.is_dir():
        for child in sorted(target.glob("*.json")):
            yield load_scenario(child, ruleset)
        return
    suffix = target.suffix.lower()
    if suffix == ".jsonl":
        for line_no, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise InvalidActionError(BAD_REQUEST, f"invalid JSONL at line {line_no}: {exc}") from exc
            yield scenario_from_dict(data, ruleset)
        return
    yield load_scenario(target, ruleset)


def load_scenarios(paths: str | Path | Iterable[str | Path],
                   ruleset: Ruleset = VANILLA_SUBSET_V1) -> list[Scenario]:
    """读取多个来源并做批量校验（重复 scenario_id 会被拒绝）。"""
    if isinstance(paths, (str, Path)):
        source_list = [paths]
    else:
        source_list = list(paths)
    scenarios: list[Scenario] = []
    seen: set[str] = set()
    for source in source_list:
        for scenario in iter_scenarios(source, ruleset):
            if scenario.scenario_id in seen:
                raise InvalidActionError(BAD_REQUEST, f"duplicate scenario_id: {scenario.scenario_id}")
            seen.add(scenario.scenario_id)
            scenarios.append(scenario)
    return scenarios


def scenario_hash(scenario: Scenario) -> str:
    """场景内容的 sha256（用于 task_id/manifest 去重）。"""
    payload = json.dumps(scenario.to_dict(), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def to_reset_spec(scenario: Scenario) -> ResetSpec:
    """把 Scenario 转成 Environment 的 ResetSpec。

    Raises:
        ValueError: extensions 非空（v2 起不再支持任何扩展；正常应已被 validator 拦截）。
    """
    ruleset = ruleset_for(scenario.extensions)
    allowed = scenario.constraints.allowed_action_kinds
    if allowed is None:
        if scenario.decision_type == "play":
            allowed = ("play",)
        elif scenario.decision_type == "discard":
            allowed = ("discard",)
        elif scenario.decision_type == "shop":
            allowed = ("choose_joker", "sell_joker", "reroll_shop")
    return ResetSpec(
        seed=scenario.seed,
        hand_ids=scenario.initial_state.hand_ids,
        joker_ids=scenario.initial_state.joker_ids,
        ruleset=ruleset,
        allowed_action_kinds=tuple(allowed) if allowed is not None else None,
        max_steps=scenario.constraints.max_steps,
        blind_idx=scenario.initial_state.blind_idx,
        total_score=scenario.initial_state.total_score,
        hands_left=scenario.initial_state.hands_left,
        discards_left=scenario.initial_state.discards_left,
        target=scenario.initial_state.target,
        money=scenario.initial_state.money,
        shop_open=scenario.initial_state.shop_open,
        scenario_id=scenario.scenario_id,
    )


def write_scenario(path: str | Path, scenario: Scenario) -> None:
    """把场景写成 JSON 文件（父目录自动创建；UTF-8）。"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(scenario.to_dict(), ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
