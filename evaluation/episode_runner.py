"""Episode Runner：驱动一个 Environment + Agent 跑完一局，并落 Trace/Result。

职责：
- 每个 episode 独立 Environment（reset 后无人共享可变状态）；
- 逐步调用 Agent → 校验/执行动作 → 记录 trace（合法与非法都记）；
- 计算单 episode 指标：legality、play 决策的 local regret / optimality、分数进度、
  agent/env 延迟、token 用量；
- 终止语义：terminated（win/loss）与 truncated（max_steps/超时）分开记录；
- 失败隔离：Agent 解析失败、非法动作超限、超时、环境异常都变成结构化 status，
  不向上抛异常污染批次（除非 Trace 写入失败——证据丢失必须显式失败）。

并发：``run_episode`` 是同步便捷入口；``run_episode_async`` 是 batch runner 使用的
异步入口（模型等待期间不阻塞其他 episode）。
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from bench.actions import Action
from bench.environment import Environment
from bench.errors import (
    AGENT_ERROR,
    INTERNAL,
    TIMEOUT,
    BenchError,
    InvalidActionError,
)
from bench.observation import render_observation
from bench.oracle import best_play, score_action
from bench.rules_version import VANILLA_SUBSET_V1, Ruleset
from bench.serialize import state_hash
from scenarios.loader import scenario_hash, to_reset_spec
from scenarios.schema import Scenario

from .agents import Agent, AsyncAgent, decide_async
from .config import ExperimentConfig, ExperimentStore
from .trace import TraceRecorder

EPISODE_RESULT_SCHEMA_VERSION = 1

# Episode 状态枚举：
# completed（规则内结束 win/loss）/ truncated（max_steps）/ timeout（墙钟超时）/
# agent_error（模型/策略未能产出可解析动作）/ invalid_action_limit（连续非法动作超限）/
# env_error（环境不变量/内部异常）。
EPISODE_STATUSES = ("completed", "truncated", "timeout", "agent_error",
                    "invalid_action_limit", "env_error")


@dataclass
class EpisodeResult:
    """一个 episode 的结构化结果（也是 results.jsonl 的一行）。"""

    task_id: str
    run_id: str
    episode_id: str
    scenario_id: str
    scenario_hash: str
    agent_id: str
    seed: int
    decision_type: str = "episode"
    rules_version: str = VANILLA_SUBSET_V1.rules_version
    status: str = "completed"
    outcome: str | None = None
    steps: int = 0
    total_reward: int = 0
    blind_scores: list[int] = field(default_factory=list)
    blinds_cleared: int = 0
    final_phase: str | None = None
    final_blind_idx: int | None = None
    final_money: int = 0
    legality_rate: float | None = None
    invalid_actions: int = 0
    play_decisions: int = 0
    action_type_mismatch: int = 0
    mean_regret: float | None = None
    max_regret: float | None = None
    optimality_rate: float | None = None
    total_usage: dict = field(default_factory=dict)
    latency_ms: dict = field(default_factory=dict)
    trace_path: str | None = None
    error: dict | None = None
    result_schema_version: int = EPISODE_RESULT_SCHEMA_VERSION

    def to_dict(self) -> dict:
        """导出为 JSON 友好 dict（results.jsonl 行）。"""
        return {
            "result_schema_version": self.result_schema_version,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "scenario_id": self.scenario_id,
            "scenario_hash": self.scenario_hash,
            "agent_id": self.agent_id,
            "seed": self.seed,
            "decision_type": self.decision_type,
            "rules_version": self.rules_version,
            "status": self.status,
            "outcome": self.outcome,
            "steps": self.steps,
            "total_reward": self.total_reward,
            "blind_scores": list(self.blind_scores),
            "blinds_cleared": self.blinds_cleared,
            "final_phase": self.final_phase,
            "final_blind_idx": self.final_blind_idx,
            "final_money": self.final_money,
            "legality_rate": self.legality_rate,
            "invalid_actions": self.invalid_actions,
            "play_decisions": self.play_decisions,
            "action_type_mismatch": self.action_type_mismatch,
            "mean_regret": self.mean_regret,
            "max_regret": self.max_regret,
            "optimality_rate": self.optimality_rate,
            "total_usage": self.total_usage,
            "latency_ms": self.latency_ms,
            "trace_path": self.trace_path,
            "error": self.error,
        }


def _effective_max_steps(scenario: Scenario, config: ExperimentConfig) -> int | None:
    candidates = [x for x in (scenario.constraints.max_steps, config.max_steps) if x is not None]
    return min(candidates) if candidates else None


async def run_episode_async(
    scenario: Scenario,
    agent: Agent | AsyncAgent,
    config: ExperimentConfig,
    store: ExperimentStore,
    task_id: str,
    *,
    code_hash: str = "",
    episode_index: int = 0,
    seed_override: int | None = None,
) -> EpisodeResult:
    """异步运行一个 episode，写 trace 与 result，返回结构化结果。

    Args:
        scenario: 已校验场景。
        agent: Agent 实例（每次 episode 应为新实例，避免共享可变状态）。
        config: 实验配置（并发/超时/重试在 batch 层；本函数用超时与 max_invalid_actions）。
        store: run 目录存储。
        task_id: 稳定任务 ID。
        code_hash: 代码哈希（写入 trace 头）。
        episode_index: 重试序号（trace 文件名后缀）。
        seed_override: 覆盖场景 seed（重复实验用 scenario.seed + repeat）。

    Returns:
        EpisodeResult（无论成功/失败都返回；trace 写入失败会抛出）。

    行为：
        - 每步先记录 action 与 agent 指标，再执行；非法动作记录 ``valid=False`` 且**不推进**
          状态，累计超过 ``max_invalid_actions`` 后终止为 ``invalid_action_limit``；
        - 超时（``config.episode_timeout_s``）终止为 ``timeout``；
        - ``oracle_enabled=True`` 时，在每个 play 决策前计算 O1 最优分，用于 regret/optimality。
    """
    if seed_override is not None:
        scenario = _with_seed(scenario, seed_override)
    reset_spec = to_reset_spec(scenario)
    ruleset: Ruleset = reset_spec.ruleset
    env = Environment(ruleset)
    observation = env.reset(reset_spec)
    max_steps = _effective_max_steps(scenario, config)
    env.max_steps = max_steps
    episode_id = f"{task_id}-e{episode_index}"
    trace_path = store.trace_path(task_id, episode_index)
    recorder = TraceRecorder(trace_path, run_id=config.experiment_id, task_id=task_id,
                             episode_id=episode_id, fsync=config.trace_fsync)
    recorder.start(scenario=scenario.to_dict(), ruleset=ruleset, code_hash=code_hash,
                   config=config.to_dict(), scenario_hash=scenario_hash(scenario))

    start = time.perf_counter()
    status = "completed"
    error_payload: dict | None = None
    invalid_actions = 0
    valid_steps = 0
    total_reward = 0
    play_scores: dict[int, int] = {}
    regrets: list[float] = []
    optimal_hits = 0
    play_decisions = 0
    action_type_mismatch = 0
    blinds_cleared = 0
    agent_latency_total = 0.0
    env_latency_total = 0.0
    usage_total: dict[str, int] = {}

    allowed = reset_spec.allowed_action_kinds

    try:
        async with asyncio.timeout(config.episode_timeout_s):
            while True:
                if env.is_terminated():
                    break
                if env.is_truncated():
                    status = "truncated"
                    break
                legal = env.legal_actions()
                if not legal:
                    status = "env_error"
                    error_payload = {"code": INTERNAL, "message": "no legal actions but not terminated"}
                    break
                state_before = env.state
                assert state_before is not None
                before_hash = state_hash(state_before)
                oracle_best: int | None = None
                if config.oracle_enabled and state_before.phase == "play":
                    oracle_best = best_play(state_before).score

                decision = await decide_async(agent, observation, legal)
                agent_latency_total += decision.latency_ms
                for name, value in decision.usage.items():
                    if isinstance(value, int):
                        usage_total[name] = usage_total.get(name, 0) + value

                if decision.action is None:
                    status = "agent_error"
                    error_payload = {"code": decision.error_code or AGENT_ERROR,
                                     "message": decision.error_message or "agent failed"}
                    recorder.step(
                        step=env.step_count + 1, action=None, valid=False, error=error_payload,
                        reward=0, terminated=False, truncated=False, termination_reason=None,
                        state_hash_before=before_hash, state_hash_after=None,
                        observation_text=render_observation(observation), score=None,
                        latency_agent_ms=decision.latency_ms, latency_env_ms=0.0,
                        raw_output=decision.raw_output, usage=decision.usage,
                    )
                    break

                action: Action = decision.action
                # 局部 regret 只在“play 决策”上定义；discard/商店动作不计入 regret。
                action_regret: float | None = None
                action_exact: int | None = None
                if state_before.phase == "play" and action.kind == "play":
                    try:
                        exact = score_action(state_before, action)
                    except BenchError:
                        exact = None
                    if exact is not None:
                        action_exact = exact.final_score
                        if oracle_best is not None and oracle_best > 0:
                            action_regret = max(0.0, (oracle_best - action_exact) / oracle_best)
                            regrets.append(action_regret)
                            play_decisions += 1
                            if action_exact == oracle_best:
                                optimal_hits += 1
                elif state_before.phase == "play":
                    action_type_mismatch += 1

                env_start = time.perf_counter()
                try:
                    result = env.step(action)
                except BenchError as exc:
                    env_latency_total += (time.perf_counter() - env_start) * 1000
                    invalid_actions += 1
                    recorder.step(
                        step=env.step_count + 1, action=action.to_dict(), valid=False,
                        error=exc.to_dict(), reward=0, terminated=False, truncated=False,
                        termination_reason=None, state_hash_before=before_hash,
                        state_hash_after=state_hash(state_before),
                        observation_text=render_observation(observation), score=None,
                        latency_agent_ms=decision.latency_ms,
                        latency_env_ms=(time.perf_counter() - env_start) * 1000,
                        raw_output=decision.raw_output, usage=decision.usage,
                    )
                    if invalid_actions > config.max_invalid_actions:
                        status = "invalid_action_limit"
                        error_payload = exc.to_dict()
                        break
                    continue
                env_latency_total += (time.perf_counter() - env_start) * 1000
                valid_steps += 1
                total_reward += result.reward
                # 用动作前的盲注下标记账（engine 可能在同一 step 内推进盲注）。
                blind_before = state_before.blind_idx
                play_scores[blind_before] = play_scores.get(blind_before, 0) + result.reward
                if state_before.total_score < state_before.target <= int(result.info.get("total_score", 0)):
                    blinds_cleared += 1
                observation = result.observation
                recorder.step(
                    step=env.step_count,
                    action=action.to_dict(),
                    valid=True,
                    error=None,
                    reward=result.reward,
                    terminated=result.terminated,
                    truncated=result.truncated,
                    termination_reason=result.info.get("termination_reason"),
                    state_hash_before=before_hash,
                    state_hash_after=result.info.get("state_hash_after"),
                    observation_text=render_observation(observation),
                    score=result.info.get("score"),
                    latency_agent_ms=decision.latency_ms,
                    latency_env_ms=(time.perf_counter() - env_start) * 1000,
                    raw_output=decision.raw_output,
                    usage=decision.usage,
                )
                if action_regret is not None:
                    # 单独写一条指标事件，便于离线做 regret 时间序列分析。
                    recorder.decision_metric(
                        step=env.step_count,
                        action_code=action.code,
                        oracle_score=oracle_best,
                        actual_score=action_exact,
                        regret=action_regret,
                    )
                if result.terminated:
                    status = "completed"
                    break
                if result.truncated:
                    # decision-point 场景（play/discard）的 horizon 就是 max_steps：
                    # 完成一次决策后按“场景完成”记 completed；episode 场景才算截断。
                    if scenario.decision_type != "episode" and valid_steps >= 1:
                        status = "completed"
                    else:
                        status = "truncated"
                    break
    except TimeoutError:
        status = "timeout"
        error_payload = {"code": TIMEOUT,
                         "message": f"episode exceeded {config.episode_timeout_s}s"}
    except BenchError as exc:
        status = "env_error"
        error_payload = exc.to_dict()
    except Exception as exc:  # noqa: BLE001 - 失败隔离：不让单 episode 炸掉批次
        status = "env_error"
        error_payload = {"code": INTERNAL, "message": f"{type(exc).__name__}: {exc}"}

    duration_ms = (time.perf_counter() - start) * 1000
    final_state = env.state
    assert final_state is not None
    legal_total = valid_steps + invalid_actions
    metrics = {
        "legality_rate": (valid_steps / legal_total) if legal_total else None,
        "invalid_actions": invalid_actions,
        "play_decisions": play_decisions,
        "action_type_mismatch": action_type_mismatch,
        "mean_regret": (sum(regrets) / len(regrets)) if regrets else None,
        "max_regret": max(regrets) if regrets else None,
        "optimality_rate": (optimal_hits / play_decisions) if play_decisions else None,
        "blinds_cleared": play_scores,
        "final_money": final_state.money,
        "agent_latency_ms": round(agent_latency_total, 4),
        "env_latency_ms": round(env_latency_total, 4),
        "total_duration_ms": round(duration_ms, 4),
        "usage": usage_total,
    }
    recorder.end(status=status, outcome=final_state.outcome, steps=env.step_count,
                 total_reward=total_reward,
                 blinds_cleared=blinds_cleared,
                 blind_scores=[play_scores.get(i, 0) for i in sorted(play_scores)],
                 metrics=metrics, duration_ms=duration_ms, error=error_payload)
    recorder.close()

    result = EpisodeResult(
        task_id=task_id,
        run_id=config.experiment_id,
        episode_id=episode_id,
        scenario_id=scenario.scenario_id,
        scenario_hash=scenario_hash(scenario),
        agent_id=getattr(agent, "agent_id", config.agent_id),
        seed=scenario.seed,
        decision_type=scenario.decision_type,
        rules_version=ruleset.rules_version,
        status=status,
        outcome=final_state.outcome,
        steps=env.step_count,
        total_reward=total_reward,
        blind_scores=[play_scores.get(i, 0) for i in sorted(play_scores)],
        blinds_cleared=blinds_cleared,
        final_phase=final_state.phase,
        final_blind_idx=final_state.blind_idx,
        final_money=final_state.money,
        legality_rate=metrics["legality_rate"],
        invalid_actions=invalid_actions,
        play_decisions=play_decisions,
        action_type_mismatch=action_type_mismatch,
        mean_regret=metrics["mean_regret"],
        max_regret=metrics["max_regret"],
        optimality_rate=metrics["optimality_rate"],
        total_usage=usage_total,
        latency_ms={"agent": round(agent_latency_total, 4),
                     "env": round(env_latency_total, 4),
                     "total": round(duration_ms, 4)},
        trace_path=str(trace_path),
        error=error_payload,
    )
    store.append_result(result.to_dict())
    return result


def run_episode(
    scenario: Scenario,
    agent: Agent | AsyncAgent,
    config: ExperimentConfig,
    store: ExperimentStore,
    task_id: str,
    *,
    code_hash: str = "",
    episode_index: int = 0,
    seed_override: int | None = None,
) -> EpisodeResult:
    """同步入口：内部用 ``asyncio.run`` 执行 ``run_episode_async``。

    Raises:
        RuntimeError: 在已有事件循环的线程中调用（请改用 ``run_episode_async``）。
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(run_episode_async(
            scenario, agent, config, store, task_id, code_hash=code_hash,
            episode_index=episode_index, seed_override=seed_override,
        ))
    raise RuntimeError("run_episode() cannot be called inside a running event loop; "
                       "use run_episode_async()")


def _with_seed(scenario: Scenario, seed: int) -> Scenario:
    """返回替换 seed 后的场景副本（用于重复实验；保持其余字段不变）。"""
    from dataclasses import replace

    return replace(scenario, seed=seed)
