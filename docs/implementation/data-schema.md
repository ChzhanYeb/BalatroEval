# 数据 Schema（Scenario / Action / Observation / Trace / Result）

> 所有 schema 都在代码里显式带版本字段；新增/改名字段必须升版本并同步本文件与消费方。
> 存储原则：**JSON** 放配置与小结果；**JSONL** 放逐 episode / 逐步事件（append-only）；大规模分析时再由外部脚本转 Parquet（本项目**未内置** Parquet 依赖）。

## 1. Scenario（`scenarios/schema.py`，`scenario_schema_version=1`）

```json
{
  "scenario_schema_version": 1,
  "scenario_id": "dev-play-pair-7h7d",
  "rules_version": "vanilla_1.0.1o_subset_v1",
  "seed": 42,
  "origin": "synthetic_dev",
  "decision_type": "play",
  "goal": {"type": "reach_score", "target": 48},
  "initial_state": {
    "hand_ids": ["c7h", "c7d", "c2s", "c3c", "c5d", "c9s", "c11c", "c13d"],
    "joker_ids": [],
    "blind_idx": 0,
    "total_score": 0,
    "hands_left": 4,
    "discards_left": 4,
    "target": 300
  },
  "constraints": {"max_steps": 1, "allowed_action_kinds": ["play"]},
  "extensions": [],
  "boss_blind": null,
  "metadata": {"description": "golden pair", "tags": ["dev", "golden"]}
}
```

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `scenario_schema_version` | int | 是 | 必须 = 1 |
| `scenario_id` | str | 是 | 1–120 字符；批量内唯一 |
| `rules_version` | str | 是 | 必须等于引擎 `rules_version` |
| `seed` | int | 是 | `task seed = scenario.seed + repeat` |
| `origin` | str | 是 | `synthetic_dev` / `real_capture` / `real_counterfactual` |
| `decision_type` | str | 是 | `episode` / `play` / `discard` |
| `goal.type` | str | 是 | `clear_ante1` / `maximize_score` / `reach_score`（后者需 target>0） |
| `initial_state.hand_ids` | list[str] | 否 | ≤8 张、唯一、标准 ID；None=按 seed 发牌 |
| `initial_state.joker_ids` | list[str] | 否 | ≤5、唯一、8 具名 ID |
| `initial_state.blind_idx` | int | 否 | 0/1/2；=2 时必须声明 `boss_blind` |
| `initial_state.total_score` | int | 否 | ≥0 且不得已达标 |
| `initial_state.hands_left` / `discards_left` | int | 否 | 0..4 |
| `initial_state.target` | int | 否 | >0；默认按盲注 |
| `constraints.max_steps` | int | 否 | >0；与 config.max_steps 取较小值 |
| `constraints.allowed_action_kinds` | list[str] | 否 | `play`/`discard`/`choose_joker`；decision_type=play 时必须仅 `["play"]` |
| `extensions` | list[str] | 否 | 仅 `free_joker_choice`；real_* 场景不允许 |
| `boss_blind` | object/null | 否 | `{"name":..., "effect": null}`；**非空 effect 被拒绝**（UNSUPPORTED_RULE） |
| `metadata` | object | 否 | `capture_id`（real_capture 必填）、tags、description |

**未知顶层字段会被拒绝**（避免拼写错误被静默忽略）。

## 2. Action（`bench/actions.py`）

```json
{"kind": "play", "card_ids": ["c7h", "c7d"], "hand_indices_snapshot": [0, 1], "joker_index": null, "code": "play:c7d,c7h"}
```

| kind | 字段 | 约束 |
|---|---|---|
| `play` / `discard` | `card_ids: list[str]` | 1–5 个、唯一、标准 ID |
| `choose_joker` | `joker_index: int\|null` | 仅商店扩展；null=跳过 |
| `advance` | 无 | 预留（当前运行时不使用） |

