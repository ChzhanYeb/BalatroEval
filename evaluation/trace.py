"""Trace 记录器：每步一行 JSONL（schema_version=2），append-only。

为什么逐步一行（而不是整局一个 JSON 对象）：
- 可流式写入：episode 运行中即可落盘，崩溃时已完成的步骤不丢；
- 可单步分析：失败步定位、regret 时间序列、诊断（F1–F4）直接按行过滤；
- 可并发：每个 task 独立一个 trace 文件，无跨进程写冲突。

字段（每行都有 ``schema_version`` / ``event`` / ``run_id`` / ``task_id`` / ``timestamp``）：
- ``episode_start``：scenario、规则声明、code hash、config 摘要；
- ``step``：动作、是否合法、错误、reward、terminated/truncated、前后 state_hash、
  observation 文本、计分过程、agent/env 延迟；
- ``episode_end``：status/outcome/steps/总 reward/指标/总耗时/错误。

约束：本模块**只追加**、不重写历史；同一 task 重跑会写新文件（task_id 含 config hash，
避免同名覆盖）。写失败直接抛异常——Trace 丢证据比 episode 失败更严重。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bench.rules_version import Ruleset

TRACE_SCHEMA_VERSION = 2


def utc_now() -> str:
    """当前 UTC 时间（ISO 8601，毫秒精度）。"""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class TraceRecorder:
    """一个 episode 的 JSONL trace 写入器。

    Args:
        path: trace 文件路径（父目录自动创建）。
        run_id: 实验/批次 ID。
        task_id: 稳定任务 ID（experiment+scenario+agent+seed+config hash）。
        episode_id: episode 实例 ID（task_id + 重试序号）。
    """

    def __init__(self, path: str | Path, run_id: str, task_id: str, episode_id: str,
                 *, fsync: bool = True) -> None:
        self.path = Path(path)
        self.run_id = run_id
        self.task_id = task_id
        self.episode_id = episode_id
        self.fsync = fsync
        self._handle = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")

    # ------------------------------------------------------------------ write
    def _write(self, event: dict) -> None:
        row = {
            "schema_version": TRACE_SCHEMA_VERSION,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "episode_id": self.episode_id,
            "timestamp": utc_now(),
        }
        row.update(event)
        assert self._handle is not None
        self._handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self._handle.flush()
        if self.fsync:
            os.fsync(self._handle.fileno())

    def start(self, *, scenario: dict, ruleset: Ruleset, code_hash: str,
              config: dict, scenario_hash: str) -> None:
        """记录 episode_start（场景、规则、代码版本、配置摘要）。"""
        self._write({
            "event": "episode_start",
            "scenario": scenario,
            "scenario_hash": scenario_hash,
            "rules_version": ruleset.rules_version,
            "rules_signature": ruleset.signature(),
            "code_hash": code_hash,
            "config": config,
        })

    def step(self, *, step: int, action: dict | None, valid: bool, error: dict | None,
             reward: int, terminated: bool, truncated: bool, termination_reason: str | None,
             state_hash_before: str | None, state_hash_after: str | None,
             observation_text: str, score: dict | None,
             latency_agent_ms: float, latency_env_ms: float,
             raw_output: str | None = None, usage: dict | None = None) -> None:
        """记录一个动作步（合法与非法动作都落盘）。"""
        self._write({
            "event": "step",
            "step": step,
            "action": action,
            "valid": valid,
            "error": error,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "termination_reason": termination_reason,
            "state_hash_before": state_hash_before,
            "state_hash_after": state_hash_after,
            "observation_text": observation_text,
            "score": score,
            "latency_ms": {"agent": round(latency_agent_ms, 4),
                            "env": round(latency_env_ms, 4)},
            "raw_output": raw_output,
            "usage": usage or {},
        })

    def end(self, *, status: str, outcome: str | None, steps: int, total_reward: int,
            blinds_cleared: int, blind_scores: list[int], metrics: dict, duration_ms: float,
            error: dict | None = None) -> None:
        """记录 episode_end（终止原因、指标、总耗时）。"""
        self._write({
            "event": "episode_end",
            "status": status,
            "outcome": outcome,
            "steps": steps,
            "total_reward": total_reward,
            "blinds_cleared": blinds_cleared,
            "blind_scores": blind_scores,
            "metrics": metrics,
            "duration_ms": round(duration_ms, 4),
            "error": error,
        })

    def decision_metric(self, *, step: int, action_code: str, oracle_score: int | None,
                        actual_score: int | None, regret: float) -> None:
        """记录一步 play 决策的 oracle 对照（供离线 regret 分析）。"""
        self._write({
            "event": "decision_metric",
            "step": step,
            "action_code": action_code,
            "oracle_score": oracle_score,
            "actual_score": actual_score,
            "regret": regret,
        })

    def close(self) -> None:
        """关闭文件句柄（幂等）。"""
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def __enter__(self) -> "TraceRecorder":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def read_trace(path: str | Path) -> list[dict]:
    """读取一个 trace JSONL 文件为事件列表（逐行解析，忽略空行）。"""
    events: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def trace_step_events(events: list[dict]) -> list[dict]:
    """过滤出 step 事件。"""
    return [e for e in events if e.get("event") == "step"]


def trace_summary(events: list[dict]) -> dict:
    """从 trace 提取摘要（start/end/合法率/总奖励），供报告与校验使用。"""
    start = next((e for e in events if e.get("event") == "episode_start"), None)
    end = next((e for e in events if e.get("event") == "episode_end"), None)
    steps = trace_step_events(events)
    valid = sum(1 for s in steps if s.get("valid"))
    return {
        "scenario_id": (start or {}).get("scenario", {}).get("scenario_id"),
        "status": (end or {}).get("status"),
        "outcome": (end or {}).get("outcome"),
        "steps": len(steps),
        "valid_steps": valid,
        "legality_rate": (valid / len(steps)) if steps else None,
        "total_reward": (end or {}).get("total_reward"),
        "duration_ms": (end or {}).get("duration_ms"),
    }
