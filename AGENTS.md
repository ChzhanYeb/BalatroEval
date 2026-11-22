# AGENTS.md — BalatroEval 契约速览

> **项目正式名**：**BalatroEval**。**定位**：面向大模型 Agent 的**长线规划测试集**——用可判定、可复现的 Balatro 规则子集评测跨回合资源分配、多步决策、长期构建与失败恢复。 \
> **当前状态（2026-11-22）**：`bench/` 已实现 **vanilla 1.0.1o 严格子集 v2**（`rules_version = vanilla_1.0.1o_subset_v2`，v2 = v1 计分 + **金钱/利息/商店经济**），规则状态 **IMPLEMENTED + TESTED**（157 项测试通过）；与真游戏的对齐（A2/A3）**实测 0 行**，`fidelity_status: NOT_VERIFIED`、`alignment_level: L0`。真游戏接入、`scenarios/v3/`（60 决策点）、12 局终验、归因器**均未执行**。 \
> **阅读顺序**：[README.md](README.md)（入口）→ 本文件（契约速览）→ [docs/implementation/README.md](docs/implementation/README.md)（实现文档）→ [plan/详细版/07-真实游戏接入与终验.md](plan/详细版/07-真实游戏接入与终验.md)（两阶段/对齐契约的唯一决策基线）。 \
> **历史说明**：项目曾用名 **BalatroBench**；W2/L0 时期的 [程序员手册](archive/legacy-2026-11-22/程序员手册.md) 等已归档到 [archive/legacy-2026-11-22/INDEX.md](archive/legacy-2026-11-22/INDEX.md)，git 历史提交信息不改写。 \
> **长线四支柱**：③ 跨回合资源分配**已具备可测载体**（金钱/利息/商店），但**尚无指标定义与场景集**；② 长期构建 / ④ 失败恢复 / 长线指标仍**未覆盖**，不得声称已覆盖；差距见 README「定位与当前实现差距」。

---

## 1. 这是什么

`bench/` 是一个**可重复、可测试的 Balatro 风格子集环境**（Python，stdlib-only），提供：

- 规则层：牌 / Joker / 对局状态；12 种牌型识别；等级 1 的牌型基础 Chips×Mult + 计分牌筛选；8 个具名 vanilla Joker；确定性 RNG；快照/还原/state hash。
- 经济层：起始 $4；通关奖励 $3/$4/$5；每剩余 1 手 +$1、每未用 1 弃牌 +$1；利息每 $5 得 $1（上限 $5）；Small/Big 之后的**付费商店**（2 个报价、按稀有度固定价、买入/卖出/reroll/离开）。
- 环境层：`Environment`（reset/observe/legal_actions/step/snapshot/restore）、统一 `Action`、Observation + 紧凑状态文本、11 个稳定错误码。
- 工具层：7 个 Agent 工具（`get_state` / `play_cards` / `discard_cards` / `choose_joker`（买/离开）/ `sell_joker` / `reroll_shop` / `reset_episode`）；`bridge/server.py` 是 MCP 薄壳。
- 场景层：`scenarios/`（RULES_VERSION + `rules_v2.json` + Schema/Loader/Validator + 7 个 dev 场景，含 1 个经济决策点）。
- 评测层：`evaluation/`（Episode/Batch Runner、Trace schema 2、指标聚合 + bootstrap CI、manifest + code hash、断点续跑/重试、oracle-greedy/random/HTTP Adapter）。
- 参照策略：O1 精确局部 argmax、O2 弃牌 EV 近似、O3 贪心整局参照（商店“能买就买第一个”）。
- CLI：`python -m bench {rules,demo,verify,ev}`；`python -m evaluation {run,batch,report,rules}`；`python -m benchmarks.bench --quick`。

**两阶段定位**：`bench/` 是训练/开发环境；真实游戏（Balatro + Lovely + Steamodded + balatrobot）只做捕获与 12 局小样本终验（📋 未接入）。

## 2. 这不是什么（红线，任何输出都不得越过）

