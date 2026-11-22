"""实验配置、运行目录与断点续跑索引。

目录结构（一个实验 = 一个 run dir）：:

    runs/<experiment_id>/
      manifest.json          # 配置 + 规则声明 + code hash + 场景清单（一次写入）
      results.jsonl          # 每个 task 一行 EpisodeResult（append-only）
      traces/<task_id>.jsonl  # 每 episode 一个 trace（append-only）

断点续跑：``results.jsonl`` 的 ``task_id`` 是唯一键；``ExperimentStore.completed_task_ids()``
返回已完成任务，batch runner 默认跳过。task_id 含 config hash，因此改配置不会误复用旧结果。

并发：同一 run dir 只允许一个 batch 进程写入（本模块用线程锁保护进程内并发；跨进程
并发写 JSONL 不在支持范围内，需要时按 task 分片）。
"""
from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from bench.rules_version import VANILLA_SUBSET_V1, Ruleset

RESULT_SCHEMA_VERSION = 1
MANIFEST_SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def compute_code_hash(roots: Iterable[str | Path] = ("bench", "evaluation", "scenarios"),
                      base_dir: str | Path = ".") -> str:
    """对运行时 Python 源码做内容哈希（排序后逐文件 sha256，再整体 sha256）。

    用途：结果可追溯“是哪份代码跑出来的”。只哈希 ``*.py``，不含 data/runs/docs。
    """
    base = Path(base_dir)
    files: list[Path] = []
    for root in roots:
        directory = base / root
        if directory.is_dir():
            files.extend(sorted(p for p in directory.rglob("*.py") if "__pycache__" not in p.parts))
    hasher = hashlib.sha256()
    for path in files:
        rel = path.relative_to(base).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    """一次批量实验的配置（影响结果的字段进入 config_hash）。

    Attributes:
        experiment_id: 运行目录名（建议 ``<agent>-<date>-<tag>``）。
        scenario_paths: 场景来源（JSON/JSONL/目录）列表。
        agent_id: Agent 标识（模型名或脚本策略名）。
        agent_params: 影响模型输出的参数（model/temperature/max_tokens/...）。
        repeats: 每个场景重复次数；task seed = scenario.seed + repeat。
        max_steps: 覆盖场景 max_steps（None 用场景值）。
        episode_timeout_s: 单 episode 墙钟超时。
        max_concurrency: 同时运行的 episode 数。
        agent_concurrency: 同时进行模型调用的上限（脚本 Agent 可设大）。
        retry_attempts / retry_backoff_s: episode 级重试策略。
        max_invalid_actions: 连续非法动作容忍度（超过则 episode 失败）。
        oracle_enabled: 是否在运行中计算 O1 局部 oracle（用于 regret/optimality）。
        output_dir: run 根目录。
        resume / retry_failed: 断点续跑行为。
        scenario_max_count: 可选，只跑前 N 个场景（pilot 用）。
    """

    experiment_id: str
    scenario_paths: tuple[str, ...]
    agent_id: str = "oracle-greedy"
    agent_params: dict = field(default_factory=dict)
    repeats: int = 1
    max_steps: int | None = None
    episode_timeout_s: float = 60.0
    max_concurrency: int = 4
    agent_concurrency: int = 4
    retry_attempts: int = 1
    retry_backoff_s: float = 0.5
    max_invalid_actions: int = 3
    oracle_enabled: bool = True
    trace_fsync: bool = True
    output_dir: str = "runs"
    resume: bool = True
    retry_failed: bool = False
    scenario_max_count: int | None = None
    ruleset: Ruleset = VANILLA_SUBSET_V1

    def __post_init__(self) -> None:
        if not self.experiment_id or any(ch in self.experiment_id for ch in "\\/:*?\"<>|"):
            raise ValueError("experiment_id must be a filesystem-safe non-empty name")
        if self.repeats < 1:
            raise ValueError("repeats must be >= 1")
        if self.max_concurrency < 1 or self.agent_concurrency < 1:
            raise ValueError("concurrency must be >= 1")
        if self.retry_attempts < 1:
            raise ValueError("retry_attempts must be >= 1")
        if self.episode_timeout_s <= 0:
            raise ValueError("episode_timeout_s must be positive")

    def result_affecting_dict(self) -> dict:
        """影响结果的配置子集（进入 config_hash 与 task_id）。"""
        return {
            "rules_version": self.ruleset.rules_version,
            "rules_signature": self.ruleset.signature(),
            "agent_id": self.agent_id,
            "agent_params": self.agent_params,
            "repeats": self.repeats,
            "max_steps": self.max_steps,
            "max_invalid_actions": self.max_invalid_actions,
            "oracle_enabled": self.oracle_enabled,
        }

    def config_hash(self) -> str:
        """结果相关配置的 sha256（前 16 位）。并发/超时/重试不入哈希。"""
        payload = json.dumps(self.result_affecting_dict(), ensure_ascii=False,
                             sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        data = {
            "experiment_id": self.experiment_id,
            "scenario_paths": list(self.scenario_paths),
            "agent_id": self.agent_id,
            "agent_params": self.agent_params,
            "repeats": self.repeats,
            "max_steps": self.max_steps,
            "episode_timeout_s": self.episode_timeout_s,
            "max_concurrency": self.max_concurrency,
            "agent_concurrency": self.agent_concurrency,
            "retry_attempts": self.retry_attempts,
            "retry_backoff_s": self.retry_backoff_s,
            "max_invalid_actions": self.max_invalid_actions,
            "oracle_enabled": self.oracle_enabled,
            "trace_fsync": self.trace_fsync,
            "output_dir": self.output_dir,
            "resume": self.resume,
            "retry_failed": self.retry_failed,
            "scenario_max_count": self.scenario_max_count,
            "rules_version": self.ruleset.rules_version,
            "config_hash": self.config_hash(),
        }
        return data


class ExperimentStore:
    """run 目录管理：manifest / results.jsonl / traces/ 与续跑索引。

    Args:
        config: 实验配置。

    Raises:
        ValueError: run 目录已有不同配置的 manifest（防止混跑）。
    """

    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config
        self.run_dir = Path(config.output_dir) / config.experiment_id
        self.traces_dir = self.run_dir / "traces"
        self.results_path = self.run_dir / "results.jsonl"
        self.manifest_path = self.run_dir / "manifest.json"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._index: dict[str, dict] | None = None

    def write_manifest(self, *, code_hash: str, scenarios: list[dict]) -> dict:
        """写入（或校验）manifest.json。

        Args:
            code_hash: ``compute_code_hash`` 结果。
            scenarios: ``[{"scenario_id":..., "scenario_hash":...}, ...]``。

        Returns:
            manifest dict。

        Raises:
            ValueError: 已有 manifest 的 config_hash 与本次不同。
        """
        manifest = {
            "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
            "created_at": utc_now(),
            "config": self.config.to_dict(),
            "rules": self.config.ruleset.to_dict(),
            "rules_signature": self.config.ruleset.signature(),
            "code_hash": code_hash,
            "scenarios": scenarios,
            "scenario_count": len(scenarios),
        }
        if self.manifest_path.exists():
            existing = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if existing.get("config", {}).get("config_hash") != self.config.config_hash():
                raise ValueError(
                    "run dir already contains a different config; use a new experiment_id"
                )
            return existing
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest

    def append_result(self, row: dict) -> None:
        """追加一条 EpisodeResult（进程内加锁）。"""
        payload = {"result_schema_version": RESULT_SCHEMA_VERSION, "stored_at": utc_now(), **row}
        with self._lock:
            with self.results_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()

    def load_results(self) -> list[dict]:
        """读取全部结果行（按写入顺序）。"""
        if not self.results_path.exists():
            return []
        rows: list[dict] = []
        for line in self.results_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def result_index(self) -> dict[str, dict]:
        """返回 ``task_id -> 最后一条结果`` 的索引（同一 task 重跑取最新）。"""
        if self._index is None:
            index: dict[str, dict] = {}
            for row in self.load_results():
                task_id = row.get("task_id")
                if task_id:
                    index[str(task_id)] = row
            self._index = index
        return self._index

    def completed_task_ids(self, *, success_only: bool = True) -> set[str]:
        """已完成 task_id 集合。

        Args:
            success_only: True 只算 completed/truncated（规则内结束或被 max_steps 截断）；
                False 会把 agent_error/timeout 等也算“已记录”（用于 retry_failed=False
                时避免无限重跑）。
        """
        success_status = {"completed", "truncated"}
        result: set[str] = set()
        for task_id, row in self.result_index().items():
            if not success_only or row.get("status") in success_status:
                result.add(task_id)
        return result

    def trace_path(self, task_id: str, episode_index: int = 0) -> Path:
        """返回某任务的 trace 路径（重试用 episode_index 区分）。"""
        suffix = "" if episode_index == 0 else f"-r{episode_index}"
        return self.traces_dir / f"{task_id}{suffix}.jsonl"

    def invalidate(self) -> None:
        """丢弃内存索引（外部追加结果后强制重读）。"""
        self._index = None
