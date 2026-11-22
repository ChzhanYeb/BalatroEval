# BalatroEval

**定位：** BalatroEval 是面向大模型 Agent 的长线规划测试集，用可判定、可复现的 Balatro 规则子集评测模型在**跨回合资源分配、多步决策、长期构建和失败恢复**上的能力。

> **2026-11-17 实现更新（vanilla 子集 v1）**：`bench/` 已从 L0 自定义公式升级为 **vanilla 1.0.1o 严格子集**：Red Deck / White Stake / Ante 1、三盲注 **300/450/600**、**4 手 / 4 弃**、手牌 8、Joker 槽 **5**、**8 个具名 Joker**、**牌型基础 Chips×Mult + 计分牌筛选**、完整快照/还原与确定性 RNG。新增 `evaluation/`（单 episode / batch runner、Trace schema 2、指标聚合、断点续跑、模型 Adapter）与 `scenarios/`（Schema/Loader/Validator + dev 场景），`bridge/server.py` 已接入 5 个工具。**规则实现 ≠ 对齐验证**：`fidelity_status` 仍为 `NOT_VERIFIED`，A2/A3 真游戏实测 0 行；长线四支柱仍未被机制覆盖。
> 实现文档入口：**[docs/implementation/README.md](docs/implementation/README.md)**；规则声明：[scenarios/RULES_VERSION](scenarios/RULES_VERSION) / [scenarios/rules_v1.json](scenarios/rules_v1.json)。

---

## 定位与当前实现差距

| 长线规划支柱 | 当前是否覆盖 | 证据 / 缺口 | 本轮是否声称 |
|---|---|---|---|
| ① 跨回合资源分配（商店 / 金钱 / 利息 / 跳盲 / reroll） | **未覆盖** | `bench/engine.py` 的 shop 只是“免费三选一 Joker”，无金钱/利息/价格/reroll；`scenarios/RULES_VERSION` 把 `money, interest, shop_money` 列入 `excluded`；资源每盲注重置（`hands/discards`），不跨期积累 | 不声称；登记 W3 机制改造候选 |
| ② 长期构建（Joker / 卡组协同、构建路径） | **未覆盖** | 60 个场景是单决策点（局面 + 合法动作 + oracle），无“跨盲注 build 路径”场景与评分；商店决策已被移出训练场景集 | 不声称；登记 W3 场景改造候选 |
| ③ 失败恢复（失败后重新规划） | **未覆盖** | 无“先失败、后恢复”的场景构造，也无恢复率/恢复代价指标定义 | 不声称；登记 W3 指标/场景候选 |
| ④ 长线指标（跨期资源效率、长程进度、恢复） | **未覆盖** | 主指标只有单步 `Local Regret`；`Episode Progress` 粒度粗且明令不得当主指标；`Pass^k` 已取消 | 不声称；登记 W3 指标候选 |
| ⑤ 场景分层（L1/L2 vs L3/L4） | **部分覆盖** | L1/L2 共 40/60 为单步战术；L3（15）仅“同一盲注内”多次 play/discard；L4（5）为高风险单步；无跨盲注长期构建/恢复场景 | 只声称“战术与盲注内多步”；不声称“长线规划已覆盖” |


## 当前状态

| 项 | 状态 |
|---|---|
| 项目名称 | **BalatroEval** |
| 项目定位 | 面向大模型 Agent 的**长线规划测试集** |
| 规则等级 | **L0（未对齐，实现已按 vanilla 1.0.1o 子集 v1）**：Red Deck/White Stake/Ante 1；300/450/600；4 手/4 弃；5 槽；8 个具名 Joker；牌型基础 Chips×Mult + 计分牌筛选。与真游戏一致性 **NOT_VERIFIED**（A2/A3 未实测） |
| 真实接入（balatrobot） | 📋 未开始（W3）；`bridge/realgame.py`、`scenarios/v3/`、`runs/w5-real/` 尚不存在 |
| 训练集（60 决策点） | 📋 未创建（W3） |
| 失败归因器 | 📋 未创建（W4） |
| L0–L3 对齐等级 | 当前 **L0**；W3 目标 L2；W5 目标 L3（真游戏 12 局小样本终验） |



