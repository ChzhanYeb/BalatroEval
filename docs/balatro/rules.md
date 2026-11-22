# vanilla Balatro 规则机制事实台账

> **适用范围：vanilla Balatro 1.0.1o（PC/Steam）；Wiki 抓取日期 2026-11-15，Wiki 可能已含后续版本内容，与 1.0.1o 冲突处在文中标注 ⏳ 待真游戏核对。**
>
> 用途：把原版（vanilla）的**机制与数值事实**整理成台账，作为 W3 把 `bench/` 引擎对齐到 1.0.1o 的**目标值**。 \
> **边界（红线）**：本文只描述 vanilla 事实，**不评估、不声称** `bench/` 已对齐/已验证。`bench/` 现状与差异见 [engine-gap.md](engine-gap.md)；对齐等级与证据见 [../engine-fidelity.md](../engine-fidelity.md)。
> 版本：2026-11-15 ｜ 状态：📋 事实台账（✅ 已核 / △ 仅元数据 / ⏳ 未核实）
> 合规：数据取自 `balatrowiki.org`（**CC BY-NC-SA 3.0**）。按 [../data-sources.md](../data-sources.md) §5 红线（L7–L9）：**只提取不可版权的事实数值（名称/数字/条件/表格数值），全部描述用中文自行重写，未逐句搬运 Wiki 文本，未贴图**。

---

## 0. 范围、版本与证据约定

### 0.1 本文覆盖什么

| 覆盖 | 不含（本文不写） |
|---|---|
| 一局结构（run/底注/盲注/回合/商店）、资源常量、算分顺序、牌型与等级、经济、商店、卡牌改造、盲注与底注数值、Tag、模式与牌组 | Joker 逐个效果（见 [../joker-semantics.md](../joker-semantics.md)）、Tarot/Spectral 逐张效果、成就、解锁条件细节、UI 操作 |
| 数值口径：**vanilla 1.0.1o 的"事实值"** | 社区 mod、其它版本（移动端/主机端差异）、demo 版本数值 |

### 0.2 证据等级

| 标记 | 含义 | 判定标准 |
|---|---|---|
| ✅ | **已核** | 本次实际 `web_fetch` 打开的页面明确给出该数值/规则 |
| △ | **仅元数据** | 数值来自页面中的模板/数据模块/汇总表，或由页面事实直接推导（推导过程在文中写明） |
| ⏳ | **未核实** | 未取得来源页面、页面缺失（404）、或与 1.0.1o 可能冲突；**不得当作目标值落地，必须先真游戏核对** |

### 0.3 抓取方法说明（供复核）

- `https://balatrowiki.org/w/<Page>?action=raw` 返回 **wikitext 全文**，紧凑但**模板不展开**（如 `{{Ante Table}}`、`{{Modifier Table|Enhancements}}`、`{{Tag Table}}`）。适合取正文与内联表格。
- `https://balatrowiki.org/w/<Page>`（渲染页）会把模板展开成表格，适合取**模板生成的表**；代价是夹带导航与页脚。
- 因此本文对同一数据可能同时引用 raw 与渲染页：**数值以实际展开后的表为准**，来源清单逐条登记。

### 0.4 版本冲突风险（已知）

| 风险点 | 说明 | 处理 |
|---|---|---|
| Wiki 编辑时间晚于 1.0.1o | 部分页面最后编辑于 2026-10-09 / 2026-11-15（如 Stakes、Tags），晚于 1.0.1o 发布 | 与 1.0.1o 可能不一致处标 ⏳ |
| 页面含后续平台内容 | 如 Switch 2 版（2026-02-25）、`naneinf` 溢出讨论 | 只取与 1.0.1o 机制相关事实，平台差异不入台账 |
| 数值可能被后续补丁改动 | 页面写了 Update history（如 1.0.1f 改 Investment Tag 为 $25） | 以"当前页面值"为准，并保留 ⏳ 复核提示 |

### 0.5 术语约定

中文优先、首次出现给英文原名，全文用词统一（完整对照见 §12）：`Chips` = 筹码、`Mult` = 倍率、`xMult` = 乘倍率（写作 ×倍率）。

