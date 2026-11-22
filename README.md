# BalatroEval

**定位：** BalatroEval 是面向大模型 Agent 的长线规划测试集，用可判定、可复现的 Balatro 规则子集评测模型在**跨回合资源分配、多步决策、长期构建和失败恢复**上的能力。

> **当前实现（2026-11-22 文档同步）**：`bench/` 已实现 **vanilla 1.0.1o 严格子集 v2**：Red Deck / White Stake / Ante 1、三盲注 **300/450/600**、**4 手 / 4 弃**、手牌 8、Joker 槽 **5**、**8 个具名 Joker**、**牌型基础 Chips×Mult + 计分牌筛选**、确定性 RNG、完整快照/还原；**v2 新增经济层**：起始 **$4**、通关奖励 **$3/$4/$5**、每剩余 1 手/未用 1 弃牌 **+$1**、利息 **每 $5 得 $1（上限 $5）**、Small/Big 之后的**付费商店**（2 个报价、按稀有度固定价、买入/卖出/reroll/离开）；`evaluation/`（单 episode / batch runner、Trace schema 2、指标聚合、断点续跑、模型 Adapter）与 `scenarios/`（Schema/Loader/Validator + dev 场景）已可用。
> **规则实现 ≠ 对齐验证**：`fidelity_status` 仍为 `NOT_VERIFIED`，对齐等级仍 **L0**，A2/A3 真游戏实测 **0 行**；真游戏接入、`scenarios/v3/`、12 局终验、归因器**均未执行**。
> 实现文档入口：**[docs/implementation/README.md](docs/implementation/README.md)**；规则声明：[scenarios/RULES_VERSION](scenarios/RULES_VERSION) / [scenarios/rules_v2.json](scenarios/rules_v2.json)。

---

## 定位与当前实现差距

| 长线规划支柱 | 当前是否覆盖 | 证据 / 缺口 | 本轮是否声称 |
|---|---|---|---|
| ① 跨回合资源分配（商店 / 金钱 / 利息 / reroll） | **仅有载体，未定义指标** | v2 已实现 `money` 跨盲注保留、利息、2 报价付费商店、买入/卖出/reroll；但**没有**跨期资源效率/商店决策收益差等指标，也没有经济场景集；价格/权重/利息顺序均 `unverified` | 只说“具备载体”；指标登记 W3 |
| ② 长期构建（Joker / 卡组协同、构建路径） | **未覆盖** | 商店能买 Joker 了，但没有“跨盲注 build 路径”的场景设计与评分；`scenarios/dev/` 只有 1 个经济决策点 | 不声称；登记 W3 场景改造候选 |
| ③ 失败恢复（失败后重新规划） | **未覆盖** | 无“先失败、后恢复”的场景构造，也无恢复率/恢复代价指标（经济给了构造前提，但未构造） | 不声称；登记 W3 指标/场景候选 |
| ④ 长线指标（跨期资源效率、长程进度、恢复） | **未覆盖** | 主指标只有单步 `Local Regret`（仅 play 决策）；`final_money` / `mean_final_money` 只是描述量，不是跨期效率指标 | 不声称；登记 W3 指标候选 |
| ⑤ 场景分层 | **部分覆盖（仅 dev 场景）** | 无 60 决策点 ATS；`scenarios/v3/` 未创建 | 不声称“长线规划已覆盖” |

## 当前状态

| 项 | 状态 |
|---|---|
| 项目名称 | **BalatroEval** |
| 项目定位 | 面向大模型 Agent 的**长线规划测试集** |
| 规则实现 | **vanilla 1.0.1o 严格子集 v2**，IMPLEMENTED + TESTED：Red Deck/White Stake/Ante 1；300/450/600；4 手/4 弃；5 槽；8 个具名 Joker；等级 1 基础 Chips×Mult + 计分牌筛选；**经济（$4 起始、$3/$4/$5 奖励、利息 cap $5、2 报价付费商店、买/卖/reroll/离开）** |
| 与真游戏对齐 | **NOT_VERIFIED / L0**：A2（单步分数）与 A3（规则子集）实测 0 行；`docs/quality/engine-fidelity.md` A/B 表 PENDING |
| 真实接入（balatrobot） | 📋 未开始；`bridge/realgame.py`、`bench/realgame.py`、`scenarios/v3/`、`runs/w5-real/` 尚不存在 |
| 训练集（60 决策点 ATS） | 📋 未创建 |
| 失败归因器 | 📋 未创建（诊断报告层，不是主定位） |
| 对齐等级 | 当前 **L0**；W3 目标 L2；W5 目标 L3（真游戏 12 局小样本终验） |

