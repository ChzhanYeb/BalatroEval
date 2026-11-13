# BalatroEval Joker 语义台账（v3.0）

> 本文为中文版（W2 v2.1 历史版见提交 `c65fb9b`）。
> 版本：v3.0-2026-11-13 ｜ 依据：`plan/详细版/07-真实游戏接入与终验.md` §7.2
> 关联：`bench/jokers.py`（当前实现）、`docs/engine-fidelity.md`（对齐台账）、`scenarios/RULES_VERSION`

---

## 0. 一句话结论

**当前 `bench/jokers.py` 里的 8 个 Joker 是 L0 合成测试夹具（`jc_*` / `jm_*` / `jx_*`），不是原版 Joker，不得进入训练集或主表。** v3.0 的 vanilla 目录（§2）是 W3 的实现目标，仍全部 📋 未实现、未实测。

| 目录 | 身份 | 当前状态 | 允许用途 | 禁止用途 |
|---|---|---|---|---|
| 合成夹具（§4 附录） | 工程默认值 | ✅ 已实现（L0） | 单元测试、分派/顺序回归、日志验证 | 训练集、主表、任何“原版 Joker”表述 |
| vanilla 目录（§2） | 具名原版 Joker | 📋 未实现 | W3 实现目标与验收清单 | 声称“已实现/已对齐” |

> **替换铁律**：只有在 (a) 数值与触发条件有来源链接、(b) 有金样测试或真游戏实测、(c) 已写入 `docs/engine-fidelity.md` A 表之后，才允许把某个 vanilla Joker 从 📋 改为 ✅。仅“Wiki 上写着”不构成实现完成。

---

## 1. 术语与边界

- **区域（area）**：本实现自带 `G.jokers` 标签；vanilla/SMODS 的区域语义更细（`G.jokers` / `G.play` / `G.hand` 等），**不要假定一一对应**。
- **阶段（phase）**：本实现自带 `before` / `individual` 标签；SMODS 有 `before`、`initial_scoring_step`、`main_scoring`、`individual`、`repetition` 等上下文，语义并不等同（见 §3）。
- **槽位顺序**：Joker 从左到右依次应用，顺序敏感（W2 自定义子集示例，非 vanilla 数值：`+4Mult → x1.5` = 126，`x1.5 → +4Mult` = 98，基于 7♥7♦）。vanilla 是否同样按槽位顺序、以及各类效果的先后分组，**仍需实测验证**。
- **“含对子 / 含三条”**：vanilla 的条件判断以“打出的牌是否构成某牌型或其超集”为准（例如 Two Pair、Full House 通常都含 Pair），具体边界必须以真游戏实测确认，📋 待验证。

---

## 2. v3.0 vanilla Joker 目录（8 个，📋 全部未实现）

> 数值与条件来自 `balatrowiki.org` 的**事实性数值**（名称 / 数值 / 条件），描述为本项目自写；不搬运 Wiki 文本（CC BY-NC-SA，见 [data-sources.md](data-sources.md)）。
> `待实现` 列含义：📋 = 未实现；⏳ = 实现中；✅ = 已实现且有 A 表实测行（当前无 ✅）。

| # | Joker | 效果 | 触发条件（vanilla 事实，待实测确认） | 效果类型 | 来源 | 待实现 |
|---:|---|---|---|---|---|---|
| 1 | **Joker** | +4 Mult | 无条件（始终生效） | add_mult | https://balatrowiki.org/w/Joker | 📋 |
| 2 | **Jolly Joker** | +8 Mult | 打出的牌含对子（Pair 或含对子的更大牌型，边界待实测） | add_mult | https://balatrowiki.org/w/Jolly_Joker | 📋 |
| 3 | **Zany Joker** | +12 Mult | 打出的牌含三条 | add_mult | https://balatrowiki.org/w/Zany_Joker | 📋 |
| 4 | **Sly Joker** | +50 Chips | 打出的牌含对子（同 #2 的边界问题） | add_chips | https://balatrowiki.org/w/Sly_Joker | 📋 |
| 5 | **Wily Joker** | +100 Chips | 打出的牌含三条 | add_chips | https://balatrowiki.org/w/Wily_Joker | 📋 |
| 6 | **Half Joker** | +20 Mult | 打出的牌 ≤3 张 | add_mult | https://balatrowiki.org/w/Half_Joker | 📋 |
| 7 | **The Duo** | ×2 Mult | 打出的牌含对子 | mul_mult | https://balatrowiki.org/w/The_Duo | 📋 |
| 8 | **The Trio** | ×3 Mult | 打出的牌含三条 | mul_mult | https://balatrowiki.org/w/The_Trio | 📋 |

