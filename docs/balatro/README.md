# Balatro 规则与设计调研总纲（vanilla 1.0.1o）

> **本目录是什么**：对《Balatro》（LocalThunk / Playstack，2024-02-20 发行，基线版本 **1.0.1o**）**完整规则与设计**的调研总结，供 BalatroEval 的 W3「规则对齐（L0→L2）」与后续报告引用。 \
> **不是什么**：不是对齐证据，也不是本仓库引擎的现状描述。`bench/` 已于 2026-11-17 实现 **vanilla 1.0.1o 子集 v1**（IMPLEMENTED），但对齐等级仍为 **L0**、`fidelity_status` 仍 `NOT_VERIFIED`（A2/A3 实测 0 行），因此本目录只提供 **vanilla 事实/目标值**，任何“已对齐 / A2 通过 / L2 达成”的表述都必须等 `docs/engine-fidelity.md` A 表有真游戏实测行。当前实现状态见 [../implementation/implementation-status.md](../implementation/implementation-status.md)。
> 调研日期：**2026-11-15** ｜ 证据等级：✅ 已打开页面核对 / △ 仅元数据 / ⏳ 仅检索未核实
> 语言：中文（首次出现给英文原名）｜ 版本：v1.0
>
> **本次调研规模**：4 份正文 + 1 份差异映射，合计约 2,930 行（rules 958 / content 774 / design 727 / engine-gap 213 / 本页 261）；各文件文末来源清单合计 60+ 条（含跨文件重复），逐条带 URL、证据等级与抓取日期。

---

## 0. 快速导航

| 文件 | 内容 | 适合谁 |
|---|---|---|
| **[rules.md](rules.md)** | 规则机制事实：一局结构、算分、牌型与等级、盲注/Ante、资源、经济、商店、卡牌改造、Tag、模式、术语表 | 实现 `bench/` 规则、写对齐文档 |
| **[content.md](content.md)** | 全内容目录：150 Joker、消耗品 22/12/18、Voucher 32、牌组 15、赌注 8、Boss 28、Tag、增强/封蜡/版本、补充包、随机权重 | 选卡、做内容映射、核对数值 |
| **[design.md](design.md)** | 设计分析：为什么 chips×mult、加法/乘法复利、随机性与信息、UX 可读性、难度阶梯、美术音频、商业与评价、可迁移教训 | 写报告"相关工作/设计启示"、理解评测环境取舍 |
| **[engine-gap.md](engine-gap.md)** | **本仓库 `bench/`（L0）与 vanilla 的 23 项差异表 + W3 目标值清单 + 验收映射** | W3 直接执行 |
| [../data-sources.md](../data-sources.md) | 来源与许可总清单（本目录引用的新增来源已登记） | 合规检查 |
| [../joker-semantics.md](../joker-semantics.md) | W3 要实现的 8 个 vanilla Joker 语义台账（📋 未实现） | W3 任务 4 |
| [../engine-fidelity.md](../engine-fidelity.md) | 对齐台账 A0–A4（📋 未实测） | 验收 |

---

## 1. 证据分级与许可（先读）

- **✅ 已核**：本次调研用 `web_fetch` 打开页面，数值/事实在页面正文中可直接核对。
- **△ 仅元数据**：只核对了页面标题/版本号，正文数值未逐项抄录。
- **⏳ 仅检索未核实**：只出现在检索结果或二手转述中；报告中引用时必须保持"未核实"措辞。
- **来源许可**：`balatrowiki.org` 为 **CC BY-NC-SA 3.0** —— 本目录**只提取不可版权的事实数值**（名称/数字/条件/价格/表格数值），**所有描述均为自写**，未搬运 Wiki 句子、表格布局或图片。Wikipedia 为 CC BY-SA，同样只取事实并改写。媒体报道只作简短引用并注明来源。
- **L8 红线**：不包含游戏文件、mod、`.jkr` 存档、含游戏素材的截图；本目录全部为文字与自绘表格。

> 与 `plan/00-项目全貌.md` 决策 D12/D14、`docs/data-sources.md` §5 一致；新增来源已在 `docs/data-sources.md` **第 8 节**登记（§9 为变更记录）。

---

## 2. 一页看懂：核心规则速览

### 2.1 一局的结构

```
Run（选牌组 + 赌注）
  └─ Ante 1..8（每 Ante 3 个盲注：Small → Big → Boss；Ante 8 的 Boss 是 Showdown）
       └─ Blind Select → Round（出牌/弃牌）→ Cash Out（结算）→ Shop（商店）→ 下一个盲注
```