## 两阶段架构

```text
阶段一：训练/开发环境（vanilla 1.0.1o 子集 v2：计分 + 经济；对齐仍未验证）
  真游戏捕获（balatrobot）──┐
                           ├─► 对齐场景集 ATS（60 个决策点）→ bench 引擎 / O1–O3 / 训练 Agent
  自建反事实变体（save/load）┘
  ── 对齐契约 A0–A4 ──► 真实游戏终验（RGFT，W5，目标 L3，📋 未执行）
       Balatro + Lovely + Steamodded + balatrobot + bridge/realgame.py（规划）
```

- **训练环境**：快、可枚举、可 CI；负责开发 Agent、算 oracle、跑训练集。
- **真游戏终验**：慢、不可并行、最终证据；只跑 12 局小样本，回答“离开自建环境结论还成立吗”。
- **不是二选一**：训练集自建，但每条局面都必须通过 A0–A4 对齐；真实游戏是终验，不是批量主环境。

## 30 秒验证

环境：Windows + PowerShell + Python ≥ 3.11（实测 3.15），**无第三方依赖**（stdlib only；MCP SDK 只在 bridge 运行时需要）。

```powershell
Set-Location C:\WorkData\005.Agent\BalatroEval

python -m unittest discover -s tests                    # 实测：Ran 157 tests / OK
python -m bench rules                                   # 规则声明（300/450/600、4/4、5 槽、8 Joker、$4/利息/商店）
python -m bench verify --samples 10 --seed 20261112     # O1 vs 独立枚举，passed true，每例 218 候选
python -m bench demo --seed 20261112 --max-steps 50     # 一局贪心参照：win / steps=12 / blind_scores=[412,620,640] / total=1672 / money=14
python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy --experiment smoke --out runs --no-oracle
python -m evaluation report --run-dir runs/smoke        # 分组指标 + Markdown 表
```

> 以上命令是**训练环境自洽证据**（规则实现、确定性、Trace、批量执行），**不能**证明“与真游戏对齐”“真游戏终验通过”或“已覆盖长线规划”。对齐证据见 [docs/quality/engine-fidelity.md](docs/quality/engine-fidelity.md)（A/B 表仍为 `PENDING`）与 [07](plan/详细版/07-真实游戏接入与终验.md) §3。
> `demo`/`batch` 的胜负不是 bug：固定 seed + 贪心/脚本策略下一次对局结果；判断引擎对错看**规则断言与轨迹自洽性**。v2 的贪心参照会在商店里买 Joker，所以它现在常常能打通 Ante 1 —— 它**没有**为利息存钱，别把“赢了”当成策略优秀。

**当前已验证（训练环境自洽，实测非声明）**：157/157 单元/集成测试通过；牌型/基础分/计分牌筛选/8 Joker 条件与顺序有 golden 测试；`7♥7♦` Pair = 48（vanilla 等级 1）回归；**经济口径有专项测试**（结算明细、利息上限、买入/卖出/reroll/离开、钱不够与槽位满的拒绝路径、快照含 money、观察含 shop）；同 seed 整局/逐步状态可复现；快照 roundtrip 通过；非法动作不改变状态；batch 支持并发、失败隔离、断点续跑；Trace JSONL schema 2 可读并含 state hash。性能实测见 [docs/implementation/performance.md](docs/implementation/performance.md)。

**尚未验证 / 未执行**：
- 与 vanilla 1.0.1o 的规则/分数对齐（A2–A3）：📋 W3；[docs/quality/engine-fidelity.md](docs/quality/engine-fidelity.md) 的 A/B 表全为 `PENDING`。
- **经济口径**：价格是稀有度中值、商店候选均匀抽样、利息按入账前金额 —— 三条都未与真游戏实测（`Ruleset.unverified`）。
- 真游戏捕获/回放（A4）与 `scenarios/v3/` 60 决策点：📋 未开始。
- 真实游戏接入（balatrobot）与 12 局终验（L3）：📋 未开始。
- 真实模型端点（HTTP Adapter 仅 fake transport 测试）与 MCP stdio 端到端。
- **长线规划四支柱**：跨回合资源分配**只有载体、没有指标与场景集**；长期构建、失败恢复、长线指标**未覆盖**（W3 候选）。

