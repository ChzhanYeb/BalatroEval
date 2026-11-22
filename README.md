# BalatroEval

面向大模型 Agent 的**确定性长线规划评测环境**：在 Balatro（vanilla 1.0.1o）的可判定规则子集上，评测 Agent 的多步决策、跨回合资源分配与长期构建能力。

- **目标用户**：做 Agent 评测 / 训练的研究者与工程团队；需要一个可枚举、可回放、可批量跑、无外部依赖的决策测试床。
- **技术栈**：Python 3.11+（纯标准库，运行时零第三方依赖）、JSON / JSONL、可选 MCP（stdio）。
- **形态**：规则引擎 + 场景集 + 批量评测器 + MCP 工具桥；**不是**完整 Balatro 模拟器。

> **当前状态**：v2 规则（计分 + 经济 / 商店）已实现，157 项测试通过；与真游戏的对齐为 **`NOT_VERIFIED` / L0**（A2/A3 实测 0 行）。引用结论前请先读 [能力边界](#能力边界必读)。

---

## 快速开始

### 环境要求

| 项 | 要求 |
|---|---|
| Python | ≥ 3.11（本机实测 3.15.2） |
| 第三方依赖 | 无（`pyproject.toml` 中 `dependencies = []`） |
| 操作系统 | Windows + PowerShell（已实测）；macOS / Linux 未验证 `[待补充: 平台矩阵]` |
| 可选依赖 | `mcp` SDK，仅启动 `bridge/` 的 MCP 服务时需要 |

### 安装

在仓库根目录直接运行即可，**无需安装、无构建步骤**。所有 CLI 都以仓库根目录为工作目录。

```powershell
cd <仓库根目录>
python --version    # 需 >= 3.11
```

可选：把 `bench` 作为库安装（仅注册 `bench` 包；`evaluation/`、`scenarios/` 未打包，CLI 仍在仓库根目录运行）。

```powershell
python -m pip install -e .
```

### 3 分钟验证

```powershell
# 1) 全量测试
python -m unittest discover -s tests

# 2) 规则引擎的 Oracle 交叉检查
python -m bench verify --samples 10 --seed 20261112

# 3) 跑一局贪心参照（stdout 输出 JSON，不写文件）
python -m bench demo --seed 20261112 --max-steps 50
```

预期结果（固定 seed，可复现）：

| 命令 | 关键输出 |
|---|---|
| `unittest discover` | `Ran 157 tests` + `OK` |
| `bench verify` | `"passed": true`；10/10 例一致，每例 218 个候选出牌 |
| `bench demo` | `outcome: win`、`steps: 12`、`blind_scores: [412, 620, 640]`、`total_scored: 1672`、`money: 14` |

接着跑一次批量评测：

```powershell
python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy --experiment demo --out runs
python -m evaluation report --run-dir runs/demo
```

`batch` 预期 `counts.completed = 7`（`scenarios/dev/` 共 7 个场景）；`report` 输出分组指标与 Markdown 表。

> 以上命令是**训练环境自洽证据**：证明规则实现、确定性、轨迹与批量执行可用。它们**不能**证明“与真游戏对齐”或“长线规划能力已被测到”，原因见 [能力边界](#能力边界必读)。

---

## 核心功能

| 能力 | 说明 | 代码入口 |
|---|---|---|
| 确定性规则引擎 | 52 张 Red Deck、White Stake、Ante 1；12 种牌型（等级 1）计分；8 个具名 vanilla Joker；纯函数转移 + 快照 / 还原 / state hash | `bench/engine.py`、`bench/scoring.py` |
| 经济与商店（v2） | 起始 $4；通关奖励 $3/$4/$5；剩余手牌 / 弃牌各 +$1；利息每 $5 得 $1（上限 $5）；Small/Big 后 2 报价付费商店（买 / 卖 / reroll / 离开） | `bench/engine.py`、`bench/rules_version.py` |
| 环境、工具与 Agent 接入 | `reset / observe / legal_actions / step / snapshot / restore`；统一 `Action`；11 个稳定错误码；7 个 Agent 工具；MCP stdio 薄壳与 OpenAI 兼容 HTTP Adapter | `bench/environment.py`、`bench/tools.py`、`bridge/server.py` |
| 场景与批量评测 | Scenario Schema 2 + Loader/Validator；单 episode、批量并发、重试、断点续跑；Trace JSONL schema 2；指标聚合（regret、optimality、final_money、bootstrap CI） | `scenarios/`、`evaluation/` |
| 参照策略与 Oracle | O1 精确局部最优、O2 弃牌 EV 近似、O3 贪心整局；`verify` 用独立暴力枚举交叉检查 O1 | `bench/oracle.py` |

---

## 核心用法

### 1. 引擎 CLI：规则、单局、Oracle、弃牌 EV

```powershell
python -m bench rules                                   # 打印机器可读规则声明（JSON）
python -m bench demo --seed 20261112 --max-steps 50     # 一局 O1 贪心参照
python -m bench verify --samples 10 --seed 20261112     # O1 vs 独立暴力枚举
python -m bench ev --seed 20261112 -k 50                # 初始手牌的弃牌 EV 估计（近似，K 越大越慢）
```

### 2. 批量评测与报告

```powershell
# 单场景：7♥7♦ 对子 golden 决策点
python -m evaluation run --scenarios scenarios/dev/play-pair-7h7d.json --agent oracle-greedy --experiment demo-single

# 多场景 × 重复 × 并发
python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy --experiment demo-batch --repeats 2 --max-concurrency 4

# 聚合已有 run（只读 results.jsonl）
python -m evaluation report --run-dir runs/demo-batch
```

常用参数（`run` / `batch` 共用）：

| 参数 | 默认 | 作用 |
|---|---|---|
| `--scenarios` | `scenarios/dev` | 场景文件 / 目录，可多个 |
| `--agent` | `oracle-greedy` | `oracle-greedy` / `random` / `first-legal` / `http` |
| `--experiment` | `<agent>-<场景名>` | run 目录名，落盘到 `--out/<experiment>` |
| `--out` | `runs` | 实验根目录 |
| `--repeats` | `1` | 每场景重复次数（task seed = 场景 seed + 序号） |
| `--max-steps` | 场景值 | 覆盖单局步数上限 |
| `--timeout` | `60.0` | 单 episode 墙钟超时（秒） |
| `--max-concurrency` / `--agent-concurrency` | `4` / `4` | episode 并发 / 模型调用并发 |
| `--no-oracle` | 默认不传（即计算 O1） | 传入后不算 O1：省时，但没有 regret 指标 |
| `--no-resume` / `--retry-failed` | 默认不传（即续跑、不重跑失败项） | 关闭断点续跑 / 只重跑失败任务 |

输出目录为 `<out>/<experiment>/{manifest.json,results.jsonl,traces/}`，`results.jsonl` 为 append-only；同一 `--experiment` 重跑默认跳过已完成任务。

### 3. Python API

```python
from bench.environment import Environment
from bench.oracle import best_play, greedy_shop_action

env = Environment(max_steps=50)
obs = env.reset(seed=20261112)

while not (env.is_terminated() or env.is_truncated()):
    if obs["episode"]["phase"] == "shop":
        action = greedy_shop_action(env.state)       # 买得起就买，否则离开
    else:
        action = {"kind": "play", "card_ids": list(best_play(env.state).card_ids)}
    obs = env.step(action).observation

print(obs["episode"]["outcome"], obs["episode"]["step"], obs["economy"]["money"])
```

同 seed 输出：`win 12 14`。

- Observation 为 Agent 公开视图（schema 2）：`episode.phase`、`blind`、`economy.money`、`shop.offers`、`hand`；不含完整牌堆顺序与内部 RNG。
- 完整合法动作用 `env.legal_actions()` 获取；8 张手牌时为 218 出牌 + 218 弃牌 = 436 条。
- `env.step()` 接受 `Action` 或 `{"kind": ..., "card_ids": [...]}`；非法动作抛 `InvalidActionError`（带稳定错误码），且不改变状态。

### 4. 自定义场景

场景是声明式 JSON，`scenarios/validator.py` 会拒绝未知字段、未实现规则（如 Boss 效果）与版本不一致。最小可用示例（精简自 `scenarios/dev/play-pair-7h7d.json`）：

```json
{
  "scenario_schema_version": 2,
  "scenario_id": "dev-play-pair-7h7d",
  "rules_version": "vanilla_1.0.1o_subset_v2",
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
    "target": 300,
    "money": null,
    "shop_open": false
  },
  "constraints": {"max_steps": 1, "allowed_action_kinds": ["play"]},
  "extensions": [],
  "boss_blind": null,
  "metadata": {"description": "7h 7d Pair = (10+14)x2 = 48"}
}
```

| 字段 | 取值 | 说明 |
|---|---|---|
| `scenario_schema_version` | 固定 `2` | 版本不匹配直接拒绝 |
| `rules_version` | `vanilla_1.0.1o_subset_v2` | 必须与引擎一致 |
| `origin` | `synthetic_dev` / `real_capture` / `real_counterfactual` | 场景来源 |
| `decision_type` | `episode` / `play` / `discard` / `shop` | 决策点类型；`shop` 需 `shop_open: true` |
| `goal.type` | `clear_ante1` / `maximize_score` / `reach_score` / `maximize_money` | `reach_score` 需正整数 `target` |
| `initial_state` | 手牌、Joker、盲注、分数、资源、`money`、`shop_open` | 只覆盖起点，不改规则常量 |
| `constraints` | `max_steps`、`allowed_action_kinds` | `play` / `discard` 场景会限制合法动作种类 |
| `extensions` / `boss_blind` | `[]` / `null`（Boss 场景可声明对象，但 `effect` 必须为 `null`） | v2 无扩展；Boss 效果未实现，请求即被拒绝 |

经济决策点示例见 `scenarios/dev/shop-buy-or-bank.json`（存钱吃利息 vs 现在买 Joker）。

### 5. MCP 接入（可选）

`bridge/` 把 7 个工具暴露为 MCP stdio 服务，自身不含规则逻辑。它需要 `mcp` SDK（未安装时 `python -m pip install mcp`；本机 `bridge/.venv` 中已装好）。启动：

```powershell
cd bridge
.\.venv\Scripts\python.exe -m server
```

客户端配置模板见 [`bridge/mcp-overlay.example.yml`](bridge/mcp-overlay.example.yml)（需替换为绝对路径的 Python 与 `bridge/` 目录）。服务启动后等待客户端连接，不打印交互提示。

---

## 目录结构

```text
BalatroEval/
├─ bench/            # 规则唯一实现：牌/牌型/计分/Joker/引擎/环境/工具/Oracle/序列化
├─ evaluation/       # Episode & Batch Runner、Trace(schema 2)、指标、Agent Adapter、CLI
├─ scenarios/        # RULES_VERSION、rules_v2.json、Schema/Loader/Validator、dev 场景
├─ bridge/           # MCP 薄壳（stdio）+ 示例 overlay；不实现规则
├─ benchmarks/       # 性能基准（规则/环境/Oracle/Episode/批量）
├─ tests/            # 157 项单元 / 集成 / property / 性能 smoke 测试
├─ docs/             # quality（对齐台账）/ implementation / balatro / ops / research
├─ plan/             # 项目计划；决策基线为 plan/详细版/07-真实游戏接入与终验.md
├─ data/             # 历史实验证据（只读，不覆盖）
├─ evidence/         # 历史验收证据（只读；真游戏素材不对外分发）
├─ archive/          # 历史归档（旧名 BalatroBench / 旧口径），引用需注明日期
├─ runs/             # 实验产物（本地生成，不跨机复用）
├─ AGENTS.md         # Agent 契约速览：红线 / 依赖分层 / 验收命令
└─ pyproject.toml    # 包元数据：name=balatroeval，requires-python>=3.11，无依赖
```

依赖方向是硬约束：只能上层 import 下层，`engine` 不得 import `oracle` / `environment` / `tools`；规则只允许在 `bench/` 实现一份，`scenarios/`、`evaluation/`、`bridge/` 不得复算分数、价格或利息。详见 [`AGENTS.md`](AGENTS.md) §3。

---

## 配置项与环境变量

项目**没有配置文件**；实验参数经 CLI 或 `evaluation.config.ExperimentConfig` 传入。只有 HTTP Agent 读取环境变量：

| 名称 | 默认 | 作用 |
|---|---|---|
| `BALATROEVAL_LLM_URL` | 无（`--agent http` 时必填） | OpenAI 兼容的 `chat/completions` 完整 URL |
| `BALATROEVAL_LLM_KEY` | 空 | 请求头 `Authorization: Bearer <key>` |
| `PYTHONPYCACHEPREFIX` | 无 | 非项目配置；受限环境下重定向 `__pycache__`，仅在写盘被拒时使用 |

```powershell
$env:BALATROEVAL_LLM_URL = "https://<your-endpoint>/v1/chat/completions"
$env:BALATROEVAL_LLM_KEY = "<token>"
python -m evaluation run --agent http --model <model-name> --scenarios scenarios/dev/play-pair-7h7d.json
```

其他可调项：`--retry-attempts`（默认 `1`）、`--retry-backoff`（默认 `0.5` 秒）、`--max-steps`、`--timeout`（见上表）；`ExperimentConfig.trace_fsync` 仅代码可设（默认 `True`，基准场景可关掉换吞吐）。

---

## 测试与构建

| 目的 | 命令 | 通过标准 |
|---|---|---|
| 全量测试 | `python -m unittest discover -s tests` | `Ran 157 tests` + `OK` |
| 规则声明 | `python -m bench rules` | 输出 JSON，`fidelity_status: NOT_VERIFIED`、`alignment_level: L0` |
| Oracle 交叉检查 | `python -m bench verify --samples 10 --seed 20261112` | `"passed": true` |
| 端到端单局 | `python -m bench demo --seed 20261112 --max-steps 50` | `outcome: win`、`money: 14` |
| 语法 / 导入自检 | `python -m compileall -q bench evaluation scenarios benchmarks bridge/server.py` | 退出码 `0`，无输出 |
| 性能基准 | `python -m benchmarks.bench --quick` | 输出 JSON（环境侧耗时，不含模型推理） |

- **Lint**：未配置 `[待补充: 是否引入 ruff / flake8 及规则集]`。
- **Build**：无构建步骤（纯 Python，无打包产物）；需要安装时用 `python -m pip install -e .`。
- 测试会写 `runs/_test_tmp/`。若在受限文件沙箱内被拒（`PermissionError`），换普通终端运行，或把仓库复制到沙箱可写位置再跑；这不是测试失败。

---

## 规则与数据口径（速览）

| 项 | 值 |
|---|---|
| 规则版本 | `vanilla_1.0.1o_subset_v2` |
| 牌组 / 赌注 / Ante | Red Deck / White Stake / Ante 1 |
| 盲注目标 | Small 300 / Big 450 / Boss 600（Boss 仅按目标分建模，效果未实现） |
| 每盲注资源 | 4 手 / 4 弃 / 手牌 8 / Joker 槽 5 |
| 牌型 | 12 种，等级 1 基础 Chips×Mult，仅计分牌计入 |
| Joker | 8 个具名 vanilla Joker（槽位从左到右依次生效） |
| 经济 | 起始 $4；奖励 $3/$4/$5；每剩余 1 手 / 未用 1 弃牌 +$1；利息 `min(money // 5, 5)`（按入账前金额，口径未验证） |
| 商店 | Small/Big 通关后开放；2 个报价；Common $5 / Uncommon $7 / Rare $9；卖出半价（最低 $1）；reroll $5 起、每次 +$1 |
| 合法动作 | 8 张手牌 → 218 出牌 + 218 弃牌 = 436 条；商店阶段另有买 / 卖 / reroll / 离开 |

```text
chips = 牌型基础 Chips + Σ(计分牌 rank chips；A=11, J/Q/K=10, 其余=点数) + Σ(+Chips 效果)
mult  = 牌型基础 Mult，按 Joker 槽位从左到右逐项应用（+Mult 加算 / ×Mult 乘算）
final = floor(chips × mult)        # 末尾 floor 为候选口径，未与真游戏验证
```

牌型基础（等级 1）：HC 5×1 / P 10×2 / 2P 20×2 / 3K 30×3 / ST 30×4 / FL 35×4 / FH 40×4 / 4K 60×7 / SF 100×8 / 5K 120×12 / FHouse 140×14 / FFive 160×16。

机器可读权威是 `bench/rules_version.py`；人类可读镜像为 [`scenarios/RULES_VERSION`](scenarios/RULES_VERSION) 与 [`scenarios/rules_v2.json`](scenarios/rules_v2.json)，测试断言三者一致。

---

## 能力边界（必读）

| ❌ 不得声称 | 事实 |
|---|---|
| 已与 vanilla 1.0.1o 对齐 / 已终验 | 只实现**等级 1 子集**；A2/A3 真游戏实测 **0 行**，`fidelity_status: NOT_VERIFIED`，对齐等级 **L0** |
| 8 个 Joker 覆盖了 Joker 系统 | 仅 8 个具名 vanilla Joker；其余、Joker 版本、重触发、Blueprint 等均在 `Ruleset.excluded` |
| 经济就是原版经济 | 价格取稀有度中值、商店候选均匀抽样（无原版权重）、利息按入账前金额计算；三条均 `unverified` |
| 157 项测试通过 = 原版兼容 | 测试只覆盖已实现行为，证明**子集自洽 + 基础设施正确** |
| `verify` 通过 = 计分公式正确 | O1 与暴力枚举**共用** `score_hand()`，只证明两条搜索路径一致；O1 是局部最优 |
| `demo` 赢了 = 引擎正确 / 策略优秀 | 固定 seed + 贪心策略的一次对局；该策略会在商店买 Joker，**不为利息存钱** |
| 捕获回放 = 真游戏终验 | 回放只验证 A2/A4 的分数与轨迹；终验是 Agent 在真游戏跑完 12 局（未执行） |
| 训练集结果 = 真游戏结果 | 两套环境；环境分歧须单列 `env_divergence`（E1），不得混入 Agent 失败 |

长线规划四支柱的覆盖情况（**目标能力，不等于已覆盖**）：

| 支柱 | 当前状态 | 缺口 |
|---|---|---|
| ① 跨回合资源分配 | **仅有载体** | `money` 跨盲注保留；无指标定义、无经济场景集 |
| ② 长期构建 | **未覆盖** | 无跨盲注 build 路径场景与评分 |
| ③ 失败恢复 | **未覆盖** | 无“先失败、后恢复”场景与恢复率指标 |
| ④ 长线指标 | **未覆盖** | 主指标仍是单步 `Local Regret`；`final_money` 只是描述量 |

要把 `fidelity_status` 改为已验证，唯一合法流程是 A0 版本锁定 → A1 schema 对齐 → A2 单步分数实测 → A3 规则子集 → A4 场景来源与回放，证据写入 [`docs/quality/engine-fidelity.md`](docs/quality/engine-fidelity.md)。理由与清单见 [`plan/详细版/07-真实游戏接入与终验.md`](plan/详细版/07-真实游戏接入与终验.md) §3。

---

## 常见问题

- **`demo` 为什么有时赢有时输？** 它是一次固定 seed 下的贪心对局，不是引擎正确性判据。判断引擎看规则断言、`verify` 与轨迹自洽性。
- **能复现原版 Balatro 的同种子局面吗？** 不能。项目内确定性可复现；RNG（尤其商店抽样）不是原版 RNG。
- **为什么包名是 `bench`、项目名却是 BalatroEval？** 项目名与 Python 发行名（`balatroeval`）和包 / CLI（`bench`、`python -m bench`）解耦；改包名会破坏测试与调用方。
- **想加规则 / Joker / 经济口径怎么办？** 先读 [`AGENTS.md`](AGENTS.md) 与 [`docs/implementation/`](docs/implementation/)；新规则只加在 `bench/`，并同步 `Ruleset.excluded`、状态矩阵与测试。

---

## 文档导航

| 文档 | 内容 |
|---|---|
| [`docs/README.md`](docs/README.md) | docs 总索引（quality / implementation / balatro / ops / research） |
| [`docs/implementation/README.md`](docs/implementation/README.md) | 实现文档入口：架构、模块、测试与运行方式 |
| [`docs/implementation/rules-implementation.md`](docs/implementation/rules-implementation.md) | 规则版本、计分顺序、Joker、经济与排除项 |
| [`docs/implementation/api-reference.md`](docs/implementation/api-reference.md) | 函数 / 类接口（参数、返回、异常、确定性） |
| [`docs/quality/engine-fidelity.md`](docs/quality/engine-fidelity.md) | 对齐台账：A/B 表、A0–A4 清单与签核模板（当前全 `PENDING`） |
| [`docs/ops/windows-pitfalls.md`](docs/ops/windows-pitfalls.md) | Windows / DSH / 真游戏环境的坑与解法 |
| [`plan/详细版/07-真实游戏接入与终验.md`](plan/详细版/07-真实游戏接入与终验.md) | 决策基线：两阶段架构、对齐契约、终验方案 |
| [`AGENTS.md`](AGENTS.md) | Agent 契约速览：红线、依赖分层、验收命令、硬约束 |

---

## 参与开发

1. 改完必跑：`python -m unittest discover -s tests`、`python -m bench verify`、`python -m bench demo`、`compileall`，并贴原始输出。
2. 规则常量、计分公式、Joker 目录、CLI 参数、测试数量变化时，同步 `docs/implementation/`、`scenarios/RULES_VERSION` 与 `scenarios/rules_v2.json`。
3. 不要顺手扩展未实现规则（Boss 效果、消耗品、增强等），也不要覆盖 `data/`、`evidence/` 中的历史证据。

---

## 许可

- 本仓库自身代码的许可证**尚未确定** `[待补充: MIT / Apache-2.0 / 内部项目]`；确定前请勿对外分发。
- `bench/` 为独立实现，未复制第三方代码；借鉴线索与来源许可见 [`docs/quality/data-sources.md`](docs/quality/data-sources.md)。
- Balatro 及其素材归其权利人所有；游戏文件、mod、`.jkr` 存档与含游戏素材的截图不入库。
