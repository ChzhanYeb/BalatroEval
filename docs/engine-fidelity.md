# BalatroEval 引擎对齐台账

## 0. 一句话结论与措辞边界

**当前 W2 引擎（提交 `c65fb9b`）是 L0：自定义子集公式 + 合成 Joker + 3 槽位 + 300/800/2000 + 4 手/2 弃，没有一条与真游戏逐位对齐的证据。** 本台账的存在目的不是“证明已对齐”，而是**把对齐变成可验收、可签核、不可自嗨的流程**。

| 可以写 | 不可以写 |
|---|---|
| “自定义子集内自洽；25 项单测、verify 10/10 只覆盖已实现行为” | “实现了原版 Balatro 计分” |
| “对齐等级 L0，A0–A4 全部未签核” | “已对齐 / 已终验 / 已达到 L2” |
| “真游戏捕获 0 行实测，20 例人工对拍 0/20，抽检 0/5” | “20/20 通过”“第三方抽检通过” |
| “捕获回放（A2/A4）已验证某局面单步分数一致（附证据路径）” | “捕获回放 = 真游戏终验” |
| “W3 计划做 vanilla 对齐改造（📋）” | “W3 已对齐” |

### 0.1 对齐等级（与 07 §3.1 一致）

| 等级 | 含义 | 当前状态 |
|---|---|---|
| **L0 未对齐** | 当前 W2 引擎（自定义公式、合成 Joker） | ✅ **本项目当前等级** |
| L1 分数对齐 | A2 在覆盖局面上 100% 一致 | 📋 未达 |
| L2 规则子集对齐 | A2 + A3 全部通过 | 📋 W3 目标 |
| L3 终验通过 | 真游戏终验完成且结果可复现 | ⏳ W5 目标 |

> **红线**：`scenarios/RULES_VERSION` 的 `alignment_level` 与 `fidelity_status` 只能在本文 §6 签核模板填满、且 A0–A4 全部勾选之后修改。未签核就改 = 越线（07 §8 红线 L9）。

---

## 1. 本轮改造的定位（v2.x → v3.0）

| 项 | v2.x（历史） | v3.0（本文） |
|---|---|---|
| 文档标题 | 引擎保真度 — 人工单手分数对照 | **引擎对齐台账** |
| 状态口径 | `NOT VERIFIED`（未验证） | **L0 未对齐；目标 L2**（更精确：不是“没测”，而是“等级为 0”） |
| 主门槛 | 20 例人工对拍 + 5 例抽检 | **A0–A4 对齐契约**（A 表真游戏捕获 + B 表 save/load 反事实回放） |
| 旧 20 + 5 | 唯一验收物 | **降级为辅助证据**，不再是主门槛，也不再是“通过/不通过”的唯一依据 |
| 差异归因 | 7 条（含牌型、取整等） | 7 类重排：**新增 vanilla 基础 Chips×Mult、计分牌筛选、Joker 触发条件**三类显式归因 |
| 训练集来源 | 无（W2 未建集） | 每条必须有真游戏来源或回放证据（A4）；无证据不得入集 |

> **为什么降级旧表**：20 例人工对拍是“单点抽样 + 手工记录”，既无法覆盖 218 个动作，也无法区分“牌型错”与“Joker 条件错”。A0–A4 用**同局面、同动作、逐字段 diff** 替代它作为主门槛；旧表保留用于快速回归与人工交叉核对。

---

## 2. A 表 — 真游戏捕获对齐记录（📋 全 PENDING）

> **用途**：A2/A3 的主证据。每一行 = 一个真游戏捕获的决策点，在真游戏中执行某一动作，记录真游戏得分；引擎重放同一动作后比对。
> **入表前提**：A0 版本锁定完成（`scenarios/v3/MANIFEST.json` 存在）；A1 字段映射通过。
> **当前状态**：**0/30 行实测**（真游戏未接入，balatrobot 未安装）。分层列为 W3 计划的抽样配额，**不是已捕获数据**。

