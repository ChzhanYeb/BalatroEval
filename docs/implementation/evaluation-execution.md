# 评测执行：单 Episode、批量、并发、重试与断点续跑

> 入口：`python -m evaluation`。所有 episode 使用**独立 Environment**；模型调用与环境执行解耦；Trace/结果 append-only。

## 1. 单 Episode

### 1.1 代码方式

```python
from scenarios.loader import load_scenarios
from evaluation.config import ExperimentConfig, ExperimentStore
from evaluation.agents import OracleGreedyAgent
from evaluation.episode_runner import run_episode

scenario = load_scenarios("scenarios/dev/play-pair-7h7d.json")[0]
config = ExperimentConfig(
    experiment_id="single-demo", scenario_paths=("scenarios/dev/play-pair-7h7d.json",),
    agent_id="oracle-greedy", output_dir="runs", oracle_enabled=True,
)
store = ExperimentStore(config)
result = run_episode(scenario, OracleGreedyAgent(), config, store, task_id="my-task")
print(result.status, result.total_reward, result.mean_regret, result.optimality_rate)
```

输出（本机实测）：`completed 48 0.0 1.0`，trace 在 `runs/single-demo/traces/my-task.jsonl`。

### 1.2 CLI

```powershell
python -m evaluation run --scenarios scenarios/dev/play-pair-7h7d.json \
  --agent oracle-greedy --experiment demo-pair --out runs
```

`--agent` 支持 `oracle-greedy` / `random` / `first-legal` / `http`。

### 1.3 执行顺序（单 episode 内严格串行）

```text
reset → observe → agent.decide_async → validate → step → observe → ...
       ↑                                                        │
       └──────────────── 直到 terminated/truncated/timeout/error ┘
```

- 每步记录 trace（含 action、valid/error、reward、前后 state_hash、observation 文本、score、延迟）；
- `oracle_enabled=True` 时，在每个 **play 决策**前计算 O1 最优分，写 `decision_metric`（regret/optimality）；
- discard 决策不进入 regret 分母（避免“正确弃牌被记最大 regret”）。

## 2. 批量执行

```powershell
python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy \
  --experiment demo-batch --repeats 2 --max-concurrency 4 --max-tasks 12
```

等价代码：

```python
import asyncio
from scenarios.loader import load_scenarios
from evaluation.config import ExperimentConfig
from evaluation.batch_runner import run_batch_async

scenarios = load_scenarios("scenarios/dev")
config = ExperimentConfig(experiment_id="demo-batch", scenario_paths=("scenarios/dev",),
                         agent_id="oracle-greedy", repeats=2, max_concurrency=4,
                         output_dir="runs")
summary = asyncio.run(run_batch_async(scenarios, config))
print(summary.counts, summary.skipped, len(summary.results))
```

### 2.1 任务展开与 ID

```text
tasks = scenarios × repeats
task_id = sha256(experiment_id | scenario_id | scenario_hash | agent_id | repeat | config_hash)[:20]
task seed = scenario.seed + repeat
```

`config_hash` 只包含**影响结果**的字段（rules_version/signature、agent_id/params、repeats、max_steps、max_invalid_actions、oracle_enabled）。并发/超时/重试/输出目录**不进** hash，因此调整并发不会误判为“新实验”。

### 2.2 并发控制（三层）

| 控制 | 配置 | 作用 |
|---|---|---|
| Episode 并发 | `max_concurrency` | 同时跑多少个 episode（各自独立 env/agent/trace） |
| Agent/模型并发 | `agent_concurrency` | 同时允许多少个 `decide` 在飞行（模型限流） |
| Rate limit | `TokenBucket(rate, burst)` | 每秒请求上限（HTTP Agent 可选） |

- episode 内不并行（状态依赖）；
- 单进程内 CPU 规则计算受事件循环/GIL 限制，`max_concurrency` 提高不会提升 CPU 吞吐（性能文档实测）；
- 模型等待型任务可重叠：实测 5ms 模拟延迟、60 任务，c=1→2.43s，c=4→1.09s（2.2×）；
- 需要真多进程时，按 scenario 分片多次调用 `run_batch`（不同 `experiment_id` 或不同切片），结果文件可分别保存。

### 2.3 失败隔离与重试

```text
每个 task：
  attempt 0..retry_attempts-1
    try: run_episode_async
    except: fallback_result(status=env_error 或 agent_error)     # 不污染其他 task
    成功（completed/truncated）或最后一次 → 返回
    否则 sleep(retry_backoff_s * 2^attempt) 后重试
```

- Agent 构造失败 → `agent_error`；episode 内部异常 → `env_error`；模型超时 → `timeout`；
- 连续非法动作 > `max_invalid_actions` → `invalid_action_limit`；
- 任何失败都不抛给批次（除非 Trace 写入本身失败，见 §4）；
- `retry_attempts=1` 表示不重试。

## 3. 断点续跑