### 2.1 实现时需要的字段（映射到 `bench/jokers.py`）

| 字段 | 含义 | 本实现现状 | W3 需新增 |
|---|---|---|---|
| `jid` | 稳定身份 | `jc_*` / `jm_*` / `jx_*` | 具名 id（如 `joker`、`jolly_joker`），与合成夹具**分开命名空间** |
| `kind` | 效果类型 | `add_chips` / `add_mult` / `mul_mult` | 同左（够用） |
| `value` | 数值 | 合成默认值 | +4/+8/+12/+50/+100/+20/×200/×300 |
| `condition` | 触发条件 | 当前无（无条件生效） | **新增**：无条件 / 含对子 / 含三条 / 打出张数 ≤3 |
| `area` / `phase` | 区域与阶段 | 自定义 `G.jokers` / `before`·`individual` | 保留自定义标签，但**不得**声称等价 SMODS 上下文 |

> `condition` 是本轮最关键的缺口：8 个 vanilla Joker 里有 6 个带条件，而当前夹具全部无条件生效。新增 `condition` 时按 AGENTS.md 的红线**两处登记**（`PHASE_BY_KIND` + `EFFECT_DISPATCH`），并补条件不满足时不触发的测试。

### 2.2 条件评估所需的输入

条件判断需要“本次打出的牌构成了哪些牌型”的信息。当前 `scoring.py` 已有牌型识别结果，但只保留单一 `hand_type`；判断“含对子 / 含三条”需要**牌型包含关系**（`contains_pair`、`contains_three_of_a_kind`）或等价的可枚举判定。📋 这是 W3 的实现任务，不在 W2 范围内。

---

## 3. 分派契约说明（当前实现 vs vanilla）

### 3.1 当前实现的分派契约（L0，已实现并测试）

- 扑克牌的点数筹码以 `G.play × individual` 元数据的形式产出。
- 每张 Joker 都按稳定的、从左到右的槽位顺序被访问。
- `add_chips` 与 `add_mult` 使用自定义阶段标签 `before`；`mul_mult` 使用自定义阶段标签 `individual`。
- 本实现按**槽位顺序**应用效果，因此 `+Mult` 与 `xMult` 的先后可以改变结果。区域／阶段标签会被记录进 trace，但它们尚不是对完整 SMODS 调度器的模拟。
- 精确算术使用 `fractions.Fraction`；只有最终分数会被向下取整。

### 3.2 与来源的对应关系（为什么不能照 Wiki 直接实现）

SMODS 文档区分了 `before`、`initial_scoring_step`、`main_scoring`、`individual`、`repetition` 等上下文。文档指出：从 `context.before` 返回的筹码／倍率**不会**被计入分数，而 `initial_scoring_step` 与 `main_scoring` 具有特定的计分职责。因此，把 `before` 当作通用的计分修正阶段，**并不能证明**与原版行为等价。本实现选择显式标注自己的契约，而不是声称存在一一对应关系。

### 3.3 vanilla 触发顺序必须实测（📋 待验证）

> **规则：vanilla 的触发顺序、效果分组与上下文归属，不可仅凭 Wiki 文本断言。**

必须通过真游戏捕获/回放（A2/A4）确认的至少 4 项：

1. **槽位顺序**：多个 Joker 同时满足条件时，是否严格按从左到右应用；`+Mult` 与 `×Mult` 是否按槽位混排而非分组。
2. **条件求值时机**：条件（含对子/含三条/张数≤3）是在出牌时判定，还是在计分过程中判定；是否会因计分牌筛选而变化。
3. **与牌型基础分的先后**：vanilla 牌型基础 Chips×Mult 与 Joker 效果的应用次序（基础分先结算，再逐个 Joker）。
4. **取整时机**：`×Mult` 中间结果是否取整、在何处取整（vanilla 通常中间不取整，末尾取整；需实测）。

