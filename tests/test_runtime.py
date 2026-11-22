"""评测执行层测试：单 episode、trace、batch 并发/续跑/失败隔离、指标、模型适配器。"""
from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path

from bench.environment import Environment, ResetSpec
from bench.errors import AGENT_ERROR
from bench.rules_version import VANILLA_SUBSET_V1
from scenarios.loader import load_scenarios
from scenarios.schema import Scenario
from tests.tmp_utils import workspace_tmp

from evaluation.agents import (
    AgentDecision,
    CallableAgent,
    HttpChatAgent,
    OracleGreedyAgent,
    ResponseCache,
    parse_action_text,
)
from evaluation.batch_runner import run_batch_async
from evaluation.config import ExperimentConfig, ExperimentStore
from evaluation.episode_runner import run_episode, run_episode_async
from evaluation.metrics import bootstrap_ci, group_summaries, render_markdown_table, summarize
from evaluation.trace import read_trace, trace_summary

DEV_DIR = Path(__file__).resolve().parents[1] / "scenarios" / "dev"


def _scenario_by_id(scenario_id: str) -> Scenario:
    for scenario in load_scenarios(DEV_DIR):
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(scenario_id)


def _config(tmp: str, *, agent_id: str = "oracle-greedy", experiment: str = "test-run",
            **overrides) -> ExperimentConfig:
    values = {
        "experiment_id": experiment,
        "scenario_paths": (str(DEV_DIR),),
        "agent_id": agent_id,
        "output_dir": tmp,
        "max_concurrency": 2,
        "agent_concurrency": 2,
        "episode_timeout_s": 30.0,
        "oracle_enabled": True,
        "resume": True,
    }
    values.update(overrides)
    return ExperimentConfig(**values)


class TestSingleEpisode(unittest.TestCase):
    def test_golden_pair_episode(self):
        scenario = _scenario_by_id("dev-play-pair-7h7d")
        with workspace_tmp() as tmp:
            config = _config(tmp)
            store = ExperimentStore(config)
            result = run_episode(scenario, OracleGreedyAgent(), config, store, "task-golden")
            self.assertEqual(result.status, "completed")
            self.assertEqual(result.total_reward, 48)
            self.assertEqual(result.play_decisions, 1)
            self.assertEqual(result.mean_regret, 0.0)
            self.assertEqual(result.optimality_rate, 1.0)
            self.assertEqual(result.legality_rate, 1.0)
            events = read_trace(result.trace_path)
            self.assertEqual(events[0]["event"], "episode_start")
            self.assertEqual(events[-1]["event"], "episode_end")
            step = next(e for e in events if e["event"] == "step")
            self.assertEqual(step["action"]["code"], "play:c7d,c7h")
            self.assertEqual(len(step["state_hash_after"]), 64)
            metric = next(e for e in events if e["event"] == "decision_metric")
            self.assertEqual(metric["regret"], 0.0)

    def test_discard_decision_point_completes(self):
        scenario = _scenario_by_id("dev-discard-point-flush-draw")
        with workspace_tmp() as tmp:
            config = _config(tmp)
            store = ExperimentStore(config)
            result = run_episode(scenario, OracleGreedyAgent(), config, store, "task-discard")
            self.assertEqual(result.status, "completed")
            self.assertEqual(result.decision_type, "discard")
            self.assertEqual(result.play_decisions, 0)

    def test_agent_error_is_isolated(self):
        scenario = _scenario_by_id("dev-play-pair-7h7d")

        def boom(observation, legal_actions):
            raise RuntimeError("model exploded")

        with workspace_tmp() as tmp:
            config = _config(tmp)
            store = ExperimentStore(config)
            result = run_episode(scenario, CallableAgent("boom", boom), config, store, "task-boom")
            self.assertEqual(result.status, "agent_error")
            self.assertEqual(result.error["code"], AGENT_ERROR)

    def test_invalid_action_limit(self):
        scenario = _scenario_by_id("dev-play-pair-7h7d")

        def always_discard(observation, legal_actions):
            card_id = observation["hand"][0]["id"]
            return {"kind": "discard", "card_ids": [card_id]}

        with workspace_tmp() as tmp:
            config = _config(tmp, max_invalid_actions=3)
            store = ExperimentStore(config)
            result = run_episode(scenario, CallableAgent("bad", always_discard), config, store,
                                 "task-invalid")
            self.assertEqual(result.status, "invalid_action_limit")
            self.assertEqual(result.invalid_actions, 4)  # 超过 3 次后终止
            self.assertEqual(result.legality_rate, 0.0)
            events = read_trace(result.trace_path)
            invalid_steps = [e for e in events if e["event"] == "step" and not e["valid"]]
            self.assertEqual(len(invalid_steps), 4)
            self.assertEqual(invalid_steps[0]["error"]["code"], "NOT_ALLOWED")

    def test_deterministic_replay(self):
        scenario = _scenario_by_id("dev-play-pair-7h7d")
        traces = []
        with workspace_tmp() as tmp:
            for index in range(2):
                config = _config(tmp, experiment=f"replay-{index}")
                store = ExperimentStore(config)
                result = run_episode(scenario, OracleGreedyAgent(), config, store, "task-replay")
                events = read_trace(result.trace_path)
                traces.append({
                    "actions": [e["action"]["code"] for e in events if e["event"] == "step"],
                    "rewards": [e["reward"] for e in events if e["event"] == "step"],
                    "hashes": [e["state_hash_after"] for e in events if e["event"] == "step"],
                })
        self.assertEqual(traces[0], traces[1])