| 事实 | 值 | 证据 |
|---|---|---|
| 一局 Ante 数 | 8（Ante 8 Showdown 通关；之后可进 Endless） | ✅ [Blinds & Antes](https://balatrowiki.org/w/Blinds_and_Antes) |
| 每 Ante 盲注 | 3：Small / Big / Boss | ✅ 同上 |
| 可跳过 | Small、Big 可跳过换 Tag；Boss 不可跳过 | ✅ 同上 |
| 盲注总数 | 30 = 2 非 Boss + 23 常规 Boss + 5 Showdown | ✅ 同上 |
| Ante 推进 | 击败 Boss 后进入下一 Ante | ✅ [Gameplay loop](https://balatrowiki.org/w/Gameplay_loop) |
| 失败 | 手牌用完仍未达目标分即输 | ✅ 同上 |
| Endless | Ante 9 起指数级缩放，Ante 39 溢出 `naneinf` | ✅ [Blinds & Antes](https://balatrowiki.org/w/Blinds_and_Antes) |

### 2.2 资源常量（基础值）

| 资源 | 基础值 | 可变来源（示例） | 证据 |
|---|---:|---|---|
| 每回合出牌次数 | **4** | Blue Deck +1；Black Deck −1；The Needle 固定 1 | ✅ [Hands](https://balatrowiki.org/w/Hands) |
| 每回合弃牌次数 | **3** | Red Deck +1；Blue Stake −1；The Water 固定 0 | ✅ [Discards](https://balatrowiki.org/w/Discards) |
| 手牌上限 | **8** | Painted Deck 10；The Manacle −1 | ✅ [Hand size](https://balatrowiki.org/w/Hand_size) |
| Joker 槽位 | **5** | Black Deck 6；Painted 4；Negative 版本 +1 | ✅ [Jokers](https://balatrowiki.org/w/Jokers) |
| 消耗品槽位 | **2** | Crystal Ball Voucher +1 | ✅ [Consumables](https://balatrowiki.org/w/Consumables) |
| 初始金钱 | **$4** | Yellow Deck $14 | ✅ [Money](https://balatrowiki.org/w/Money) |
| 牌组 | 52 张标准牌（4 花色 × 13 点） | 15 种牌组改变构成/效果 | ✅ [Decks](https://balatrowiki.org/w/Decks) |
| 出牌/弃牌张数 | 1–5 张 | — | ✅ [Poker hands](https://balatrowiki.org/w/Poker_hands) |

### 2.3 算分：chips × mult（末尾取整方式 ⏳ 待实测）

- 起始 **Chips** = 牌型基础 Chips + 参与计分牌的 rank chips（A=11，J/Q/K=10，数字=面值）。
- 起始 **Mult** = 牌型基础 Mult。
- 之后按 **Joker 槽位从左到右** 应用 `+Chips / +Mult / ×Mult`；卡牌增强/版本/封蜡与重触发也会插入。
- 中间是否取整、末尾如何取整，**Wiki 未明写**（⏳ 待 A2 实测）；实测前按 `floor(chips × mult)` 作为**候选口径**，不得写成已核事实。
- **只有参与牌型的牌计分**：高牌只计最高 1 张；对子 2 张；两对 4 张；三条 3 张；顺子/同花/葫芦/同花顺 5 张；四条 4 张（可带 1 张不计分牌）。

### 2.4 牌型基础表（等级 1）与每级增量

| 牌型 | 基础 Chips × Mult | 每级升级（Planet） | 计分牌数 |
|---|---:|---|---:|
| 高牌 High Card | 5 × 1 | +10 Chips / +1 Mult | 1 |
| 对子 Pair | 10 × 2 | +15 / +1 | 2 |
| 两对 Two Pair | 20 × 2 | +20 / +1 | 4 |
| 三条 Three of a Kind | 30 × 3 | +20 / +2 | 3 |
| 顺子 Straight | 30 × 4 | +30 / +3 | 5 |
| 同花 Flush | 35 × 4 | +15 / +2 | 5 |
| 葫芦 Full House | 40 × 4 | +25 / +2 | 5 |
| 四条 Four of a Kind | 60 × 7 | +30 / +3 | 4 |
| 同花顺 Straight Flush | 100 × 8 | +40 / +4 | 5 |
| *隐藏* 五条 Five of a Kind | 120 × 12 | +35 / +3 | 5 |
| *隐藏* 同花葫芦 Flush House | 140 × 14 | +40 / +4 | 5 |
| *隐藏* 同花五条 Flush Five | 160 × 16 | +50 / +3 | 5 |

> 来源：✅ [Poker hands](https://balatrowiki.org/w/Poker_hands)（基础值 + 各 Planet 描述中的升级增量）。
> 等级无上限；Royal Flush 在选牌时单独显示，但计分/等级/统计均等同同花顺。隐藏牌型需要改牌组或消耗品才可能出现，标准 52 张牌组无法达成。

### 2.5 盲注目标：Ante 基础分与倍率

| Ante | 基础分 | 说明 |
|---:|---:|---|
| 0 及以下 | 100 | 仅 Hieroglyph/Petroglyph 可达 |
| 1 | **300** | 本项目 W3 目标|
| 2 | 800 | |
| 3 | 2,000 | |
| 4 | 5,000 | |
| 5 | 11,000 | |
| 6 | 20,000 | |
| 7 | 35,000 | |
| 8（Showdown） | 50,000 | 通关 |
| 9 起 | Endless | `Req(a) = Req₈ × (1.6 + (0.75·n)^(1+0.2n))^n`（n = a−8），结果保留 2 位有效数字；n≥2 与表中数值逐项吻合，n=1（Ante 9）表中 110,000 与公式算得 115,435 有差异 ⏳ |

- **Small = 1× 基础分；Big = 1.5×；Boss = 2×**；例外：The Wall 4×、The Needle 1×、Violet Vessel 6×。
- **Green Stake / Purple Stake** 使用更高的分表（Ante 2 起：900/1,000 …；Ante 8：100,000/200,000）。
- **Plasma Deck** 所有目标分 ×2。
- 来源：✅ [Blinds & Antes](https://balatrowiki.org/w/Blinds_and_Antes)。

### 2.6 经济（Cash Out）

| 项 | 金额 | 证据 |
|---|---|---|
| 击败 Small / Big / Boss / Showdown | $3 / $4 / $5 / $8 | ✅ [Money](https://balatrowiki.org/w/Money) |
| 每剩余 1 手牌 | $1（Green Deck $2） | ✅ 同上 |
| 每未使用 1 弃牌 | $1 | ✅ 同上 |
| 利息 | 每持有 $5 得 $1，**上限 $5**（$25 封顶） | ✅ 同上 |
| Red Stake 起 | Small Blind **无**奖励钱 | ✅ [Stakes](https://balatrowiki.org/w/Stakes) |
| 出售 | `floor(buy_cost / 2)`，最低 $1 | ✅ [The Shop](https://balatrowiki.org/w/The_Shop) |
| 负债 | 默认最低 $0；Credit Card 可到 −$20 | ✅ [Money](https://balatrowiki.org/w/Money) |

### 2.7 商店

| 项 | 规则 | 证据 |
|---|---|---|
| 常驻槽位 | 2 张随机卡（Joker/Tarot/Planet）+ 2 个补充包 + 1 个 Voucher | ✅ [The Shop](https://balatrowiki.org/w/The_Shop) |
| 首店保底 | 首个商店必有一个普通 Buffoon 包 | ✅ 同上 |
| 随机卡权重 | Joker 20 / Tarot 4 / Planet 4（≈71.4% / 14.3% / 14.3%） | ✅ 同上 |
| 稀有度权重 | Common 70% / Uncommon 25% / Rare 5% | ✅ 同上 |
| 价格 | Common $1–6 / Uncommon $4–8 / Rare $7–10 / Legendary $20；Tarot·Planet $3；Spectral $4；普通包 $4 / Jumbo $6 / Mega $8；Voucher $10 | ✅ 同上 |
| 刷新 | 起价 $5，每次 +$1，换店重置；Reroll Surplus $3 / Reroll Glut $1 | ✅ 同上 |
| 折扣 | Clearance Sale 25%、Liquidation 50% | ✅ 同上 |

### 2.8 内容规模

| 内容 | 数量 | 备注 | 证据 |
|---|---:|---|---|
| Joker | **150** | 首局可用 105，45 个需解锁；稀有度 **Common 61 / Uncommon 64 / Rare 20 / Legendary 5**（Legendary 仅经 The Soul） | ✅ [Jokers](https://balatrowiki.org/w/Jokers) + [content.md](content.md) §1.1 |
| Tarot / Planet / Spectral | 22 / 12 / 18 | 详见 [content.md](content.md) | ✅ content.md §2 |
| Voucher | 32 | 16 组基础 + 升级 | ✅ content.md §3 |
| 牌组 | 15 | Red/Blue/Yellow/…/Plasma/Erratic | ✅ [Decks](https://balatrowiki.org/w/Decks) |
| 赌注 | 8 | White/Red/Green/Black/Blue/Purple/Orange/Gold，效果累积 | ✅ [Stakes](https://balatrowiki.org/w/Stakes) |
| 盲注 | 30 | 2 + 23 Boss + 5 Showdown | ✅ [Blinds & Antes](https://balatrowiki.org/w/Blinds_and_Antes) |
| 挑战 | 20 | 仅 White Stake | ✅ [Decks](https://balatrowiki.org/w/Decks) |

### 2.9 容易踩坑的机制细节（写代码/写报告前必看）

1. **"Contains" 不是字符串包含**：三条"含"对子；但四条**不**"含"两对；五条**不**"含"葫芦；同花五条**不**"含"同花葫芦。判定依据是牌型包含关系表（📋 完整表见 rules.md；4K/5K 对 Pair/Three 的边界 ⏳ 待真游戏实测）。
2. **Joker 顺序是显式策略**：可拖拽重排；`+Mult` 与 `×Mult` 的先后显著改变分数（示例见 [engine-gap.md](engine-gap.md) §2）。
3. **Joker 重复**：同一次运行中，屏上已存在的 Joker 不会重复出现；要复制已有 Joker 需 Ankh / Invisible Joker 等特例。
4. **伪弃牌**：出 1–4 张牌时，未参与牌型的牌不计分但会离手，等价于一次"免费过滤"（但消耗 1 次出牌）。
5. **版本（Edition，部分文档写作"版式"，同义）**：Foil +50 Chips、Holographic +10 Mult、Polychrome ×1.5、Negative +1 Joker 槽位。
6. **利息是经济核心**：$25 处利息封顶 $5；这使"存钱 vs 花钱"成为跨回合决策。
7. **Boss 选择反重复**：只在"出场次数最少"的候选中抽，且各有最低 Ante；Ante 1 只有 8 个候选。
8. **种子**：决定 Boss、商店、抽牌顺序与概率判定；seeded run 不记录新收集与分数统计。
9. **用词约定（全目录统一）**：Enhancement = **增强**；Seal = **封蜡**；Edition = **版本**（content.md 用"版式"，同义）；Sticker = **贴纸**（Eternal / Perishable / Rental）。早期草稿曾把 Seal 写作"贴纸"，以本节为准。

### 2.10 已知不确定项（⏳，引用时必须保留"未核实"）

| # | 不确定项 | 现状 | 对项目的影响 | 核实方式 |
|---:|---|---|---|---|
| 1 | 单次得分是否 `floor(chips × mult)` | Wiki 的 Score 页只写"相乘"，未写取整方式 | W3 单步分数口径 | A2 真游戏单步对拍 |
| 2 | 中间步骤是否取整（×1.5 产生小数时） | Wiki 未明示 | 同一局面可能差 1 分 | A2 多组 ×1.5 局面 |
| 3 | 每级升级增量是否恒定 | 逐级表页 404；仅由 Planet 单次增量推导 | 等级 2+ 的 Chips/Mult | 真游戏使用 Planet 实测 |
| 4 | **Daily Run 是否存在** | 三处页面 + rules.md §11 均未证实，`/w/Daily_Run` 404 | **不得写成既有模式** | 真游戏主界面/更新日志 |
| 5 | 挑战牌组 #14–20 规则 | 抓取截断，仅核 13 个 | 内容目录覆盖面 | 补抓/实测 |
| 6 | 暗牌是否正常计分、是否触发封蜡 | 只确认"仍参与" | Boss 场景计分 | The House / The Wheel 捕获 |
| 7 | 500 万销量 / "移动版占一半" | 经 Wikipedia 转述，原文付费墙 | design.md §10 引用口径 | 打开 Globe and Mail 原文或保持"据报道" |
| 8 | 作曲家 AMA 原文（Risk of Rain 2 参考、降速） | 经 Wiki 转述 | design.md §9.3 引用口径 | Reddit AMA 原文 |

> 完整清单见 [rules.md](rules.md) §13.1 / 附录 A 与 [design.md](design.md) §13；本表只列**对 W3 有直接影响**的项。已解决项示例：版式加价（Foil +$2 / Holo +$3 / Poly +$5 / Negative +$5）已由 `/w/Card_modifiers` 渲染页 ✅ 核实。

---

## 3. 调研结论（12 条）

1. **Balatro 的核心不是扑克，而是"筹码 × 倍率"的双通道数值系统**：扑克牌型只提供起始 Chips/Mult 与"哪些牌计分"，真正的增长来自 Joker 的加法与乘法叠加。这使牌型熟悉度可以复用，而成长曲线完全由构筑决定。
2. **9 种常规牌型 + 3 种隐藏牌型构成难度梯度**：基础 Chips×Mult 从 5×1 到 160×16，中间用 Planet 等级线性增强；隐藏牌型只在改牌组后出现，服务于"极限 build"。
3. **一局 8 Ante × 3 盲注的结构把"短反馈"与"长构建"分层**：每回合 4 手/3 弃是短决策，Ante 目标是长约束；目标分从 300 涨到 50,000，逼玩家把加法 build 升级为乘法 build。
4. **经济系统是第二个资源维度**：$3/$4/$5 盲注奖励、每手 $1、未用弃牌 $1、利息每 $5 得 $1（cap $5），使"何时买、何时存、何时 reroll"成为跨回合规划。
5. **商店随机性是可控的**：2 卡 + 2 包 + 1 Voucher、权重 20/4/4、稀有度 70/25/5、reroll 线性涨价；玩家可以用钱把随机性转成选择权。
6. **Boss Blind 是"规则修改器"而非数值墙**：23 个常规 Boss + 5 个 Showdown，效果包括花色 debuff、手牌上限、出牌次数、暗牌、禁重复牌型等；它们改变的是可行动作集，而不只是目标分。
7. **难度阶梯（8 Stake）是累积式修正**：Red（Small 无奖励）→ Green/Purple（分数缩放更快）→ Black（Eternal）→ Blue（−1 弃）→ Orange（Perishable）→ Gold（Rental $3/回合）。这为"同一环境不同难度"提供了现成模板。
8. **信息设计克制**：分数预览、牌型预览、逐张结算动画、Run Info 把"为什么输"暴露给玩家；暗牌只出现在特定 Boss。可读性是这款游戏被认为"上手快"的关键。
9. **内容量是设计的一部分**：150 Joker（105 首局可用）、32 Voucher、15 牌组、22/12/18 消耗品、20 挑战；随机组合支撑重玩，但也带来平衡与"build 收敛"问题。
10. **商业与口碑**：2024-02-20 发行后成为现象级独立游戏，获 TGA 2024 最佳独立游戏/最佳首秀独立游戏/最佳移动游戏等多项奖；2024-03 因 PEGI 18（赌博意象）在部分地区商店 **暂时下架**（2025-02 改判 12+；细节与来源等级见 [design.md](design.md) §10.4 ⏳）；2024-09 推出移动版。
11. **设计观（LocalThunk）**：刻意不先玩同类 roguelike、以"重新发明轮子"的方式做原型；后续也承认从 Slay the Spire 学习。设计上强调"简单规则 + 深组合"，而不是堆系统。
12. **对本项目最重要的三条**：① 可判定性来自 `chips × mult` 与固定牌型表；② 长线规划来自"经济 + 构筑 + 盲注目标"三层资源；③ 失败恢复来自 4 手/3 弃与 Boss 规则修改器——这三点正好对应 BalatroEval 的长线四支柱。

---

## 4. 对 BalatroEval 的直接结论
| 结论 | 含义 | 落点 |
|---|---|---|
| **调研时（2026-11-15）`TARGETS=(300,800,2000)` 不是 Ante 1 的三盲注** | 它是 Ante 1/2/3 的基础分；Ante 1 三盲注应为 300/450/600。**2026-11-17 已按此改造实现**（见 [../implementation/implementation-status.md](../implementation/implementation-status.md)），对齐仍未验证 | [engine-gap.md](engine-gap.md) §1/§4 |
| **计分缺的是"牌型基础 Chips×Mult + 计分牌筛选"** | 不只是换数值表；high card 5 张只计 1 张，四条带 kicker 只计 4 张 | 同上 §2 |
| **Red Deck 目标配置 = 4 手 / 4 弃 / 5 槽 / 300/450/600** | 与 plan W3 任务 4 一致；基础牌组是 4 手/3 弃，Red Deck +1 弃 | 同上 §7 |
| **Boss 效果不在 W3 范围，但 Boss 仍会出现** | 场景入集时必须排除带效果的 Boss，或在场景元数据注明"无 Boss 效果" | 同上 §5 |
| **vanilla 触发顺序与"contains"语义必须实测** | 不能只照 Wiki 实现 Joker 条件；A2/A4 需要区分 4K/5K 的包含边界 | 同上 §2.1 + [joker-semantics.md](../joker-semantics.md) §3.3 |
| **本目录不能当对齐证据** | 所有数值只是"目标值"；`fidelity_status` 未签核前保持 `NOT_VERIFIED` | plan/07 §3 |

---

## 5. 与现有计划/文档的关系

| 文档 | 关系 |
|---|---|
| `plan/00-项目全貌.md` | D1/D2/D11/D12/D14 的环境与数据来源决策；本目录为其提供规则事实底座 |
| `plan/01-每周任务.md`  | 任务 3（vanilla 计分）、任务 4（8 Joker + 资源/盲注）直接引用 [engine-gap.md](engine-gap.md) §7 |
| `plan/详细版/07-真实游戏接入与终验.md` | A0–A4 对齐契约；本目录的数值需经 A2/A4 实测才算数 |
| `docs/data-sources.md` | 来源与许可总清单；本目录新增来源已登记（§8） |
| `docs/joker-semantics.md` | 8 个 vanilla Joker 的语义台账（📋 未实现）；本目录 [content.md](content.md) 补全其目录位置 |
| `docs/engine-fidelity.md` | 对齐台账；只有 A 表/B 表实测行能改变 `fidelity_status` |
| `scenarios/RULES_VERSION` | 规则版本与 `excluded` 列表；W3 改造后同步 |

---

## 6. 维护约定

1. **版本优先**：vanilla 事实以 1.0.1o 为准；Wiki 若已更新到后续版本，冲突处标 ⏳ 并以真游戏 `gamestate` 为准。
2. **数值变更**：任何数值改动先改来源清单与证据等级，再改正文；不得出现"无来源的新数字"。
3. **对齐状态**：本目录任何"目标值"不得被改写为"已验证"；状态变更只发生在 `docs/engine-fidelity.md`。
4. **合规**：继续遵守 CC BY-NC-SA 的"只取事实、描述自写"；不新增游戏文件/截图；新增来源先登记 `docs/data-sources.md`。
5. **更新触发**：游戏/mod 版本变化、W3 对齐改造、A2/A4 实测结果出现时，同步更新本目录对应章节与 [engine-gap.md](engine-gap.md)。

---

## 7. 来源清单（本页直接引用）

| 来源 | 用途 | 证据 | 许可 |
|---|---|---|---|
| [Poker hands](https://balatrowiki.org/w/Poker_hands) | 牌型基础分/升级/计分牌筛选 | ✅ 2026-11-15 | CC BY-NC-SA 3.0 |
| [Blinds & Antes](https://balatrowiki.org/w/Blinds_and_Antes) | Ante 表/盲注倍率/Boss 列表/Endless | ✅ 2026-11-15 | 同上 |
| [Gameplay loop](https://balatrowiki.org/w/Gameplay_loop) | 一局结构与阶段 | ✅ 2026-11-15 | 同上 |
| [Hands](https://balatrowiki.org/w/Hands) / [Discards](https://balatrowiki.org/w/Discards) / [Hand size](https://balatrowiki.org/w/Hand_size) | 4 手/3 弃/8 手牌 | ✅ 2026-11-15 | 同上 |
| [Jokers](https://balatrowiki.org/w/Jokers) | 150 Joker/稀有度/槽位/版本/Contains 语义 | ✅ 2026-11-15 | 同上 |
| [Money](https://balatrowiki.org/w/Money) | Cash Out/利息/负债 | ✅ 2026-11-15 | 同上 |
| [The Shop](https://balatrowiki.org/w/The_Shop) | 商店槽位/权重/价格/reroll/折扣 | ✅ 2026-11-15 | 同上 |
| [Stakes](https://balatrowiki.org/w/Stakes) | 8 赌注与修正 | ✅ 2026-11-15 | 同上 |
| [Decks](https://balatrowiki.org/w/Decks) / [Red Deck](https://balatrowiki.org/w/Red_Deck) | 15 牌组/Red Deck +1 弃 | ✅ 2026-11-15 | 同上 |
| [Consumables](https://balatrowiki.org/w/Consumables) | 2 消耗品槽/三类消耗品 | ✅ 2026-11-15 | 同上 |

> 完整来源（含 design.md 的媒体来源）见各文末来源清单与 `docs/data-sources.md` §8。

---

## 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-15 | 初版：四文件结构（总纲/rules/content/design/engine-gap）；核心数值速览、12 条结论、W3 结论、来源与许可 |
