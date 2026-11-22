"""指标聚合：从 results.jsonl 计算分组统计、bootstrap 置信区间与 Markdown 表。

指标语义（与 plan/详细版/03 对齐，避免把不同量混在一起）：
- ``success_rate``：status=completed 且 outcome=win 的比例（Ante 1 通关）；
- ``completion_rate``：status=completed（规则内结束，含胜/负）比例；
- ``truncation_rate`` / ``timeout_rate`` / ``error_rate``：外部截断/超时/异常比例，
  **不计入**成功率；
- ``mean_regret`` / ``optimality_rate``：只在 play 决策上定义；discard 决策不计入
  （避免旧版“正确弃牌被记最大 regret”的偏差，methodology P0-3）；
- ``legality_rate``：合法工具调用 / 全部工具调用；
- ``latency_ms``：agent / env / total 分开统计；模型推理时间不混入规则引擎性能；
- ``usage``：模型 token 用量（脚本 Agent 为空）。

统计约定：样本量小（n<10）时只报计数与描述统计；bootstrap CI 只是区间估计，不是
显著性检验。报告中必须同时给 n。
"""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path
from typing import Callable, Iterable, Sequence

METRIC_KEYS = (
    "success_rate", "completion_rate", "truncation_rate", "timeout_rate", "error_rate",
    "mean_reward", "median_reward", "mean_blinds", "mean_steps", "mean_legality",
    "mean_regret", "optimality_rate", "mean_final_money",
    "p50_agent_ms", "p95_agent_ms",
    "p50_env_ms", "p95_env_ms", "p50_total_ms", "p95_total_ms",
)


def load_results(path: str | Path) -> list[dict]:
    """读取 run 目录的 results.jsonl（或直接给文件）。"""
    target = Path(path)
    if target.is_dir():
        target = target / "results.jsonl"
    if not target.exists():
        return []
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _rate(count: int, total: int) -> float | None:
    return (count / total) if total else None


def summarize(results: Sequence[dict]) -> dict:
    """对一组结果行计算描述统计（不分组）。

    Args:
        results: results.jsonl 的行（dict）或 EpisodeResult.to_dict()。

    Returns:
        dict；键见 ``METRIC_KEYS`` + ``n`` / ``counts`` / ``usage``。
    """
    rows = [r for r in results]
    n = len(rows)
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status"))
        counts[status] = counts.get(status, 0) + 1
    wins = sum(1 for r in rows if r.get("status") == "completed" and r.get("outcome") == "win")
    completed = counts.get("completed", 0)
    rewards = [float(r.get("total_reward") or 0) for r in rows]
    blinds = [float(r.get("blinds_cleared") or 0) for r in rows]
    steps = [float(r.get("steps") or 0) for r in rows]
    legality = [float(r["legality_rate"]) for r in rows if r.get("legality_rate") is not None]
    regret = [float(r["mean_regret"]) for r in rows if r.get("mean_regret") is not None]
    optimality = [float(r["optimality_rate"]) for r in rows if r.get("optimality_rate") is not None]
    final_money = [float(r["final_money"]) for r in rows if r.get("final_money") is not None]
    agent_ms = [float((r.get("latency_ms") or {}).get("agent", 0)) for r in rows]
    env_ms = [float((r.get("latency_ms") or {}).get("env", 0)) for r in rows]
    total_ms = [float((r.get("latency_ms") or {}).get("total", 0)) for r in rows]
    usage: dict[str, int] = {}
    for row in rows:
        for name, value in (row.get("total_usage") or {}).items():
            if isinstance(value, int):
                usage[name] = usage.get(name, 0) + value
    return {
        "n": n,
        "counts": counts,
        "success_rate": _rate(wins, n),
        "completion_rate": _rate(completed, n),
        "truncation_rate": _rate(counts.get("truncated", 0), n),
        "timeout_rate": _rate(counts.get("timeout", 0), n),
        "error_rate": _rate(counts.get("agent_error", 0) + counts.get("env_error", 0)
                            + counts.get("invalid_action_limit", 0), n),
        "mean_reward": statistics.fmean(rewards) if rewards else None,
        "median_reward": statistics.median(rewards) if rewards else None,
        "mean_blinds": statistics.fmean(blinds) if blinds else None,
        "mean_steps": statistics.fmean(steps) if steps else None,
        "mean_legality": statistics.fmean(legality) if legality else None,
        "mean_regret": statistics.fmean(regret) if regret else None,
        "optimality_rate": statistics.fmean(optimality) if optimality else None,
        "mean_final_money": statistics.fmean(final_money) if final_money else None,
        "p50_agent_ms": _percentile(agent_ms, 50),
        "p95_agent_ms": _percentile(agent_ms, 95),
        "p50_env_ms": _percentile(env_ms, 50),
        "p95_env_ms": _percentile(env_ms, 95),
        "p50_total_ms": _percentile(total_ms, 50),
        "p95_total_ms": _percentile(total_ms, 95),
        "usage": usage,
    }


def _percentile(values: Sequence[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct / 100
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def group_summaries(results: Sequence[dict], group_by: Sequence[str] = ("agent_id",)) -> list[dict]:
    """按字段分组汇总，返回按组键排序的列表（含 ``group`` 字段）。"""
    groups: dict[tuple, list[dict]] = {}
    for row in results:
        key = tuple(row.get(field, "") for field in group_by)
        groups.setdefault(key, []).append(row)
    output = []
    for key in sorted(groups, key=lambda item: tuple(str(x) for x in item)):
        summary = summarize(groups[key])
        summary["group"] = dict(zip(group_by, key))
        output.append(summary)
    return output


def bootstrap_ci(values: Sequence[float], statistic: Callable[[Sequence[float]], float] = statistics.fmean,
                 n_resamples: int = 1000, confidence: float = 0.95, seed: int = 20261117) -> dict:
    """bootstrap 置信区间（描述统计，不是显著性检验）。

    Args:
        values: 样本。
        statistic: 统计量函数（默认均值）。
        n_resamples: 重采样次数。
        confidence: 置信水平（0.95）。
        seed: 固定种子，保证可复现。

    Returns:
        ``{"mean":..., "low":..., "high":..., "n":..., "confidence":...}``；空样本返回
        low/high/mean 均为 None。
    """
    if not values:
        return {"mean": None, "low": None, "high": None, "n": 0, "confidence": confidence}
    rng = random.Random(seed)
    samples = [statistic(values)]
    for _ in range(n_resamples):
        resample = [values[rng.randrange(len(values))] for _ in range(len(values))]
        samples.append(statistic(resample))
    samples.sort()
    alpha = (1 - confidence) / 2
    low = samples[int(alpha * len(samples))]
    high = samples[min(len(samples) - 1, int((1 - alpha) * len(samples)))]
    return {"mean": samples[0] if len(samples) == 1 else statistic(values),
            "low": low, "high": high, "n": len(values), "confidence": confidence}


def render_markdown_table(rows: Sequence[dict], columns: Sequence[str] | None = None) -> str:
    """把分组统计渲染为 Markdown 表（报告/CLI 使用）。"""
    if not rows:
        return "_(no results)_"
    columns = list(columns or ("group", "n", "success_rate", "completion_rate",
                               "mean_reward", "mean_regret", "optimality_rate",
                               "mean_legality", "timeout_rate", "error_rate"))
    header = "| " + " | ".join(columns) + " |"
    divider = "|" + "|".join(["---"] * len(columns)) + "|"
    lines = [header, divider]
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, dict):
                value = ", ".join(f"{k}={v}" for k, v in value.items())
            elif isinstance(value, float):
                value = f"{value:.4f}"
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)