| ❌ 不得声称 | 事实 |
|---|---|
| 实现了原版 Balatro 计分 / 已对齐 vanilla | 实现了 vanilla 1.0.1o **等级 1 子集**；A2/A3 真游戏实测 **0 行**，`fidelity_status: NOT_VERIFIED`，对齐等级 **L0** |
| 8 个 Joker 是全部原版 Joker / 已覆盖 Joker 系统 | 只实现 8 个**具名 vanilla Joker**（数值来自 Wiki 事实页）；其余 142 个、Joker 版本、重触发、Blueprint 等均 `excluded`；触发/条件语义未经真游戏实测 |
| **经济是 vanilla 原版经济 / 已对齐** | 价格是**按稀有度取的中值**（Common $5 / Rare $9），商店候选是**均匀抽样**（无 70/25/5 权重），利息按**入账前**金额算、换报价用的是自带 RNG。三条都记 `unverified`，不得写成“原版经济” |
| **金钱能跨盲注 = 跨回合资源分配已覆盖** | 只有**载体**：`money` 跨盲注保留；⑤指标定义、经济场景集、regret/优化基线**均未做**。只能写“具备载体、尚未覆盖”，登记 W3 |
| 手数/弃牌也能跨盲注攒 | 仍每盲注重置 4/4；vanilla 也不允许“省手牌到下一盲注”，**不要**为了长线性伪造这条 |
| 固定 seed 复现了原版 RNG | 只保证本项目内可复现；不保证与真游戏同种子同局面（商店抽样尤其不是原版 RNG） |
| 157 测试通过 = 原版兼容 / 已对齐 | 测试只覆盖已实现行为，只证**子集自洽 + 基础设施正确** |
| `verify` 通过 = 计分公式正确 / 已对齐 | 两条路径**共用** `score_hand()`，只证明搜索路径一致；O1 是**局部**最优，不是全局最优 |
| `demo` 赢了 = 引擎正确 / 策略优秀 | 固定 seed + 贪心策略下的一次对局结果；它会花钱买 Joker，**不**会为利息存钱 |
| 已接入 balatrobot / 已对齐 / 已终验 | 真游戏接入、`scenarios/v3/`、12 局终验**均未执行（📋）** |
| 训练集结果 = 真游戏结果 | 两套环境；环境分歧记 **E1 `env_divergence`**（数据质量门禁，非 Agent 失败），必须单列 |
| 捕获回放 = 真游戏终验 | 捕获回放只做 A2/A4 分数/回放验证；终验是 Agent 在真游戏跑完 12 局（`CAPTURE_REPLAY_ONLY` 是降级状态） |
| 真游戏 12 局小样本 = 统计显著 | 只做描述统计 + 95% CI，不做显著性主张 |
| 游戏文件 / mod / `.jkr` 存档 / 含游戏素材截图可以入库 | L8：只提交脱敏状态 JSON、分数、trace、版本清单 |
| **② 长期构建 / ④ 失败恢复 / 长线指标已覆盖** | **三项仍未覆盖**；只能写“目标能力，尚未覆盖，登记 W3” |

## 3. 依赖分层（只允许上层 import 下层）

| 层 | 模块 | 允许 import 的兄弟模块 |
|---:|---|---|
| L0 | `errors.py` / `rules_version.py` | 无 |
| L1 | `model.py` / `rng.py` | `rules_version` |
| L2 | `cards.py` / `hand_eval.py` | `errors`, `model`, `rules_version` |
| L3 | `jokers.py` / `scoring.py` | `hand_eval`, `model` |
| L4 | `actions.py` / `serialize.py` / `logging.py`(legacy) | `cards`, `errors`, `jokers`, `model`, `rules_version` |
| L5 | `engine.py` | `actions`, `cards`, `errors`, `jokers`, `model`, `rng`, `rules_version`, `scoring` |
| L6 | `observation.py` / `environment.py` | `actions`, `engine`, `errors`, `model`, `rules_version`, `scoring` |
| L7 | `tools.py` | `environment`, `errors`, `observation`, `rules_version` |
| L8 | `oracle.py` | `actions`, `cards`, `engine`, `errors`, `model`, `rules_version`, `scoring` |
| CLI | `__main__.py` | `cards`, `engine`, `oracle`, `rules_version`, `scoring` |

【硬约束】只能向下依赖；`engine` **不得** import `oracle` / `environment` / `tools`；`tools`/`bridge` **不得**复算规则、分数或价格；`logging.py` 是 W2 legacy（schema 1），新链路用 `evaluation.trace`（schema 2）。

## 4. 不可不知的契约