## 仓库结构

| 路径 | 内容 | 修改时注意 |
|---|---|---|
| `README.md` | 本文件：项目入口、定位与差距、快速验证、文档导航 | 命令与数字变了要同步 |
| `bench/` | ★ 规则与环境（18 个 `.py`）：rules_version/model/hand_eval/scoring/jokers/engine/actions/observation/environment/tools/oracle/serialize/rng/cards/errors/logging(legacy) | 规则唯一实现；依赖分层见 [AGENTS.md](AGENTS.md) §3 |
| `scenarios/` | `RULES_VERSION`（人类可读声明）、`rules_v2.json`（JSON 镜像）、`dev/`（7 个自造开发场景，含 1 个经济决策点）、`schema.py`/`loader.py`/`validator.py` | 场景必须声明 rules_version；Boss 效果/任何扩展都会被拒绝；经济决策点用 `shop_open=true` |
| `evaluation/` | Episode Runner、Batch Runner、Trace（schema 2）、metrics（含 `mean_final_money`）、config、agents（含 HTTP Adapter）、CLI | 每个 episode 独立 Environment；结果 append-only |
| `tests/` | 157 项测试：规则/经济/环境/scenario/runner/并发/断点/property/性能 smoke | 新增测试要同步数字 |
| `bridge/` | MCP 薄壳：`server.py` 暴露 7 个工具（6 游戏 + reset），调用 `bench.tools` | 薄壳不写规则、不复算价格；MCP SDK 延迟导入 |
| `benchmarks/` | 性能基准（规则/环境/Oracle/Episode/批量） | 结果见 `docs/implementation/performance.md` |
| `runs/` | 实验产物：`runs/<experiment_id>/{manifest.json,results.jsonl,traces/}` | 不入库；`_test_tmp/` 为测试临时目录 |
| `docs/` | 文档总入口见 [docs/README.md](docs/README.md)：`quality/`（对齐台账/来源许可/Joker 口径）、`implementation/`（实现）、`balatro/`（原版事实调研）、`ops/`（环境坑）、`research/`（调研） | 结论措辞受红线约束；新增文档先登记到 [docs/README.md](docs/README.md) |
| `docs/quality/` | **凭什么相信环境**：[engine-fidelity.md](docs/quality/engine-fidelity.md)（对齐台账）、[data-sources.md](docs/quality/data-sources.md)（来源/许可）、[joker-semantics.md](docs/quality/joker-semantics.md)（Joker 口径） | 状态只能在 A0–A4 签核后改 |
| `docs/implementation/` | 实现文档入口（架构/规则/API/Schema/执行/测试/性能/状态） | 与实际代码同步 |
| `docs/ops/` | 环境与运维：Windows/DSH/真游戏环境的坑与解法（[windows-pitfalls.md](docs/ops/windows-pitfalls.md)） | 只记现象/根因/解法，不写规则 |
| `data/` | 历史实验产物（W2 证据） | **属证据，不要覆盖** |
| `plan/` | 项目计划、每周任务、详细版设计；**决策基线在 `plan/详细版/07-真实游戏接入与终验.md`** | 上游约束；冲突时以 07 为准 |
| `evidence/` | 历史验收证据（W1） | 只读；真游戏截图只放 `evidence/` 且不对外分发 |
| `archive/legacy-2026-11-13/` | 旧名 BalatroBench / 旧定位文档 | 非当前定位；引用需注明日期 |
| `archive/legacy-2026-11-22/` | W2/L0 时期手册与报告（`程序员手册.md` 等） | 历史口径，已被 `docs/implementation/` 取代 |
| `AGENTS.md` | 给 Agent 的契约速览（规则/分层/验收/硬约束） | 与 `docs/implementation/` 同步 |

## 规则速览（vanilla 1.0.1o 子集 v2）

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

经济（v2）：起始 $4
  通关结算 = 盲注奖励(3/4/5) + 剩余手数×$1 + 未用弃牌×$1 + 利息 min(钱÷5, 5)
  Small/Big 通关后进商店：2 个报价（Common $5 / Rare $9），可买 / 卖(半价) / reroll($5 起，每次 +$1) / 离开
  Boss 通关即 win（不进商店）；手数/弃牌仍每盲注重置，只有钱跨盲注保留

