"""Batch Runner：把 (scenario × agent × repeat) 展开成任务并发执行。

并发策略（刻意分层，见 docs/implementation/evaluation-execution.md）：
- **episode 内**：严格顺序（下一动作依赖上一状态），不能并行；
- **episode 间**：互相独立，用 ``asyncio.Semaphore(max_concurrency)`` 限制同时运行的
  episode 数；每个 episode 独立 Environment / Agent / trace 文件；
- **模型调用**：额外的 ``agent_concurrency`` 信号量，独立于 episode 并发（一个慢模型
  不会拖垮所有 episode 的调度）；
- **Trace/Result 写入**：每个 task 独立 trace 文件；结果由 ``ExperimentStore`` 加锁 append。

失败处理：
- 每个任务重试 ``retry_attempts`` 次（退避 ``retry_backoff_s``），只对非成功状态重试；
- 单任务异常被捕获并转成 ``env_error`` 结果，不影响其他任务；
- 断点续跑：默认跳过 results.jsonl 中已记录的任务；``retry_failed=True`` 时只跳过成功项。
"""
from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from typing import Callable, Sequence

from bench.errors import AGENT_ERROR, INTERNAL
from bench.rules_version import Ruleset, VANILLA_SUBSET_V1
from scenarios.loader import scenario_hash
from scenarios.schema import Scenario

from .agents import (
    Agent,
    AsyncAgent,
    FirstLegalAgent,
    HttpChatAgent,
    OracleGreedyAgent,
    RandomAgent,
    ResponseCache,
    TokenBucket,
    decide_async,
)
from .config import ExperimentConfig, ExperimentStore, compute_code_hash
from .episode_runner import EpisodeResult, run_episode_async

TASK_SCHEMA_VERSION = 1
SUCCESS_STATUSES = {"completed", "truncated"}


@dataclass(frozen=True, slots=True)
class Task:
    """一个待执行 episode 的全部输入（可序列化，便于分片/重放）。"""

    task_id: str
    scenario: Scenario
    seed: int
    repeat_index: int
    task_schema_version: int = TASK_SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "scenario_id": self.scenario.scenario_id,
            "seed": self.seed,
            "repeat_index": self.repeat_index,
        }