字段说明：

- `capture_id`：格式 `cap-YYYYMMDD-NNN`，与 `scenarios/v3/*.jsonl` 的 `game.capture_id` 一致；
- `版本`：记录 `game_version / build_id / lovely / smods / balatrobot` 五元组，统一写 `MANIFEST` 版本号（如 `v3.0-0`），**不在此列写自由文本版本**，避免同一批实验混版本（A0）；
- `牌组/赌注`：固定 `RED / WHITE`；出现其他值即该行作废；
- `手牌`：捕获时的 8 张稳定 id（`c7h` 形式）；
- `Jokers`：vanilla 具名 Joker 及其槽位顺序；含 `modifier`（edition/seal/enhancement）的非空 Joker 不入表（A3 排除项）；
- `出牌`：本次决策执行的合法动作（`play:c3h,c7s` 或 `discard:c5d`），绑定稳定 id，**不以下标为主键**；
- `真游戏分数` / `引擎分数`：同一动作的单步得分；仅当两者相等才可在 `是否一致` 写 `✅`；
- `证据路径`：`evidence/W3/align/<capture_id>.json`（脱敏 JSON：状态投影、动作、双分数、diff 字段；**不放 `.jkr` 存档、游戏截图或游戏素材**，见 L8）。

| # | capture_id | 版本 | 牌组/赌注 | 分层（计划配额） | 手牌 | Jokers（槽位顺序） | 出牌 | 真游戏分数 | 引擎分数 | 是否一致 | 证据路径 |
|---:|---|---|---|---|---|---|---|---:|---:|---|---|
| 1 | `cap-PENDING-001` | PENDING | RED/WHITE | 无 Joker | PENDING | — | PENDING | — | — | PENDING | PENDING |
| 2 | `cap-PENDING-002` | PENDING | RED/WHITE | 无 Joker | PENDING | — | PENDING | — | — | PENDING | PENDING |
| 3 | `cap-PENDING-003` | PENDING | RED/WHITE | 无 Joker | PENDING | — | PENDING | — | — | PENDING | PENDING |
| 4 | `cap-PENDING-004` | PENDING | RED/WHITE | 无 Joker | PENDING | — | PENDING | — | — | PENDING | PENDING |
| 5 | `cap-PENDING-005` | PENDING | RED/WHITE | 无 Joker | PENDING | — | PENDING | — | — | PENDING | PENDING |
| 6 | `cap-PENDING-006` | PENDING | RED/WHITE | 无 Joker | PENDING | — | PENDING | — | — | PENDING | PENDING |
| 7 | `cap-PENDING-007` | PENDING | RED/WHITE | 单 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 8 | `cap-PENDING-008` | PENDING | RED/WHITE | 单 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 9 | `cap-PENDING-009` | PENDING | RED/WHITE | 单 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 10 | `cap-PENDING-010` | PENDING | RED/WHITE | 单 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 11 | `cap-PENDING-011` | PENDING | RED/WHITE | 单 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 12 | `cap-PENDING-012` | PENDING | RED/WHITE | 单 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 13 | `cap-PENDING-013` | PENDING | RED/WHITE | 单 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 14 | `cap-PENDING-014` | PENDING | RED/WHITE | 单 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 15 | `cap-PENDING-015` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 16 | `cap-PENDING-016` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 17 | `cap-PENDING-017` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 18 | `cap-PENDING-018` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 19 | `cap-PENDING-019` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 20 | `cap-PENDING-020` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 21 | `cap-PENDING-021` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 22 | `cap-PENDING-022` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 23 | `cap-PENDING-023` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 24 | `cap-PENDING-024` | PENDING | RED/WHITE | 双 Joker | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 25 | `cap-PENDING-025` | PENDING | RED/WHITE | 含 xMult | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 26 | `cap-PENDING-026` | PENDING | RED/WHITE | 含 xMult | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 27 | `cap-PENDING-027` | PENDING | RED/WHITE | 含 xMult | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 28 | `cap-PENDING-028` | PENDING | RED/WHITE | 含 xMult | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 29 | `cap-PENDING-029` | PENDING | RED/WHITE | 多弃牌 | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |
| 30 | `cap-PENDING-030` | PENDING | RED/WHITE | 多弃牌 | PENDING | PENDING | PENDING | — | — | PENDING | PENDING |