候选动作：8 张手牌 ⇒ 218 出牌 + 218 弃牌 = 436 条；商店阶段另给买/卖/reroll/离开
```

> **边界（不得越线）**：以上是 **IMPLEMENTED + TESTED**，不是 **VERIFIED**。Boss 效果、消耗品、增强/蜡封/版本、多牌组/多赌注、Tag/Endless/手牌等级>1/重触发仍在 `Ruleset.excluded` 明列；Boss 场景由 validator 拒绝效果；**经济已移出 excluded，但价格（稀有度中值）、商店候选（均匀抽样）、利息顺序（入账前）三条口径未与真游戏实测**，不得写成“原版经济”。
> **长线机制现状**：金钱是**唯一**可跨盲注累积的资源（手数/弃牌仍重置）；引擎已能提供“存钱吃利息 vs 现在买 Joker”的取舍，但**尚无可测指标与经济场景集**，因此当前**不能**主张“跨回合资源分配已被测到”。

实现细节（计分顺序、contains 口径、快照/哈希、错误码、trace schema）见 [docs/implementation/rules-implementation.md](docs/implementation/rules-implementation.md) 与 [docs/implementation/architecture.md](docs/implementation/architecture.md)。

## 常用命令

```powershell
# 全量测试（规则/环境/scenario/runner/并发/断点/property/性能 smoke）
python -m unittest discover -s tests

# 规则声明（JSON）
python -m bench rules

# O1 与独立暴力枚举对照
python -m bench verify --samples 10 --seed 20261112

# 跑一局贪心参照（stdout JSON；不写文件）
python -m bench demo --seed 20261112 --max-steps 50

# 弃牌 EV 采样估计（近似；K=50 较慢）
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

## 文档导航

| 文档 | 内容 | 语言 |
|---|---|---|
| [docs/README.md](docs/README.md) | **docs 总索引**：5 个目录各装什么、状态口径、归档约定 | 中文 |
| [docs/quality/engine-fidelity.md](docs/quality/engine-fidelity.md) | **对齐台账**：A 表真游戏捕获 + B 表 `save`/`load` 反事实回放（全 `PENDING`）+ A0–A4 检查清单 + 签核模板 | 中文 |
| [docs/quality/data-sources.md](docs/quality/data-sources.md) | 来源与许可：规则数值出处、只借鉴不抄代码的项目、合规红线（L7–L9） | 中文 |
| [docs/quality/joker-semantics.md](docs/quality/joker-semantics.md) | 8 个具名 vanilla Joker 目录、触发条件与槽位顺序；哪些口径未验证 | 中文 |
| [docs/ops/windows-pitfalls.md](docs/ops/windows-pitfalls.md) | Windows/DSH/真游戏环境的坑与解法（已实测 5 条 + 预期 6 条） | 中文 |
| [docs/implementation/README.md](docs/implementation/README.md) | **实现文档入口**：目标/范围/模块/测试与运行方式 | 中文 |
| [docs/implementation/architecture.md](docs/implementation/architecture.md) | 架构、模块职责、数据流、Episode 生命周期 | 中文 |
| [docs/implementation/rules-implementation.md](docs/implementation/rules-implementation.md) | 规则版本、实现范围、计分顺序、Joker、排除项与对齐边界 | 中文 |
| [docs/implementation/api-reference.md](docs/implementation/api-reference.md) | 真实函数/类接口（参数/返回/异常/副作用/确定性） | 中文 |
| [docs/implementation/evaluation-execution.md](docs/implementation/evaluation-execution.md) | 单 episode、批量并发、模型 Adapter、重试、断点续跑、Trace | 中文 |
| [docs/implementation/data-schema.md](docs/implementation/data-schema.md) | Scenario/Action/Observation/Trace/Result Schema 与版本 | 中文 |
| [docs/implementation/testing-and-validation.md](docs/implementation/testing-and-validation.md) | 测试分类、golden、property、并发、未验证项 | 中文 |
| [docs/implementation/performance.md](docs/implementation/performance.md) | 实测环境、基准结果、瓶颈与优化建议 | 中文 |
| [docs/implementation/implementation-status.md](docs/implementation/implementation-status.md) | NOT_IMPLEMENTED/IMPLEMENTED/TESTED/VERIFIED 状态矩阵 | 中文 |
| [AGENTS.md](AGENTS.md) | 给 Agent 的极简契约版（红线 / 依赖分层 / 验收命令 / 硬约束 / 已知边界） | 中文 |
| [plan/00-项目全貌.md](plan/00-项目全貌.md) | 项目全貌：定位、目标、决策、风险、术语、进度 | 中文 |
| [plan/详细版/07-真实游戏接入与终验.md](plan/详细版/07-真实游戏接入与终验.md) | **决策基线 / 单一事实来源**：两阶段、A0–A4、L0–L3、W3 剩余清单、真游戏 12 局终验、许可/证据边界 | 中文 |
| [plan/详细版/03-评测集与指标.md](plan/详细版/03-评测集与指标.md) | 场景分层、Schema、分层指标、统计方案 | 中文 |
| [plan/详细版/04-失败归因器.md](plan/详细版/04-失败归因器.md) | **诊断报告层**：F1–F4 + F0 判定规则、证据链、标注方案；E1 `env_divergence` 口径 | 中文 |
| [plan/详细版/05-实验与报告.md](plan/详细版/05-实验与报告.md) | 实验矩阵、基线、统计、成本、报告大纲 | 中文 |
| [docs/research/](docs/research/) | 生态与学术调研、验证方法 | 中文 |
| [scenarios/RULES_VERSION](scenarios/RULES_VERSION) | 人类可读规则声明（机器可读权威：`bench/rules_version.py`；JSON 镜像：`scenarios/rules_v2.json`；当前 `fidelity_status: NOT_VERIFIED`） | YAML 片段 |
| [archive/legacy-2026-11-13/INDEX.md](archive/legacy-2026-11-13/INDEX.md) | 历史归档：旧名/旧定位文档 | 中文 |
| [archive/legacy-2026-11-22/INDEX.md](archive/legacy-2026-11-22/INDEX.md) | 历史归档：W2/L0 手册与报告 | 中文 |