## 两阶段架构

```text
阶段一：训练/开发环境（vanilla 1.0.1o 子集 v1 已实现；对齐仍未验证）
  真游戏捕获（balatrobot）──┐
                           ├─► 对齐场景集 ATS（60 个决策点）→ bench 引擎 / O1–O3 / 训练 Agent
  自建反事实变体（save/load）┘
  ── 对齐契约 A0–A4 ──► 真实游戏终验（RGFT，W5，目标 L3，📋 未执行）
       Balatro + Lovely + Steamodded + balatrobot + bridge/realgame.py（规划）
```

- **训练环境**：快、可枚举、可 CI；负责开发 Agent、算 oracle、跑训练集。
- **真游戏终验**：慢、不可并行、最终证据；只跑 12 局小样本，回答“离开自建环境结论还成立吗”。
- **不是二选一**：训练集自建，但每条局面都必须与真游戏对齐（A0–A4）；真实游戏是终验，不是批量主环境。

## 30 秒验证

环境：Windows + PowerShell + Python ≥ 3.11（实测 3.15.2），**无第三方依赖**（stdlib only；MCP SDK 只在 bridge 运行时需要）。

```powershell
Set-Location C:\WorkData\005.Agent\dsh-agent-eval

python -m unittest discover -s tests             # 期望：Ran 124 tests / OK
python -m bench rules                            # 规则声明（300/450/600、4/4、5 槽）
python -m bench verify --samples 10 --seed 20261112   # O1 vs 独立枚举，每例 218 候选
python -m bench demo --seed 20261117 --max-steps 50   # 一局贪心参照（stdout JSON）
python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy --experiment smoke --out runs --no-oracle
python -m evaluation report --run-dir runs/smoke   # 分组指标 + Markdown 表
```

> 以上命令是**训练环境自洽证据**（规则实现、确定性、Trace、批量执行），**不能**用来证明“与真游戏对齐”“真游戏终验通过”或“已覆盖长线规划”。对齐证据见 [docs/engine-fidelity.md](docs/engine-fidelity.md)（A/B 表仍为 `PENDING`）与 07 §3。
> `demo`/`batch` 的胜负不是 bug：固定 seed + 贪心/脚本策略下一次对局结果；判断引擎对错看**规则断言与轨迹自洽性**。

---

## 这是什么 / 不是什么

| ✅ 是 | ❌ 不是 |
|---|---|
| 面向大模型 Agent 的长线规划**测试集**（目标能力；当前先交付规则子集训练环境 + 对齐/终验流程） | 长线规划能力已被覆盖的成品基准（跨期资源、长期构建、失败恢复**均未覆盖**，见上表） |
| 两阶段评测项目：训练环境（vanilla 1.0.1o 子集 v1）+ 真游戏终验（📋 规划） | 原版 Balatro 的复刻、模拟器或排行榜 |
| 确定性、可复现的训练环境（52 张牌、8 张手牌、Ante 1 三盲注、4 手/4 弃、5 Joker 槽） | 与真游戏**已验证**对齐的规则实现（当前 `NOT_VERIFIED`；A2/A3 未实测） |
| 等级 1 的 vanilla 计分：牌型基础 Chips×Mult + 计分牌筛选 + Joker 槽位顺序 | 完整原版流水线（版本/蜡封/增强、重触发、Boss 效果、手牌等级 >1 均排除） |
| **8 个具名 vanilla Joker**（Joker/Jolly/Zany/Sly/Wily/Half/The Duo/The Trio） | 150 个 Joker 全覆盖（其余 142 个明确排除） |
| O1 精确局部 argmax、O2 弃牌 EV 近似、O3 贪心整局参照 | 全局最优策略，或真游戏 oracle；局部最优 ≠ 长期规划能力 |
| Trace schema 2（逐步 JSONL）+ 124 项自动化测试 + batch/resume/并发隔离 | 与真游戏对齐 / 终验已通过的证据；也不是“统计显著”的证据 |
| 诊断报告层设计：F1–F4 + F0 + E1 `env_divergence`（📋 归因器未实现） | 已实现的自动归因器，或 LLM Judge 判定；**也不是本项目的主定位** |