`code` 是 **canonical**：卡牌 ID 排序后拼接（`play:c7d,c7h`），用于去重/回放；`card_ids` 保留选择顺序用于展示。

## 3. Observation（`bench/observation.py`，`schema_version=1`）

```json
{
  "schema_version": 1,
  "rules_version": "vanilla_1.0.1o_subset_v1",
  "target_game_version": "1.0.1o",
  "allowed_action_kinds": ["play"],
  "episode": {"phase": "play", "outcome": null, "step": 0, "terminated": false},
  "blind": {"index": 0, "kind": "small", "name": "Small Blind", "target": 300,
            "score": 0, "score_needed": 300, "hands_left": 4, "discards_left": 4,
            "boss_effect": null, "boss_effect_implemented": true},
  "hand": [{"id": "c7h", "label": "7h", "suit": "hearts", "rank": 7, "rank_label": "7", "chips": 7}],
  "hand_size": 8, "hand_size_limit": 8, "deck_count": 44, "discard_count": 0,
  "jokers": [], "joker_slots": 5, "shop_options": [],
  "legal_action_counts": {"play": 218, "discard": 218}
}
```

- **不含**牌堆顺序、RNG、oracle 结果；完整合法动作列表通过 `Environment.legal_actions()` 取（不交给 LLM，避免上下文爆炸）。
- `render_observation()` 输出 ≤1000 字符的紧凑文本（约 100–175 token），用于 MCP `get_state`。

## 4. Trace（`evaluation/trace.py`，`schema_version=2`，每 episode 一个 JSONL）

**为什么逐步一行**：可流式写入（崩溃不丢已完成步骤）、可按行过滤失败步/regret、可每 task 独立文件避免并发写冲突。代价是行数多（每步 1 行）。

每行公共字段：`schema_version=2`、`run_id`、`task_id`、`episode_id`、`timestamp`、`event`。

### 4.1 `episode_start`

```json
{"event": "episode_start", "scenario": {...}, "scenario_hash": "sha256",
 "rules_version": "vanilla_1.0.1o_subset_v1", "rules_signature": "sha256",
 "code_hash": "sha256", "config": {...}}
```

### 4.2 `step`

```json
{"event": "step", "step": 1,
 "action": {"kind": "play", "card_ids": ["c7h","c7d"], "code": "play:c7d,c7h"},
 "valid": true, "error": null, "reward": 48,
 "terminated": false, "truncated": false, "termination_reason": null,
 "state_hash_before": "64hex", "state_hash_after": "64hex",
 "observation_text": "rules=... phase=play ...",
 "score": {"hand_type": "pair", "base_chips": 10, "base_mult": 2,
           "scoring_card_ids": ["c7h","c7d"], "chips": 24, "mult": "2/1",
           "final_score": 48, "trace": [...], "analysis": {...}},
 "latency_ms": {"agent": 0.1, "env": 1.2},
 "raw_output": null, "usage": {}}
```

非法动作也写 step：`valid=false`、`error={"code","message","detail"}`、`reward=0`、`state_hash_before == state_hash_after`（状态未变）。

### 4.3 `decision_metric`（可选）

```json
{"event": "decision_metric", "step": 1, "action_code": "play:c7d,c7h",
 "oracle_score": 48, "actual_score": 48, "regret": 0.0}
```

只在 play 决策且 `oracle_enabled=true` 时写；discard/choose_joker 不写 regret。

### 4.4 `episode_end`

```json
{"event": "episode_end", "status": "completed", "outcome": "win", "steps": 12,
 "total_reward": 1350, "blinds_cleared": 3, "blind_scores": [300, 450, 600],
 "metrics": {"legality_rate": 1.0, "mean_regret": 0.0, "optimality_rate": 1.0, ...},
 "duration_ms": 42.5, "error": null}
```

`status ∈ {completed, truncated, timeout, agent_error, invalid_action_limit, env_error}`。

