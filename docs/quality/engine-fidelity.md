# 引擎对齐台账（vanilla 1.0.1o 子集 v2）

> **一句话**：本文件回答“引擎和真游戏到底像不像、能不能说已对齐”。当前 **A/B 表 0 行实测 → 等级 L0、`fidelity_status: NOT_VERIFIED`**。
> **红线**：只有 A0–A4 全部勾选 + §5 签核模板填满，才允许改 `scenarios/RULES_VERSION` 的 `alignment_level` / `fidelity_status`。本台账不是“已对齐”的证明，是“怎么才算对齐”的流程。
> 关联：[07 对齐契约](../../plan/详细版/07-真实游戏接入与终验.md) §3 · [data-sources.md](data-sources.md) · [joker-semantics.md](joker-semantics.md)

## 0. 现在能说什么 / 不能说什么

| 可以写 | 不可以写 |
|---|---|
| 子集内自洽：157 项单测、`verify` 10/10 只覆盖已实现行为 | “实现了原版 Balatro 计分” |
| 对齐等级 **L0**，A0–A4 未签核，A/B 表 **0 行** | “已对齐 / 已终验 / 已达 L2” |
| v2 规则（计分 + 经济）已实现、未验证；经济 5 条口径 `unverified` | “经济与 vanilla 一致” |
| 捕获回放（A2/A4）验证了某局面单步分数一致（附证据路径） | “捕获回放 = 真游戏终验” |

**等级**：L0 未对齐（当前）→ L1 A2 分数对齐 → L2 A2+A3 规则子集对齐 → L3 真游戏终验通过。

## 1. A 表 — 真游戏捕获（A2/A3 主证据，0/30）

**前提**：A0 版本锁定完成（`scenarios/v3/MANIFEST.json` 存在）、A1 字段映射通过。
**用法**：一行 = 一个真游戏捕获的决策点；真游戏执行某动作记录得分，引擎重放同一动作比对。

| 列 | 内容 |
|---|---|
| `capture_id` | `cap-YYYYMMDD-NNN`，与 `scenarios/v3/*.jsonl` 一致 |
| 版本 | 五元组（game/build/lovely/smods/balatrobot）统一写 MANIFEST 版本号，不写自由文本 |
| 牌组/赌注 | 固定 `RED / WHITE`，其它值该行作废 |
| 手牌 / Jokers | 8 张稳定 id（`c7h`）；Joker 按槽位顺序；带 edition/seal/enhancement 的不入表（A3 排除项） |
| 出牌 | 合法动作（`play:c3h,c7s` / `discard:c5d`），绑定稳定 id，不以下标为主键 |
| 真游戏分数 / 引擎分数 | 同一动作单步得分；相等才可写 `✅` |
| 证据路径 | `evidence/W3/align/<capture_id>.json`（脱敏；不放存档/截图，L8） |

**配额（30 行）**：无 Joker 6 / 单 Joker 8 / 双 Joker 10 / 含 xMult 4 / 多弃牌 2。
**填写规则**：① 无 `capture_id`+证据路径的行只能是 `PENDING`；② `是否一致` 只许 `✅/❌/PENDING`，写 `❌` 必须在 §4 归因；③ 同行不得混版本/混牌组；④ 含 Boss 效果/消耗牌/增强/商店要素的局面不入 A 表。

## 2. B 表 — save/load 反事实回放（A4 主证据，0/30）

**用法**：在 A 表锚点 `save` → `load` → 执行**与锚点不同的合法动作** → 用真游戏得分验证“同一局面不同选择”的对照成立，避免 oracle 靠引擎自证。

| 列 | 内容 |
|---|---|
| `variant_id` / 锚点 `capture_id` | `var-…` / `cap-…` |
| 变体动作 | 当前状态下合法且与锚点不同 |
| 真游戏分数 / 引擎分数 / 是否一致 | 同 A 表口径 |
| `save` 路径 / 证据路径 | 只记**脱敏占位**（`.jkr` 不入库，L8）；`evidence/W3/align/` |

**填写规则**：① 变体必须与锚点不同；② `load` 失败写 `❌` 并说明，不许“重跑凑一致”；③ B 表通过 ≠ 覆盖 218 个动作，`oracle.exact: true` 只在全动作验证时成立。

## 3. A0–A4 检查清单（📋 全部未勾选）

> 全勾选才可进入 §5 签核；任一未勾 → 等级保持 L0。