**填写规则（缺一不可）**：

1. 每行必须有 `capture_id` + 证据路径；无证据行视为 `PENDING`，不得写 `✅`；
2. `是否一致` 只允许 `✅` / `❌` / `PENDING`；写 `❌` 必须在 §5 差异归因中给出类别；
3. 同一行不得混入不同 `版本`、不同 `牌组/赌注`（A0 红线）；
4. 含 Boss 效果 / 消耗牌 / 增强 / 版本 / 印章 / 商店要素的局面**不入 A 表**（A3 排除项），只在终验 trace 记录。

---

## 3. B 表 — save/load 反事实回放记录（📋 全 PENDING）

> **用途**：A4 的主证据。在 A 表锚点的决策点 `save`，再 `load` 回游戏执行**与锚点不同的合法动作**，用真游戏实测得分验证“同一局面不同选择”的 oracle 对照是否成立。
> **为什么需要**：只验证“锚点动作”无法证明 oracle 覆盖面；反事实变体让 `best_actions` 的比较有真游戏依据，而不是靠引擎自证。
> **当前状态**：**0/30 行实测**（`save`/`load` 未执行；`data/realgame/saves/` 不存在）。
> **表名口径（v3.0 已统一）**：本台账 **A 表 = 真游戏捕获、B 表 = `save`/`load` 反事实回放**，第三方抽检（EFHIII 5 例）为 **附录 D 辅助证据**。07 §3 的 A2 证据列已同步为该定义；跨文档引用一律以本台账为准。

