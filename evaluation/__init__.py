"""BalatroEval 评测执行层：Episode/Batch Runner、Trace、指标与实验管理。

模块职责：
- ``agents``：Agent 协议 + 脚本/随机/Oracle/HTTP 模型适配器；
- ``trace``：逐步 JSONL trace（schema 2）；
- ``episode_runner``：单 episode 执行（同步/异步）+ 指标；
- ``batch_runner``：任务展开、并发、重试、断点续跑；
- ``config``：实验配置、run 目录、manifest、code hash；
- ``metrics``：分组统计、bootstrap CI、Markdown 表；
- ``cli``：``python -m evaluation`` 入口。

边界：本包不实现规则（规则只在 ``bench``）；不修改全局状态；每个 episode 独立
Environment，模型调用与环境执行解耦。
"""
from .agents import (
    Agent,
    AgentDecision,
    AsyncAgent,
    CallableAgent,
    FirstLegalAgent,
    HttpChatAgent,
    OracleGreedyAgent,
    RandomAgent,
    ResponseCache,
    TokenBucket,
)
from .batch_runner import BatchSummary, Task, build_tasks, run_batch, run_batch_async
from .config import ExperimentConfig, ExperimentStore, compute_code_hash
from .episode_runner import EpisodeResult, run_episode, run_episode_async
from .metrics import bootstrap_ci, group_summaries, load_results, render_markdown_table, summarize
from .trace import TraceRecorder, read_trace, trace_summary

__all__ = [
    "Agent", "AgentDecision", "AsyncAgent", "CallableAgent", "FirstLegalAgent",
    "HttpChatAgent", "OracleGreedyAgent", "RandomAgent", "ResponseCache", "TokenBucket",
    "BatchSummary", "Task", "build_tasks", "run_batch", "run_batch_async",
    "ExperimentConfig", "ExperimentStore", "compute_code_hash",
    "EpisodeResult", "run_episode", "run_episode_async",
    "bootstrap_ci", "group_summaries", "load_results", "render_markdown_table", "summarize",
    "TraceRecorder", "read_trace", "trace_summary",
]