- **A0 版本锁定**：`MANIFEST.json` 记录 game/build/deck/stake/lovely/smods/balatrobot；同批不跨版本。
- **A1 状态映射**：`gamestate` ↔ `GameState` 八类字段（手牌/牌堆/ Joker/盲注/目标/出牌/弃牌/阶段）逐字段 diff；动作绑定稳定 id。
- **A2 单步分数**：A 表 ≥30 行且覆盖局面上 `engine_score == real_score`；不一致行归因或入 `rejected`。
- **A3 规则子集**：9 牌型基础分、计分牌筛选、8 Joker 数值与条件有来源+金样；未实现规则在 `RULES_VERSION.excluded`；**经济口径 5 条**（利息顺序/售价区间/商店权重/reroll 曲线/卖出后回池）逐条实测。
- **A4 场景来源**：每个局面有 `origin` + `capture_id`；B 表 ≥30 行；无证据局面进 `rejected` 并写原因。

## 4. 差异归因（任何 `❌` 必须落到 D1–D7）

| # | 类别 | 典型表现 |
|---:|---|---|
| D1 | 牌型分类与优先级（A 作低/作高、同花/顺子边界） | 引擎判 Pair、真游戏判 Two Pair |
| D2 | 牌型基础 Chips×Mult（等级 1） | 引擎少一段基础分，或倍率表不同 |
| D3 | 计分牌筛选 | 引擎对每张打出的牌计点数码；真游戏只计参与牌型的牌 |
| D4 | 牌面筹码值 | A=11 / J Q K=10 / 其余面值不一致 |
| D5 | Joker 触发条件 | “含对子”未判，或对“含对子或更大”理解不同 |
| D6 | Joker 效果类型与槽位顺序 | +Mult 当 ×Mult；换序结果颠倒 |
| D7 | 取整时机与调度语义 | 中间取整；把自定义 `before/individual` 当 SMODS context |

## 5. 签核模板（📋 未签核；空着就是当前状态）

| 字段 | 值 |
|---|---|
| 签核日期 / 游戏版本 / 三件套版本 | `PENDING` |
| `scenarios/v3/MANIFEST.json` | `PENDING`（未创建） |
| A0 / A1 / A2 / A3 / A4 | `📋 未通过`；A2、A4 均为 `0 / 30` |
| 未解决差异（D1–D7）/ `rejected` 清单 | `PENDING` |
| **对齐等级结论** | **L0（未对齐）** |
| 允许修改 `alignment_level` / `fidelity_status` | ❌ **否 —— 未签核** |

签核人：`PENDING` ｜ 复核人：`PENDING` ｜ 证据索引：`evidence/W3/align/`（📋 未创建）

## 6. 两条必须区分的结论

| 项 | 捕获回放（A2/A4） | 真游戏终验（W5） |
|---|---|---|
| 回答的问题 | 引擎这一步分数与真游戏同一步是否一致？ | Agent 在真游戏里能不能打好？失败属于哪类？ |
| 证据 | A/B 表 + `evidence/W3/align/*.json` | `runs/w5-real/*` + 终验报告 |
| 允许的结论 | “覆盖局面上单步分数一致（n=…）” | “完成 n=12 描述性终验” |
| 不能推出 | 完整规则一致、Agent 能力、统计显著 | —— |

**改状态的唯一合法路径**：填满 A/B 表 → 勾选 A0–A4 → 完成 D1–D7 归因（未解决项进 `rejected`）→ 填 §5 → 才可同步改 `RULES_VERSION`、`docs/implementation/`、README、AGENTS、07。缺一步即越线，不允许“先改状态、后补证据”。

## 附录 — 历史辅助证据（v2.x 遗留，不作门槛）

- **20 例人工单手对拍（0/20 PENDING）**：字段 = 分层/手牌/Jokers/出牌/游戏分/引擎分/是否一致/证据版本；只作快速回归，覆盖不了 218 个动作。
- **5 例第三方计算器抽检（0/5 PENDING）**：EFHIII 计算器（MIT，不集成），仅辅助交叉核对。
- 早期 v2.x 的 6 项阻塞项已并入 D2/D3/D5/D6/D7；完整旧表在 git 历史（提交 `c65fb9b` 前后）。

**参考**：[07 对齐契约](../../plan/详细版/07-真实游戏接入与终验.md) §3/§7 · balatrobot API <https://coder.github.io/balatrobot/latest/api/> · SMODS 计算函数 <https://docs.smods.dev/> · Balatro Wiki（只取事实）<https://balatrowiki.org/>