| # | variant_id | 锚点 capture_id | 变体动作 | 真游戏分数 | 引擎分数 | 是否一致 | save 路径 | 证据路径 |
|---:|---|---|---|---:|---:|---|---|---|
| 1 | `var-PENDING-001` | `cap-PENDING-001` | PENDING | — | — | PENDING | PENDING | PENDING |
| 2 | `var-PENDING-002` | `cap-PENDING-002` | PENDING | — | — | PENDING | PENDING | PENDING |
| 3 | `var-PENDING-003` | `cap-PENDING-003` | PENDING | — | — | PENDING | PENDING | PENDING |
| 4 | `var-PENDING-004` | `cap-PENDING-004` | PENDING | — | — | PENDING | PENDING | PENDING |
| 5 | `var-PENDING-005` | `cap-PENDING-005` | PENDING | — | — | PENDING | PENDING | PENDING |
| 6 | `var-PENDING-006` | `cap-PENDING-006` | PENDING | — | — | PENDING | PENDING | PENDING |
| 7 | `var-PENDING-007` | `cap-PENDING-007` | PENDING | — | — | PENDING | PENDING | PENDING |
| 8 | `var-PENDING-008` | `cap-PENDING-008` | PENDING | — | — | PENDING | PENDING | PENDING |
| 9 | `var-PENDING-009` | `cap-PENDING-009` | PENDING | — | — | PENDING | PENDING | PENDING |
| 10 | `var-PENDING-010` | `cap-PENDING-010` | PENDING | — | — | PENDING | PENDING | PENDING |
| 11 | `var-PENDING-011` | `cap-PENDING-011` | PENDING | — | — | PENDING | PENDING | PENDING |
| 12 | `var-PENDING-012` | `cap-PENDING-012` | PENDING | — | — | PENDING | PENDING | PENDING |
| 13 | `var-PENDING-013` | `cap-PENDING-013` | PENDING | — | — | PENDING | PENDING | PENDING |
| 14 | `var-PENDING-014` | `cap-PENDING-014` | PENDING | — | — | PENDING | PENDING | PENDING |
| 15 | `var-PENDING-015` | `cap-PENDING-015` | PENDING | — | — | PENDING | PENDING | PENDING |
| 16 | `var-PENDING-016` | `cap-PENDING-016` | PENDING | — | — | PENDING | PENDING | PENDING |
| 17 | `var-PENDING-017` | `cap-PENDING-017` | PENDING | — | — | PENDING | PENDING | PENDING |
| 18 | `var-PENDING-018` | `cap-PENDING-018` | PENDING | — | — | PENDING | PENDING | PENDING |
| 19 | `var-PENDING-019` | `cap-PENDING-019` | PENDING | — | — | PENDING | PENDING | PENDING |
| 20 | `var-PENDING-020` | `cap-PENDING-020` | PENDING | — | — | PENDING | PENDING | PENDING |
| 21 | `var-PENDING-021` | `cap-PENDING-021` | PENDING | — | — | PENDING | PENDING | PENDING |
| 22 | `var-PENDING-022` | `cap-PENDING-022` | PENDING | — | — | PENDING | PENDING | PENDING |
| 23 | `var-PENDING-023` | `cap-PENDING-023` | PENDING | — | — | PENDING | PENDING | PENDING |
| 24 | `var-PENDING-024` | `cap-PENDING-024` | PENDING | — | — | PENDING | PENDING | PENDING |
| 25 | `var-PENDING-025` | `cap-PENDING-025` | PENDING | — | — | PENDING | PENDING | PENDING |
| 26 | `var-PENDING-026` | `cap-PENDING-026` | PENDING | — | — | PENDING | PENDING | PENDING |
| 27 | `var-PENDING-027` | `cap-PENDING-027` | PENDING | — | — | PENDING | PENDING | PENDING |
| 28 | `var-PENDING-028` | `cap-PENDING-028` | PENDING | — | — | PENDING | PENDING | PENDING |
| 29 | `var-PENDING-029` | `cap-PENDING-029` | PENDING | — | — | PENDING | PENDING | PENDING |
| 30 | `var-PENDING-030` | `cap-PENDING-030` | PENDING | — | — | PENDING | PENDING | PENDING |

**填写规则**：

1. 变体动作必须是**当前状态下的合法动作**，且与锚点动作不同（否则不构成反事实）；
2. `save 路径` 只记录**本机路径的脱敏占位**（如 `data/realgame/saves/<capture_id>-stepNN.jkr`）；`.jkr` 文件本身**不入库**（L8）；
3. `load` 失败（版本不兼容 / 存档损坏）必须写 `❌` 并在备注说明，不允许“重跑一次凑一致”；
4. B 表通过 ≠ 覆盖全部 218 个动作；`oracle.exact: true` 只在全动作验证时成立（07 §5.2）。

---

## 4. A0–A4 对齐检查清单（📋 全部未勾选）

> 只有全部勾选才可进入 §6 签核。任一未勾选 → 对齐等级保持 L0。

### A0 版本锁定 — 📋

- [ ] `scenarios/v3/MANIFEST.json` 已创建并记录 `game_version`、`build_id`、`deck`、`stake`、`lovely_version`、`smods_version`、`balatrobot_version`；
- [ ] 同一批实验不跨版本（A 表 `版本` 列取值唯一）；
- [ ] 游戏/注入链/适配器版本与 `scenarios/RULES_VERSION.rules_version` 的声明不冲突。

### A1 状态/动作 schema — 📋