class TestBatch(unittest.TestCase):
    def _scenarios(self):
        return [_scenario_by_id("dev-play-pair-7h7d"),
                _scenario_by_id("dev-play-boss-blind-score-only")]

    def test_batch_runs_and_writes_results(self):
        scenarios = self._scenarios()
        with workspace_tmp() as tmp:
            config = _config(tmp, experiment="batch-1")
            summary = asyncio.run(run_batch_async(scenarios, config))
            self.assertEqual(len(summary.results), 2)
            self.assertEqual(summary.counts.get("completed"), 2)
            store = ExperimentStore(config)
            rows = store.load_results()
            self.assertEqual(len(rows), 2)
            self.assertTrue((store.run_dir / "manifest.json").exists())
            self.assertEqual(len(list((store.run_dir / "traces").glob("*.jsonl"))), 2)
            # 结果里的 trace 路径可读，scenario 与 result 对应
            for row in rows:
                events = read_trace(row["trace_path"])
                self.assertEqual(events[0]["scenario"]["scenario_id"], row["scenario_id"])

    def test_resume_skips_completed(self):
        scenarios = self._scenarios()
        with workspace_tmp() as tmp:
            config = _config(tmp, experiment="batch-resume")
            asyncio.run(run_batch_async(scenarios, config))
            second = asyncio.run(run_batch_async(scenarios, config))
            self.assertEqual(second.skipped, 2)
            self.assertEqual(len(second.results), 0)
            self.assertEqual(len(ExperimentStore(config).load_results()), 2)

    def test_retry_failed_reruns_errors(self):
        scenarios = self._scenarios()

        def failing_factory(task):
            if task.scenario.scenario_id == "dev-play-pair-7h7d":
                raise RuntimeError("factory failed")
            return OracleGreedyAgent()

        with workspace_tmp() as tmp:
            config = _config(tmp, experiment="batch-retry")
            first = asyncio.run(run_batch_async(scenarios, config, agent_factory=failing_factory))
            self.assertEqual(first.counts.get("agent_error"), 1)
            self.assertEqual(first.counts.get("completed"), 1)
            # retry_failed=True：只跳过成功项，失败项重跑
            config2 = _config(tmp, experiment="batch-retry", retry_failed=True)
            second = asyncio.run(run_batch_async(
                scenarios, config2, agent_factory=lambda task: OracleGreedyAgent()))
            self.assertEqual(second.skipped, 1)
            self.assertEqual(second.counts.get("completed"), 1)

    def test_failure_isolation(self):
        scenarios = self._scenarios()

        def factory(task):
            if task.scenario.scenario_id == "dev-play-pair-7h7d":
                raise RuntimeError("only this one fails")
            return OracleGreedyAgent()

        with workspace_tmp() as tmp:
            config = _config(tmp, experiment="batch-isolate")
            summary = asyncio.run(run_batch_async(scenarios, config, agent_factory=factory))
            statuses = {r.scenario_id: r.status for r in summary.results}
            self.assertEqual(statuses["dev-play-pair-7h7d"], "agent_error")
            self.assertEqual(statuses["dev-play-boss-blind-score-only"], "completed")

    def test_concurrent_state_isolation(self):
        scenarios = load_scenarios(DEV_DIR)
        with workspace_tmp() as tmp:
            config = _config(tmp, experiment="batch-concurrency", max_concurrency=4)
            summary = asyncio.run(run_batch_async(scenarios, config))
            task_ids = [r.task_id for r in summary.results]
            self.assertEqual(len(task_ids), len(set(task_ids)))
            for result in summary.results:
                events = read_trace(result.trace_path)
                self.assertEqual(events[0]["scenario"]["scenario_id"], result.scenario_id)
                self.assertEqual(events[0]["task_id"], result.task_id)