建议的实测最小集（📋）：

| 实测项 | 局面 | 期望能区分的差异 |
|---|---|---|
| 单个 Joker 无歧义 | 无 Joker 对照 + `Joker`(+4 Mult) | 基础分是否正确、+4 是否生效 |
| 条件命中 / 不命中 | `Jolly Joker` + 对子 vs 高牌 | 条件是否真的在判 |
| 顺序敏感 | `Joker`(+4) + `The Duo`(×2) 换序 | 是否按槽位顺序而非分组 |
| 张数条件 | `Half Joker` + 3 张 vs 4 张 | 张数阈值边界 |
| 加 Chips 与加 Mult | `Sly Joker`(+50C) + `Zany Joker`(+12M) | chips×mult 的结算次序 |

---

## 4. 附录 — W2 v2.1 合成夹具目录（历史 / L0 测试夹具）

> **地位：L0 测试夹具，不得进入训练集或主表。** v2.1 规范只给了“八种通用确定性效果”，没给原版名字与数值。为了让引擎在**不编造**与原版卡牌虚假映射的前提下可运行，才使用下列合成夹具。
> W3 起应与 vanilla 目录**分开命名**（建议 `synthetic_*` 前缀或迁到 `tests/fixtures/`），避免下游把夹具误当 vanilla 卡。

| ID | 种类 | 数值 | 区域标签 | 阶段标签 | 作用对象 | 是否对槽位顺序敏感？ | 证据／状态 |
|---|---|---|---|---|---|---|---|
| `jc_flat_chips_10` | add_chips | +10 Chips | `G.jokers` | `before` | 筹码累加器 | 否（相对其它加筹码效果） | 合成夹具；不是原版 Joker |
| `jc_flat_chips_20` | add_chips | +20 Chips | `G.jokers` | `before` | 筹码累加器 | 否（相对其它加筹码效果） | 合成夹具；不是原版 Joker |
| `jc_flat_chips_30` | add_chips | +30 Chips | `G.jokers` | `before` | 筹码累加器 | 否（相对其它加筹码效果） | 合成夹具；不是原版 Joker |
| `jm_add_mult_2` | add_mult | +2 Mult | `G.jokers` | `before` | 当前倍率 | 是，相对于 xMult | 合成夹具；不是原版 Joker |
| `jm_add_mult_4` | add_mult | +4 Mult | `G.jokers` | `before` | 当前倍率 | 是，相对于 xMult | 合成夹具；不是原版 Joker |
| `jm_add_mult_6` | add_mult | +6 Mult | `G.jokers` | `before` | 当前倍率 | 是，相对于 xMult | 合成夹具；不是原版 Joker |
| `jx_mul_mult_150` | mul_mult | x1.5 | `G.jokers` | `individual` | 当前倍率 | 是，相对于 +Mult | 合成夹具；不是原版 Joker |
| `jx_mul_mult_200` | mul_mult | x2.0 | `G.jokers` | `individual` | 当前倍率 | 是，相对于 +Mult | 合成夹具；不是原版 Joker |

> 合成夹具的存在价值：验证“效果是否被调用 / 顺序是否符合本项目定义 / 组合是否可预测 / 日志是否记录触发过程”。它不验证任何原版语义。

---

## 5. 来源与许可边界

| 来源 | 许可 | 用法 | 边界 |
|---|---|---|---|
| https://balatrowiki.org/w/Joker 等 8 个页面 | CC BY-NC-SA 3.0 | 只取**名称 / 数值 / 条件**等不可版权事实 | 不搬运描述文本、不复制表格、不贴图片 |
| https://docs.smods.dev/（Calculate Functions） | GPL-3.0（文档） | 理解上下文/区域概念 | 不复制文档文本；不引入 GPL 代码 |
| https://github.com/DivvyCr/Balatro-Simulation | GPL-3.0 | 借鉴 effect 分派设计 | 不复制代码 |
| 真游戏捕获（balatrobot） | 游戏为商业软件 | W3 实测触发顺序与数值 | 游戏文件/存档/截图不入库（L8） |

参考：

- https://docs.smods.dev/API%20Documentation/Calculate-Functions/
- https://github.com/DivvyCr/Balatro-Simulation
- `plan/详细版/07-真实游戏接入与终验.md` §4、§7.2
