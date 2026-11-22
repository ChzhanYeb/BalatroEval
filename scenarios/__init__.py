"""Scenario 包：评测场景的数据模型、校验与加载。

- ``schema``：Scenario/Goal/InitialState/Constraints 数据类；
- ``validator``：规则兼容性校验（Boss 效果、扩展、ID、资源范围）；
- ``loader``：JSON/JSONL/目录加载 + 转 ``Environment.ResetSpec``。

说明：``scenarios/`` 目录同时保存 ``RULES_VERSION``（规则声明镜像）与 ``dev/``
（自造开发场景）。真实捕获场景按 plan 规划放在 ``scenarios/v3/``，本包不生成假捕获数据。
"""
from .schema import (
    SCENARIO_SCHEMA_VERSION,
    Constraints,
    Goal,
    InitialState,
    Scenario,
)
from .loader import (
    iter_scenarios,
    load_scenario,
    load_scenarios,
    scenario_from_dict,
    scenario_hash,
    to_reset_spec,
    write_scenario,
)
from .validator import validate_scenario, validate_scenarios

__all__ = [
    "SCENARIO_SCHEMA_VERSION",
    "Constraints",
    "Goal",
    "InitialState",
    "Scenario",
    "iter_scenarios",
    "load_scenario",
    "load_scenarios",
    "scenario_from_dict",
    "scenario_hash",
    "to_reset_spec",
    "write_scenario",
    "validate_scenario",
    "validate_scenarios",
]