- [ ] `gamestate` ↔ `GameState` 映射表（07 §4.3）逐字段有 diff 报告；
- [ ] 手牌/牌堆计数/Joker 列表/盲注/目标分/剩余出牌/剩余弃牌/阶段八类字段可一一映射；
- [ ] 动作绑定稳定卡牌 id，并在 JSONL 同时记录 `card_ids` 与 `hand_indices`（下标不作回放主键）；
- [ ] `tests/test_realgame_schema.py`（📋 未创建）覆盖字段映射。

### A2 单步分数 — 📋

- [ ] A 表至少 30 行实测且 `engine_score == real_score`（覆盖局面上 100%）；
- [ ] 不一致行已归因（§5）或该局面被排除并写入 `rejected` 清单；
- [ ] 引擎重放路径不只跑 `score_hand()`，还要覆盖计分牌筛选后的牌面 Chips 累加。

### A3 规则子集 — 📋

- [ ] vanilla 9 种牌型的基础 Chips×Mult（等级 1）有来源链接与金样测试；
- [ ] 计分牌筛选规则有金样测试（高牌 1 张 / 对子 2 张 / 两对 4 张 / 三条 3 张 / 顺子·同花·葫芦·同花顺 5 张 / 四条 4 张）；
- [ ] 8 个 vanilla Joker 的数值、触发条件、槽位顺序有实测或来源依据（见 [joker-semantics.md](joker-semantics.md)）；
- [ ] 未实现规则全部列入 `scenarios/RULES_VERSION.excluded`，且不出现在训练集中；
- [ ] 合成 Joker 夹具已与 vanilla 目录分离命名（如 `synthetic_*` 或 `tests/fixtures`）。

### A4 场景来源与回放 — 📋

- [ ] 每个训练/开发集局面有 `origin`（`real_capture` / `real_counterfactual`）与 `capture_id`；
- [ ] B 表至少 30 行反事实变体通过真游戏回放；
- [ ] 无证据局面进入 `rejected` 清单并写明原因，不静默丢弃；
- [ ] `evidence/W3/align/<scenario_id>.json` 存在且可重放。

---

## 5. 7 类差异归因（v3.0 重排）

> 任何 A 表/B 表的 `❌` 必须归到下面 7 类之一；归不进去说明台账字段不足，应补字段而不是写“其他”。
> 前 3 类是本轮 v3.0 **新增**的显式归因项（v2.x 只在阻塞项里笼统提过）。

| # | 类别 | 典型表现 | 检查方法 |
|---:|---|---|---|
| **D1** | 牌型分类与优先级（含 A 作低/作高、同花/顺子边界） | 引擎判 Pair、真游戏判 Two Pair | 用同一手牌打印引擎 `hand_type` vs 真游戏牌型高亮 |
| **D2** | **vanilla 牌型基础 Chips×Mult（等级 1）** — v3.0 新增 | 引擎少一段基础分（无 base Chips）；倍率表不同 | 对照 07 §7.1 的 9 行表，逐牌型金样测试 |
| **D3** | **计分牌筛选** — v3.0 新增 | 引擎对打出的每张牌都计点数码；真游戏只计参与牌型的牌（高牌只计最高 1 张） | 构造 5 张中含 2 张无关牌的手牌，比对分数差 |
| **D4** | 牌面筹码值 | A=11 / J/Q/K=10 / 其余面值是否一致 | 逐点数单牌金样 |
| **D5** | **Joker 触发条件** — v3.0 新增 | `+8 Mult` 条件“打出的牌含对子”未判；或对“含对子或更大”理解不同 | 用不含对子/含三条等边界手牌逐条触发验证 |
| **D6** | Joker 效果类型与槽位顺序 | 把 +Mult 当 ×Mult；或 `+4Mult → x1.5` 与 `x1.5 → +4Mult` 顺序颠倒 | 双 Joker 换序对照（引擎已证明顺序敏感：126 vs 98） |
| **D7** | 取整时机与调度语义 | 中间取整；把自定义 `before` / `individual` 标签当作 SMODS `context.before` / `individual` | 检查是否只末尾 `floor` 一次；对照 smods 文档说明（见 joker-semantics §3） |

