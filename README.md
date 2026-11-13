# BalatroBench — Balatro 子集的可判定评测与失败归因

> **英文副标题**：A Decidable Evaluation and Failure-Attribution Benchmark for Long-Horizon Agents
> **仓库**：`C:\WorkData\005.Agent\dsh-agent-eval` ｜ 文档版本 **v3.0（2026-11-13，真实游戏终验决策）**
> **代码基线**：`bench/` 提交 `c65fb9b`（规则版本 `W2-v2.1-2026-11-12`），对齐等级 **L0（未对齐）**
> **决策基线**：[plan/详细版/07-真实游戏接入与终验.md](plan/详细版/07-真实游戏接入与终验.md)（单一事实来源；与其他文档冲突时以 07 为准）
> 遵循 `plan/` 中的项目约束：**数值可引，文本自写；设计可借鉴，代码不复制**（见 [docs/data-sources.md](docs/data-sources.md)）

**一句话：** BalatroBench 用一个**规则可判定、分数可精确计算**的 Balatro 子集环境评测 LLM Agent 的**多步决策能力**，并给出**可自动判定的失败归因**（F1–F4 + F0，另设环境分歧 E1 `env_divergence`）。v3.0 起环境分两阶段：**① 自建“与真游戏对齐”的训练/开发环境（当前 W2 `bench/` 引擎 = L0 底座，W3 目标 L2）；② 真实游戏（Balatro + balatrobot）小样本终验（12 局，W5 目标 L3）**。真实游戏接入与终验 **尚未执行**（📋）。

> **与同名项目区分（必读）**：GitHub 已有同名 `coder/balatrobench`——它是 BalatroLLM 对局记录的**排行榜 / 结果分析工具**，做展示、不做判定。本项目与它**同名不同目标**：它回答“谁分高”，本项目回答“**为什么低、错在哪类决策**”。所有对外材料（README/报告/简历/演示）标题必须含“失败归因”，且首段显式区分（D12）。

> **v3.0 当前状态**：真实游戏接入（balatrobot）、对齐训练集 `scenarios/v3/`（60 决策点）、真游戏终验（12 局）**均未开始**，标 📋；仓库里**不存在**“已接入 / 已对齐 / 已终验”的证据。现有 25 项测试、`verify`、`demo` 只证明 **L0 自定义子集自洽**，**不是**对齐证据，也**不是**终验证据。

---

## v3.0 改了什么（决策级变更，不是执行回填）

| # | 决策变更 | 内容 |
|---|---|---|
| ① | **D1/D2 反转** | v2.2 的“只做自建子集（D1）/ 不接入真游戏（D2）”→ v3.0 **两阶段**：对齐训练/开发环境 + 真实游戏终验 |
| ② | **训练集必须对齐** | 60 决策点 = 30 真游戏锚点 + 30 真游戏反事实变体；每个入集局面必须有真游戏捕获或 `save`/`load` 回放证据（A0–A4），不通过即 `rejected` |
| ③ | **规则口径** | 自定义子集公式 → **vanilla 1.0.1o 严格子集**（Red Deck / White Stake / Ante 1 三盲注 300-450-600 / 4 手 4 弃 / 5 槽位 / 8 个 vanilla 具名 Joker）；未实现规则必须在 `RULES_VERSION.excluded` 明列 |
| ④ | **命名** | 正式名固定为 **BalatroBench — Balatro 子集的可判定评测与失败归因**；所有标题必须含“失败归因”（D12） |
| ⑤ | **W2 重新定位** | `bench/` 仍是有效交付，但从“唯一评测环境”降为 **L0 训练环境底座**；W3 做对齐改造（目标 L2），W5 做真游戏终验（目标 L3） |
| ⑥ | **归因扩展** | F1–F4 + F0 之外新增 **E1 `env_divergence`（环境分歧，非 Agent 失败）**，隔离“引擎/适配器与真游戏不一致”造成的失败 |
| ⑦ | **预算不变** | 仍为 100h；批量实验 180→90 局、Pass^k 取消、商店/金钱不实现等抵消真游戏接入成本 |

---

## 两阶段架构