## 保真度与定位红线（任何报告/注释/回复都不得越线）

| ❌ 不得声称 | 事实 |
|---|---|
| 实现了原版 Balatro 计分 / 已对齐 vanilla | 实现了 vanilla 1.0.1o **等级 1 子集**的计分路径，但 A2/A3 真游戏实测 **0 行**；`fidelity_status: NOT_VERIFIED`，对齐等级仍 **L0** |
| 8 个 Joker 是全部原版 Joker / 已覆盖 Joker 系统 | 只实现 8 个**具名 vanilla Joker**（数值来自 Wiki 事实页）；其余 142 个、Joker 版本、重触发、Blueprint 等均 `excluded` |
| 固定 seed 复现了原版 RNG | 只保证本项目内可复现；不承诺与真游戏同种子同局面（商店抽样用的是自带 RNG） |
| **经济是 vanilla 原版经济 / 已对齐** | 价格是稀有度中值（Common $5 / Rare $9）、商店候选均匀抽样（无原版权重）、利息按入账前金额；三条均 `unverified` |
| **有钱 = 跨回合资源分配已覆盖** | 只有载体（`money` 跨盲注保留）；指标定义、经济场景集、优化基线均未做 |
| 手数/弃牌也能跨盲注攒 | 仍每盲注重置 4/4；不要为了“更长期”伪造这条（vanilla 也不允许） |
| 157 测试通过 = 原版兼容 / 已对齐 | 测试只覆盖已实现行为，只证**子集自洽 + 基础设施正确** |
| `verify` 通过 = 计分公式正确 / 已对齐 | 两条路径**共用** `score_hand()`；O1 是**局部**最优，不是长期规划最优 |
| `demo` 赢了/输了 = 引擎对/错 | 固定 seed + 贪心/脚本策略下的一次对局结果；v2 的贪心会买 Joker，赢了也不代表策略或经济对 |
| 已接入 balatrobot / 已对齐 / 已终验 | 真游戏接入、`scenarios/v3/`、12 局终验**均未执行（📋）** |
| **已覆盖跨回合资源分配 / 长期构建 / 失败恢复 / 长线指标** | **四项均未覆盖**；经济只给了①的**载体**，指标与场景集未做；只能写“目标能力，尚未覆盖，登记 W3” |
| 训练集结果 = 真游戏结果 | 两套环境；`env_divergence` 必须单列，不得混入 Agent 失败 |
| 捕获回放 = 真游戏终验 | 捕获回放只做 A2/A4 分数/回放验证；终验是 Agent 在真游戏跑完 12 局（`CAPTURE_REPLAY_ONLY` 是降级状态） |
| 真游戏 12 局小样本 = 统计显著 | n=12 只做描述统计 + 95% CI，**不做显著性主张** |
| 游戏文件 / mod / `.jkr` 存档 / 含游戏素材截图可以入库 | L8：只提交脱敏后的状态 JSON、分数、trace、版本清单；截图只放 `evidence/` 且不对外分发 |