---

## 6. 签核模板（📋 未签核）

> 只有在 A0–A4 全部勾选、A/B 表填满并完成归因后，才允许填写下列字段。**空模板本身就是当前状态**。

| 字段 | 值 |
|---|---|
| 签核日期 | `PENDING` |
| 游戏版本 / build_id | `PENDING` |
| Lovely / Steamodded / balatrobot 版本 | `PENDING` |
| `scenarios/v3/MANIFEST.json` | `PENDING`（未创建） |
| A0 版本锁定 | `📋 未通过` |
| A1 schema 映射 | `📋 未通过` |
| A2 单步分数一致行数 | `0 / 30`（要求 ≥30 且 100% 一致） |
| A3 规则子集（9 牌型 / 8 Joker / 排除项） | `📋 未通过` |
| A4 场景来源与回放（B 表通过数） | `0 / 30` |
| 未解决差异（按 D1–D7 分类） | `PENDING` |
| `rejected` 局面清单 | `PENDING`（无证据不得入集） |
| **对齐等级结论** | **L0（未对齐）** |
| 允许修改 `RULES_VERSION.alignment_level` | ❌ **否 —— 未签核** |
| 允许修改 `RULES_VERSION.fidelity_status` | ❌ **否 —— 未签核** |

签核人：`PENDING` ｜ 复核人：`PENDING` ｜ 证据索引：`evidence/W3/align/`（📋 未创建）

---

## 7. 两条必须区分的结论

### 7.1 捕获回放 ≠ 真游戏终验

| 项 | 捕获回放（A2/A4） | 真游戏终验（RGFT，W5） |
|---|---|---|
| 回答的问题 | “引擎算的这一步分数，与真游戏同一步是否一致？” | “Agent 在真游戏里能不能打好？失败属于哪类？” |
| 执行物 | 捕获状态 + `save`/`load` + 引擎重放 | dsh Agent + balatrobot + 12 局 Ante 1 |
| 证据 | A 表、B 表、`evidence/W3/align/*.json` | `runs/w5-real/*`、终验报告 |
| 允许的结论 | “覆盖局面上单步分数一致（n=…）” | “完成 n=12 描述性终验” |
| 不能推出的结论 | 完整规则一致、Agent 能力、统计显著 | —— |

> 07 §8 红线 L9：**不得把“真游戏捕获回放”写成“真实游戏终验”**；也不得把“单步分数一致”写成“完整规则一致”。

### 7.2 未签核不得改 `RULES_VERSION`

`scenarios/RULES_VERSION` 仍是 `fidelity_status: NOT_VERIFIED`、`alignment_level: L0`。修改流程（唯一合法路径）：

1. 填满本文 A/B 表并勾选 A0–A4；
2. 完成 §5 的 D1–D7 归因，未解决项写入 `rejected` 清单；
3. 填 §6 签核模板（含签核人/复核人/证据索引）；
4. **然后**才改 `RULES_VERSION.alignment_level` / `fidelity_status`，并同步 `README.md`、`AGENTS.md`、`程序员手册.md` §17/§21、`plan/详细版/02-规则引擎与对拍.md`；
5. 任何一步缺失都视为越线；不允许“先改状态、以后补证据”。

---

## 附录 C — v2.x 遗留：20 例人工单手对拍（降级为辅助）

> **状态：保留作历史与快速回归，不再是主门槛。** 20 行全部 `PENDING`（0/20 实测）。主门槛见 §2 A 表。
> 本表的价值：人工快速核对“引擎算出来像不像”。局限：单点抽样、无法覆盖 218 动作、无法定位 D2/D3/D5 类差异。

记录稳定的游戏版本／构建号，并抓取构成出牌的确切牌以及任何 Joker 效果。不得从不同对局、不同游戏版本或不同 Joker 条件下复制分数。

