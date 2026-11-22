"""性能基准：规则计算、环境转移、Oracle、单 episode、batch 并发与 Trace 开销。

运行：
    python -m benchmarks.bench --quick
    python -m benchmarks.bench            # 全量（约 1–2 分钟）

说明：
- 这是**环境侧**性能，不含任何模型推理时间；模型延迟由 trace 的 ``latency_ms.agent`` 单独记录。
- 结果打印为 JSON（可重定向到文件），并给出机器可读的 ``per_op_us`` / ``throughput_eps``。
- 所有耗时用 ``time.perf_counter``；测量前做 warmup；批量实验写到 ``runs/_bench`` 并尽量清理。
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import statistics
import sys
import time
import tracemalloc
import uuid
from pathlib import Path

from bench.cards import standard_deck
from bench.engine import new_game
from bench.environment import Environment, ResetSpec
from bench.hand_eval import evaluate_hand
from bench.jokers import CATALOG_BY_ID
from bench.oracle import best_play
from bench.scoring import score_hand
from scenarios.loader import load_scenarios

from evaluation.agents import OracleGreedyAgent
from evaluation.batch_runner import run_batch
from evaluation.config import ExperimentConfig, ExperimentStore
from evaluation.episode_runner import run_episode

ROOT = Path(__file__).resolve().parents[1]
BENCH_TMP = ROOT / "runs" / "_bench"


def _timeit(fn, iterations: int) -> dict:
    """返回总耗时/单次耗时（微秒）/标准差（微秒）。"""
    for _ in range(min(20, iterations)):  # warmup
        fn()
    samples = []
    start_total = time.perf_counter()
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1e6)
    total = time.perf_counter() - start_total
    return {
        "iterations": iterations,
        "total_s": round(total, 6),
        "per_op_us": round(total / iterations * 1e6, 4),
        "p50_us": round(statistics.median(samples), 4),
        "p95_us": round(sorted(samples)[int(0.95 * (len(samples) - 1))], 4),
    }


def bench_rule_core(quick: bool) -> dict:
    rng = random.Random(20261117)
    deck = standard_deck()
    hands = [rng.sample(deck, 5) for _ in range(200)]
    eval_n = 2000 if quick else 20000
    score_n = 2000 if quick else 20000
    oracle_n = 50 if quick else 300
    jokers = [CATALOG_BY_ID[jid] for jid in ("joker", "jolly_joker", "the_duo")]
    state8 = new_game(20261117)
    return {
        "evaluate_hand": _timeit(lambda: evaluate_hand(rng.choice(hands)), eval_n),
        "score_hand_3jokers": _timeit(lambda: score_hand(rng.choice(hands), jokers), score_n),
        "oracle_best_play_218": _timeit(lambda: best_play(state8), oracle_n),
    }


def bench_engine(quick: bool) -> dict:
    init_n = 1000 if quick else 5000
    step_n = 500 if quick else 2000
    init = _timeit(lambda: new_game(20261117), init_n)

    def one_step() -> None:
        env = Environment()
        env.reset(ResetSpec(seed=20261117))
        action = next(a for a in env.legal_actions() if a.kind == "play")
        env.step(action)

    return {"new_game": init, "reset_plus_play_step": _timeit(one_step, step_n)}


def bench_episode(quick: bool) -> dict:
    scenarios = load_scenarios(ROOT / "scenarios" / "dev")
    scenario = next(s for s in scenarios if s.scenario_id == "dev-play-pair-7h7d")
    n = 20 if quick else 100
    BENCH_TMP.mkdir(parents=True, exist_ok=True)
    run_dir = BENCH_TMP / uuid.uuid4().hex
    config = ExperimentConfig(experiment_id="bench", scenario_paths=(str(ROOT / "scenarios" / "dev"),),
                              agent_id="oracle-greedy", output_dir=str(run_dir), oracle_enabled=False,
                              max_concurrency=1, episode_timeout_s=30, trace_fsync=False)
    store = ExperimentStore(config)

    def one_episode() -> None:
        run_episode(scenario, OracleGreedyAgent(), config, store,
                    task_id=f"bench-{uuid.uuid4().hex[:8]}", code_hash="bench")

    result = _timeit(one_episode, n)
    result["note"] = "no fsync; includes trace JSONL write + results append"
    shutil.rmtree(run_dir, ignore_errors=True)
    return {"run_episode_with_trace": result}


def bench_batch(quick: bool) -> dict:
    scenarios = load_scenarios(ROOT / "scenarios" / "dev")
    repeats = 4 if quick else 20
    BENCH_TMP.mkdir(parents=True, exist_ok=True)
    output = {}
    for concurrency in (1, 2, 4):
        run_dir = BENCH_TMP / uuid.uuid4().hex
        config = ExperimentConfig(
            experiment_id=f"bench-c{concurrency}",
            scenario_paths=(str(ROOT / "scenarios" / "dev"),),
            # 用 first-legal 隔离“环境/执行架构吞吐”；oracle-greedy 的 discard EV 是 Agent
            # 侧 CPU 成本（见 docs/implementation/performance.md），不应混入环境基准。
            agent_id="first-legal",
            output_dir=str(run_dir),
            repeats=repeats, max_concurrency=concurrency, agent_concurrency=concurrency,
            oracle_enabled=False, episode_timeout_s=60, trace_fsync=False,
        )
        total_tasks = len(scenarios) * repeats
        tracemalloc.start()
        start = time.perf_counter()
        summary = run_batch(scenarios, config)
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        output[f"concurrency_{concurrency}"] = {
            "tasks": total_tasks,
            "elapsed_s": round(elapsed, 4),
            "throughput_eps": round(total_tasks / elapsed, 3) if elapsed else None,
            "counts": summary.counts,
            "peak_mem_mb": round(peak / 1024 / 1024, 3),
        }
        shutil.rmtree(run_dir, ignore_errors=True)
    return output


def bench_async_overlap(quick: bool) -> dict:
    """模拟“模型等待型”并发：每个决策 await 5ms，验证 asyncio 能把等待重叠。

    这不是模型服务基准，只证明执行架构在 I/O 等待下能扩展；真实模型延迟由 trace 记录。
    """
    import asyncio

    scenarios = load_scenarios(ROOT / "scenarios" / "dev")
    repeats = 4 if quick else 10
    tasks_total = len(scenarios) * repeats

    class SleepAgent:
        agent_id = "sleep-5ms"

        async def decide_async(self, observation, legal_actions):
            from evaluation.agents import AgentDecision
            await asyncio.sleep(0.005)
            return AgentDecision(legal_actions[0])

    output = {}
    for concurrency in (1, 4, 8):
        run_dir = BENCH_TMP / uuid.uuid4().hex
        config = ExperimentConfig(
            experiment_id=f"bench-async-c{concurrency}",
            scenario_paths=(str(ROOT / "scenarios" / "dev"),), agent_id="sleep-5ms",
            output_dir=str(run_dir), repeats=repeats, max_concurrency=concurrency,
            agent_concurrency=concurrency, oracle_enabled=False, episode_timeout_s=60,
            trace_fsync=False,
        )
        start = time.perf_counter()
        summary = run_batch(scenarios, config, agent_factory=lambda task: SleepAgent())
        elapsed = time.perf_counter() - start
        output[f"concurrency_{concurrency}"] = {
            "tasks": tasks_total,
            "elapsed_s": round(elapsed, 4),
            "throughput_eps": round(tasks_total / elapsed, 3) if elapsed else None,
            "counts": summary.counts,
        }
        shutil.rmtree(run_dir, ignore_errors=True)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmarks.bench")
    parser.add_argument("--quick", action="store_true", help="fewer iterations")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    report = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "cwd": str(ROOT),
        "quick": args.quick,
        "rules": {
            "rules_version": "vanilla_1.0.1o_subset_v1",
            "hands_per_blind": 4, "discards_per_blind": 4,
            "hand_size": 8, "joker_slots": 5,
        },
        "rule_core": bench_rule_core(args.quick),
        "engine": bench_engine(args.quick),
        "episode": bench_episode(args.quick),
        "batch": bench_batch(args.quick),
        "async_overlap": bench_async_overlap(args.quick),
    }
    report["total_s"] = round(time.perf_counter() - started, 4)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