**当前已验证（训练环境自洽，实测非声明）**：124/124 单元/集成测试通过；牌型/基础分/计分牌筛选/8 Joker 条件与顺序有 golden 测试；`7♥7♦` Pair = 48（vanilla 等级 1）回归；同 seed 整局/逐步状态可复现；快照 roundtrip 通过；env 非法动作不改变状态；batch 支持并发、失败隔离、断点续跑；Trace JSONL schema 2 可读并含 state hash。**性能**实测见 [docs/implementation/performance.md](docs/implementation/performance.md)。

**尚未验证 / 未执行**：
- 与 vanilla 1.0.1o 的规则/分数对齐（A2–A3）：📋 W3；[docs/engine-fidelity.md](docs/engine-fidelity.md) 的 20 例人工对拍 + 5 例抽检仍为 `PENDING`（v3.0 降级为辅助证据）。
- 真游戏捕获/回放（A4）与 `scenarios/v3/` 60 决策点：📋 W3，未开始。
- 真实游戏接入（balatrobot）与 12 局终验（L3）：📋 W5，未开始；`bridge/realgame.py`、`runs/w5-real/` 尚不存在。
- **长线规划四支柱**：跨回合资源分配、长期构建、失败恢复、长线指标：**均未覆盖**（W3 候选）。

---

## 仓库结构

| 路径 | 内容 | 修改时注意 |
|---|---|---|
| `README.md` | 本文件：项目入口、定位与差距、快速验证、文档导航 | 命令与数字变了要同步 |
| `bench/` | ★ 规则与环境（16 个 `.py`）：rules_version/model/hand_eval/scoring/jokers/engine/actions/observation/environment/tools/oracle/serialize/rng/cards/errors | 规则唯一实现；依赖分层见手册 §2.2 |
| `scenarios/` | `RULES_VERSION`（人类可读声明）、`rules_v1.json`（JSON 镜像）、`dev/`（自造开发场景）、`schema.py`/`loader.py`/`validator.py` | 场景必须声明 rules_version；Boss 效果/未知扩展会被拒绝 |
| `evaluation/` | Episode Runner、Batch Runner、Trace（schema 2）、metrics、config、agents（含 HTTP Adapter）、CLI | 每个 episode 独立 Environment；结果 append-only |
| `tests/` | 124 项测试：规则/环境/scenario/runner/并发/断点/property/性能 smoke | 新增测试要同步数字 |
| `bridge/` | MCP 薄壳：`server.py` 暴露 5 个工具（4 游戏 + reset），调用 `bench.tools` | 薄壳不写规则；MCP SDK 延迟导入 |
| `runs/` | 实验产物：`runs/<experiment_id>/{manifest.json,results.jsonl,traces/}` | 不入库；`_test_tmp/`、`_bench/` 为测试/基准临时目录 |
| `docs/` | 保真度台账、Joker 语义、数据来源、`balatro/` 规则调研、`implementation/` 实现文档 | 结论措辞受红线约束 |
| `docs/implementation/` | 本次实现文档入口（架构/规则/API/Schema/执行/测试/性能/状态） | 与实际代码同步 |
| `data/` | 历史实验产物（W2 证据） | **属证据，不要覆盖** |
| `plan/` | 项目计划、每周任务、详细版设计；**决策基线在 `plan/详细版/07-真实游戏接入与终验.md`** | 上游约束；冲突时以 07 为准 |
| `evidence/` | 历史验收证据（W1；W3 对齐证据规划在 `evidence/W3/align/`） | 只读；真游戏截图只放 `evidence/` 且不对外分发 |
| `archive/legacy-2026-11-13/` | **历史归档**（旧名 BalatroBench / 旧定位文档） | 非当前定位；引用需注明日期 |
| `程序员手册.md` | W2/L0 时期的手册（§21 为对齐/终验规划） | 已部分过时；新实现以 `docs/implementation/` 为准 |
| `AGENTS.md` | 给 Agent 的极简契约版（W2/L0 基线 `c65fb9b`） | 本次升级已超出该基线；新任务以 `docs/implementation/` 为准 |