> 来源：[Balatro Wiki 首页导航与页面 footer 许可声明](https://balatrowiki.org/w/Tags) ✅（2026-11-15，页面 footer 明示 CC BY-NC-SA 3.0）

---

## 1. 一局结构：run → 底注 → 盲注 → 回合 → 商店

### 1.1 层级定义

| 层级 | 英文 | 数量/边界 | 说明 |
|---|---|---|---|
| 一局 | run | 1 次开始→胜/败 | 选牌组 + 赌注后开始；中途可退出续玩 |
| 底注 | Ante | 标准 8 级（1–8） | 每级由 3 个盲注组成；击败首领盲注后底注 +1 |
| 盲注 | Blind | 每底注 3 个 | 小盲注 / 大盲注 / 首领盲注（随机） |
| 决战盲注 | Showdown Blind | 底注 8，及 Endless 的 16/24/32 | 首领盲注的特例，仅出现在 8 的倍数底注 |
| 回合 | Round | 每个盲注 1 个回合 | 一个回合含 4 个阶段（见 1.2） |

> 30 个盲注总数 = 2 个可跳过盲注 + 23 个常规首领盲注 + 5 个决战盲注（页面图注口径）✅

### 1.2 回合的四个阶段

| 顺序 | 阶段（英文） | 玩家可做什么 | 退出条件 |
|---:|---|---|---|
| 0 | 盲注选择（Blind Select） | 打小/大盲注，或**跳过**换 Tag；首领盲注**不可跳过** | 选定盲注 |
| 1 | 盲注（Blind / Round） | 出牌 1–5 张、弃牌 1–5 张、用消耗品 | 累计分数 ≥ 目标分；或资源耗尽判负 |
| 2 | 结算（Cash Out） | 领取盲注奖励 + 剩余手牌 + 利息 + Joker 结算 | 点结算 |
| 3 | 商店（The Shop） | 买 Joker/消耗品/补充包/Voucher，可重掷 | 离开商店 → 回到阶段 0 |

- 一局开始时回合序号为 0，停在**盲注选择**；进入盲注后记为回合 1 ✅
- 击败**首领盲注**会在**进入结算阶段时**把底注 +1 ✅
- 商店结束后回到盲注选择，循环 ✅

### 1.3 状态机（文字版）

```
选牌组+赌注
   │
   ▼
[底注 N: 1..8] ──> 盲注选择 ──(跳过小/大盲注 → 获得 Tag)──────┐
                        │                                  │
                        ▼                                  │
                  盲注回合（出牌/弃牌）                      │
                        │ 达标                             │
                        ▼                                  │
                    结算 ──> 商店 ──(离开)──────────────────┘
                        │
                        └─(击败的是首领盲注) → 底注 N+1
底注 8 击败决战盲注 → 通关 → 可选 Endless（底注 9 起，16/24/32 再遇决战盲注）
回合中资源耗尽仍不达标 → 失败（例外：Mr. Bones）
```

### 1.4 胜利与失败

| 情形 | 判定 | 证据 |
|---|---|---|
| 通关 | 完成底注 8 并打赢**决战盲注** | ✅ |
| 继续玩 | 通关后可选 Endless Mode，从底注 9 起无限爬升 | ✅ |
| 失败 | 回合内手牌用完/无法继续，且总分未达目标 | ✅ |
| 唯一"免死" | `Mr. Bones`：达到目标分的 25% 时可避免整局失败 | ✅ |
| 数值天花板 | 底注 39 目标分超过双精度上限（≈1.8e308）→ 分数变 NaN（显示 `naneinf`），无法再通关 | ✅（1.0.1o 行为，页面明确） |

### 1.5 打断与续玩

- 游戏自动保存当前 run，可在主界面 Continue 页签继续 ✅
- 续玩时盲注图标/要求分**可能短暂消失**（页面记为疑似 bug），可通过 Run Info 查看 ✅

> 来源：[Gameplay loop](https://balatrowiki.org/w/Gameplay_loop?action=raw) ✅、[Blinds and Antes](https://balatrowiki.org/w/Blinds_and_Antes) ✅（2026-11-15）

---

## 2. 牌与牌组构成

### 2.1 基础牌组

| 项 | 值 | 证据 |
|---|---|---|
| 基础牌数 | 52（4 花色 × 13 点数） | ✅ |
| 点数集合 | A, 2–10, J, Q, K | ✅ |
| 花色 | ♠ 黑桃 / ♥ 红桃 / ♦ 方块 / ♣ 梅花 | ✅ |
| 单张牌可带改造 | 1 个增强（Enhancement）+ 1 个版本（Edition）+ 1 个封蜡（Seal） | ✅ |
| Red Deck 内容 | 标准 52 张（无额外牌） | ✅ |

### 2.2 点数 → 筹码（未改造时）

| 点数 | 计分筹码 | 说明 | 证据 |
|---|---:|---|---|
| A | 11 | 顺子中可当高（A K Q J 10）或低（A 2 3 4 5），但**不能同时**；A 永远按"大"给 11 筹码 | ✅ |
| 2–10 | = 点数本身 | 如 7 给 7 筹码 | ✅ |
| J / Q / K | 10 | 三者为"面牌（face cards）"，各给 10 筹码 | ✅ |

- 牌型识别时"K A 2 3 4"**不是**合法顺子（不能跨头接尾）✅
- 社区简称：三条/四条/五条常写作 3oak/4oak/5oak ✅（仅术语，无机制含义）

### 2.3 牌型优先级（覆盖关系）

- 多个牌型同时成立时，取**等级更高**的那个牌型计分，与手牌等级、分数高低无关 ✅
  - 例：9 9 9 9 2 且全为方块 → 判为**四条**，不判同花 ✅
- "包含（contains）"语义：四条不视为包含两对；五条/同花五条不包含葫芦；四条含同花时可触发"同花类" Joker ✅（影响 Joker 条件判定，不影响基础分）
- 出牌顺序不影响牌型判定 ✅

### 2.4 牌组列表（15 个）

见 §11.2（牌组影响起始资源/经济，不改基础 52 张构成）。

> 来源：[Card Ranks](https://balatrowiki.org/w/Card_Ranks?action=raw) ✅、[Chips](https://balatrowiki.org/w/Chips?action=raw) ✅、[Poker hands](https://balatrowiki.org/w/Poker_hands?action=raw) ✅、[Red Deck](https://balatrowiki.org/w/Red_Deck?action=raw) ✅、[Card modifiers](https://balatrowiki.org/w/Card_modifiers) ✅（2026-11-15）

---

## 3. 出牌 / 弃牌 / 手牌 / 资源常量

### 3.1 资源常量总表（W3 目标值）

| 常量 | 基础值 | 可变来源（例） | 证据 |
|---|---:|---|---|
| 每回合出牌次数（hand） | **4** | Blue Deck +1；Black Deck −1；Blue Stake 只减弃牌不减手；`Burglar` +3；`Grabber`/`Nacho Tong` 各 +1；`The Needle` 强制 =1 | ✅ |
| 每回合弃牌次数（discard） | **3** | Red Deck +1；Blue Stake −1；`Drunkard` +1；`Merry Andy` +3；`Wasteful`/`Recyclomancy` 各 +1；`The Water` 强制 =0 | ✅ |
| 手牌上限（hand size） | **8** | Painted Deck +2；`Paint Brush`/`Palette` 各 +1；`Juggler` +1；`The Manacle` −1 | ✅ |
| Joker 槽位 | **5** | Black Deck +1；Painted Deck −1；`Antimatter` +1；Negative 版本 +1 | ✅ |
| 消耗品槽位 | **2** | `Crystal Ball` +1；Nebula Deck −1 | ✅ |
| 单次出牌张数上限 | **5** | Four Fingers 可放宽"所需张数"（不放宽上限） | ✅ |
| 单次弃牌张数上限 | **5** | — | ✅ |
| 每底注盲注数 | **3** | — | ✅ |
| 通关所需底注数 | **8** | — | ✅ |

### 3.2 出牌与弃牌的规则要点

| 规则 | 内容 | 证据 |
|---|---|---|
| 出牌 | 从手牌选 1–5 张打出，消耗 1 次 hand，判型后按 §4 计分 | ✅ |
| 弃牌 | 从手牌选 1–5 张弃掉，消耗 1 次 discard，随后补牌 | ✅ |
| 抽牌 | 出牌/弃牌后，若手牌数 < 手牌上限，抽到上限；牌堆不足则抽完为止 | ✅ |
| 手牌上限不是硬顶 | 特定效果可让手牌**超过**上限（如 `DNA`、`Certificate`、`Cryptid` 等） | ✅ |
| 手牌上限 ≤ 0 | 进入盲注即**立即失败**（`Mr. Bones` 也救不了） | ✅ |
| 出牌即补牌时序 | 打出的牌先离开手牌，随后才补牌到上限（页面只写"出/弃后抽到上限"，先后顺序属直接推论 △） | ✅/△ |
| 每回合出牌 1 次 = 一手 | 一次出牌动作只计一手；一回合内按 hand 次数可出多手 | ✅ |
| 结算比较 | 回合内**各手分数累加**，与盲注目标分比较，≥ 即达标 | ✅ |

### 3.3 牌型预览与暗牌

- 选牌阶段左侧计分板会**预览判型名**（Run Info 也可查当前等级/基础分）✅
- 遇到会把手中牌变**暗牌**的首领盲注（如 The House / The Wheel / The Fish / The Mark）时，预览显示 `???`，打出后才知道 ✅
- 暗牌（face-down）：牌面信息不可见，但**仍参与计分**（以真游戏表现为准；⏳ 具体计分细节待 A2 核对）

### 3.4 与 bench 相关的边界提示

- 当前 `bench/` 的 `HANDS_PER_BLIND=4` / `DISCARDS_PER_BLIND=2` / 3 个 Joker 槽位均**不是** vanilla 值；本文 §3.1 是 W3 目标值，不构成"已对齐"证据。差异见 [engine-gap.md](engine-gap.md) §1 第 3–5 行。

> 来源：[Hands](https://balatrowiki.org/w/Hands?action=raw) ✅、[Discards](https://balatrowiki.org/w/Discards?action=raw) ✅、[Hand size](https://balatrowiki.org/w/Hand_size?action=raw) ✅、[Jokers](https://balatrowiki.org/w/Jokers?action=raw) ✅（"Most runs will begin with 5 empty Joker slots"）、[Consumables](https://balatrowiki.org/w/Consumables?action=raw) ✅（"2 consumable slots are available initially"）、[Gameplay loop](https://balatrowiki.org/w/Gameplay_loop?action=raw) ✅（"select up to five cards"）、[Score](https://balatrowiki.org/w/Score?action=raw) ✅（2026-11-15）

---

## 4. 算分机制

### 4.1 总分公式

| 层级 | 公式 | 证据 |
|---|---|---|
| 单张牌贡献 | 见 4.4 顺序；基础为"该牌筹码" | ✅ |
| 单次出牌得分 | `score_hand = Chips × Mult`（计分结束时的最终 Chips 与 Mult 相乘） | ✅ |
| 回合总分 | 该回合各手 `score_hand` 之和 | ✅ |
| 达标 | 回合总分 ≥ 盲注目标分 | ✅ |
| 取整 | **⏳ 未核实**：Wiki 的 Score 页只写"相乘"，未写取整方式。仓库内 [engine-gap.md](engine-gap.md) §2 按 `floor(chips × mult)` 记录（内部口径），但**本次抓取未能取得 Wiki 明文**，W3 必须以真游戏 A2 单步分数核对 | ⏳ |

### 4.2 哪些牌参与计分（计分牌筛选）

| 牌型 | 计分牌数 | 说明 | 证据 |
|---|---:|---|---|
| 高牌 High Card | **1** | 只计点数最高的那张；其余最多 4 张不计分 | ✅ |
| 对子 Pair | **2** | 同点数的 2 张；可带最多 3 张不计分牌 | ✅ |
| 两对 Two Pair | **4** | 两组不同点数的对子；可带 1 张不计分牌 | ✅ |
| 三条 Three of a Kind | **3** | 同点数 3 张；可带最多 2 张不计分牌 | ✅ |
| 顺子 Straight | **5** | 五张连号 | ✅ |
| 同花 Flush | **5** | 五张同花色 | ✅ |
| 葫芦 Full House | **5** | 三条 + 对子（3+2） | ✅ |
| 四条 Four of a Kind | **4** | 同点数 4 张；可带 1 张不计分牌 | ✅ |
| 同花顺 Straight Flush | **5** | 同花且连号 | ✅ |
| 五条 Five of a Kind（隐藏） | 5 | 同点数 5 张（标准 52 张无法自然达成） | △ 由"5 张同点数"直接推导 |
| 同花葫芦 Flush House（隐藏） | 5 | 三条 + 对子，且 5 张同花色 | △ 同上 |
| 同花五条 Flush Five（隐藏） | 5 | 5 张同点数同花色 | △ 同上 |
| 王同花顺 Royal Flush | 5 | 显示独立但机制等同同花顺（见 §5.3） | ✅ |

**改变筛选的例外**（W3 若实现须单独登记）：

| 来源 | 效果 | 证据 |
|---|---|---|
| `Splash` Joker | 打出的所有牌都计分（无视筛选） | ✅ |
| `Four Fingers` Joker | 顺子/同花/同花顺只需 4 张成立；可做出"含重复点数的顺子"等变体 | ✅ |
| `Shortcut` Joker | 顺子允许间隔 1 个点数 | ✅ |
| Stone Card 增强 | 无点数无花色，+50 筹码；即使被当"额外牌"打出也可贡献 | ✅ |

### 4.3 重要推论：加分牌 ≠ 计分牌

- 打超出手牌张数（如 3 张对子 + 2 张废牌）**不会**让废牌贡献筹码，除非有 `Splash` ✅
- 但废牌仍会被**弃入弃牌堆并从牌堆补回**，等价于一次"伪弃牌（pseudo-discard）"✅
- 四条的 1 张 kicker 同理：不计分，仅占位 ✅

### 4.4 结算顺序（关键：顺序敏感）

一手牌的完整激活顺序如下（编号用于代码/日志对齐）：

| 步 | 阶段 | 内容 | 证据 |
|---:|---|---|---|
| 1 | 首领盲注效果 | 如 `The Flint`（基础筹码与倍率减半）、`The Arm`（降低该牌型等级）先结算 | ✅ |
| 2 | "出牌触发"型 Joker | 计分开始前触发（如 `DNA`、`To Do List`、部分"每次出牌成长"类） | ✅ |
| 3 | 打出的牌逐张计分 | **从左到右**；每张牌内部的固定子序：① 基础筹码（含 Bonus 等加筹码）→ ② 卡牌改造（增强 → 封蜡 → 版本）→ ③ "计分触发"型 Joker（同一张牌触发的多个 Joker 按槽位从左到右）→ ④ **重触发** | ✅ |
| 4 | 重触发（Retrigger） | 每次重触发把第 3 步的 ①–④ 整套再跑一遍；多个重触发**叠加**；Red Seal **最先**，随后按槽位从左到右的重触发 Joker | ✅ |
| 5 | 手牌中触发（held in hand） | 手牌**从左到右**检查：Steel 增强 → "持牌触发"型 Joker（如 `Shoot the Moon`、`Baron`）→ 重触发（Red Seal 先，`Mime` 类从左到右） | ✅ |
| 6 | Joker 版本与"独立"Joker | 按槽位**从左到右**：Foil/Holographic 加成 → 独立型 Joker（如 `The Duo`、`Blackboard`）→ 依赖其他 Joker 的（`Baseball Card`）→ Polychrome 加成 | ✅ |
| 7 | 消耗品 | 买了 `Observatory` 时，消耗品区的星球牌给对应牌型 ×1.5 倍率，从左到右 | ✅ |
| 8 | Plasma Deck 平衡 | 若用 Plasma Deck，最后把 Chips 与 Mult 取平均（双向"平衡"） | ✅ |

### 4.5 顺序敏感示例（自算，非 Wiki 原文）

设牌型基础 `10 筹码 × 2 倍率`，另有 `+4 倍率` 与 `×2 倍率` 两个效果：

| 排列 | 计算 | 结果 |
|---|---|---:|
| +4 在 ×2 之前 | `(2 + 4) × 2 = 12` → `10 × 12` | **120** |
| ×2 在 +4 之前 | `(2 × 2) + 4 = 8` → `10 × 8` | **80** |

结论：**加倍率（+Mult）排在乘倍率（xMult）左侧得分更高**；打出的牌与手牌中的排列同理 ✅

### 4.6 重触发的三条硬规则

| 规则 | 内容 | 证据 |
|---|---|---|
| Red Seal 只重触发 1 次 | Red Seal 自身给"再触发 1 次"，但**不会再被** `Mime`/`Hack` 二次重触发 | ✅ |
| 例：Red Seal 的 2 点 | 初始触发 1 次 + `Hack` 重触发 1 次 + Red Seal 再 1 次 = 共 **3 次** | ✅ |
| 重触发会重跑全套 | 包括牌自身筹码、增强、版本、封蜡（Red Seal 除外）与"计分触发"型 Joker | ✅ |
| `Mime` 只重触发"手牌中"的牌 | 因此不重触发牌的筹码与版本（那张牌没被打出计分） | ✅ |

### 4.7 中间是否取整

- **⏳ 未核实**：Wiki 页面未明示"中间步骤是否取整、x1.5 类乘倍率产生小数时如何展示/累积"。
- 已知事实：Steel（×1.5）、Glass（×2）、Polychrome（×1.5）、`Observatory`（×1.5）都会产生非整数倍率，因此"小数倍率参与后续相乘"是必然的；但**是保留小数还是每步截断**必须真游戏核对。
- W3 建议：以 A2（单步分数一致）为准，先把"最终一次取整 + 中间精确有理数"作为**候选假设**（`bench/scoring.py` 当前用 `Fraction` 精确运算，只 floor 一次）并在 `RULES_VERSION` 注明 ⏳。

> 来源：[Guide: Activation Sequence](https://balatrowiki.org/w/Guide:_Activation_Sequence?action=raw) ✅、[Score](https://balatrowiki.org/w/Score?action=raw) ✅、[Chips](https://balatrowiki.org/w/Chips?action=raw) ✅、[Mult](https://balatrowiki.org/w/Mult?action=raw) ✅、[Poker hands](https://balatrowiki.org/w/Poker_hands?action=raw) ✅、[Card modifiers](https://balatrowiki.org/w/Card_modifiers) ✅（2026-11-15）

---

## 5. 牌型与等级

### 5.1 等级 1 基础 Chips × Mult（W3 核心目标值）

| # | 牌型（中） | 英文 | 基础筹码 | 基础倍率 | 计分牌 | 对应星球牌 | 证据 |
|---:|---|---|---:|---:|---:|---|---|
| 1 | 高牌 | High Card | 5 | 1 | 1 | Pluto | ✅ |
| 2 | 对子 | Pair | 10 | 2 | 2 | Mercury | ✅ |
| 3 | 两对 | Two Pair | 20 | 2 | 4 | Uranus | ✅ |
| 4 | 三条 | Three of a Kind | 30 | 3 | 3 | Venus | ✅ |
| 5 | 顺子 | Straight | 30 | 4 | 5 | Saturn | ✅ |
| 6 | 同花 | Flush | 35 | 4 | 5 | Jupiter | ✅ |
| 7 | 葫芦 | Full House | 40 | 4 | 5 | Earth | ✅ |
| 8 | 四条 | Four of a Kind | 60 | 7 | 4 | Mars | ✅ |
| 9 | 同花顺 | Straight Flush | 100 | 8 | 5 | Neptune | ✅ |
| 10 | 五条（隐藏） | Five of a Kind | 120 | 12 | 5 | Planet X | ✅ |
| 11 | 同花葫芦（隐藏） | Flush House | 140 | 14 | 5 | Ceres | ✅ |
| 12 | 同花五条（隐藏） | Flush Five | 160 | 16 | 5 | Eris | ✅ |

> 排序与"难度越高基础分越高"一致：同花顺 100×8 > 四条 60×7 > 葫芦 40×4。

### 5.2 每级升级增量（星球牌单次使用）

| 牌型 | 星球牌 | 每次升级 +筹码 | 每次升级 +倍率 | 证据 |
|---|---|---:|---:|---|
| 高牌 | Pluto | +10 | +1 | ✅ |
| 对子 | Mercury | +15 | +1 | ✅ |
| 两对 | Uranus | +20 | +1 | ✅ |
| 三条 | Venus | +20 | +2 | ✅ |
| 顺子 | Saturn | +30 | +3 | ✅ |
| 同花 | Jupiter | +15 | +2 | ✅ |
| 葫芦 | Earth | +25 | +2 | ✅ |
| 四条 | Mars | +30 | +3 | ✅ |
| 同花顺 | Neptune | +40 | +4 | ✅ |
| 五条 | Planet X | +35 | +3 | ✅ |
| 同花葫芦 | Ceres | +40 | +4 | ✅ |
| 同花五条 | Eris | +50 | +3 | ✅ |

**等级数值的推算口径**：

| 项 | 内容 | 证据 |
|---|---|---|
| 等级公式（候选） | `值(L) = 等级1值 + (L−1) × 每级增量`，筹码与倍率分别累加 | △ 由"基础值 + 每次升级固定增量"直接推导；**Wiki 未取得逐级数值表**（`Hand_levels`/`Poker_Hand_levels` 均 404），故"每级增量恒定"标 ⏳ 待真游戏核对 |
| 等级上限 | **无上限**，可无限升级 | ✅ |
| 等级重置 | 每次新开一局回到等级 1 | ✅ |
| 降级 | `The Arm` 永久降低被打出的牌型等级；等级可降到 1 以下吗 → ⏳ 未核实（页面只说"decrease level"） | △/⏳ |
| 批量升级 | `Black Hole`（Spectral）升级所有牌型（含未解锁的隐藏牌型）；`Orbital` Tag 升 3 级 | ✅ |

### 5.3 Royal Flush（王同花顺）显示特例

| 项 | 内容 | 证据 |
|---|---|---|
| 显示 | 选牌时计分板会显示独立的"Royal Flush" | ✅ |
| 机制 | 其余一切等同同花顺：共用星球牌等级、计入 `Obelisk`/`Supernova` 的"出牌次数"统计、在 `The Eye`/`The Mouth` 中视为同一牌型 | ✅ |
| 星球牌 | **没有**专属星球牌；随同花顺一起升级 | ✅ |

### 5.4 隐藏牌型的出现条件

| 项 | 内容 | 证据 |
|---|---|---|
| 解锁方式 | 只能通过给牌组**加入额外牌**或改造现有牌（消耗品/Joker）打出 | ✅ |
| Run Info 显示 | 未打出前不在列表；打出至少 1 次后才出现 | ✅ |
| 星球牌可得性 | 对应星球牌（Planet X / Ceres / Eris）在**本局内**才可获取 | ✅ |
| 标准 52 张 | 不可能自然达成（13 张/花色，无重复点数） | ✅ |

### 5.5 星球牌总量

| 项 | 值 | 证据 |
|---|---|---|
| 星球牌总数 | **12**（其中 3 张隐藏：Planet X / Ceres / Eris） | ✅ |
| 商店价 | $3 | ✅ |
| 使用后 | 提升对应牌型等级；不消耗手牌 | ✅ |
| `Observatory` Voucher | 消耗品区每张星球牌 → 对应牌型 ×1.5 倍率 | ✅ |

> 来源：[Poker hands](https://balatrowiki.org/w/Poker_hands?action=raw) ✅（基础值 + 星球牌增量表）、[Planet cards](https://balatrowiki.org/w/Planet_cards?action=raw) ✅（12 张、无上限、Royal Flush 无星球牌）、[The Shop](https://balatrowiki.org/w/The_Shop?action=raw) ✅（星球牌 $3）（2026-11-15）

---

## 6. 经济（Money）

### 6.1 结算（Cash Out）构成与顺序

| 顺序 | 项目 | 金额 | 条件/备注 | 证据 |
|---:|---|---|---|---|
| 1 | 盲注奖励 | 小盲注 $3 / 大盲注 $4 / 首领盲注 $5 / 决战盲注 $8 | 被 `Mr. Bones` 救下的盲注**无**奖励；Red Stake 起小盲注**无**奖励 | ✅ |
| 2 | 剩余手牌 | 每剩 1 手 +$1 | Green Deck 改为每剩 1 手 $2；The Omelette / Mad World 不给 | ✅ |
| 3 | Joker 结算类 | 视 Joker 而定（如 `Golden Joker`） | 在"剩余手牌"之后结算 | ✅ |
| 4 | Investment Tag | 击败**首领盲注** +$25 | 被 `Mr. Bones` 救下也照给 | ✅ |
| 5 | 利息 Interest | 每持有 $5 给 $1 | 基础上限 **$5**/回合（即 $25 封顶）；`Seed Money` 提到 $10，`Money Tree` 提到 $20；Green Deck / The Omelette / Mad World 无利息（Green 用"每剩 1 弃 +$1"替代） | ✅ |

### 6.2 起始金钱

| 项 | 金额 | 证据 |
|---|---:|---|
| 多数牌组起始 | $4 | ✅ |
| Yellow Deck 起始 | $14（+$10） | ✅ |
| Rich get Richer（挑战牌组） | $100 | ✅ |
| Golden Needle（挑战牌组） | $10 | ✅ |

### 6.3 赌注（Stake）对经济的影响

| 赌注 | 经济影响 | 证据 |
|---|---|---|
| Red Stake 起 | 小盲注不给奖励金 | ✅ |
| Green Stake 起 | 目标分按底注更快增长（见 §9.1 第 2 列） | ✅ |
| Purple Stake 起 | 目标分进一步增长（见 §9.1 第 3 列） | ✅ |
| Gold Stake | 商店可出现 Rental 小丑（每回合 −$3） | ✅ |

### 6.4 花钱的地方

| 用途 | 金额 | 证据 |
|---|---|---|
| 商店购买 | 见 §7.3 价格表 | ✅ |
| 商店重掷（reroll） | 起始 $5，每次 +$1，进新商店重置 | ✅ |
| 重掷首领盲注 | `Director's Cut` 每底注 1 次；每次 $10；`Retcon` 可无限次 | ✅ |
| 被动扣款 | `The Tooth`（每打出 1 张牌 −$1）、`The Ox`（打出"最常打牌型"→ 金钱归 0）、Rental 贴纸（每回合 −$3）、`Wraith`（造传奇 Joker，金钱归 0） | ✅ |
| Golden Needle 挑战 | 每次弃牌 −$1 | ✅ |

### 6.5 负债与上限

| 项 | 内容 | 证据 |
|---|---|---|
| 最低金钱 | 通常为 $0（不可为负） | ✅ |
| 负债例外 | `Credit Card` Joker 允许欠债至 **−$20** | ✅ |
| 减债 | `Wraith`、`The Ox` 会把金钱**设为 0**（等于清债） | ✅ |
| 翻倍类效果 | `Economy` Tag、`The Hermit` 不会把负债翻倍 | ✅ |

> 来源：[Money](https://balatrowiki.org/w/Money?action=raw) ✅、[Stakes](https://balatrowiki.org/w/Stakes) ✅、[Decks](https://balatrowiki.org/w/Decks) ✅、[The Shop](https://balatrowiki.org/w/The_Shop?action=raw) ✅、[Vouchers](https://balatrowiki.org/w/Vouchers) ✅（2026-11-15）

---

## 7. 商店（The Shop）

### 7.1 布局与补货

| 项 | 内容 | 证据 |
|---|---|---|
| 出现时机 | 每击败一个盲注（小/大/首领）后，结算完进商店 | ✅ |
| 默认槽位 | **2 个随机卡**（多为 Joker，也可 Tarot/Planet；有 `Magic Trick` 可出扑克牌；Ghost Deck 可出 Spectral）+ **2 个补充包** + **1 个 Voucher** | ✅ |
| 首店特例 | 一局**第一次**进商店时，必出 1 个普通 Buffoon 包 | ✅ |
| 重掷范围 | 只重掷"随机卡"（2 张）；**不动**补充包与 Voucher | ✅ |
| 补充包补货 | 进新商店才补 | ✅ |
| Voucher 补货 | 击败首领盲注后才补 | ✅ |
| 随机卡权重 | Joker 20 / Tarot 4 / Planet 4 → 约 71.4% / 14.3% / 14.3% | ✅ |
| Joker 稀有度权重 | Common 70% / Uncommon 25% / Rare 5% | ✅ |
| 槽位扩容 | `Overstock` → 3 张；`Overstock Plus` → 4 张 | ✅ |

### 7.2 重掷成本曲线

| 项 | 值 | 证据 |
|---|---|---|
| 起始价 | $5 | ✅ |
| 每次递增 | +$1 | ✅ |
| 重置时机 | 进入新商店回到 $5 | ✅ |
| `Reroll Surplus` | 每底注起始价 −$2（→ $3） | ✅ |
| `Reroll Glut` | 再 −$2（→ $1） | ✅ |
| `Chaos the Clown` Joker | 本店首次重掷免费 | ✅ |
| `D6` Tag | 下一个商店重掷从 $0 起 | ✅ |

### 7.3 基础价格

| 类别 | 价格 | 证据 |
|---|---|---|
| Joker · Common | $1–6 | ✅ |
| Joker · Uncommon | $4–8 | ✅ |
| Joker · Rare | $7–10 | ✅ |
| Joker · Legendary | $20（商店不可出现） | ✅ |
| 扑克牌 | $1 | ✅ |
| Tarot | $3 | ✅ |
| Planet | $3 | ✅ |
| Spectral | $4 | ✅ |
| 补充包 · 普通 / Jumbo / Mega | $4 / $6 / $8 | ✅ |
| Voucher | $10（`Clearance Sale`/`Liquidation` 也会隐性降低 Voucher 价） | ✅ |

### 7.4 版本（Edition）附加成本

| 版本 | Joker | 消耗品 | 扑克牌 | 证据 |
|---|---:|---|---:|---|
| Foil | +$2 | 不可 | +$2 | ✅ |
| Holographic | +$3 | 不可 | +$3 | ✅ |
| Polychrome | +$5 | 不可 | +$5 | ✅ |
| Negative | +$5 | +$5（仅 `Perkeo` 生成） | 不可 | ✅ |

### 7.5 买价与卖价公式

| 步骤 | 买价（buy cost） | 证据 |
|---:|---|---|
| 1 | 基础价 + 版本附加价 + 通胀（Inflation 挑战每次购买 +$1） | ✅ |
| 2 | 乘折扣系数：`Clearance Sale` → 0.75，`Liquidation` → 0.5 | ✅ |
| 3 | **四舍五入（half down，8.5→8）** | ✅ |
| 4 | 若结果 ≤ $0 则置为 **$1** | ✅ |
| 5 | 再套特殊规则（`Astronomer` 星球牌 $0、`Coupon` Tag 全店 $0、Rental 贴纸强制 $1 等） | ✅ |

| 步骤 | 卖价（sell value） | 证据 |
|---:|---|---|
| 1 | 重算当前买价（应用期间买的折扣/特殊规则） | ✅ |
| 2 | 买价 ÷ 2 | ✅ |
| 3 | **向下取整（floor，3.75→3）** | ✅ |
| 4 | 若 ≤ $0 则置为 $1 | ✅ |
| 5 | 再加 `Egg` / `Gift Card` 的额外卖价（不受折扣影响） | ✅ |

### 7.6 补充包（Booster Packs）

五种、各三档；**开包即离开商店**，选完/跳过回到商店 ✅。

| 类别 | 普通 $4 | Jumbo $6 | Mega $8 | 证据 |
|---|---|---|---|---|
| Arcana（Tarot） | 3 选 1 | 5 选 1 | 5 选 2 | ✅ |
| Celestial（Planet） | 3 选 1 | 5 选 1 | 5 选 2 | ✅ |
| Standard（扑克牌加入牌组） | 3 选 1 | 5 选 1 | 5 选 2 | ✅ |
| Buffoon（Joker） | 2 选 1 | 4 选 1 | 4 选 2 | ✅ |
| Spectral | 2 选 1 | 4 选 1 | 4 选 2 | ✅ |

| 补充包权重（出现概率） | Normal | Jumbo | Mega | 合计 |
|---|---:|---:|---:|---:|
| Standard / Arcana / Celestial（各） | 4（17.84%） | 2（8.92%） | 0.5（2.23%） | 28.99% |
| Buffoon | 1.2（5.35%） | 0.6（2.68%） | 0.15（0.67%） | 8.7% |
| Spectral | 0.6（2.68%） | 0.3（1.34%） | 0.07（0.31%） | 4.33% |

### 7.7 Voucher（32 个 / 16 对）

> 每对由"基础款 + 升级款"组成；只有买过基础款，升级款才可能在后续商店出现；同局不能重复买同一张；每张通常 $10。

| 基础款（效果） | 升级款（效果） | 证据 |
|---|---|---|
| Overstock（+1 商店卡槽） | Overstock Plus（再 +1，且立刻补满空槽） | ✅ |
| Clearance Sale（全店 −25%） | Liquidation（全店 −50%，同时降低已有 Joker 卖价） | ✅ |
| Hone（Foil/Holo/Poly 出现率 ×2） | Glow Up（×4；Poly 实际 ×7 于 Joker） | ✅ |
| Reroll Surplus（重掷 −$2） | Reroll Glut（再 −$2） | ✅ |
| Crystal Ball（+1 消耗品槽） | Omen Globe（Arcana 包内每张牌 20% 换成 Spectral） | ✅ |
| Telescope（Celestial 包必含最常打牌型的星球牌） | Observatory（消耗品区星球牌 → 对应牌型 ×1.5 倍率） | ✅ |
| Grabber（永久 +1 手/回合） | Nacho Tong（再 +1 手/回合） | ✅ |
| Wasteful（永久 +1 弃/回合） | Recyclomancy（再 +1 弃/回合） | ✅ |
| Tarot Merchant（Tarot 出现率 ×2） | Tarot Tycoon（×4） | ✅ |
| Planet Merchant（Planet 出现率 ×2） | Planet Tycoon（×4） | ✅ |
| Seed Money（利息上限 → $10） | Money Tree（利息上限 → $20） | ✅ |
| Blank（无效果） | Antimatter（+1 Joker 槽） | ✅ |
| Magic Trick（商店可卖扑克牌） | Illusion（商店扑克牌可带增强/版本/封蜡；**1.0.1o 有 bug：不出封蜡，且不吃 Hone/Glow Up**） | ✅ |
| Hieroglyph（底注 −1，每回合 −1 手） | Petroglyph（底注 −1，每回合 −1 弃） | ✅ |
| Director's Cut（每底注可重掷 1 次首领盲注，$10/次） | Retcon（无限次重掷首领盲注，$10/次） | ✅ |
| Paint Brush（+1 手牌上限） | Palette（再 +1 手牌上限） | ✅ |

> 来源：[The Shop](https://balatrowiki.org/w/The_Shop?action=raw) ✅、[Booster Packs](https://balatrowiki.org/w/Booster_Packs?action=raw) ✅、[Vouchers](https://balatrowiki.org/w/Vouchers) ✅、[Card modifiers](https://balatrowiki.org/w/Card_modifiers) ✅（版本附加价）（2026-11-15）

---

## 8. 卡牌改造系统（Modifiers）

四类：版本/版式（Edition）、增强（Enhancement）、封蜡（Seal）、贴纸（Sticker）。

| 对象 | 可带 | 证据 |
|---|---|---|
| 扑克牌 | 1 增强 + 1 版本 + 1 封蜡 | ✅ |
| Joker | 1 版本 + 多个贴纸（Sticker） | ✅ |
| 消耗品 | 通常不可；`Perkeo` 可生成 Negative | ✅ |
| Voucher / 补充包 | 永不可 | ✅ |
| 覆盖规则 | 增强与封蜡可被**替换**；版本与贴纸**永久不可覆盖** | ✅ |
| 失效（Debuff） | 失效牌/失效 Joker 的所有改造失效，**例外**：Negative（+1 槽）与 Stone（无点数花色）仍生效；失效的 Wild 按原花色算 | ✅ |

### 8.1 增强（8 种）

| 增强 | 效果 | 证据 |
|---|---|---|
| Bonus 奖励牌 | +30 筹码 | ✅ |
| Mult 倍率牌 | +4 倍率 | ✅ |
| Wild 万能牌 | 可当任意花色 | ✅ |
| Glass 玻璃牌 | ×2 倍率；1/4 概率碎掉（永久移除） | ✅ |
| Steel 钢铁牌 | **留在手中**时 ×1.5 倍率 | ✅ |
| Stone 石头牌 | +50 筹码；无点数无花色 | ✅ |
| Gold 黄金牌 | 回合结束仍在手中 → +$3 | ✅ |
| Lucky 幸运牌 | 1/5 概率 +20 倍率；1/15 概率 +$20 | ✅ |

### 8.2 封蜡（Seal，4 种）

| 封蜡 | 效果 | 证据 |
|---|---|---|
| Gold Seal 金封蜡 | 该牌被打出并计分时 +$3 | ✅ |
| Red Seal 红封蜡 | 该牌**重触发 1 次** | ✅ |
| Blue Seal 蓝封蜡 | 留在手中时，生成"本回合最后一手牌型"的星球牌（需有空槽） | ✅ |
| Purple Seal 紫封蜡 | 该牌被弃掉时生成 1 张 Tarot（需有空槽） | ✅ |

### 8.3 版本（Edition）

| 版本 | 效果 | 证据 |
|---|---|---|
| Base 基础 | 无额外效果 | ✅ |
| Foil 闪箔 | +50 筹码 | ✅ |
| Holographic 全息 | +10 倍率 | ✅ |
| Polychrome 多彩 | ×1.5 倍率 | ✅ |
| Negative 负片 | +1 Joker 槽 **或** +1 消耗品槽 | ✅ |

> **口径说明**：Wiki 计 **5 种（含 Base）**；任务/工程侧常说的"4 版本"= 4 种**非 Base** 版本。本文两种口径都保留，避免代码常量与文档对不上 ✅

### 8.4 贴纸（Sticker）

| 贴纸 | 效果 | 出现条件 | 证据 |
|---|---|---|---|
| Eternal 永恒 | 不能出售/摧毁 | Black Stake 起进商店 | ✅ |
| Perishable 易腐 | 5 回合后失效（角标显示剩余） | Orange Stake 起进商店 | ✅ |
| Rental 租用 | 每回合结束 −$3；买价强制 $1 | Gold Stake 起进商店 | ✅ |
| 赌注贴纸（8 种） | 纯外观，记录该 Joker/牌组在哪个赌注通关 | 通关后自动获得 | ✅ |

- 有少数 Joker 不能带 Eternal 或不能带 Perishable；**所有 Joker 都可带 Rental** ✅
- 生成概率（无 Voucher）：Negative 0.3% / Poly 0.3% / Holo 1.4% / Foil 2%；贴纸各 30% ✅

### 8.5 暗牌与失效在伤害层面的效果

| 状态 | 玩法影响 | 证据 |
|---|---|---|
| Debuff（失效） | 该牌不参与计分、不触发其效果；失效 Joker 不触发（仍保留卖价，仍可被随机效果指定） | ✅ |
| Face-down（暗牌） | 手上/刚抽的牌背面朝上，选牌时牌型预览显示 `???` | ✅ |
| 强制选中 | `Cerulean Bell`（决战盲注）强制 1 张牌始终被选中 | ✅ |
| 禁用 Joker | `Crimson Heart`（决战盲注）每手随机禁用 1 个 Joker；`Verdant Leaf` 卖 1 个 Joker 前全牌失效 | ✅ |

### 8.6 出现率（补充包内）

| 对象 | 默认 | `Hone` | `Glow Up` | 证据 |
|---|---|---|---|---|
| 扑克牌 · Poly | 1.2% | 2.4% | 4.8% | ✅ |
| 扑克牌 · Holo | 2.8% | 5.6% | 11.2% | ✅ |
| 扑克牌 · Foil | 4% | 8% | 16% | ✅ |
| 扑克牌 · 增强 | 40% | — | — | ✅ |
| 扑克牌 · 封蜡 | 20% | — | — | ✅ |

> 来源：[Card modifiers](https://balatrowiki.org/w/Card_modifiers) ✅、[Jokers](https://balatrowiki.org/w/Jokers?action=raw) ✅、[Stakes](https://balatrowiki.org/w/Stakes) ✅、[Blinds and Antes](https://balatrowiki.org/w/Blinds_and_Antes) ✅（2026-11-15）

---

## 9. 盲注与底注

### 9.1 底注基础要求分（Base Chip Requirement）

| 底注 | 基础 | Green Stake 及以上 | Purple Stake 及以上 | 证据 |
|---:|---:|---:|---:|---|
| 0 及以下 | 100 | 100 | 100 | ✅ |
| **1（起始）** | **300** | **300** | **300** | ✅ |
| 2 | 800 | 900 | 1,000 | ✅ |
| 3 | 2,000 | 2,600 | 3,200 | ✅ |
| 4 | 5,000 | 8,000 | 9,000 | ✅ |
| 5 | 11,000 | 20,000 | 25,000 | ✅ |
| 6 | 20,000 | 36,000 | 60,000 | ✅ |
| 7 | 35,000 | 60,000 | 110,000 | ✅ |
| **8（决战）** | **50,000** | **100,000** | **200,000** | ✅ |

- 白注/Red Stake 一局里：**底注 1 基础 300**，由此推出 Ante 1 三盲注目标：小 300 / 大 450 / 首领 600 ✅
- 上表数值同时来自渲染页与 `Module:Ante_Table` 数据模块，两处一致 ✅

### 9.2 盲注倍率（决定该盲注目标分）

| 盲注 | 目标分倍率 | 证据 |
|---|---|---|
| Small Blind | **×1** 基础 | ✅ |
| Big Blind | **×1.5** 基础 | ✅ |
| Boss Blind（多数） | **×2** 基础 | ✅ |
| The Wall（首领） | **×4** 基础 | ✅ |
| The Needle（首领） | **×1** 基础（但只允许 1 手牌） | ✅ |
| Violet Vessel（决战） | **×6** 基础 | ✅ |
| Plasma Deck | 以上所有目标分**再 ×2**（对所有赌注生效） | ✅ |

> 例：底注 1 白注 + Plasma Deck → 小 600 / 大 900 / 首领 1200（由 ×1/×1.5/×2 再 ×2 推出 △）

### 9.3 30 个盲注明细

**可跳过盲注（2）**

| 盲注 | 效果 | 最低底注 | 倍率 | 奖励 | 证据 |
|---|---|---|---:|---:|---|
| Small Blind | 无特殊效果，可跳过换 Tag | 任意 | ×1 | $3 | ✅ |
| Big Blind | 无特殊效果，可跳过换 Tag | 任意 | ×1.5 | $4 | ✅ |

**首领盲注（23）**

| 盲注 | 效果 | 最低底注 | 倍率 | 奖励 | 证据 |
|---|---|---|---:|---:|---|
| The Hook | 每打出一手牌，随机弃掉 2 张手牌 | 任意 | ×2 | $5 | ✅ |
| The Ox | 打出"本局最常打牌型"→ 金钱归 0 | 6 | ×2 | $5 | ✅ |
| The House | 第一手牌抽成暗牌 | 2 | ×2 | $5 | ✅ |
| The Wall | 超大型盲注（目标分超高） | 2 | **×4** | $5 | ✅ |
| The Wheel | 1/7 的牌抽成暗牌 | 2 | ×2 | $5 | ✅ |
| The Arm | 打出该牌型时降低其等级 | 2 | ×2 | $5 | ✅ |
| The Club | 所有梅花牌失效 | 任意 | ×2 | $5 | ✅ |
| The Fish | 每手牌后抽到的牌为暗牌 | 2 | ×2 | $5 | ✅ |
| The Psychic | 必须打出 5 张牌 | 任意 | ×2 | $5 | ✅ |
| The Goad | 所有黑桃牌失效 | 任意 | ×2 | $5 | ✅ |
| The Water | 本回合起始弃牌数为 0 | 2 | ×2 | $5 | ✅ |
| The Window | 所有方块牌失效 | 任意 | ×2 | $5 | ✅ |
| The Manacle | 手牌上限 −1 | 任意 | ×2 | $5 | ✅ |
| The Eye | 本回合不能重复同一牌型 | 3 | ×2 | $5 | ✅ |
| The Mouth | 本回合只能打同一种牌型 | 2 | ×2 | $5 | ✅ |
| The Plant | 所有面牌失效 | 4 | ×2 | $5 | ✅ |
| The Serpent | 每次出牌/弃牌后固定抽 3 张 | 5 | ×2 | $5 | ✅ |
| The Pillar | 本底注内此前打出过的牌失效 | 任意 | ×2 | $5 | ✅ |
| The Needle | 本回合只能出 1 手牌 | 2 | **×1** | $5 | ✅ |
| The Head | 所有红桃牌失效 | 任意 | ×2 | $5 | ✅ |
| The Tooth | 每打出 1 张牌 −$1 | 3 | ×2 | $5 | ✅ |
| The Flint | 该牌型基础筹码与倍率减半 | 2 | ×2 | $5 | ✅ |
| The Mark | 所有面牌抽成暗牌 | 2 | ×2 | $5 | ✅ |

**决战盲注（5，仅底注 8/16/24/32）**

| 盲注 | 效果 | 最低底注 | 倍率 | 奖励 | 证据 |
|---|---|---|---:|---:|---|
| Amber Acorn | 所有 Joker 被翻转并重排 | 8 | ×2 | $8 | ✅ |
| Verdant Leaf | 卖掉 1 个 Joker 前所有牌失效 | 8 | ×2 | $8 | ✅ |
| Violet Vessel | 超大型盲注 | 8 | **×6** | $8 | ✅ |
| Crimson Heart | 每手随机禁用 1 个 Joker | 8 | ×2 | $8 | ✅ |
| Cerulean Bell | 强制 1 张牌永远处于选中状态 | 8 | ×2 | $8 | ✅ |

### 9.4 首领盲注的抽取与规避

| 规则 | 内容 | 证据 |
|---|---|---|
| 不可跳过 | 首领盲注必须打 | ✅ |
| 抽取规则 | 先按"最低底注"过滤；只从**出场次数最少**的候选中抽 → 全轮换一遍才会重复 | ✅ |
| 底注 1 候选 | 只有 8 个首领盲注可在底注 1（或更低）出现 | ✅ |
| 重掷 | `Director's Cut`（每底注 1 次）/`Retcon`（无限）；重掷时 8 的倍数底注必出决战盲注，其余必出常规首领 | ✅ |
| 关闭效果 | `Luchador`/`Chicot` 可禁用首领效果；对超高倍率盲注（The Wall / Violet Vessel）目标分回到 ×2，The Needle 不加分（仍 1 手） | ✅ |

### 9.5 Endless Mode

| 项 | 内容 | 证据 |
|---|---|---|
| 起点 | 底注 9 | ✅ |
| 决战盲注 | 底注 16 / 24 / 32 再出现 | ✅ |
| 目标分公式 | `Req(a) = Req₈ × (1.6 + (0.75·n)^(1+0.2n))^n`，其中 `n = a − 8` | ✅（raw wikitext 的 `<math>` 原文；n≥2 与表中数值逐项吻合） |
| ⏳ 公式与表不符项 | Ante 9：公式算得 115,435 → 2 位有效数字 120,000，但表中为 **110,000** | ⏳ 待真游戏核对 |
| 取整 | 结果**保留 2 位有效数字** | ✅ |
| 底注 9–16 实测值 | 110,000 / 560,000 / 7,200,000 / 300,000,000 / 47,000,000,000 / 2.9e13 / 7.7e16 / 8.6e20 | ✅ |
| 上限 | 底注 39 目标分溢出双精度（4.8e309）→ `naneinf`，无法继续 | ✅ |
| 备注 | 底注 17 起"未在 Collection 里列出"（页面标注 Untracked） | ✅ |
| 底注 0 / −1 | 可通过 `Hieroglyph`/`Petroglyph` 把底注往下推（极端玩法） | ✅ |

> 来源：[Blinds and Antes](https://balatrowiki.org/w/Blinds_and_Antes) ✅（渲染页给出 30 盲注全表）、[Module:Ante_Table](https://balatrowiki.org/w/Module:Ante_Table?action=raw) ✅（数据模块：逐底注三档数值）、[Decks](https://balatrowiki.org/w/Decks) ✅（Plasma ×2）（2026-11-15）

---

## 10. 跳过盲注与 Tag

### 10.1 跳过规则

| 规则 | 内容 | 证据 |
|---|---|---|
| 可跳过对象 | 仅 **Small Blind / Big Blind**；首领与决战盲注不可跳 | ✅ |
| 收益 | 每跳 1 个得 1 个 Tag（Tag 立即或按条件延后生效） | ✅ |
| 叠加 | Tag 可累积；**按获得顺序（旧→新）结算**，界面显示新在上 | ✅ |
| Tag 总数 | 24 个；**底注 1（含更低）只有 15 个可出现** | ✅ |
| 概率 | 每个 Tag 等概率；同一 Tag 可在同局/同底注重复出现 | ✅ |
| 底注 1 排除项 | Negative / Standard / Meteor / Buffoon / Handy / Garbage / Ethereal / Top-up / Orbital 不出现 | ✅ |
| 隐藏解锁 | Rare Tag 需先发现 `Blueprint`；Negative/Foil/Holo/Poly Tag 需先发现对应版本 | ✅ |
| 其它来源 | `Diet Cola` Joker、Anaglyph Deck 可生成 Double Tag | ✅ |

### 10.2 Tag 全表（24）

| Tag | 效果 | 可得底注 | 证据 |
|---|---|---|---|
| Uncommon Tag | 商店出现 1 个免费 Uncommon Joker | 任意 | ✅ |
| Rare Tag | 商店出现 1 个免费 Rare Joker | 任意 | ✅ |
| Negative Tag | 下个基础版 Joker 免费并获得 Negative | 2+ | ✅ |
| Foil Tag | 下个基础版 Joker 免费并获得 Foil | 任意 | ✅ |
| Holographic Tag | 下个基础版 Joker 免费并获得 Holographic | 任意 | ✅ |
| Polychrome Tag | 下个基础版 Joker 免费并获得 Polychrome | 任意 | ✅ |
| Investment Tag | 击败首领盲注后 +$25 | 任意 | ✅ |
| Voucher Tag | 下个商店多 1 张 Voucher | 任意 | ✅ |
| Boss Tag | 重掷首领盲注 | 任意 | ✅ |
| Standard Tag | 免费 Mega Standard 包 | 2+ | ✅ |
| Charm Tag | 免费 Mega Arcana 包 | 任意 | ✅ |
| Meteor Tag | 免费 Mega Celestial 包 | 2+ | ✅ |
| Buffoon Tag | 免费 Mega Buffoon 包 | 2+ | ✅ |
| Handy Tag | 本局每打出过 1 手 +$1 | 2+ | ✅ |
| Garbage Tag | 本局每浪费过 1 次弃牌 +$1 | 2+ | ✅ |
| Ethereal Tag | 免费 Spectral 包 | 2+ | ✅ |
| Coupon Tag | 下个商店的初始卡与补充包免费 | 任意 | ✅ |
| Double Tag | 复制下一个被选中的 Tag（Double 本身除外） | 任意 | ✅ |
| Juggle Tag | 下回合 +3 手牌上限 | 任意 | ✅ |
| D6 Tag | 下个商店重掷从 $0 起 | 任意 | ✅ |
| Top-up Tag | 生成最多 2 个 Common Joker（需空槽） | 2+ | ✅ |
| Speed Tag | 本局每跳过 1 个盲注 +$5 | 任意 | ✅ |
| Orbital Tag | 指定牌型升 3 级 | 2+ | ✅ |
| Economy Tag | 金钱翻倍（上限 +$40） | 任意 | ✅ |

> 来源：[Tags](https://balatrowiki.org/w/Tags) ✅（渲染页给出 24 行 Tag 表）、[Blinds and Antes](https://balatrowiki.org/w/Blinds_and_Antes) ✅、[Gameplay loop](https://balatrowiki.org/w/Gameplay_loop?action=raw) ✅（2026-11-15）

---

## 11. 游戏模式与牌组/赌注

### 11.1 模式

| 模式 | 内容 | 证据 |
|---|---|---|
| Campaign（标准一局） | 选牌组 + 赌注，从底注 1 打到 8 通关 | ✅ |
| Challenges（挑战牌组） | 20 个挑战牌组，**只能用 White Stake**；初始解锁 5 个，其余按顺序通关解锁 | ✅ |
| Seeded Run（种子局） | 新局界面勾选 Seeded Run 后输入种子（0–8 位大写字母数字）；种子决定商店/抽牌/概率/Boss 等；**种子局不给成就与解锁**，多数统计不计 | ✅ |
| Endless | 通关后可选，底注 9 起（见 §9.5） | ✅ |
| Daily Run（每日局） | **⏳ 未取得来源**：`Daily_Run`/`Daily_Runs` 两页均 404，Wiki 未见独立页面；本文不写其规则 | ⏳ |

### 11.2 牌组（15）

| # | 牌组 | 效果 | 证据 |
|---:|---|---|---|
| 1 | Red Deck | 每回合 +1 弃牌（→ 4 手 / 4 弃） | ✅ |
| 2 | Blue Deck | 每回合 **+1 出牌次数（hand）** | ✅ |
| 3 | Yellow Deck | 起始 +$10 | ✅ |
| 4 | Green Deck | 回合结束：每剩 1 手 +$2、每剩 1 弃 +$1；无利息 | ✅ |
| 5 | Black Deck | +1 Joker 槽，每回合 −1 手 | ✅ |
| 6 | Magic Deck | 起始带 `Crystal Ball` Voucher + 2 张 `The Fool` | ✅ |
| 7 | Nebula Deck | 起始带 `Telescope` Voucher，−1 消耗品槽 | ✅ |
| 8 | Ghost Deck | 商店可出现 Spectral 牌，起始带 `Hex` | ✅ |
| 9 | Abandoned Deck | 牌组内无面牌 | ✅ |
| 10 | Checkered Deck | 26 黑桃 + 26 红桃 | ✅ |
| 11 | Zodiac Deck | 起始带 Tarot Merchant + Planet Merchant + Overstock | ✅ |
| 12 | Painted Deck | +2 手牌上限，−1 Joker 槽 | ✅ |
| 13 | Anaglyph Deck | 每击败 1 个首领盲注得 1 个 Double Tag | ✅ |
| 14 | Plasma Deck | 计分时均衡 Chips 与 Mult；盲注目标分 ×2 | ✅ |
| 15 | Erratic Deck | 全牌组点数与花色随机化 | ✅ |

### 11.3 赌注（Stake，8 级，累计生效）

| 顺序 | 赌注 | 效果 | 证据 |
|---:|---|---|---|
| 1 | White Stake | 基准难度 | ✅ |
| 2 | Red Stake | 小盲注不给奖励金 | ✅ |
| 3 | Green Stake | 目标分随底注增长更快 | ✅ |
| 4 | Black Stake | 商店可出现 Eternal Joker | ✅ |
| 5 | Blue Stake | **−1 弃牌**（→ 2 弃） | ✅ |
| 6 | Purple Stake | 目标分进一步加速 | ✅ |
| 7 | Orange Stake | 商店可出现 Perishable Joker | ✅ |
| 8 | Gold Stake | 商店可出现 Rental Joker | ✅ |

### 11.4 挑战牌组（20；已核 13 个）

| # | 挑战 | 关键规则 | 证据 |
|---:|---|---|---|
| 1 | The Omelette | 盲注无奖励金；剩余手牌不给钱；无利息 | ✅ |
| 2 | 15 Minute City | 无特殊规则（双份面牌、无 A/2/3） | ✅ |
| 3 | Rich get Richer | 起始 $100；分数不能超过当前金钱 | ✅ |
| 4 | On a Knife's Edge | 起始带 Eternal 且"钉住"的 `Ceremonial Dagger`（永远最左） | ✅ |
| 5 | X-ray Vision | 1/4 的牌抽成暗牌 | ✅ |
| 6 | Mad World | 剩余手牌不给钱；无利息；仅 2–9 点数（32 张） | ✅ |
| 7 | Luxury Tax | 每持有 $5 手牌上限 −1；起始手牌上限 10 | ✅ |
| 8 | Non-Perishable | 所有 Joker 自带 Eternal；禁若干 Joker/盲注 | ✅ |
| 9 | Medusa | 所有面牌为 Stone | ✅ |
| 10 | Double or Nothing | 打出的牌计分后失效；全牌组带 Red Seal | ✅ |
| 11 | Typecast | 击败底注 4 首领后：所有 Joker 变 Eternal，Joker 槽位归 0 | ✅ |
| 12 | Inflation | 每次购买后全店价格永久 +$1；禁折扣 Voucher | ✅ |
| 13 | Bram Poker | Joker 不再出现在商店；起始带 Eternal `Vampire` + `The Emperor` | ✅ |
| 14–20 | ⏳ 其余 7 个 | 抓取页面被截断，未取得完整表 | ⏳ |

### 11.5 其它可选项

| 项 | 内容 | 证据 |
|---|---|---|
| 种子开关 | 新局界面 Seeded Run 勾选框（默认关） | ✅ |
| 续玩 | 主界面 Continue 页签 | ✅ |
| 教学局 | 首次游玩会进 Jimbo 教学 | ✅ |
| 统计/收藏 | 解锁项在 Collection；种子局不清成就 | ✅ |

> 来源：[Gameplay loop](https://balatrowiki.org/w/Gameplay_loop?action=raw) ✅、[Decks](https://balatrowiki.org/w/Decks) ✅、[Stakes](https://balatrowiki.org/w/Stakes) ✅、[Seed](https://balatrowiki.org/w/Seed?action=raw) ✅、[Balatro](https://balatrowiki.org/w/Balatro?action=raw) ✅（150 Joker / 32 Voucher / 30 Blind / 24 Tag / 15 Deck / 8 难点）（2026-11-15）

---

## 12. 术语表（英文 → 中文，供文档与代码统一）

| 英文 | 中文（本文用词） | 备注 |
|---|---|---|
| Run | 一局 | 从开局到胜/败 |
| Ante | 底注 | 也译"注级"，本文统一"底注" |
| Blind | 盲注 | Small / Big / Boss / Showdown |
| Showdown Blind | 决战盲注 | 游戏代码称 finisher blind |
| Round | 回合 | 一个盲注对应一个回合 |
| Hand（次数） | 出牌次数 / 手数 | 资源含义；与"一手牌"区分 |
| Hand size | 手牌上限 | 基础 8 |
| Discard | 弃牌 | 资源与动作同名 |
| Chips | 筹码 | 蓝色数值 |
| Mult | 倍率 | 红色数值 |
| xMult | 乘倍率 | 写作 ×倍率 |
| Score | 分数 | = Chips × Mult（每手） |
| Poker Hand | 牌型 | 12 种（9 常规 + 3 隐藏） |
| High Card … Flush Five | 高牌 … 同花五条 | 见 §5.1 |
| Level | 等级 | 牌型等级，无上限 |
| Planet Card | 星球牌 | 升牌型等级 |
| Tarot Card | 塔罗牌 | 主要改牌 |
| Spectral Card | 幻灵牌 | 高强度一次性效果 |
| Consumable | 消耗品 | 塔罗/星球/幻灵统称 |
| Joker | 小丑 | 常驻被动 |
| Joker Slot | Joker 槽位 | 基础 5 |
| Deck | 牌组 | 15 种 |
| Stake | 赌注 | 8 级，累计生效 |
| The Shop | 商店 | 每盲注后出现 |
| Reroll | 重掷 | $5 起，每次 +$1 |
| Voucher | 优惠券 | 32 张 / 16 对 |
| Booster Pack | 补充包 | 5 类 × 3 档 |
| Tag | 标签 | 跳过盲注获得，24 种 |
| Cash Out | 结算 | 盲注奖励 + 利息等 |
| Interest | 利息 | 每 $5 给 $1，上限 $5 |
| Enhancement | 增强 | 8 种 |
| Edition | 版本 | 5 种（含 Base）/ 4 种非 Base |
| Seal | 封蜡 | 4 种 |
| Sticker | 贴纸 | Eternal / Perishable / Rental + 赌注贴纸 |
| Retrigger | 重触发 | Red Seal / 各类 Joker |
| Debuff | 失效 | 效果全部关闭（Negative/Stone 例外） |
| Face-down | 暗牌 | 牌面不可见 |
| Endless Mode | 无尽模式 | 底注 9 起 |
| Seeded Run | 种子局 | 输入种子复现随机 |
| Challenge Deck | 挑战牌组 | 20 个，仅 White Stake |
| Common/Uncommon/Rare/Legendary | 普通/罕见/稀有/传奇 | Joker 稀有度 |
| Foil / Holographic / Polychrome / Negative | 闪箔 / 全息 / 多彩 / 负片 | 版本名（社区译名，非官方） |

---

## 13. 来源清单

> 抓取日期统一为 **2026-11-15**；证据等级说明见 §0.2。所有页面均为 `balatrowiki.org`（CC BY-NC-SA 3.0），仅取事实数值，描述全部中文重写。

| # | URL | 取用的内容 | 证据 |
|---:|---|---|---|
| 1 | https://balatrowiki.org/w/Poker_hands?action=raw | 12 牌型基础 Chips×Mult、星球牌升级增量、Royal Flush 特例、隐藏牌型、计分牌筛选与例外 | ✅ |
| 2 | https://balatrowiki.org/w/Blinds_and_Antes | 30 盲注全表（最低底注/倍率/奖励/效果）、Small/Big/Boss/Showdown 定义、Endless 公式与取整、底注 39 溢出 | ✅ |
| 3 | https://balatrowiki.org/w/Blinds_and_Antes?action=raw | 同页正文（含 1.0.1f 底注改动历史、Ante −1/0） | ✅ |
| 4 | https://balatrowiki.org/w/Module:Ante_Table?action=raw | 底注 0–39 的 base/Green/Purple 三档数值（数据模块） | △ 元数据 |
| 5 | https://balatrowiki.org/w/Money?action=raw | 结算各项顺序与金额、利息公式与上限、起始金钱、被动扣款、负债 | ✅ |
| 6 | https://balatrowiki.org/w/The_Shop?action=raw | 商店布局/权重/稀有度/价格表/版本附加价/折扣/买价卖价算法/重掷曲线 | ✅ |
| 7 | https://balatrowiki.org/w/Gameplay_loop?action=raw | 回合四阶段、回合序号、通关与失败、Run Info、种子局 | ✅ |
| 8 | https://balatrowiki.org/w/Card_modifiers | 8 增强 / 4 封蜡 / 5 版本（含 Base）/ 3 在局贴纸 / debuff 例外 / 出现率 | ✅ |
| 9 | https://balatrowiki.org/w/Booster_Packs?action=raw | 5 类 × 3 档补充包价格与选取数、出现权重与概率 | ✅ |
| 10 | https://balatrowiki.org/w/Stakes | 8 赌注效果与解锁顺序、赌注贴纸 | ✅ |
| 11 | https://balatrowiki.org/w/Decks | 15 牌组效果与解锁条件；挑战牌组前 13 项 | ✅ |
| 12 | https://balatrowiki.org/w/Tags | 24 Tag 全表、底注 1 排除项、叠加与结算顺序 | ✅ |
| 13 | https://balatrowiki.org/w/Vouchers | 32 Voucher / 16 对全表、单价 $10、Illusion 1.0.1o bug | ✅ |
| 14 | https://balatrowiki.org/w/Guide:_Activation_Sequence?action=raw | 一手牌的 8 步激活顺序、重触发规则、+Mult/xMult 顺序原则 | ✅ |
| 15 | https://balatrowiki.org/w/Hands?action=raw | 基础 4 手/回合、剩余手牌换钱、手数增减来源 | ✅ |
| 16 | https://balatrowiki.org/w/Discards?action=raw | 基础 3 弃/回合、Blue Stake −1、弃牌上限 5、伪弃牌 | ✅ |
| 17 | https://balatrowiki.org/w/Hand_size?action=raw | 手牌上限 8、抽牌规则、手牌上限 0 立即失败、上限增减来源 | ✅ |
| 18 | https://balatrowiki.org/w/Jokers?action=raw | Joker 槽位基础 5、稀有度权重、150 Joker、关键术语（含"包含"语义） | ✅ |
| 19 | https://balatrowiki.org/w/Consumables?action=raw | 消耗品槽基础 2、Crystal Ball +1 | ✅ |
| 20 | https://balatrowiki.org/w/Chips?action=raw | A=11 / 面牌=10 / 数字牌=点数；Foil +50、Bonus +30、Stone +50 | ✅ |
| 21 | https://balatrowiki.org/w/Card_Ranks?action=raw | 13 点数、A 高/低、面牌定义 | ✅ |
| 22 | https://balatrowiki.org/w/Score?action=raw | 单次出牌分 = Chips × Mult、回合总分求和、达标判定 | ✅ |
| 23 | https://balatrowiki.org/w/Mult?action=raw | 加/乘倍率定义与来源 | ✅ |
| 24 | https://balatrowiki.org/w/Planet_cards?action=raw | 12 星球牌、无等级上限、Royal Flush 无专属星球牌 | ✅ |
| 25 | https://balatrowiki.org/w/Red_Deck?action=raw | Red Deck = 标准 52 张 + 每回合 +1 弃牌 | ✅ |
| 26 | https://balatrowiki.org/w/Seed?action=raw | 种子格式/作用/种子局禁用成就 | ✅ |
| 27 | https://balatrowiki.org/w/Balatro?action=raw | 总览数字：150 Joker / 32 Voucher / 30 Blind / 24 Tag / 15 Deck / 8 难度 / 12 Planet | ✅ |

### 13.1 未取得来源 / 抓取失败（对应 ⏳ 项）

| 目标 | 结果 | 影响 |
|---|---|---|
| `https://balatrowiki.org/w/Hand_levels`、`/Hand_Levels`、`/Poker_Hand_levels` | **HTTP 404** | 无逐级数值表；"每级增量恒定/线性叠加"只能标 △/⏳ |
| `https://balatrowiki.org/w/Daily_Run`、`/Daily_Runs` | **HTTP 404** | Daily Run 规则标 ⏳，不写细节 |
| `https://en.wikipedia.org/wiki/Balatro` | **fetch failed**（网络层） | 本文未使用 Wikipedia 任何内容 |
| `https://balatrowiki.org/w/Scoring` | 重定向到 `Guide: Activation Sequence#Hand Sequence` | 已改抓该页（#14） |
| `https://balatrowiki.org/w/Shop`、`/Gameplay_rules`、`/Hand`、`/Discard`、`/Challenges`、`/Seeded`、`/Endless_Mode` | 均为重定向 | 已按重定向目标重新抓取 |
| 渲染页 `Decks` 的挑战牌组表 | 内容被截断（只到 #13） | 挑战 #14–20 标 ⏳ |

---

## 附录 A：未核实项与 W3 核对清单（⏳）

| # | 待核对项 | 当前处理 | 核对手段 |
|---:|---|---|---|
| A1 | 单次出牌分的**取整方式**（末尾 floor？还是显示层截断？） | 标 ⏳；候选假设：最终一次 floor（仓库 [engine-gap.md](engine-gap.md) §2 亦按 floor 记录，但非 Wiki 明文） | 真游戏 A2 单步分数：构造产生小数的局（Steel ×1.5）实测 |
| A2 | **中间步骤是否取整**（连续 ×1.5 时小数是否保留） | 标 ⏳；候选：中间保留精确值，仅末尾取整 | 同上，叠加 2 个以上 ×1.5 效果 |
| A3 | "每级增量恒定"（等级 L 值 = 基础 + (L−1)×增量） | 标 △（由 Planet 增量直接推导） | 打出对子/同花等并连升 3 级，记录显示值 |
| A4 | 等级能否降到 1 以下（`The Arm`） | 标 ⏳ | 用 `The Arm` 连续降级观察下限 |
| A5 | 新盲注是否重发满手牌 / 牌堆与弃牌堆如何延续 | 标 ⏳（Wiki 未明写） | A1/A4 状态捕获对比 |
| A6 | 暗牌（face-down）牌是否正常计分、是否正常触发封蜡 | 标 ⏳（只确认"仍参与"） | 用 The House / The Wheel 捕获对拍 |
| A7 | Daily Run 模式规则 | 标 ⏳（Wiki 无页面） | 真游戏主界面观察 |
| A8 | 挑战牌组 #14–20 明细 | 标 ⏳（抓取截断） | 重新抓取完整渲染页 |
| A9 | 1.0.1o 与当前 Wiki 值的差异（Wiki 后续编辑） | 全文已标风险 | 以 1.0.1o 客户端实测为准，冲突即改台账 |

> 说明：本附录**不是**对齐证据，只是把"哪些数值还必须真游戏核对"显式登记，避免 W3 把 ⏳ 当 ✅ 落进代码常量。