## 5. Result（`runs/<experiment_id>/results.jsonl`，`result_schema_version=1`）

一行 = 一个 task 的 `EpisodeResult.to_dict()`：

| 字段 | 说明 |
|---|---|
| `task_id` | sha256(experiment + scenario_hash + agent + repeat + config_hash)[:20]，唯一键 |
| `run_id` / `episode_id` | 实验 / episode 实例 |
| `scenario_id` / `scenario_hash` / `decision_type` | 场景身份与类型 |
| `agent_id` / `seed` / `rules_version` | 执行身份 |
| `status` / `outcome` | 见上；`outcome ∈ {win, loss, null}` |
| `steps` / `total_reward` / `blind_scores` / `blinds_cleared` | 进度 |
| `legality_rate` / `invalid_actions` | 合规指标 |
| `play_decisions` / `action_type_mismatch` / `mean_regret` / `max_regret` / `optimality_rate` | 战术指标（仅 play） |
| `total_usage` / `latency_ms` | token 与延迟（agent/env/total 分开） |
| `trace_path` / `error` | 证据路径 / 结构化错误 |

同一 task 重跑会 append 新行；`ExperimentStore.result_index()` 取**最新**一行。

## 6. Snapshot（`bench/serialize.py`，`snapshot_schema_version=1`）

```json
{"env_schema_version": 1, "step_count": 3, "total_reward": 120,
 "allowed_action_kinds": null, "max_steps": 120,
 "state": {"snapshot_schema_version": 1, "rules_version": "...", "...": "...",
           "hand": ["c7h", "..."], "deck": ["..."], "discard_pile": [],
           "jokers": ["joker"], "shop_options": [],
           "rng_state": "[...]", "seed": 42},
 "state_hash": "64hex"}
```

- 还原校验：schema 版本、卡牌 ID、52 张唯一性、state_hash；
- 用于回放/分支/断点，不允许只存摘要。

## 7. Manifest（`runs/<experiment_id>/manifest.json`，`manifest_schema_version=1`）

```json
{
  "manifest_schema_version": 1,
  "created_at": "2026-11-17T...Z",
  "config": {"experiment_id": "...", "config_hash": "16hex", "...": "..."},
  "rules": {"rules_version": "...", "blinds": [...], "...": "..."},
  "rules_signature": "64hex",
  "code_hash": "64hex",
  "scenarios": [{"scenario_id": "...", "scenario_hash": "64hex"}],
  "scenario_count": 6
}
```

- 同一 run 目录只允许一种 `config_hash`；冲突抛错（防止不同配置混跑）。
- `code_hash` = `bench/` + `evaluation/` + `scenarios/` 全部 `.py` 内容哈希（排序后）。

## 8. 版本与兼容

| Schema | 当前版本 | 变更规则 |
|---|---:|---|
| Scenario | 1 | 加字段需升版本；validator 拒绝未知顶层字段 |
| Observation | 1 | 工具契约；改字段需升版本并同步 MCP 工具描述 |
| Trace | 2 | schema 1 是旧 L0 episode 日志；v2 增加 event/step_id/hash/latency/error 等 |
| Result | 1 | 加字段向后兼容（消费者忽略未知键）；删除/改义需升版本 |
| Snapshot | 1 | 不允许跨版本还原（显式拒绝） |
| Manifest | 1 | 同 run 目录配置冲突拒绝 |

## 9. JSONL vs Parquet

- **JSONL**（本实现）：append-only、易流式读、适合逐 episode/trace、便于人工排查；缺点是体积大（含 observation 文本与 score trace）。
- **Parquet**（未内置）：适合把 `results.jsonl` 拉平成列式表做大规模统计；建议离线转换（pandas/pyarrow 属外部依赖，不进入本仓库依赖）。
- **不引入数据库/消息队列**：当前规模（百–千 episode）本地文件足够；并发写由“每 task 独立 trace + 单进程 results 锁”保证。