```
阶段一：对齐训练/开发环境（ATE，W2 已交付 L0 底座，W3 目标 L2）
  真游戏捕获（balatrobot）──┐
                            ├─► 对齐场景集 ATS（60 个决策点）→ bench 引擎 / O1–O3 / 训练 Agent
  自建反事实变体（save/load）┘
  ── 对齐契约 A0–A4 ──► 真实游戏终验（RGFT，W5，目标 L3，📋 未执行）
       Balatro + Lovely + Steamodded + balatrobot + bridge/realgame.py（规划）
```

- **训练环境**：快、可枚举、可 CI；负责开发 Agent、算 oracle、跑训练集。
- **真游戏终验**：慢、不可并行、最终证据；只跑 12 局小样本，回答“离开自建环境结论还成立吗”。
- **不是二选一**：训练集自建，但每条局面都必须与真游戏对齐（A0–A4）；真实游戏是终验，不是批量主环境。

## 30 秒验证（三条命令，仅证 L0 自洽）

环境：Windows + PowerShell + Python ≥ 3.11（实测 3.15.2），**无第三方依赖**（stdlib only）。

```powershell
Set-Location C:\WorkData\005.Agent\dsh-agent-eval

python -m unittest discover -s tests -v               # 期望：Ran 25 tests / OK
python -m bench verify --samples 10 --seed 20261112   # 期望：passed true，每例 218 个候选
python -m bench demo --seed 20261112 --max-steps 50 --log $env:TEMP\demo.jsonl
# 期望：phase=done / outcome=loss / steps=13 / blind_idx=2 / total_score_in_current_blind=1430
```

> 以上三条是 **L0 自洽证据**（自定义子集内可复现、O1 与枚举一致、demo 能走完），**不能**用来证明“与真游戏对齐”或“真游戏终验通过”。对齐证据见 [docs/engine-fidelity.md](docs/engine-fidelity.md)（A/B 表仍为 `PENDING`）与 07 §3。
> `demo` 输了不是 bug：这是固定 seed + 贪心策略 + 子集规则下的一次对局结果。判断引擎对错看**轨迹自洽性**，不看胜负。

---

## 这是什么 / 不是什么

| ✅ 是 | ❌ 不是 |
|---|---|
| 两阶段评测项目：L0 训练环境（W2 已交付）+ 真游戏终验（📋 规划） | 原版 Balatro 的复刻、模拟器或排行榜 |
| 确定性、可复现的 L0 子集引擎（52 张牌、8 张手牌、3 盲注、4 手 2 弃） | 与 vanilla 对齐的规则实现（当前 **L0**；对齐改造在 W3） |
| 自定义子集计分公式（Fraction 精确运算 + 槽位顺序语义） | 原版计分流水线（缺牌型基础 Chips、无计分牌筛选） |
| 8 个**合成** Joker 效果夹具（仅测试用，不得进入训练集/主表） | 8 个原版具名 Joker（W3 另建，见 07 §7.2） |
| O1 精确 argmax、O2 弃牌 EV 采样、O3 贪心整局 三种参照策略 | 全局最优策略，或真游戏 oracle |
| append-only JSONL 轨迹 + 25 项自动化测试 | 与真游戏对齐 / 终验已通过的证据 |
| 失败归因设计：F1–F4 + F0 + E1 `env_divergence`（📋 归因器未实现） | 已实现的自动归因器，或 LLM Judge 判定 |

**当前已验证（L0 自洽，实测非声明）**：25/25 单元测试通过；同 seed 整局状态完全一致；RNG 状态完整往返；`verify` 10/10 与独立暴力枚举一致（每例 218 候选）；demo 13 步走到终局并写出 13 条日志；`ev -k 50` 覆盖 218 个动作。

**尚未验证 / 未执行**：
- 与 vanilla 1.0.1o 的规则/分数对齐（A2–A3）：📋 W3；[docs/engine-fidelity.md](docs/engine-fidelity.md) 的 20 例人工对拍 + 5 例抽检仍为 `PENDING`（v3.0 降级为辅助证据）。
- 真游戏捕获/回放（A4）与 `scenarios/v3/` 60 决策点：📋 W3，未开始。
- 真实游戏接入（balatrobot）与 12 局终验（L3）：📋 W5，未开始；`bridge/realgame.py`、`runs/w5-real/` 尚不存在。

