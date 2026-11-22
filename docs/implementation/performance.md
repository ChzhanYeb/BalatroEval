# 性能实测

> 目的：给出**真实测得**的环境侧性能、并发吞吐与瓶颈；不虚构数据。
> 测量时间：2026-11-17 ｜ 机器：AMD Ryzen 9 8945HS（16 逻辑 CPU）、Windows 11（10.0.26200）、Python 3.15.2（CPython）、stdlib-only。
> 方法：`python -m benchmarks.bench`（warmup 后计时，`time.perf_counter`；批量实验写 `runs/_bench` 并清理）。
> **不包含**模型推理延迟；模型延迟由 trace 的 `latency_ms.agent` 单独记录。

## 1. 规则核心（单次操作）

| 操作 | 次数 | 总耗时 | 单次均值 | p50 | p95 |
|---|---:|---:|---:|---:|---:|
| `evaluate_hand`（5 张） | 20,000 | 0.319 s | **16.0 µs** | 13.2 µs | 22.0 µs |
| `score_hand`（5 张 + 3 Joker） | 20,000 | 0.765 s | **38.3 µs** | 31.2 µs | 56.1 µs |
| `oracle.best_play`（8 张手牌，218 候选） | 300 | 1.886 s | **6.29 ms** | 6.38 ms | 8.01 ms |

## 2. 环境转移

| 操作 | 次数 | 单次均值 | p50 | p95 |
|---|---:|---:|---:|---:|
| `new_game(seed)` | 5,000 | **136 µs** | 132 µs | 210 µs |
| `Environment.reset + legal_actions + play step` | 2,000 | **6.88 ms** | 6.81 ms | 9.02 ms |

分解（单独测量、同一台机器）：

| 组件 | 中位耗时 | 说明 |
|---|---:|---|
| `new_game` | ~0.08 ms | 洗牌 52 张 + 编码 RNG 状态 |
| `build_observation` | ~0.69 ms | 含 `legal_plays`/`legal_discards` 计数 |
| `legal_actions`（436 个 Action） | ~2.2 ms | 主要成本：构造 436 个 dataclass |
| `engine.play`（单次计分） | ~0.33 ms | 含 deepcopy 状态 |
| `env.reset` | ~0.80 ms | new_game + observation |
| `env.step`（play） | ~1.0–1.3 ms | engine + observation + 两次 state_hash |

> `reset+legal_actions+play` 的 6.9 ms 主要是 `legal_actions` 构造 436 个动作；单步状态转移本身约 1 ms。Agent 使用完整动作集（Oracle/评测）时才需要这 2.2 ms。

## 3. 单 Episode（含 Trace 写盘，不含 fsync）

| 场景 | 次数 | 单次均值 | p50 | p95 |
|---|---:|---:|---:|---:|
| golden 决策点（1 step）`run_episode` | 100 | **18.2 ms** | 17.3 ms | 21.0 ms |

包含：Environment reset、Trace start/step/end JSONL 写入、results append。`trace_fsync=True` 时每条 trace 行额外 fsync；本机实测会显著增加耗时（与磁盘/杀软相关），批量场景建议正式实验保留默认、基准/临时实验用 `trace_fsync=False`。

## 4. Batch 吞吐（环境侧，first-legal Agent，`trace_fsync=False`）

| 并发 | 任务数 | 耗时 | 吞吐 | 峰值 tracemalloc |
|---:|---:|---:|---:|---:|
| 1 | 120 | 9.05 s | **13.26 eps/s** | 0.67 MB |
| 2 | 120 | 9.61 s | 12.48 eps/s | 0.90 MB |
| 4 | 120 | 10.30 s | 11.65 eps/s | 1.46 MB |

**结论**：单进程内提高 episode 并发**不会提升 CPU 吞吐**（规则计算与事件循环在单线程；trace 写入同步）。并发参数的价值在于**隔离慢任务**（模型等待时其他 episode 继续）与资源上限控制，而不是让 CPU 环境变快。需要线性扩展时按 scenario 分片多进程。

## 5. 模型等待型并发（模拟 5 ms/决策的 Agent）

| 并发 | 任务数 | 耗时 | 吞吐 | 相对 c=1 |
|---:|---:|---:|---:|---:|
| 1 | 60 | 2.43 s | 24.6 eps/s | 1.00× |
| 4 | 60 | 1.09 s | 55.1 eps/s | **2.24×** |
| 8 | 60 | 1.02 s | 58.7 eps/s | 2.38× |

**结论**：`asyncio` + `agent_concurrency` 能把模型等待重叠；真实模型延迟远大于 5 ms 时收益更明显。超过 4 后受单进程事件循环/CPU 限制趋平。

## 6. 成本热点与优化建议

| 热点 | 现状 | 建议（按收益排序） |
|---|---|---|
| Trace fsync | 每行 fsync，证据安全但慢 | 正式实验保留；批量重跑/基准用 `trace_fsync=False`；或按 episode 结束批量 fsync（需改 Trace，风险：崩溃丢部分步骤） |
| `legal_actions` 构造 436 Action | 2.2 ms/步 | 提供惰性/按 kind 的枚举；Agent 侧只取需要 kind；Oracle 用下标枚举（`legal_plays`）已更快 |
| `state_hash` 每步两次 | 小成本 | 可改为只在 start/end + 每 k 步记录；当前保留完整证据 |
| `build_observation` 每步 | 0.7 ms | 可缓存 legal counts；当前实现简单优先 |
| Oracle O1 6.3 ms | 218 × `score_hand` | 可批量化/向量化（当前 stdlib 纯 Python）；评测时 `oracle_enabled=False` 可关闭 |
| O2 discard EV | 218 弃牌子集 × K × 218 组合；默认 K=10 时单次决策可达 ~1.4 s（实测 discard 场景） | **不要**在批量中默认用 oracle-greedy 的 discard 决策；降 K、缓存、或改用启发式 |
| 多进程 | 未实现 | 按 scenario 分片调用 `run_batch`；每进程独立 `experiment_id`/目录，事后合并 |

## 7. 复现

```powershell
Set-Location C:\WorkData\005.Agent\dsh-agent-eval
$env:PYTHONPYCACHEPREFIX = "$env:TEMP\balatroeval-pycache"
python -m benchmarks.bench --quick     # ~11 s
python -m benchmarks.bench             # ~54 s（本机实测 total_s=53.70）
```

原始 JSON 可直接重定向保存；`benchmarks/bench.py` 中每项都注明 iterations 与是否含 trace/fsync，避免把不同口径混在一起比较。