---

## 规则速览（vanilla 1.0.1o 子集 v1）

```
牌组 52 张 Red Deck ──► 初始手牌 8 张 ──► 每盲注 4 次出牌 / 4 次弃牌（Red +1）
Ante 1 三盲注：Small 300 / Big 450 / Boss 600（Boss 仅按目标分，效果未实现）
计分：chips = 牌型基础 Chips + Σ 参与计分牌的 rank chips(A=11, J/Q/K=10, 其余=点数)
       mult  = 牌型基础 Mult，按槽位顺序逐项应用 Joker（+Mult 加法 / ×Mult 乘法）
       final = floor(chips × mult)              # 候选口径（Wiki 未明写，标 UNVERIFIED）
牌型基础（等级 1）：HC 5×1 / P 10×2 / 2P 20×2 / 3K 30×3 / ST 30×4 / FL 35×4 /
                    FH 40×4 / 4K 60×7 / SF 100×8 / 5K 120×12 / FHouse 140×14 / FFive 160×16
8 个具名 Joker：Joker +4M / Jolly +8M(含对子) / Zany +12M(含三条) / Sly +50C(含对子) /
                 Wily +100C(含三条) / Half +20M(≤3 张) / The Duo ×2M(含对子) / The Trio ×3M(含三条)
候选动作：8 张手牌 ⇒ 218 出牌 + 218 弃牌 = 436 条合法动作
```

> **边界（不得越线）**：以上是 **IMPLEMENTED**，不是 **VERIFIED**。双盲注/金钱/商店经济/Boss 效果/消耗品/增强/版本/蜡封/多牌组/多赌注/Tag/Endless/手牌等级>1/重触发全部在 `Ruleset.excluded` 明列；Boss 场景由 validator 拒绝效果；`shop` 默认关闭，`free_joker_choice` 是显式 benchmark 扩展（非 vanilla）。
> **长线机制缺口**：仍无金钱/利息/购买/出售/reroll，无可累积的跨期资源；因此当前**不能**用本引擎主张“跨回合资源分配/长期构建/失败恢复”已被测到。四支柱仍登记为 W3/W4 候选。

实现细节（计分顺序、contains 口径、快照/哈希、错误码、trace schema）见 [docs/implementation/rules-implementation.md](docs/implementation/rules-implementation.md) 与 [docs/implementation/architecture.md](docs/implementation/architecture.md)。

---

## 常用命令

```powershell
# 全量测试（规则/环境/scenario/runner/并发/断点/property/性能 smoke）
python -m unittest discover -s tests

# 规则声明（JSON）
python -m bench rules

# O1 与独立暴力枚举对照
python -m bench verify --samples 10 --seed 20261112

# 跑一局贪心参照（stdout JSON；不写文件）
python -m bench demo --seed 20261117 --max-steps 50

# 弃牌 EV 采样估计（近似；K=50 在高样本下较慢）
python -m bench ev --seed 20261112 -k 50

# 单 episode / 批量（结果写 runs/<experiment>/）
python -m evaluation run   --scenarios scenarios/dev/play-pair-7h7d.json --agent oracle-greedy --experiment demo-run
python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy --experiment demo-batch --repeats 2 --max-concurrency 4
python -m evaluation report --run-dir runs/demo-batch

# 性能基准（环境侧，不含模型推理）
python -m benchmarks.bench --quick

# 语法/导入自检（本机 pycache ACL 受限时用 PYTHONPYCACHEPREFIX 指到临时目录）
$env:PYTHONPYCACHEPREFIX = "$env:TEMP\balatroeval-pycache"
python -m compileall -q bench evaluation scenarios benchmarks bridge/server.py
```