---

## 仓库结构

| 路径 | 内容 | 修改时注意 |
|---|---|---|
| `README.md` | 本文件：项目入口、快速验证、文档导航 | 命令与数字变了要同步 |
| `bench/` | ★ 引擎源码（11 个 `.py`，中文注释齐全），**训练环境 = L0 底座** | 唯一需要改的代码目录；依赖分层见手册 §2.2 |
| `tests/test_w2_rules.py` | 25 项规则与引擎测试（L0） | 新增测试要同步更新文档里的“25” |
| `scenarios/RULES_VERSION` | 规则版本、覆盖项、排除项、保真度状态 | 改规则常量必须同步这里 |
| `scenarios/v3/` | 📋 **规划**：对齐后的 60 个决策点（30 真游戏锚点 + 30 反事实变体） | 只有通过 A0–A4 的局面可入集；当前**未创建** |
| `bridge/` | MCP 薄壳：`server.py`（W1 训练环境，4 工具）；`realgame.py` 📋 规划（真游戏 5 工具） | 薄壳不写规则；适配器只做 RPC/字段映射/错误码 |
| `runs/` | 📋 **规划**：`runs/<run_id>/`（训练集轨迹）、`runs/w5-real/`（真游戏终验 trace） | 当前**不存在**；产物不入库前先脱敏 |
| `docs/` | 保真度台账、Joker 语义、数据来源、实现报告（均为中文单版本） | 结论措辞受红线约束 |
| `data/` | 实验产物（JSON / JSONL） | **属证据，不要覆盖**；注意 PowerShell 重定向产生的是 UTF-16 |
| `plan/` | 项目计划、每周任务、详细版设计；**v3.0 决策基线在 `plan/详细版/07-真实游戏接入与终验.md`** | 上游约束来源；冲突时以 07 为准 |
| `evidence/` | 历史验收证据（W1；W3 对齐证据规划在 `evidence/W3/align/`） | 只读；真游戏截图只放 `evidence/` 且不对外分发 |
| `程序员手册.md` | bench/ + v3.0 对齐/终验的完整程序员手册（约 1300 行，见 §21） | 代码一改就要同步 |
| `AGENTS.md` | 给 Agent 的极简契约版 | 与手册冲突时以手册为准 |

---

## 规则速览（W2 现状 = L0 自定义子集；v3.0 对齐目标见 07 §7）

```
牌组 52 张 ──► 初始手牌 8 张 ──► 每盲注 4 次出牌 / 2 次弃牌
盲注 3 段：目标分 300 / 800 / 2000 ──► 达标进商店（3 选 1 Joker，最多 3 个槽位）
计分：chips = Σ 点数筹码(A=11, J/Q/K=10, 其余=点数)   # 无牌型基础 Chips
       mult = HAND_MULT[牌型]（自定义表：SF12/4K10/FH8/FL6/ST5/3K4/2P3/P2/HC1）
       按【槽位顺序】逐个应用 Joker：+Chips / +Mult / ×(value/100)
       final = floor(chips × mult)                     # Fraction 精确运算，只 floor 一次
候选动作：8 张手牌 ⇒ 恒 218 个（C(8,1..5)）
```

> **W2 = L0**：上面是 W2 的自定义子集，**不是** vanilla 规则。**W3 对齐改造目标（L2，尚未实现）**：Red Deck / White Stake / Ante 1 三盲注 300-450-600 / 4 手 4 弃 / 5 Joker 槽位 / 8 个 vanilla 具名 Joker / 牌型基础 Chips×Mult + 计分牌筛选。未实现规则（Boss 效果、消耗牌、增强/版本/印章、金钱/商店等）在 `RULES_VERSION.excluded` 明列，且不得进入训练集。

细节（含顺序敏感示例、`_draw` 顺序不变式、交换盲注的六项重置）见 [程序员手册.md](程序员手册.md) §6 与 §9；v3.0 两阶段/对齐契约见 §21。

---

## 常用命令