要把 `fidelity_status` 从 `NOT_VERIFIED` 改成已验证，唯一合法流程是：**A0 版本锁定 → A1 schema 对齐 → A2 单步分数（真游戏捕获实测）→ A3 规则子集 → A4 场景来源与回放**；证据写入 [docs/quality/engine-fidelity.md](docs/quality/engine-fidelity.md) 的 A/B 表与 `evidence/W3/align/`，再同步 `RULES_VERSION`、README/AGENTS 与 07。旧的人工对拍/第三方抽检只是辅助证据，单独通过不足以改状态。

## 贡献与修改约定

1. **先读** [AGENTS.md](AGENTS.md)（契约速览）与 [docs/implementation/](docs/implementation/)；涉及真游戏/对齐先读 [07](plan/详细版/07-真实游戏接入与终验.md)。
2. **改完必跑**：`python -m unittest discover -s tests`、`python -m bench verify`、`python -m bench demo`、`compileall`，并贴原始输出；这些是**训练环境自洽证据**，不得改写成对齐/终验证据。
3. **文档同步**：规则常量、计分公式、Joker 目录、状态字段、CLI 参数、测试数量，同步 `docs/implementation/` 对应文档与 [scenarios/RULES_VERSION](scenarios/RULES_VERSION) / [scenarios/rules_v2.json](scenarios/rules_v2.json)；**规则对齐状态变化需同步 07 / `docs/quality/engine-fidelity.md` / `RULES_VERSION` / README / AGENTS**。
4. **真游戏证据边界**：游戏文件、mod、`.jkr` 存档、含游戏素材截图**不入库**；只提交脱敏状态 JSON、分数、trace 与版本清单（L8）。真游戏适配器是薄壳，**不写规则**。
5. **Git 安全**：禁止 `git add .` / `git commit -a` / `git reset --hard` / `git clean -fd`；只精确暂存本次工作涉及的文件。
6. **不要覆盖** `data/` 里已有实验产物；新实验写新的 `runs/<experiment_id>/`。
7. **不要顺手扩功能**：Boss 效果、消耗品、跨盲注 build 场景、失败恢复指标、真实 RNG 复刻均属后续机制改造，需单独任务与测试；经济口径的 `unverified` 条目未实测前不得改写。

## 命名与目录说明

- **项目名**：`BalatroEval`。Python 发行名 `balatroeval`；包目录仍为 `bench/`，CLI 仍为 `python -m bench`（包名/命令名与项目名解耦，改包名会破坏测试与调用方）。
- **仓库目录**：`BalatroEval`，与项目名一致；GitHub 仓库为 `ChzhanYeb/BalatroEval`（旧名 `dsh-agent-eval` 只应出现在 git 历史与旧链接重定向中）。`bridge/mcp-overlay.yml` 与 DSH profile `bench-local` 的 `cordis.patch.yml` 用绝对路径锚定该目录，**改名后必须同步重写并重建 `.venv`**。
- **MCP 连接名**：`balatro` / `balatro_bridge` / profile `bench-local` 为历史连接标识，与 `evidence/W1` 验收证据一致，本轮保留。
- **历史旧名**：`BalatroBench` 仅允许出现在 git 历史提交信息、归档件与“历史说明”中；不得出现在标题/首段/对外材料。

## 许可

`bench/` 为独立实现，未复制第三方代码（借鉴的设计线索见 [docs/quality/data-sources.md](docs/quality/data-sources.md) §2）。本仓库自身代码的许可证**尚待确定**（建议 MIT 或 Apache-2.0）；在确定之前不要对外分发。

真实游戏侧（Balatro、Lovely、Steamodded、balatrobot）的许可与边界见 [07](plan/详细版/07-真实游戏接入与终验.md) §8：balatrobot 只调用不改源码；Steamodded 只作运行时依赖、不复制不分发；游戏文件与素材不入库。