**规则常量**（`bench/rules_version.py::VANILLA_SUBSET_V1`，唯一机器可读来源）：

- 52 张 Red Deck；White Stake；Ante 1；Small 300 / Big 450 / Boss 600；4 手 / 4 弃；手牌 8；Joker 槽 5；出牌/弃牌 1–5 张。
- Boss 盲注**只按目标分建模**，具名效果未实现；请求 Boss 效果的场景会被 validator 拒绝。
- `Ruleset.excluded`（18 项）明列：Boss 效果、消耗品、Voucher、补充包、增强/蜡封/版本、多牌组/多赌注、Tag/跳盲、Endless、手牌等级 >1、重触发、Blueprint/Brainstorm、Joker 版本、负片槽、手牌内效果、特殊牌（石头/黄金/玻璃/钢铁/幸运）。
- **v2 已把经济移出 excluded**：`money` / `interest` / `shop_economy` 现在是已实现项；宣称“经济被排除”属于过期说法。

**经济常量（v2，全部整数、可判定）**：

| 项 | 值 | 说明 |
|---|---|---|
| 起始金钱 | **$4** | Red Deck 起始 |
| 通关奖励 | Small **$3** / Big **$4** / Boss **$5** | `BlindSpec.reward_money` |
| 剩余手数 | 每 1 手 **+$1** | 结算时按 `hands_left` |
| 未用弃牌 | 每 1 弃牌 **+$1** | 结算时按 `discards_left` |
| 利息 | `min(money // 5, 5)` | **用入账前**的 money 计算（原版顺序 `unverified`） |
| 商店时机 | Small / Big 通关后 | Boss 通关即 `win`，不进商店 |
| 报价 | 2 个 | 从“未拥有的 8 个 Joker”里均匀抽样 |
| 价格 | Common $5 / Uncommon $7 / Rare $9 | **固定中值**，非原版浮动价 |
| 卖出 | `max(1, price // 2)` | 只在商店阶段可卖 |
| reroll | 首次 $5，每次 +$1 | 进入下一商店重置为 $5 |

**计分**（`scoring.score_hand`，等级 1）：

```
chips = 牌型基础 Chips + Σ(参与计分牌的 rank chips；A=11, J/Q/K=10, 其余=点数) + Σ(+Chips 效果)
mult  = 牌型基础 Mult，然后按【Joker 槽位从左到右】逐项应用：+Mult 加算 / ×Mult 乘算
final = floor(chips × mult)      # Fraction 精确运算，只在末尾 floor 一次（候选口径，未验证）
```

- 牌型基础：HC 5×1 / P 10×2 / 2P 20×2 / 3K 30×3 / ST 30×4 / FL 35×4 / FH 40×4 / 4K 60×7 / SF 100×8 / 5K 120×12 / FHouse 140×14 / FFive 160×16。
- 计分牌筛选：高牌 1 / 对子 2 / 两对 4 / 三条 3 / 四条 4 / 其余 5；踢脚不计分。
- 顺序敏感：`+4 Mult → ×2` 与 `×2 → +4 Mult` 结果不同（golden 测试固化）。
- 未验证口径：末尾 floor、4K/5K 的 contains 关系、跨盲注手牌重抽、手牌等级 >1。

**流程**（`engine.py`）：

- 纯函数转移：`new_game` / `play` / `discard` / `choose_joker` / `sell_joker` / `reroll_shop` 都 `deepcopy` 后改副本，**从不修改入参**；规则层不做文件 IO。
- 阶段：`play` →（达标）**结算金钱** → `shop`（Small/Big）或 `done`（Boss=win）；手数耗尽未达标 → `done`（loss）。
- 换盲注：重置资源 4/4、`total_score=0`、换目标、**保留 money**、重置 `reroll_cost`、清空 `last_payout`；上一盲注手牌进弃牌堆后补满。
- 买卖不结束商店：买入/卖出/reroll 后仍停在 `shop`，只有 `choose_joker(None)`（离开）才进入下一盲注。
- 顺序不变式：只有牌堆空才洗弃牌堆（消耗 RNG 并写回 `rng_state`）；打出的牌在**补牌之后**才进弃牌堆。
- 守恒：`len(hand)+len(deck)+len(discard_pile) == 52`；两堆皆空时 `_draw` 会静默少发（已文档化，未测试）。

**动作 / Observation**：