```powershell
# 全量单元测试（L0）
python -m unittest discover -s tests -v

# O1 与独立暴力枚举对照（L0）
python -m bench verify --samples 10 --seed 20261112

# 跑一局贪心 demo，并把轨迹写成 JSONL（L0；写到临时目录，避免覆盖 data/ 证据）
python -m bench demo --seed 20261112 --max-steps 50 --log $env:TEMP\demo.jsonl

# 弃牌 EV 采样估计（K=50 约 23–25 秒）
python -m bench ev --seed 20261112 -k 50

# 语法/导入自检
python -m compileall -q bench
```

> 以上命令全部只作用于 **L0 训练环境**。真游戏侧命令（`health` / `gamestate` 冒烟、捕获、终验）📋 尚未提供，W3 起再补。

【坑】`engine.play/discard/choose_joker` 的 `log_path` 默认是 `data/episode.jsonl`，日志是 **append**：库调用（测试、`oracle.greedy_episode`）请显式传 `log_path=None`，跑实验请显式给带时间戳的路径。

---

## 文档导航

| 文档 | 内容 | 语言 |
|---|---|---|
| [程序员手册.md](程序员手册.md) | 完整手册：数据模型、计分契约、状态机、O1/O2/O3、日志 schema、修改配方、调试、保真度红线、**v3.0 对齐与终验（§21）**、Agent 附录 | 中文 |
| [AGENTS.md](AGENTS.md) | 同一内容的极简契约版（红线 / 依赖分层 / 验收命令 / 硬约束 / 已知粗糙点） | 中文 |
| [plan/00-项目全貌.md](plan/00-项目全貌.md) | v3.0 项目全貌：定位、目标 G1–G8、决策 D1–D17、进度、术语 | 中文 |
| [plan/详细版/07-真实游戏接入与终验.md](plan/详细版/07-真实游戏接入与终验.md) | **v3.0 决策基线 / 单一事实来源**：两阶段、A0–A4、L0–L3、W3 改造清单、真游戏 12 局终验、许可/证据边界 | 中文 |
| [W2_BalatroBench_实现说明书_中文.md](W2_BalatroBench_实现说明书_中文.md) | W2 做了什么、为什么这样做、如何工作、如何安全修改（L0 交付快照） | 中文 |
| [docs/engine-fidelity.md](docs/engine-fidelity.md) | 对齐台账：A 表真游戏捕获 + B 表 `save`/`load` 反事实回放（全 `PENDING`）+ A0–A4 检查清单；旧 20 例人工对拍 + 5 例抽检降为附录 C/D 辅助证据 | 中文 |
| [docs/joker-semantics.md](docs/joker-semantics.md) | 合成夹具的 area/phase/顺序敏感性 + v3.0 vanilla 8 Joker 目录（📋 W3 目标），与 SMODS 的对应边界 | 中文 |
| [docs/W2-implementation-report.md](docs/W2-implementation-report.md) | W2 实现报告：已执行的验证与结果一览 | 中文 |
| [docs/data-sources.md](docs/data-sources.md) | 数据来源、许可与合规红线（总表） | 中文 |
| [docs/data-sources-w2.md](docs/data-sources-w2.md) | W2 实际来源与复用决策 | 中文 |
| [docs/调研报告.md](docs/调研报告.md)、[docs/research/](docs/research/) | 生态与学术调研、验证方法、计划一致性（含 [04 生态](docs/research/04-balatro-ecosystem.md)） | 中文 |
| [scenarios/RULES_VERSION](scenarios/RULES_VERSION) | 机器可读的规则版本与覆盖范围声明（当前 `fidelity_status: NOT_VERIFIED`） | YAML 片段 |
| [plan/](plan/) | 项目全貌、每周任务、详细版设计（01 Windows 适配、02 规则与对拍、03 评测集、04 归因、05 实验、06 生态、07 真游戏终验） | 中文 |

---

## 保真度红线（任何报告/注释/回复都不得越线）