> 这些命令只作用于**训练环境**；真游戏侧命令（`health` / `gamestate` 冒烟、捕获、终验）📋 未提供。
> 断点续跑：同一 `--experiment` 目录重复执行 batch 默认跳过已记录任务；`--retry-failed` 只重跑失败项。
> 取消 `fsync`（`trace_fsync=False`，仅基准/临时实验）可显著提高吞吐（见性能文档）。

---

## 文档导航

| 文档 | 内容 | 语言 |
|---|---|---|
| [docs/implementation/README.md](docs/implementation/README.md) | **本次实现文档入口**：目标/范围/模块/测试与运行方式 | 中文 |
| [docs/implementation/architecture.md](docs/implementation/architecture.md) | 架构、模块职责、数据流、Episode 生命周期、Mermaid 图 | 中文 |
| [docs/implementation/rules-implementation.md](docs/implementation/rules-implementation.md) | 规则版本、实现范围、计分顺序、Joker、排除项与对齐边界 | 中文 |
| [docs/implementation/api-reference.md](docs/implementation/api-reference.md) | 真实函数/类接口（参数/返回/异常/副作用/确定性）与示例 | 中文 |
| [docs/implementation/evaluation-execution.md](docs/implementation/evaluation-execution.md) | 单 episode、批量并发、模型 Adapter、重试、断点续跑、Trace | 中文 |
| [docs/implementation/data-schema.md](docs/implementation/data-schema.md) | Scenario/Action/Observation/Trace/Result Schema 与版本 | 中文 |
| [docs/implementation/testing-and-validation.md](docs/implementation/testing-and-validation.md) | 测试分类、golden、property、并发、未验证项 | 中文 |
| [docs/implementation/performance.md](docs/implementation/performance.md) | 实测环境、基准结果、瓶颈与优化建议 | 中文 |
| [docs/implementation/implementation-status.md](docs/implementation/implementation-status.md) | NOT_IMPLEMENTED/IMPLEMENTED/TESTED/VERIFIED 状态矩阵 | 中文 |
| [程序员手册.md](程序员手册.md) | W2/L0 时期完整手册（部分过时；新实现以 `docs/implementation/` 为准） | 中文 |
| [AGENTS.md](AGENTS.md) | 同一内容的极简契约版（红线 / 依赖分层 / 验收命令 / 硬约束 / 已知粗糙点） | 中文 |
| [plan/00-项目全貌.md](plan/00-项目全貌.md) | 项目全貌：定位、目标、决策、风险、术语、进度 | 中文 |
| [plan/详细版/07-真实游戏接入与终验.md](plan/详细版/07-真实游戏接入与终验.md) | **决策基线 / 单一事实来源**：两阶段、A0–A4、L0–L3、W3 改造清单、真游戏 12 局终验、许可/证据边界 | 中文 |
| [plan/详细版/03-评测集与指标.md](plan/详细版/03-评测集与指标.md) | 场景分层、Schema、**分层指标（合规 → 单步 → 跨期 → 长程 → 诊断）**、统计方案 | 中文 |
| [plan/详细版/04-失败归因器.md](plan/详细版/04-失败归因器.md) | **诊断报告层**：F1–F4 + F0 判定规则、证据链、标注方案；E1 `env_divergence` 口径 | 中文 |
| [plan/详细版/05-实验与报告.md](plan/详细版/05-实验与报告.md) | 实验矩阵、基线、统计、成本、报告大纲、简历建议 | 中文 |
| [docs/engine-fidelity.md](docs/engine-fidelity.md) | 对齐台账：A 表真游戏捕获 + B 表 `save`/`load` 反事实回放（全 `PENDING`）+ A0–A4 检查清单 | 中文 |
| [docs/joker-semantics.md](docs/joker-semantics.md) | W2 合成夹具语义（历史）+ vanilla 8 Joker 目录；**2026-11-17 起 8 个已实现（见 `bench/jokers.py`），仍未与真游戏验证** | 中文 |
| [docs/data-sources.md](docs/data-sources.md) | 数据来源、许可与合规红线（总表） | 中文 |
| [docs/research/](docs/research/) | 生态与学术调研、验证方法 | 中文 |
| [archive/legacy-2026-11-13/INDEX.md](archive/legacy-2026-11-13/INDEX.md) | **历史归档索引**（旧名/旧定位文档；引用需注明日期） | 中文 |
| [scenarios/RULES_VERSION](scenarios/RULES_VERSION) | 人类可读规则声明（机器可读权威：`bench/rules_version.py`；JSON 镜像：`scenarios/rules_v1.json`；当前 `fidelity_status: NOT_VERIFIED`） | YAML 片段 |
| [plan/](plan/) | 项目全貌、每周任务、详细版设计（01 Windows 适配、02 规则与对拍、03 评测集、04 归因、05 实验、06 生态、07 真游戏终验） | 中文 |