class TestMetrics(unittest.TestCase):
    def test_summarize_and_bootstrap(self):
        rows = [
            {"status": "completed", "outcome": "win", "total_reward": 600, "steps": 10,
             "blinds_cleared": 3, "legality_rate": 1.0, "mean_regret": 0.0,
             "optimality_rate": 1.0, "latency_ms": {"agent": 10, "env": 20, "total": 30},
             "total_usage": {"prompt_tokens": 100}},
            {"status": "completed", "outcome": "loss", "total_reward": 200, "steps": 4,
             "blinds_cleared": 1, "legality_rate": 0.5, "mean_regret": 0.25,
             "optimality_rate": 0.5, "latency_ms": {"agent": 20, "env": 40, "total": 60},
             "total_usage": {"prompt_tokens": 50}},
        ]
        summary = summarize(rows)
        self.assertEqual(summary["n"], 2)
        self.assertEqual(summary["success_rate"], 0.5)
        self.assertEqual(summary["mean_reward"], 400)
        self.assertEqual(summary["usage"]["prompt_tokens"], 150)
        ci = bootstrap_ci([1.0, 2.0, 3.0], n_resamples=200)
        self.assertEqual(ci["n"], 3)
        self.assertLessEqual(ci["low"], ci["high"])
        groups = group_summaries(rows, group_by=("status",))
        self.assertIn("|", render_markdown_table(groups))

    def test_trace_summary(self):
        scenario = _scenario_by_id("dev-play-pair-7h7d")
        with workspace_tmp() as tmp:
            config = _config(tmp, experiment="trace-summary")
            store = ExperimentStore(config)
            result = run_episode(scenario, OracleGreedyAgent(), config, store, "task-ts")
            events = read_trace(result.trace_path)
            summary = trace_summary(events)
            self.assertEqual(summary["scenario_id"], scenario.scenario_id)
            self.assertEqual(summary["status"], "completed")
            self.assertEqual(summary["valid_steps"], 1)


class TestHttpAgent(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _fixed_observation() -> dict:
        env = Environment()
        return env.reset(ResetSpec(seed=42, hand_ids=(
            "c7h", "c7d", "c2s", "c3c", "c5d", "c9s", "c11c", "c13d")))

    async def test_fake_transport_and_cache(self):
        calls = {"n": 0}

        async def transport(request):
            calls["n"] += 1
            return {"text": '{"kind":"play","card_ids":["c7h","c7d"]}',
                    "usage": {"prompt_tokens": 5, "completion_tokens": 2}}

        with workspace_tmp() as tmp:
            cache = ResponseCache(str(Path(tmp) / "cache.sqlite"))
            agent = HttpChatAgent("fake-model", "fake", transport=transport, cache=cache,
                                  max_retries=1, backoff_s=0.0)
            observation = self._fixed_observation()
            first = await agent.decide_async(observation, [])
            second = await agent.decide_async(observation, [])
            self.assertTrue(first.ok)
            self.assertTrue(second.ok)
            self.assertEqual(first.action.code, "play:c7d,c7h")
            self.assertEqual(calls["n"], 1)  # 第二次命中缓存
            self.assertEqual(cache.hits, 1)
            self.assertEqual(first.usage["prompt_tokens"], 5)

    async def test_retry_then_success(self):
        attempts = {"n": 0}

        async def transport(request):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise RuntimeError("transient")
            return {"text": '{"kind":"play","card_ids":["c7h","c7d"]}'}

        agent = HttpChatAgent("retry-model", "fake", transport=transport, max_retries=2,
                              backoff_s=0.0)
        decision = await agent.decide_async(self._fixed_observation(), [])
        self.assertTrue(decision.ok)
        self.assertEqual(attempts["n"], 2)

    async def test_timeout_maps_to_timeout_code(self):
        async def transport(request):
            await asyncio.sleep(0.2)
            return {"text": "{}"}

        agent = HttpChatAgent("slow-model", "fake", transport=transport, max_retries=1,
                              timeout_s=0.01, backoff_s=0.0)
        decision = await agent.decide_async(self._fixed_observation(), [])
        self.assertFalse(decision.ok)
        self.assertEqual(decision.error_code, "TIMEOUT")

    def test_parse_action_text(self):
        action = parse_action_text('sure: {"kind":"discard","card_ids":["c2s"]}')
        self.assertEqual(action.kind, "discard")


if __name__ == "__main__":
    unittest.main()