| # | 抽样分层 | 手牌（点数+花色） | 实际 Jokers／效果状态 | 打出的牌 | 游戏分数 | 引擎分数 | 是否一致 | 证据／版本／备注 |
|---:|---|---|---|---|---:|---:|---|---|
| 1 | 无 Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 2 | 无 Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 3 | 无 Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 4 | 无 Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 5 | 无 Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 6 | 无 Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 7 | 单个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 8 | 单个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 9 | 单个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 10 | 单个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 11 | 单个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 12 | 单个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 13 | 两个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 14 | 两个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 15 | 两个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 16 | 两个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 17 | 两个 Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 18 | 含 xMult | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 19 | 含 xMult | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 20 | 含 xMult | PENDING | PENDING | PENDING | — | — | — | PENDING |

如适用，三行 `xMult` 的分层会有意重叠；请在备注列说明抽样归属。

## 附录 D — v2.x 遗留：5 项第三方计算器抽检（降级为辅助）

> **状态：0/5 实测，辅助证据。** 上游 EFHIII 的 README 提醒：少数 Joker 可能不准确。请记录确切的计算器 URL／输入，并保留不一致结果，而不是强行凑成一致。
> 计算器链接：https://github.com/EFHIII/balatro-calculator （MIT，不集成、不作依赖）

| # | 类别 | 输入／计算器 URL | 计算器结果 | 引擎结果 | 是否一致 | 备注 |
|---:|---|---|---:|---:|---|---|
| C1 | 无 Joker | PENDING | — | — | — | PENDING |
| C2 | 无 Joker | PENDING | — | — | — | PENDING |
| C3 | 单个 +Mult | PENDING | — | — | — | PENDING |
| C4 | 单个 xMult | PENDING | — | — | — | PENDING |
| C5 | 混合／边界情形 | PENDING | — | — | — | PENDING |

> 说明：v2.x 里这两张表叫 “A/B”；v3.0 起 A/B 让位给对齐主门槛，旧表改称 C/D 附录。历史英文版（提交 `c65fb9b`）中的表名仍为 A/B，引用旧版时请注意对应关系。

---

## 附录 E — v2.x 遗留的 6 项已知阻塞项（历史，已被 §5 D1–D7 吸收）

1. 自定义公式省略了原版扑克牌型的基础筹码（base Chips）；原版 1 级对子为 10 筹码 × 2 倍率，同花为 35 筹码 × 4 倍率。→ 现归 **D2**。
2. 自定义牌型倍率（同花顺 12、四条 10 等）与原版 1 级倍率不同（例如原版同花顺 8、四条 7）。→ 现归 **D2**。
3. 本子集对打出的每一张牌都计入点数筹码；原版计分可以把未参与计分的牌从打出的 5 张中排除。→ 现归 **D3**。
4. Joker 夹具是合成的，未映射到具名的原版 Joker。→ 现归 **D5/D6**，取代方案见 [joker-semantics.md](joker-semantics.md) §2。
5. 外部提供的那行数据 `7♥7♦ -> 68` 与所规定的子集公式（28）冲突，也与原版对子分数（48）冲突。→ 保留为待查冲突，不强行对齐。
6. 自定义的 `before` 阶段标签不应被误认为是 SMODS `context.before` 的计分行为。→ 现归 **D7**。

---

## 附录 F — 参考链接

- 对齐契约与验收：`plan/详细版/07-真实游戏接入与终验.md` §3、§7
- balatrobot API：https://coder.github.io/balatrobot/latest/api/
- SMODS 计算函数文档：https://docs.smods.dev/API%20Documentation/Calculate-Functions/
- Balatro Wiki（只取事实）：https://balatrowiki.org/w/Poker_hands ｜ https://balatrowiki.org/w/Blinds_and_Antes
- EFHIII 计算器：https://github.com/EFHIII/balatro-calculator