def make_task_id(experiment_id: str, scenario: Scenario, agent_id: str,
                 repeat_index: int, config_hash: str) -> str:
    """稳定 task id：experiment + scenario 内容 + agent + repeat + config hash。"""
    payload = "|".join([
        experiment_id, scenario.scenario_id, scenario_hash(scenario),
        agent_id, str(repeat_index), config_hash,
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def build_tasks(scenarios: Sequence[Scenario], config: ExperimentConfig) -> list[Task]:
    """按 repeats 展开任务；task seed = scenario.seed + repeat_index。"""
    tasks: list[Task] = []
    for scenario in scenarios:
        for repeat in range(config.repeats):
            seed = scenario.seed + repeat
            tasks.append(Task(
                task_id=make_task_id(config.experiment_id, scenario, config.agent_id,
                                     repeat, config.config_hash()),
                scenario=scenario, seed=seed, repeat_index=repeat,
            ))
    return tasks


def default_agent_factory(config: ExperimentConfig) -> Callable[[Task], Agent | AsyncAgent]:
    """按 ``config.agent_id`` 构造 Agent 工厂（每个 task 一个新实例）。

    支持的脚本 Agent：``oracle-greedy`` / ``random`` / ``first-legal``；
    ``http`` 使用 ``agent_params``：model/base_url 环境变量见 agents.HttpChatAgent。
    """
    agent_id = config.agent_id
    params = dict(config.agent_params)

    def factory(task: Task) -> Agent | AsyncAgent:
        if agent_id == "oracle-greedy":
            return OracleGreedyAgent(discard_samples=int(params.get("discard_samples", 10)))
        if agent_id == "random":
            return RandomAgent(seed=task.seed)
        if agent_id == "first-legal":
            return FirstLegalAgent()
        if agent_id == "http":
            cache = ResponseCache(params["cache_path"]) if params.get("cache_path") else None
            limiter = None
            if params.get("rate_per_second"):
                limiter = TokenBucket(float(params["rate_per_second"]),
                                      int(params.get("burst", 1)))
            return HttpChatAgent(
                agent_id=str(params.get("agent_id", "http")),
                model=str(params.get("model", "unknown")),
                temperature=float(params.get("temperature", 0.0)),
                max_tokens=int(params.get("max_tokens", 256)),
                cache=cache,
                rate_limiter=limiter,
                max_retries=int(params.get("max_retries", 3)),
                backoff_s=float(params.get("backoff_s", 0.5)),
                timeout_s=float(params.get("timeout_s", 30.0)),
            )
        raise ValueError(f"unknown agent_id: {agent_id!r}")

    return factory


class _SemaphoreAgent:
    """给任意 Agent 加“模型调用并发上限”的包装（不改变决策语义）。"""

    def __init__(self, inner: Agent | AsyncAgent, semaphore: asyncio.Semaphore) -> None:
        self.inner = inner
        self.semaphore = semaphore
        self.agent_id = getattr(inner, "agent_id", "wrapped")

    async def decide_async(self, observation, legal_actions):
        async with self.semaphore:
            return await decide_async(self.inner, observation, legal_actions)


@dataclass
class BatchSummary:
    """批次执行摘要（供 CLI/报告使用）。"""

    run_id: str
    run_dir: str
    config_hash: str
    code_hash: str
    results: list[EpisodeResult] = field(default_factory=list)
    counts: dict = field(default_factory=dict)
    skipped: int = 0
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "run_dir": self.run_dir,
            "config_hash": self.config_hash,
            "code_hash": self.code_hash,
            "counts": self.counts,
            "skipped": self.skipped,
            "duration_ms": round(self.duration_ms, 4),
            "results": [r.to_dict() for r in self.results],
        }


async def run_batch_async(
    scenarios: Sequence[Scenario],
    config: ExperimentConfig,
    *,
    agent_factory: Callable[[Task], Agent | AsyncAgent] | None = None,
    store: ExperimentStore | None = None,
    code_hash: str | None = None,
    max_tasks: int | None = None,
) -> BatchSummary:
    """异步执行一批 episode。

    Args:
        scenarios: 已校验场景列表。
        config: 实验配置（并发/重试/超时/续跑）。
        agent_factory: task → Agent；None 时按 ``config.agent_id`` 选内置工厂。
        store: 结果目录；None 时自动创建。
        code_hash: 代码 hash；None 时现场计算。
        max_tasks: 可选，只跑前 N 个任务（pilot/调试）。

    Returns:
        BatchSummary（含每个 EpisodeResult）。

    Raises:
        ValueError: manifest 配置不一致（run dir 混用）。
        OSError: Trace 写入失败（证据丢失不允许静默忽略）。
    """
    started = time.perf_counter()
    store = store or ExperimentStore(config)
    code_hash = code_hash or compute_code_hash()
    scenario_rows = [{"scenario_id": s.scenario_id, "scenario_hash": scenario_hash(s)}
                     for s in scenarios]
    store.write_manifest(code_hash=code_hash, scenarios=scenario_rows)

    tasks = build_tasks(scenarios, config)
    if config.scenario_max_count is not None:
        tasks = tasks[: config.scenario_max_count]
    if max_tasks is not None:
        tasks = tasks[:max_tasks]

    done = store.completed_task_ids(success_only=config.retry_failed)
    pending = [t for t in tasks if t.task_id not in done]
    skipped = len(tasks) - len(pending)

    factory = agent_factory or default_agent_factory(config)
    episode_sem = asyncio.Semaphore(config.max_concurrency)
    agent_sem = asyncio.Semaphore(config.agent_concurrency)
    results: list[EpisodeResult] = []

    async def run_one(task: Task) -> EpisodeResult:
        async with episode_sem:
            last_result: EpisodeResult | None = None
            for attempt in range(config.retry_attempts):
                try:
                    agent = _SemaphoreAgent(factory(task), agent_sem)
                except Exception as exc:  # noqa: BLE001 - Agent 构造失败：隔离为 agent_error
                    result = _fallback_result(task, config, exc, status="agent_error")
                    store.append_result(result.to_dict())
                    last_result = result
                    if attempt == config.retry_attempts - 1:
                        return result
                    await asyncio.sleep(config.retry_backoff_s * (2 ** attempt))
                    continue
                try:
                    result = await run_episode_async(
                        task.scenario, agent, config, store, task.task_id,
                        code_hash=code_hash, episode_index=attempt,
                        seed_override=task.seed,
                    )
                except Exception as exc:  # noqa: BLE001 - trace 写失败/未知异常：隔离为 env_error
                    result = _fallback_result(task, config, exc)
                    store.append_result(result.to_dict())
                last_result = result
                if result.status in SUCCESS_STATUSES or attempt == config.retry_attempts - 1:
                    return result
                await asyncio.sleep(config.retry_backoff_s * (2 ** attempt))
            assert last_result is not None
            return last_result

    outcomes = await asyncio.gather(*(run_one(t) for t in pending), return_exceptions=False)
    results.extend(outcomes)
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    counts["skipped"] = skipped
    counts["total"] = len(results) + skipped
    return BatchSummary(
        run_id=config.experiment_id, run_dir=str(store.run_dir),
        config_hash=config.config_hash(), code_hash=code_hash,
        results=results, counts=counts, skipped=skipped,
        duration_ms=(time.perf_counter() - started) * 1000,
    )


def _fallback_result(task: Task, config: ExperimentConfig, exc: Exception,
                     *, status: str = "env_error") -> EpisodeResult:
    """当 runner 无法写出正常结果（例如 trace 写失败）时，构造最小错误结果。

    说明：这不是“成功降级”——trace 丢失会在 ``error`` 里显式记录；调用方/报告不得把
    这类结果当作有效评测。
    """
    return EpisodeResult(
        task_id=task.task_id,
        run_id=config.experiment_id,
        episode_id=f"{task.task_id}-failed",
        scenario_id=task.scenario.scenario_id,
        scenario_hash=scenario_hash(task.scenario),
        agent_id=config.agent_id,
        seed=task.seed,
        decision_type=task.scenario.decision_type,
        status=status,
        error={"code": (AGENT_ERROR if status == "agent_error" else INTERNAL),
               "message": f"{type(exc).__name__}: {exc}"},
    )


def run_batch(
    scenarios: Sequence[Scenario],
    config: ExperimentConfig,
    *,
    agent_factory: Callable[[Task], Agent | AsyncAgent] | None = None,
    store: ExperimentStore | None = None,
    code_hash: str | None = None,
    max_tasks: int | None = None,
) -> BatchSummary:
    """同步入口（内部 ``asyncio.run``）；在已有事件循环中请用 ``run_batch_async``。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(run_batch_async(
            scenarios, config, agent_factory=agent_factory, store=store,
            code_hash=code_hash, max_tasks=max_tasks,
        ))
    raise RuntimeError("run_batch() cannot be called inside a running event loop")
