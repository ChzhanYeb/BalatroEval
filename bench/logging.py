"""LEGACY（W2/L0）append-only JSONL 迁移日志：**新链路不再调用本模块**。

历史用途：`engine.play/discard/choose_joker` 曾默认写 `data/episode.jsonl`（schema_version=1）。
本次升级后：
- 规则层（`bench.engine`）是纯函数，不做文件 IO；
- 评测链路使用 `evaluation.trace.TraceRecorder`（schema_version=2，含 step/error/hash/latency）；
- 本模块仅为兼容旧脚本/旧日志读取而保留，**不得**在新实验中使用（会写出旧 schema，缺少
  step_id/valid/error/state_hash 等证据）。

`state_summary` 仍在 `bench.model` 中提供；旧字段语义见历史提交 `c65fb9b`。
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .model import GameState, state_summary


def append_episode(path: str | Path, *, state_before: GameState, action: dict[str, Any],
                   score_delta: int, state_after: GameState, score_details: dict | None = None) -> None:
    """向 path 追加一行迁移记录；父目录不存在时自动创建。

    参数：
    - path：JSONL 路径；调用方默认给 data/episode.jsonl，测试/无痕运行传 None 由调用方
      自行跳过，本函数不做 None 判断。
    - state_before / state_after：用 model.state_summary 压缩成可序列化摘要（含完整
      rng_state，但 deck / discard_pile 只有计数），单行即可还原可见状态，不足以重放发牌。
    - action：动作字典，形如 actions.CardAction.to_dict() 或 choose_joker 的内联字典。
    - score_delta：本次计分增量；弃牌与选 Joker 记 0。
    - score_details：ScoreResult.to_dict() 或 None（非计分动作）。
    返回：None。
    副作用：创建父目录并以追加模式写文件；每次调用写一整行。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # schema_version 逐行写入（而不是写在文件头），这样单行即可自描述、可按行分发。
    row = {
        "schema_version": 1,
        "state_before": state_summary(state_before),
        "action": action,
        "score_delta": int(score_delta),
        "score_details": score_details,
        "state_after": state_summary(state_after),
    }
    # 编码选择：ensure_ascii=False 让中文（Joker 名称等）保持可读；sort_keys=True 让同
    # 一逻辑记录的键序稳定，便于逐行 diff 与跨实验比较。
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