---

## 保真度与定位红线（任何报告/注释/回复都不得越线）

| ❌ 不得声称 | 事实 |
|---|---|
| 实现了原版 Balatro 计分 / 已对齐 vanilla | 实现了 vanilla 1.0.1o **等级 1 子集**的计分路径（基础 Chips×Mult + 计分牌筛选），但 A2/A3 真游戏实测 **0 行**；`fidelity_status: NOT_VERIFIED`，对齐等级仍 **L0** |
| 8 个 Joker 是全部原版 Joker / 已覆盖 Joker 系统 | 只实现 8 个**具名 vanilla Joker**（数值来自 Wiki 事实页）；其余 142 个、Joker 版本、重触发、Blueprint 等均 `excluded`；触发/条件语义未经真游戏实测（contains 口径标 UNVERIFIED） |
| 固定 seed 复现了原版 RNG | 只保证本项目内可复现；不承诺与真游戏同种子同局面；训练集须用真游戏捕获（A4） |
| 124 测试通过 = 原版兼容 / 已对齐 | 测试只覆盖已实现行为（含 golden/边界/并发/断点），只证**子集自洽**，不证与真游戏一致 |
| `verify` 通过 = 计分公式正确 / 已对齐 | 两条路径**共用** `score_hand()`，只证明搜索路径一致；O1 是**局部**最优，不是长期规划最优 |
| `demo` 输了 = 引擎有 bug | 固定 seed + 贪心/脚本策略下的一次对局结果 |
| 已接入 balatrobot / 已对齐 / 已终验 | 真游戏接入、`scenarios/v3/`、12 局终验**均未执行（📋）**；未完成时只能写“未执行” |
| **已覆盖跨回合资源分配 / 长期构建 / 失败恢复 / 长线指标** | **四项均未覆盖**（见文首“定位与当前实现差距”）；只能写“目标能力，尚未覆盖，登记 W3” |
| 训练集结果 = 真游戏结果 | 训练集与终验是两套环境；`env_divergence` 必须单列，不得混入 Agent 失败 |
| 捕获回放 = 真游戏终验 | 捕获回放只做 A2/A4 分数/回放验证；终验指 Agent 在真游戏里跑完 12 局（`CAPTURE_REPLAY_ONLY` 是降级状态） |
| 真游戏 12 局小样本 = 统计显著 | n=12 只做描述统计 + 95% CI；**不做显著性主张** |
| 游戏文件 / mod / `.jkr` 存档 / 含游戏素材截图可以入库 | L8：只提交脱敏后的状态 JSON、分数、trace、版本清单；截图只放 `evidence/` 且不对外分发 |

要把 `fidelity_status` 从 `NOT_VERIFIED` 改成已验证，唯一合法流程按 v3.0 对齐契约：**A0 版本锁定 → A1 schema 对齐 → A2 单步分数（真游戏捕获实测）→ A3 规则子集（`RULES_VERSION.excluded` 明列排除项）→ A4 场景来源与回放**；证据写入 [docs/engine-fidelity.md](docs/engine-fidelity.md) 的 A 表（真游戏捕获）、B 表（`save`/`load` 反事实回放）与 `evidence/W3/align/`，再改 `RULES_VERSION` 并同步文档（手册 §17.2、§20.1）。旧的 20 例人工对拍 + 5 例抽检已降级为辅助证据（附录 C/D），单独通过它们不足以改状态。