- 8 张手牌 ⇒ 218 个出牌 + 218 个弃牌 = 436 条合法动作；`card_ids` 是稳定身份（如 `c7h`），`label`（`7h`）仅供展示；`card_ids` 保留选择顺序，`Action.code` 会排序后作为去重/回放键。
- 商店动作码：`choose_joker:buy:0`（买）、`choose_joker:leave`（离开）、`sell_joker:0`、`reroll_shop`。
- 商店合法动作：**买得起且有空格位**的报价 + 每个已拥有 Joker 的卖出 + （钱够时）reroll + 恒可用的离开；买不起的报价**不出现在**合法动作集里。
- `Action.from_dict` 接受 `{"kind":"choose_joker","index":0}`（也接受 `joker_index`）；`sell_joker` 同样用 `index`。
- Observation 是 Agent 公开视图（schema **2**）：不含 oracle/内部 RNG/完整牌堆顺序；含 `economy`（money、下一档利息、上次结算明细）与 `shop`（报价、价格、是否买得起、reroll 价、卖价、空槽）；只给合法动作**计数**，完整动作集用 `environment.legal_actions()`。

**轨迹**：

- 新链路：`evaluation.trace.TraceRecorder`，JSONL schema 2，含 `start` / `step` / `decision_metric` / `end`、`state_hash`、错误与延迟；append-only。
- 旧 `bench/logging.py` 是 schema 1 legacy，仅为兼容旧脚本保留，**不得**在新实验中使用。
- 每步 `info` 含 `money` / `money_delta` / `last_payout`；结果行含 `final_money`；指标聚合含 `mean_final_money`。

**环境/工具错误码**（`bench/errors.py`，11 个）：`BAD_REQUEST` / `INVALID_STATE` / `NOT_ALLOWED` / `UNKNOWN_CARD` / `DUPLICATE_CARD` / `NO_RESOURCE` / `EPISODE_DONE` / `UNSUPPORTED_RULE` / `INTERNAL` / `AGENT_ERROR` / `TIMEOUT`。经济相关：钱不够 / 槽位满 → `NO_RESOURCE`（`detail` 里带 money/price 或 slots）；在非商店阶段买卖 → `INVALID_STATE`。evaluation 与 bridge 只读取 `code`，不得复制错误码表。

**对齐契约（A0–A4，规划；详见 [07](plan/详细版/07-真实游戏接入与终验.md) §3）**：

- **A0** 版本锁定（`scenarios/v3/MANIFEST.json`）；**A1** `gamestate` ↔ `GameState` schema 映射；**A2** 单步分数 `engine_score == real_score`；**A3** 规则子集与 `RULES_VERSION.excluded`；**A4** 场景来源与回放（`origin: real_capture | real_counterfactual` + `capture_id`）。
- 等级：L0 未对齐（**当前**）/ L1 分数对齐 / L2 规则子集对齐 / L3 真游戏终验通过。
- 任何“已对齐/已终验”的表述都必须有 A2/A3 实测行与 12 局终验证据；当前都没有。
- 经济新增的 A3 风险：价格/权重/利息顺序都未实测，**不能**因为“数值来自 Wiki”就标 L1/L2。

## 5. 验收命令（改完必跑，输出要贴原始结果）

```powershell
Set-Location C:\WorkData\005.Agent\BalatroEval

python -m unittest discover -s tests                    # 必须：Ran 157 tests / OK
python -m bench rules                                   # 规则声明（300/450/600、4/4、5 槽、8 Joker、$4/利息/商店）
python -m bench verify --samples 10 --seed 20261112     # 必须：passed true，每例 218 候选
python -m bench demo --seed 20261112 --max-steps 50     # 实测：outcome=win, steps=12, blind_scores=[412,620,640], total_scored=1672, money=14
python -m compileall -q bench evaluation scenarios benchmarks bridge/server.py
```

> 这些命令只覆盖**训练环境自洽**（规则实现、确定性、Trace、批量执行）。它们**不能**替代 A2/A3 对齐验证，也不能替代真游戏终验；对齐命令（`bench/align.py` 等）与终验命令（`bridge/realgame.py`、12 局）📋 尚未提供。
> 本机 `__pycache__` 受 ACL 限制时，可设 `$env:PYTHONPYCACHEPREFIX = "$env:TEMP\balatroeval-pycache"`；这是环境绕行，不改变行为。

