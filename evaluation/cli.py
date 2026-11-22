"""评测 CLI：python -m evaluation {run,batch,report,rules}。

用法示例：
    python -m evaluation run --scenarios scenarios/dev/play-pair-7h7d.json --agent oracle-greedy
    python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy --repeats 2
    python -m evaluation report --run-dir runs/oracle-greedy-dev

约定：stdout 输出 JSON 摘要（便于自动化）；Markdown 表作为 `table` 字段一并输出。
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from bench.rules_version import VANILLA_SUBSET_V1
from scenarios.loader import load_scenarios

from .batch_runner import BatchSummary, run_batch
from .config import ExperimentConfig, compute_code_hash
from .metrics import group_summaries, load_results, render_markdown_table, summarize


def _sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "run"


def _build_config(args) -> ExperimentConfig:
    paths = tuple(str(p) for p in args.scenarios)
    experiment_id = args.experiment or _sanitize(
        f"{args.agent}-{Path(paths[0]).stem}"
    )
    agent_params: dict = {}
    if args.agent == "http":
        if not args.model:
            raise SystemExit("--model is required for --agent http")
        agent_params = {
            "model": args.model,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
        }
        if args.cache_path:
            agent_params["cache_path"] = args.cache_path
        if args.rate:
            agent_params["rate_per_second"] = args.rate
            agent_params["burst"] = args.burst
    return ExperimentConfig(
        experiment_id=experiment_id,
        scenario_paths=paths,
        agent_id=args.agent,
        agent_params=agent_params,
        repeats=args.repeats,
        max_steps=args.max_steps,
        episode_timeout_s=args.timeout,
        max_concurrency=args.max_concurrency,
        agent_concurrency=args.agent_concurrency,
        retry_attempts=args.retry_attempts,
        retry_backoff_s=args.retry_backoff,
        oracle_enabled=not args.no_oracle,
        output_dir=args.out,
        resume=not args.no_resume,
        retry_failed=args.retry_failed,
        scenario_max_count=args.max_tasks,
    )


def _summary_payload(batch: BatchSummary) -> dict:
    rows = [result.to_dict() for result in batch.results]
    groups = group_summaries(rows, group_by=("agent_id",))
    return {
        "run_id": batch.run_id,
        "run_dir": batch.run_dir,
        "config_hash": batch.config_hash,
        "code_hash": batch.code_hash,
        "counts": batch.counts,
        "skipped": batch.skipped,
        "duration_ms": round(batch.duration_ms, 4),
        "summary": summarize(rows),
        "groups": groups,
        "table": render_markdown_table(groups),
        "results": [
            {k: r.get(k) for k in ("task_id", "scenario_id", "status", "outcome",
                                   "total_reward", "steps", "mean_regret",
                                   "optimality_rate", "trace_path")}
            for r in rows
        ],
    }


def cmd_run(args) -> int:
    config = _build_config(args)
    scenarios = load_scenarios(config.scenario_paths, config.ruleset)
    if not scenarios:
        print(json.dumps({"error": "no scenarios loaded"}, ensure_ascii=False))
        return 2
    batch = run_batch(scenarios, config, max_tasks=1)
    print(json.dumps(_summary_payload(batch), ensure_ascii=False, indent=2))
    return 0 if batch.counts.get("completed", 0) + batch.counts.get("truncated", 0) else 1


def cmd_batch(args) -> int:
    config = _build_config(args)
    scenarios = load_scenarios(config.scenario_paths, config.ruleset)
    batch = run_batch(scenarios, config)
    payload = _summary_payload(batch)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_report(args) -> int:
    rows = load_results(args.run_dir)
    groups = group_summaries(rows, group_by=tuple(args.group_by.split(",")))
    print(json.dumps({
        "run_dir": str(args.run_dir),
        "n": len(rows),
        "summary": summarize(rows),
        "groups": groups,
        "table": render_markdown_table(groups),
        "manifest": json.loads((Path(args.run_dir) / "manifest.json").read_text(encoding="utf-8"))
        if (Path(args.run_dir) / "manifest.json").exists() else None,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_rules(args) -> int:
    payload = VANILLA_SUBSET_V1.to_dict()
    payload["signature"] = VANILLA_SUBSET_V1.signature()
    payload["code_hash"] = compute_code_hash()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evaluation",
                                     description="BalatroEval episode/batch runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p):
        p.add_argument("--scenarios", nargs="+", default=["scenarios/dev"],
                       help="JSON/JSONL/dir paths")
        p.add_argument("--agent", default="oracle-greedy",
                       choices=["oracle-greedy", "random", "first-legal", "http"])
        p.add_argument("--experiment", default=None)
        p.add_argument("--out", default="runs")
        p.add_argument("--repeats", type=int, default=1)
        p.add_argument("--max-steps", type=int, default=None)
        p.add_argument("--max-tasks", type=int, default=None)
        p.add_argument("--timeout", type=float, default=60.0)
        p.add_argument("--max-concurrency", type=int, default=4)
        p.add_argument("--agent-concurrency", type=int, default=4)
        p.add_argument("--retry-attempts", type=int, default=1)
        p.add_argument("--retry-backoff", type=float, default=0.5)
        p.add_argument("--no-oracle", action="store_true")
        p.add_argument("--no-resume", action="store_true")
        p.add_argument("--retry-failed", action="store_true")
        p.add_argument("--model", default=None)
        p.add_argument("--temperature", type=float, default=0.0)
        p.add_argument("--max-tokens", type=int, default=256)
        p.add_argument("--cache-path", default=None)
        p.add_argument("--rate", type=float, default=None)
        p.add_argument("--burst", type=int, default=1)

    p_run = sub.add_parser("run", help="run one episode")
    add_common(p_run)
    p_run.set_defaults(func=cmd_run)
    p_batch = sub.add_parser("batch", help="run a batch of episodes")
    add_common(p_batch)
    p_batch.set_defaults(func=cmd_batch)
    p_report = sub.add_parser("report", help="aggregate an existing run directory")
    p_report.add_argument("--run-dir", required=True)
    p_report.add_argument("--group-by", default="agent_id")
    p_report.add_argument("--out", default="runs")
    p_report.set_defaults(func=cmd_report)
    p_rules = sub.add_parser("rules", help="print machine-readable ruleset")
    p_rules.set_defaults(func=cmd_rules)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