---

## 贡献与修改约定

1. **先读** [AGENTS.md](AGENTS.md)（契约速览），再按任务查 [程序员手册.md](程序员手册.md) 的 §14 修改配方（改计分 / 加 Joker / 改流程 / 改日志 / 加 CLI / 调 RNG）；涉及真游戏/对齐先读 [07](plan/详细版/07-真实游戏接入与终验.md) 与手册 §21。
2. **改完必跑**：`python -m unittest discover -s tests`、`python -m bench verify`、`python -m bench demo`、`compileall`，并把原始输出贴出来；不要写“应该没问题”。这些结果是**训练环境自洽证据**，不得改写成对齐/终验证据，也不得改写成“长线规划已覆盖”。
3. **文档同步**：规则常量、计分公式、Joker 目录、状态字段、CLI 参数、测试数量，分别同步 `docs/implementation/` 对应文档与 [scenarios/RULES_VERSION](scenarios/RULES_VERSION) / [scenarios/rules_v1.json](scenarios/rules_v1.json)；**规则对齐状态变化需同步 07 / `docs/engine-fidelity.md` / `RULES_VERSION` / README**。
4. **真游戏证据边界**：游戏文件、mod、`.jkr` 存档、含游戏素材截图**不入库**；只提交脱敏状态 JSON、分数、trace 与版本清单（L8）。真游戏适配器是薄壳，**不写规则**。
5. **Git 安全**：仓库里还有其它未提交工作，禁止 `git add .` / `git commit -a` / `git reset --hard` / `git clean -fd`；只精确暂存本次工作涉及的文件（手册 §18）。
6. **不要覆盖** `data/` 里已有实验产物；新实验写新的 `runs/<experiment_id>/`。
7. **规则只有一份实现**：新规则/效果必须加在 `bench/`（并登记 `Ruleset.excluded` 与状态矩阵），不得在 `scenarios`/`evaluation`/`bridge` 复算分数。
8. **不要顺手扩功能**：金钱/利息/商店经济、Boss 效果、消耗品、跨盲注 build、失败恢复指标均属后续机制改造，需单独任务与测试；不得在文档/命名任务中夹带。

---

## 命名与目录说明

- **项目名**：`BalatroEval`。Python 发行名 `balatroeval`；包目录仍为 `bench/`，CLI 仍为 `python -m bench`（包名/命令名与项目名解耦，改包名会破坏测试与调用方）。
- **仓库目录**：`dsh-agent-eval` 暂不改名；`bridge/mcp-overlay.yml` 的绝对路径锚定该目录。
- **MCP 连接名**：`balatro` / `balatro_bridge` / profile `bench-local` 为历史连接标识，与 `evidence/W1` 验收证据一致，本轮保留。
- **历史旧名**：`BalatroBench` 仅允许出现在 git 历史提交信息、`archive/legacy-2026-11-13/` 归档件、以及“历史说明”中；不得出现在标题/首段/对外材料。
- **第三方同名项目**：`coder/balatrobench`（排行榜工具）与本项目无隶属关系；仅在“相关工作”中用一句客观区分（它做结果展示，本项目做长线规划测试集），**不再作为命名规则或首段内容**。

---

## 许可

`bench/` 为独立实现，未复制第三方代码（借鉴的设计线索见 [docs/data-sources.md](docs/data-sources.md) §2）。本仓库自身代码的许可证**尚待确定**（建议 MIT 或 Apache-2.0，见同文件 §4）；在确定之前不要对外分发。

真实游戏侧（Balatro、Lovely、Steamodded、balatrobot）的许可与边界见 07 §8：balatrobot 只调用不改源码；Steamodded 只作运行时依赖、不复制不分发；游戏文件与素材不入库。