## 6. Agent 硬约束

1. **不许伪造验证**：没跑过的命令不许写“通过”；实测输出与文档声明必须一致。
2. **不许降低/提高保真度表述**：不得把“未验证”写成“已验证”，也不得把“已实现”写成“已对齐”。经济口径尤其如此。
3. **规则只有一份实现**：新规则/效果加在 `bench/`，并登记 `Ruleset.excluded` 与状态矩阵；不得在 `scenarios`/`evaluation`/`bridge` 复算分数、价格或利息。
4. **真游戏适配器不写规则**：`bridge/realgame.py` / `bench/realgame.py`（📋 规划）只做 JSON-RPC、字段映射、动作 id↔下标转换、统一错误码。
5. **所有工具/环境调用返回结构化错误**，不向 Agent 抛 traceback；库调用不写文件（trace 由 evaluation 显式指定路径）。
6. **Git 安全**：禁止 `git add .` / `commit -a` / `reset --hard` / `clean -fd`；只精确暂存本次工作文件。
7. **不覆盖证据**：`data/`、`evidence/` 是历史证据，只读；新实验写新的 `runs/<experiment_id>/`。
8. **发现疑似 bug 不顺手修**：用「注意：」标注并上报，修复需单独任务 + 测试。

## 7. 已知边界 / 粗糙点（不要“顺手修”）

- **经济三条口径未实测**：利息按入账前金额（`interest_ordering_before_payout`）；价格是稀有度中值（`joker_price_fixed_mid_of_vanilla_range`）；商店候选均匀抽样（`shop_offer_pool_uniform_no_rarity_weights`、`shop_rng_not_vanilla`）；卖掉的 Joker 可能再次出现（`sold_joker_may_reappear_after_reroll`）。
- `scoring.py` 模块 docstring 的公式行写成 `base × Π(×Mult) + Σ(+Mult)`，但实现与同段说明都是**按槽位逐项应用**；以代码与 golden 测试为准（文档待单独修）。
- `_draw` 在两堆皆空时静默少发牌（不报错）；该分支未被测试覆盖。
- `__main__.verify_oracle` 只交叉检查 O1 搜索路径，不能证明 `score_hand` 与真游戏一致。
- O3 `greedy_episode` 是贪心参照：商店“能买就买第一个”，**不为利息存钱**，不是该局面理论最优，也不是经济最优。
- O2 弃牌 EV 的抽样模型与真实发牌不一致（只作启发式）。
- HTTP Agent Adapter 仅用 fake transport 测试，真实模型端点未实测；MCP stdio 端到端未做（只验证 `build_server()`）。
- 测试未覆盖：`_draw` 的两堆皆空/洗回弃牌堆分支、MCP 会话、真实模型端点。

## 8. 先读什么

| 你要做的事 | 读 |
|---|---|
| 改计分 / 加 Joker | [docs/implementation/rules-implementation.md](docs/implementation/rules-implementation.md)、[docs/implementation/api-reference.md](docs/implementation/api-reference.md)、`tests/test_w2_rules.py` |
| **改经济 / 商店 / 价格** | [docs/implementation/rules-implementation.md](docs/implementation/rules-implementation.md) §经济、`tests/test_economy.py`、`bench/rules_version.py` |
| 改环境 / 工具 / 错误码 | `bench/environment.py`、`bench/tools.py`、`docs/implementation/architecture.md` |
| 改 Trace / 批量执行 | `evaluation/trace.py`、`evaluation/batch_runner.py`、[docs/implementation/evaluation-execution.md](docs/implementation/evaluation-execution.md) |
| 判断能否声称保真度 / 对齐等级 | [docs/engine-fidelity.md](docs/engine-fidelity.md)、[07](plan/详细版/07-真实游戏接入与终验.md) §3；默认答案：不能 |
| 真游戏适配 / 捕获 / 终验 | [07](plan/详细版/07-真实游戏接入与终验.md) 全文；先做四层依赖冒烟与 A0，失败即降级 `CAPTURE_REPLAY_ONLY` |
| 完整背景 | [README](README.md)、[plan/00-项目全貌.md](plan/00-项目全貌.md)、[docs/balatro](docs/balatro/README.md) 规则调研、[docs/research/](docs/research/) 调研笔记 |
