# 实现文档入口：vanilla 1.0.1o 严格子集评测环境

> 本目录记录 **2026-11-17** 完成的引擎升级与评测基础设施实现。
> 目标：把 `bench/` 从 L0 自定义公式升级为 **规则边界明确、行为确定、接口稳定、可测试、可批量运行** 的 Balatro 子集环境，并交付单 episode / 批量 / 并发 / Trace / 指标 / 断点续跑能力。
> **边界（先读）**：规则是 **IMPLEMENTED（代码已实现、单测覆盖）**，但不是 **VERIFIED（与真游戏实测一致）**。`fidelity_status` 仍为 `NOT_VERIFIED`，对齐等级仍为 **L0**；A2/A3 真游戏实测 0 行。任何“已对齐/已终验”的表述都无效。

---

## 1. 本次交付

| 层 | 内容 | 位置 |
|---|---|---|
| 规则层 | 牌型识别（12 种）、等级 1 基础 Chips×Mult、计分牌筛选、contains、8 个具名 Joker、确定性 RNG、快照/哈希 | `bench/` |
| 环境层 | `Environment`（reset/observe/legal_actions/step/snapshot/restore）、`Action`、统一错误码、Observation/紧凑文本 | `bench/environment.py`、`bench/actions.py`、`bench/observation.py` |
| 工具层 | 4 个游戏工具 + `reset_episode`，统一错误码，MCP 与本地 runner 共用 | `bench/tools.py`、`bridge/server.py` |
| 场景层 | Scenario Schema / Loader / Validator + 6 个 dev 场景 | `scenarios/` |
| 评测层 | Episode Runner、Batch Runner、Trace（schema 2）、指标聚合、实验管理、断点续跑、模型 Adapter | `evaluation/` |
| 测试 | **124** 项：规则/环境/场景/runner/并发/断点/property/性能 smoke | `tests/` |
| 基准 | 规则/环境/Oracle/Episode/批量/异步重叠实测 | `benchmarks/bench.py` |

## 2. 快速开始

```powershell
Set-Location C:\WorkData\005.Agent\BalatroEval

# 1) 全量测试（期望：Ran 124 tests / OK）
python -m unittest discover -s tests

# 2) 规则声明（机器可读）
python -m bench rules

# 3) 单 episode（golden 决策点：7h7d Pair = 48）
python -m evaluation run --scenarios scenarios/dev/play-pair-7h7d.json --agent oracle-greedy --experiment demo-pair --out runs

# 4) 批量 + 报告
python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy --experiment demo-batch --repeats 2 --max-concurrency 4
python -m evaluation report --run-dir runs/demo-batch

# 5) 性能基准
python -m benchmarks.bench --quick
```

> 本机 `__pycache__` 目录受 DSH 沙箱 ACL 限制时，`compileall`/测试可设置
> `$env:PYTHONPYCACHEPREFIX = "$env:TEMP\balatroeval-pycache"`；这只是环境绕行，不改变代码行为。

## 3. 推荐阅读顺序

1. [architecture.md](architecture.md)：分层、调用链、Episode 生命周期、并发模型；
2. [rules-implementation.md](rules-implementation.md)：规则版本、计分顺序、Joker、排除项；
3. [api-reference.md](api-reference.md)：真实函数/类接口（参数/返回/异常/副作用/确定性）；
4. [data-schema.md](data-schema.md)：Scenario/Action/Observation/Trace/Result Schema；
5. [evaluation-execution.md](evaluation-execution.md)：单/批量执行、并发、重试、断点续跑、模型 Adapter；
6. [testing-and-validation.md](testing-and-validation.md)：测试分类、golden、property、未验证项；
7. [performance.md](performance.md)：实测数据、瓶颈；
8. [implementation-status.md](implementation-status.md)：NOT_IMPLEMENTED / IMPLEMENTED / TESTED / VERIFIED 状态矩阵。

## 4. 一句话架构

```text
Agent / MCP 工具
      │  Action(dict)
      ▼
bench.tools ──► bench.environment.Environment ──► bench.engine（唯一规则实现）
                        │                              │
                        │                              ├─ hand_eval / scoring / jokers
                        │                              └─ serialize（快照/hash）
                        ▼
               evaluation.run_episode(_async) ──► Trace JSONL（schema 2）+ results.jsonl
                        ▲
                        └── evaluation.run_batch(_async)：任务展开、并发、重试、断点续跑
```

## 5. 硬边界（不得越线）

| 不得声称 | 事实 |
|---|---|
| 已与 vanilla 1.0.1o 对齐 | 只实现了等级 1 子集；A2/A3 实测 0 行，`NOT_VERIFIED` |
| Boss 效果已处理 | Ante 1 Boss **仅按目标分 600 建模**；具名效果未实现，请求效果会被场景校验拒绝 |
| 金钱/商店经济已实现 | `money/interest/shop_economy` 明确排除；`free_joker_choice` 是 benchmark 扩展（非 vanilla） |
| 长线规划四支柱已覆盖 | 无跨期可累积资源；四支柱仍未覆盖，登记 W3/W4 |
| O1 是全局最优 | O1 是**当前手牌局部 argmax**；不评估弃牌/未来 |
| 124 测试通过 = 规则正确 | 测试只证子集自洽 + 基础设施正确；不证与真游戏一致 |

## 6. 与旧文档的关系

- `AGENTS.md` / `README.md` / `程序员手册.md` 中的 W2/L0 描述（25 测试、自定义 `HAND_MULT`、3 槽、300/800/2000、`log_path` 默认写 `data/`）**已被本次实现取代**；新实现以本目录为准。旧文档未删除，保留历史。
- `docs/balatro/` 是规则事实调研（来源、证据等级、未核实项），本次实现以其中的 `engine-gap.md` W3 目标值为准。
- `docs/engine-fidelity.md` 的 A/B 表仍为 `PENDING`；本次**没有**修改任何 fidelity 状态。