### 3.1 行为

```powershell
# 第一次
python -m evaluation batch --scenarios scenarios/dev --experiment demo --out runs
# 第二次（默认 resume=True）→ 已完成任务全部跳过，results.jsonl 不新增
python -m evaluation batch --scenarios scenarios/dev --experiment demo --out runs
# 只重跑失败项
python -m evaluation batch --scenarios scenarios/dev --experiment demo --out runs --retry-failed
```

实现：`ExperimentStore.completed_task_ids(success_only=retry_failed)`：
- 默认（`retry_failed=False`）：跳过 results.jsonl 中**任何**已记录 task（含失败），避免重复计费；
- `retry_failed=True`：只跳过 `completed`/`truncated`，失败项重跑并 append 新结果；索引取最新行。

### 3.2 为什么 task_id 含 config hash

- 改配置（模型/温度/repeats/规则版本）→ task_id 变化 → 不复用旧结果；
- 同配置重跑 → task_id 相同 → 跳过或重跑（取决于 retry 策略）；
- 因此不存在“同名覆盖”：结果只 append，索引取最新。

### 3.3 隔离等级

- ✅ 同 run 目录、单进程：安全（线程锁 + 每 task 独立 trace）；
- ⚠️ 同 run 目录、多进程同时写：**不支持**（results.jsonl 的 append 与索引可能交错）；需要多进程时每进程用独立 `experiment_id`/目录，事后合并。

## 4. Trace 与结果落盘

```text
runs/<experiment_id>/
  manifest.json            # 一次写入；config/rules/code_hash/scenarios
  results.jsonl            # 每 task 一行 EpisodeResult（append）
  traces/<task_id>.jsonl   # 每 episode 一个 trace（append；重试为 -rN 后缀）
```

- 每步 `flush`；`trace_fsync=True`（默认）额外 `fsync`，崩溃时不丢已完成步骤（性能开销见 performance.md）；
- `trace_fsync=False` 仅用于基准/临时实验；正式实验保留默认；
- Trace 写入失败会**显式抛出**，由 batch 隔离为 `env_error` 并记录错误——不允许静默丢证据。

## 5. 模型 Adapter（HTTP）

```python
from evaluation.agents import HttpChatAgent, ResponseCache, TokenBucket

agent = HttpChatAgent(
    agent_id="gpt-like", model="my-model",
    temperature=0.0, max_tokens=256,
    cache=ResponseCache("runs/_cache/llm.sqlite"),
    rate_limiter=TokenBucket(rate_per_second=2, burst=4),
    max_retries=3, backoff_s=0.5, timeout_s=30.0,
)
```

- 默认 transport 读取环境变量：`BALATROEVAL_LLM_URL`（OpenAI-compatible chat completions 完整 URL）、`BALATROEVAL_LLM_KEY`（可选 Bearer）；**未配置时抛错**，不会静默用假模型。
- 也可通过 `transport=` 注入自有实现（测试即如此）；请求体固定为 `{model, messages, temperature, max_tokens}`。
- 缓存键 = `sha256(model + messages + temperature + max_tokens)`；命中缓存不重复计费。
- 输出解析：取文本中第一个 JSON 对象 → `Action.from_dict`；解析失败 → `agent_error`（不猜动作）。
- 真实模型服务**未在本机实测**；仅用 fake transport 验证了缓存/重试/超时路径。

## 6. 指标与报告

```powershell
python -m evaluation report --run-dir runs/demo-batch
```

输出 JSON（含 `summary/groups/table/manifest`）。指标定义见 api-reference §12.4 与 metrics.py：
- `legality_rate`：合法动作 / 全部动作；
- `mean_regret` / `optimality_rate`：仅 play 决策；
- `success_rate`：status=completed 且 outcome=win；
- `truncation_rate`/`timeout_rate`/`error_rate`：单列，不混入成功率；
- `latency_ms.agent` 与 `latency_ms.env` 分开；模型推理不混入环境性能。

## 7. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 第二次 batch 什么都没跑 | resume 默认跳过已记录 task | 换 `--experiment` 或 `--retry-failed`（只重跑失败） |
| 同 experiment 报 “different config” | manifest 的 config_hash 不一致 | 换 experiment_id；不要混配置 |
| 90% 时间花在 trace | `trace_fsync=True` + 每步大量文本 | 正式实验保留；基准用 `trace_fsync=False` |
| oracle-greedy 在 discard 场景很慢 | O2 需枚举 218 弃牌子集 × K × 218 组 | 降低 `discard_samples` 或改用脚本 Agent；O2 是近似 |
| 并发调大吞吐不升 | 单进程 CPU/GIL + 同步规则计算 | 用多进程分片；模型等待型并发另算 |
| Windows 临时目录清理失败 | DSH 沙箱对系统 temp 的 chmod/删除受限 | 测试用 `runs/_test_tmp`（已 gitignore） |