| ❌ 不得声称 | 事实 |
|---|---|
| 实现了原版 Balatro 计分 | 自定义子集公式（L0）；`scenarios/RULES_VERSION` 为 `fidelity_status: NOT_VERIFIED` |
| 8 个 Joker 是原版 Joker | `jc_*/jm_*/jx_*` 是**合成测试夹具**，不入训练集/主表 |
| 固定 seed 复现了原版 RNG | 只保证本项目内可复现；v3.0 用真游戏捕获的固定局面，不靠同 seed 同局面 |
| 25 测试通过 = 原版兼容 / 已对齐 | 测试只覆盖已实现行为，只证 **L0 自洽** |
| `verify` 通过 = 计分公式正确 / 已对齐 | 两条路径**共用** `score_hand()`，只证明路径一致 |
| `demo` 输了 = 引擎有 bug | 固定 seed + 贪心策略下的一次对局结果 |
| 已接入 balatrobot / 已对齐 / 已终验 | 真游戏接入、`scenarios/v3/`、12 局终验**均未执行（📋）**；未完成时只能写“未执行” |
| 训练集结果 = 真游戏结果 | 训练集与终验是两套环境；`env_divergence` 必须单列，不得混入 Agent 失败 |
| 捕获回放 = 真游戏终验 | 捕获回放只做 A2/A4 分数/回放验证；终验指 Agent 在真游戏里跑完 12 局（`CAPTURE_REPLAY_ONLY` 是降级状态） |
| 真游戏 12 局小样本 = 统计显著 | n=12 只做描述统计 + 95% CI；**不做显著性主张** |
| 游戏文件 / mod / `.jkr` 存档 / 含游戏素材截图可以入库 | L8：只提交脱敏后的状态 JSON、分数、trace、版本清单；截图只放 `evidence/` 且不对外分发 |

要把 `fidelity_status` 从 `NOT_VERIFIED` 改成已验证，唯一合法流程按 v3.0 对齐契约：**A0 版本锁定 → A1 schema 对齐 → A2 单步分数（真游戏捕获实测）→ A3 规则子集（`RULES_VERSION.excluded` 明列排除项）→ A4 场景来源与回放**；证据写入 [docs/engine-fidelity.md](docs/engine-fidelity.md) 的 A 表（真游戏捕获）、B 表（`save`/`load` 反事实回放）与 `evidence/W3/align/`，再改 `RULES_VERSION` 并同步文档（手册 §17.2、§20.1）。旧的 20 例人工对拍 + 5 例抽检已降级为辅助证据（附录 C/D），单独通过它们不足以改状态。

---

## 贡献与修改约定

1. **先读** [AGENTS.md](AGENTS.md)（契约速览），再按任务查 [程序员手册.md](程序员手册.md) 的 §14 修改配方（改计分 / 加 Joker / 改流程 / 改日志 / 加 CLI / 调 RNG）；涉及真游戏/对齐先读 [07](plan/详细版/07-真实游戏接入与终验.md) 与手册 §21。
2. **改完必跑**：25 项测试、`verify`、`demo`、`compileall`，并把原始输出贴出来；不要写“应该没问题”。这些结果是 **L0 证据**，不得改写成对齐/终验证据。
3. **文档同步**：规则常量、计分公式、Joker 目录、状态字段、CLI 参数、测试数量，各自对应要更新的文档见手册 §20.1；**规则对齐状态变化需同步 07 / `docs/engine-fidelity.md` / `RULES_VERSION` / README**。
4. **真游戏证据边界**：游戏文件、mod、`.jkr` 存档、含游戏素材截图**不入库**；只提交脱敏状态 JSON、分数、trace 与版本清单（L8）。真游戏适配器是薄壳，**不写规则**。
5. **Git 安全**：仓库里还有其它未提交工作，禁止 `git add .` / `git commit -a` / `git reset --hard` / `git clean -fd`；只精确暂存本次工作涉及的文件（手册 §18）。
6. **不要覆盖** `data/` 里已有实验产物；新实验写新文件名。
7. **不要顺手修已知粗糙点**：手册 §15.5 列了 15 项（如 O3 无 CLI 入口、`verify_oracle` 的牌堆唯一性问题），修复需单独提交并补测试。

---

## 许可

`bench/` 为独立实现，未复制第三方代码（借鉴的设计线索见 [docs/data-sources.md](docs/data-sources.md) §2）。本仓库自身代码的许可证**尚待确定**（建议 MIT 或 Apache-2.0，见同文件 §4）；在确定之前不要对外分发。

真实游戏侧（Balatro、Lovely、Steamodded、balatrobot）的许可与边界见 07 §8：balatrobot 只调用不改源码；Steamodded 只作运行时依赖、不复制不分发；游戏文件与素材不入库。
