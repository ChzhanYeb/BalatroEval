# Balatro 全内容目录（vanilla 1.0.1o）

> **适用范围：vanilla Balatro 1.0.1o；Wiki 抓取日期 2026-11-15；若 Wiki 已含后续版本内容，冲突处标 ⏳。**
>
> 本文件只做一件事：把 vanilla 1.0.1o 的**可收集内容与随机内容**整理成可查台账，供 W3 选卡与后续规则子集实现对照。**它不描述本仓库 `bench/` 的任何实现状态，也不构成"已对齐/已验证"的证据**；`bench/` 当前对齐等级为 **L0**，见 [README](../../README.md) 与 [engine-fidelity](../engine-fidelity.md)。
>
> **证据等级约定**
>
> | 记号 | 含义 |
> |---|---|
> | ✅ | 本次实际 `web_fetch` 到该页面，数值/条件直接取自页面文本 |
> | △ | 数值来自已抓取页面中的**汇总表或版本历史表**（而非当前版本逐条表），或由已抓取事实做简单计数得到 |
> | ⏳ | 仅检索到存在性、本次未取得可引用来源；**不猜数值** |
>
> **许可与合规（`docs/data-sources.md` §5，L7–L9）**：balatrowiki.org 内容为 CC BY-NC-SA 3.0。本文件**只提取不可版权的事实**（名称、稀有度、数值、条件、价格、编号），**所有描述均为自行改写**，不逐句搬运 Wiki 文本、不复制其表格排版、不贴任何图片；游戏素材不入库。引用外部事实若与后续实测冲突，**以真游戏捕获（A2/A4）为准**（📋 未执行）。

## 0. 目录结构

| 节 | 内容 | 规模 |
|---:|---|---|
| 1 | Joker 全表（分组） | 150 |
| 2 | 消耗品：Tarot / Planet / Spectral | 22 / 12 / 18 |
| 3 | Voucher（基础 + 升级成对） | 32 |
| 4 | 牌组（Deck） | 15 |
| 5 | 赌注（Stake） | 8 |
| 6 | Boss Blind（含 Showdown） | 23 + 5（另 2 个标准盲注作单价参照） |
| 7 | Tag | 24 |
| 8 | 卡牌改造：增强 8 / 封蜡 4 / 版式 5（含 Base）/ 贴纸 3（in-run） | 20 |
| 9 | 补充包（5 类 × 3 尺寸） | 15 |
| 10 | 随机性与权重 | — |
| 11 | 术语对照 | — |
| 12 | 来源清单 | — |

---

## 1. Joker

### 1.1 总量与稀有度分布

| 项 | 值 | 证据 |
|---|---|---|
| Joker 总数 | **150** | ✅ `/w/Jokers` |
| 起始即可获得 / 需解锁 | **105 / 45** | ✅ `/w/Jokers` |
| Common | **61**（出现权重 70%） | ✅ `/w/Jokers` 计数 + 商店权重 |
| Uncommon | **64**（权重 25%） | ✅ |
| Rare | **20**（权重 5%） | ✅ |
| Legendary | **5**（商店**不出现**；只能由 Spectral 卡 `The Soul` 生成） | ✅ |
| 起始 Joker 槽位 | **5**（Negative 版 +1 槽；部分牌组改变槽位数，见 §4） | ✅ `/w/Jokers` |
| `The Soul` 在 Spectral/Arcana 包中的出现率 | **3/1000 = 0.3%** | ✅ `/w/The_Soul`、`/w/Canio` |
| 平均购买价（Wiki 统计） | 全体 $6.14；剔除 Legendary 约 $5.66 | ✅ `/w/Jokers`（Wiki 自述统计，仅作参照） |

> 注：Wiki 把 Joker 分为 7 个功能类（Chips / Additive Mult / Multiplicative Mult / Chips and Additive Mult / Effect / Retrigger / Economy），下表的"分类"列即采用该分类，便于按效果类型选卡。**分类是 Wiki 的功能归类，不是计分阶段的语义**（触发顺序必须真游戏实测，见 [joker-semantics](../joker-semantics.md) §3.3）。

### 1.2 价格与出售价规则

| 规则 | 数值 | 证据 |
|---|---|---|
| 购买价计算 | `buy_cost = (base_cost + edition_cost) × discount_percent`，**四舍五入（half down）** 后若 ≤0 则取 **1** | ✅ `/w/The_Shop` §Pricing |
| 出售价计算 | `sell_value = floor(buy_cost / 2)`，若 ≤0 则取 **1**；再叠加 `Egg` / `Gift Card` 的额外售价 | ✅ `/w/The_Shop` |
| Common / Uncommon / Rare / Legendary 基础价区间 | **$1–6 / $4–8 / $7–10 / $20** | ✅ `/w/The_Shop` |
| Rental 贴纸 | 该 Joker 购买价固定 **$1** | ✅ `/w/The_Shop` |
| Legendary 是否可在商店购买 | **否**（价格 $20 只在图鉴/内部出现） | ✅ `/w/Canio` 等 5 页 |
| 折扣 Voucher | `Clearance Sale` 25% off / `Liquidation` 50% off（卖价同步下降） | ✅ `/w/The_Shop` |
| `Astronomer` | 商店内 Planet 卡与 Celestial 包价格 → **$0** | ✅ `/w/Astronomer` |

### 1.3 Joker 全表（150，按功能分类分组）

> **来源（每组统一）**：balatrowiki.org 各 Joker 单页 `?action=raw` 的 `{{Joker info}}` 字段（`number` / `rarity` / `buyprice` / `effect` / `activation` / `type`），抓取日期 **2026-11-15**，证据等级 **✅**。单页 URL 形如 `https://balatrowiki.org/w/Jolly_Joker`。表中"编号"= 图鉴序号（Wiki `number`），可用于核对总数是否 150/150。
>
> 列说明：**价格**为商店基础购买价（不含 Edition/折扣）；**效果**为自行改写的中文概括；"缩放"指该 Joker 会在对局中永久/回合内累积数值。

#### 1.3.1 +Chips 类（Chips 19 + Chips&Additive Mult 2，共 21 条）

| 名称 | 稀有度 | 价格 | 效果 | 触发/条件 | 编号 |
|---|---|---:|---|---|---:|
| Banner | Common | $5 | +30 Chips × 剩余弃牌数 | 出牌时结算 | 22 |
| Blue Joker | Common | $5 | +2 Chips × 牌堆剩余张数 | 出牌时结算 | 53 |
| Scary Face | Common | $4 | 每张计分的 J 花牌 +30 Chips | 计分时 | 33 |
| Odd Todd | Common | $4 | 奇数点（A/9/7/5/3）每张 +31 Chips | 计分时 | 40 |
| Sly Joker | Common | $3 | **+50 Chips**，若所出牌含对子 | 无条件判定后生效 | 11 |
| Wily Joker | Common | $4 | **+100 Chips**，若含三条 | 同上 | 12 |
| Clever Joker | Common | $4 | **+80 Chips**，若含两对 | 同上 | 13 |
| Devious Joker | Common | $4 | **+100 Chips**，若含顺子 | 同上 | 14 |
| Crafty Joker | Common | $4 | **+80 Chips**，若含同花 | 同上 | 15 |
| Ice Cream | Common | $5 | 基础 +100 Chips，每打一手 −5；归 0 自毁 | 出牌时 | 50 |
| Runner（缩放） | Common | $5 | 每次所出牌含顺子，永久 +15 Chips（起始 +0） | 混合 | 49 |
| Square Joker（缩放） | Common | $4 | 所出牌恰为 4 张时永久 +4 Chips | 混合 | 65 |
| Stone Joker | Uncommon | $6 | +25 Chips × 全牌组 Stone 卡数 | 出牌时 | 89 |
| Arrowhead | Uncommon | $7 | 黑桃每张 +50 Chips（解锁：牌组 ≥30 张黑桃） | 计分时 | 118 |
| Hiker（永久加牌） | Uncommon | $5 | 每张计分牌永久 +5 Chips（可叠加、售出后保留） | 计分时 | 56 |
| Castle（缩放） | Uncommon | $6 | 每弃掉 1 张指定花色 +3 Chips；花色每回合按牌组比例更换 | 混合 | 103 |
| Bull | Uncommon | $6 | +2 Chips × 当前 $1 数 | 出牌时 | 93 |
| Wee Joker（缩放） | Rare | $8 | 每张计分的 2 永久 +8 Chips（解锁：18 回合内通关） | 混合 | 124 |
| Stuntman | Rare | $7 | **+250 Chips**，代价 −2 手牌上限（解锁：单手 ≥1 亿 Chips） | 出牌时 | 136 |
| Scholar | Common | $4 | 每张计分的 A：+20 Chips 且 +4 Mult | 计分时 | 41 |
| Walkie Talkie | Common | $4 | 每张计分的 10 或 4：+10 Chips 且 +4 Mult | 计分时 | 101 |

#### 1.3.2 +Mult 类（Additive Mult 33 + 跨类提示 2，共 35 条）

| 名称 | 稀有度 | 价格 | 效果 | 触发/条件 | 编号 |
|---|---|---:|---|---|---:|
| Joker | Common | $2 | **+4 Mult** | 恒定 | 1 |
| Greedy / Lusty / Wrathful / Gluttonous | Common | $5 各 | 方块 / 红心 / 黑桃 / 梅花每张计分 +3 Mult | 计分时 | 2 / 3 / 4 / 5 |
| Jolly Joker | Common | $3 | **+8 Mult**，若含对子 | 条件 | 6 |
| Zany Joker | Common | $4 | **+12 Mult**，若含三条 | 条件 | 7 |
| Mad Joker | Common | $4 | +10 Mult，若含两对 | 条件 | 8 |
| Crazy Joker | Common | $4 | +12 Mult，若含顺子 | 条件 | 9 |
| Droll Joker | Common | $4 | +10 Mult，若含同花 | 条件 | 10 |
| Half Joker | Common | $5 | **+20 Mult**，若所出牌 ≤3 张 | 张数条件 | 16 |
| Mystic Summit | Common | $5 | +15 Mult，当弃牌剩余 0 | 条件 | 23 |
| Misprint | Common | $4 | 随机 **+0–23 Mult**（每手重roll） | 恒定 | 27 |
| Raised Fist | Common | $5 | 手中**点数最低**的牌，将其点数×2 加到 Mult（J/Q/K=+20，A=+22） | 手中持有 | 29 |
| Fibonacci | Uncommon | $8 | 每张计分的 A/2/3/5/8：+8 Mult | 计分时 | 31 |
| Abstract Joker | Common | $4 | +3 Mult × 场上 Joker 数（含自身） | 恒定 | 34 |
| Gros Michel | Common | $5 | **+15 Mult**；回合结束 1/6 概率自毁（自毁后本局改出 Cavendish） | 恒定 | 38 |
| Even Steven | Common | $4 | 偶数点（10/8/6/4/2）每张 +4 Mult | 计分时 | 39 |
| Supernova | Common | $5 | Mult += 该牌型本局累计打出次数（回溯计入） | 恒定 | 43 |
| Ride the Bus（缩放） | Common | $6 | 连续「未计分花牌」每手 +1 Mult；计分花牌则清零 | 混合 | 44 |
| Green Joker（缩放） | Common | $4 | 每打一手 +1 Mult，每弃牌 −1（不低于 +0） | 混合 | 58 |
| Red Card（缩放） | Common | $5 | 每跳过一个补充包 +3 Mult（不回溯） | 恒定 | 63 |
| Fortune Teller（缩放） | Common | $6 | 本局每用过 1 张 Tarot +1 Mult（回溯计入） | 恒定 | 86 |
| Popcorn | Common | $5 | 基础 +20 Mult，每回合 −4；归 0 自毁 | 恒定 | 97 |
| Smiley Face | Common | $4 | 每张计分花牌 +5 Mult | 计分时 | 104 |
| Swashbuckler | Common | $4 | 其他 Joker 售价总和加到 Mult（解锁：累计卖 20 个 Joker） | 恒定 | 110 |
| Shoot the Moon | Common | $5 | 手中每张 Q +13 Mult（解锁：一回合打出全部红心） | 手中持有 | 140 |
| Bootstraps | Uncommon | $7 | 每 $5 +2 Mult（解锁：同时持有 2 个 Polychrome Joker） | 恒定 | 145 |
| Ceremonial Dagger（缩放） | Uncommon | $6 | 选盲注时摧毁右侧 Joker，把其**售价×2** 永久加到本卡 Mult | 恒定 | 21 |
| Erosion | Uncommon | $6 | 每有 1 张牌少于初始牌组张数，+4 Mult | 恒定 | 81 |
| Flash Card（缩放） | Uncommon | $5 | 每次商店重掷 +2 Mult（不回溯） | 恒定 | 96 |
| Spare Trousers（缩放） | Uncommon | $6 | 所出牌含两对时永久 +2 Mult | 混合 | 98 |
| Onyx Agate | Uncommon | $7 | 梅花每张 +7 Mult（解锁：牌组 ≥30 张梅花） | 计分时 | 119 |
| Ancient Joker | Rare | $8 | 每张「当期花色」计分牌给 **×1.5 Mult**；花色每回合末更换 | 计分时 | 99 |
| Vampire | Uncommon | $7 | 每张计分的**带增强**牌 ×0.1 Mult，并移除其增强 | 混合 | 68 |

> 说明：`Ancient Joker` / `Vampire` 的字段在 Wiki 中归入 Multiplicative Mult（见下节），此处按"含 +Mult 组件"单列提示，避免与 1.3.3 重复计数——**1.3.3 不再重复列这两张**。

（说明：`Ancient Joker`、`Vampire` 在 Wiki 的 `type` 字段中属 **Multiplicative Mult**，本表只作交叉提示，**1.3.3 不重复列出**；故 1.3.2 的 35 条 = Additive Mult 33 张 + 这两张。）
#### 1.3.3 ×Mult 类（Multiplicative Mult Jokers，33 条；`Ancient Joker`/`Vampire` 见 1.3.2，不重复计数）

| 名称 | 稀有度 | 价格 | 效果 | 触发/条件 | 编号 |
|---|---|---:|---|---|---:|
| Joker Stencil | Uncommon | $8 | 每个**空 Joker 槽**给 ×1 Mult（自身占用的槽也计入，故常驻 ≥×1） | 恒定 | 17 |
| Loyalty Card | Uncommon | $5 | 每打 6 手触发一次 ×4 Mult（倒计时从 5 开始） | 恒定 | 25 |
| Steel Joker | Uncommon | $7 | 全牌组每张 Steel 牌 ×0.2（起始 ×1，可叠到很高） | 恒定 | 32 |
| Blackboard | Uncommon | $6 | 手中剩下的牌全为黑桃/梅花时 ×3（手牌为空也触发） | 恒定 | 48 |
| Constellation（缩放） | Uncommon | $6 | 每使用 1 张 Planet ×0.1 累加（起始 ×1，不回溯） | 恒定 | 55 |
| Cavendish | Common | $4 | **×3**；回合结束 1/1000 概率自毁（仅在 Gros Michel 自毁后出现） | 恒定 | 61 |
| Card Sharp | Uncommon | $6 | 本回合内**该牌型已打过**则 ×3 | 恒定 | 62 |
| Madness（缩放） | Uncommon | $7 | 小盲/大盲被选时 ×0.5 累加，并摧毁 1 个随机 Joker（无 Joker 可毁时仍加） | 恒定 | 64 |
| Hologram（缩放） | Uncommon | $7 | 每有 1 张扑克牌加入牌组 ×0.25（起始 ×1） | 恒定 | 70 |
| Baron | Rare | $8 | 手中每张 **K** 给 ×1.5 | 手中持有 | 72 |
| Obelisk（缩放） | Rare | $8 | 连续打出「非本局最常用牌型」每手 ×0.2；一旦打出最常用牌型清零回 ×1 | 混合 | 75 |
| Photograph | Common | $5 | 本手**第一张计分花牌**给 ×2 | 计分时 | 78 |
| Lucky Cat（缩放） | Uncommon | $6 | 每张 Lucky 卡成功触发 ×0.25（起始 ×1） | 混合 | 91 |
| Baseball Card | Rare | $8 | 场上每个 **Uncommon** Joker 给 ×1.5（Rare/Legendary 不计） | 其他 Joker 触发 | 92 |
| Ramen | Uncommon | $6 | 基础 ×2，每弃 1 张 −0.01；降到 ×1 时自毁 | 混合 | 100 |
| Campfire（缩放） | Rare | $9 | 每卖出 1 张牌 ×0.25 累加；击败 Boss Blind 后回 ×1 | 恒定 | 105 |
| Acrobat | Uncommon | $6 | 本回合**最后一手** ×3（解锁：累计打 200 手） | 恒定 | 108 |
| Throwback（缩放） | Uncommon | $6 | 本局每跳过 1 次盲注 ×0.25（回溯计入；解锁：从主菜单续玩存档） | 恒定 | 114 |
| Bloodstone | Uncommon | $7 | 红心计分牌 **1/2** 概率 ×1.5（解锁：牌组 ≥30 张红心） | 计分时 | 117 |
| Glass Joker（缩放） | Uncommon | $6 | 每有 1 张 Glass 牌被摧毁 ×0.75（起始 ×1） | 恒定 | 120 |
| Flower Pot | Uncommon | $6 | 所出牌含四花色各至少 1 张计分牌时 ×3（解锁：首次到 Ante 8） | 恒定 | 122 |
| The Idol | Uncommon | $6 | 每张**指定点数+花色**的计分牌 ×2；目标每回合从牌组随机更换 | 计分时 | 127 |
| Seeing Double | Uncommon | $6 | 有计分梅花牌且有其他花色的计分牌时 ×2（解锁：单手含 4 张 7♣） | 恒定 | 128 |
| Hit the Road（缩放） | Rare | $8 | 本回合每弃 1 张 **J** ×0.5（回合末回 ×1；解锁：同时弃 5 张 J） | 混合 | 130 |
| The Duo | Rare | $8 | 所出牌**含对子** ×2（解锁：通关且全程未打过对子） | 条件 | 131 |
| The Trio | Rare | $8 | 含三条 ×3（解锁：通关且未打过三条） | 条件 | 132 |
| The Family | Rare | $8 | 含四条 ×4（解锁：通关且未打过四条） | 条件 | 133 |
| The Order | Rare | $8 | 含顺子 ×3（解锁：通关且未打过顺子） | 条件 | 134 |
| The Tribe | Rare | $8 | 含同花 ×2（解锁：通关且未打过同花） | 条件 | 135 |
| Driver's License | Rare | $7 | 全牌组 ≥16 张**增强牌**时 ×3（解锁条件相同） | 恒定 | 141 |
| Canio（缩放） | Legendary | $20 | 每有 1 张花牌被摧毁 ×1（起始 ×1） | 混合 | 146 |
| Triboulet | Legendary | $20 | 每张计分的 **K / Q** 给 ×2 | 计分时 | 147 |
| Yorick（缩放） | Legendary | $20 | 每弃满 **23** 张牌 ×1（起始 ×1） | 混合 | 148 |

#### 1.3.4 Effect 类（37 条：手牌/弃牌/槽位/概率/复制等非直接加分效果）

| 名称 | 稀有度 | 价格 | 效果 | 触发/条件 | 编号 |
|---|---|---:|---|---|---:|
| Four Fingers | Uncommon | $7 | 同花与顺子可用 **4 张**组成（同花顺更易成形） | 被动 | 18 |
| Marble Joker | Uncommon | $6 | 选盲注时向牌组加入 1 张 Stone 牌 | 选盲注 | 24 |
| 8 Ball | Common | $5 | 每张计分的 8 有 **1 in 4** 概率生成 Tarot 卡 | 计分时 | 26 |
| Chaos the Clown | Common | $4 | 每次进入商店可获得 1 次免费重掷 | 被动 | 30 |
| Pareidolia | Uncommon | $5 | 所有扑克牌都视为**花牌**（点数/花色/筹码不变） | 被动 | 37 |
| Space Joker | Uncommon | $5 | 打出牌型 **1 in 4** 概率升级 1 级（结算在计分前） | 出牌时 | 45 |
| Burglar | Uncommon | $6 | 选盲注时 **+3 手**，代价：失去全部弃牌 | 选盲注 | 47 |
| DNA | Rare | $8 | 若本回合**第一手**只出 1 张牌：永久复制该牌入牌组并抽到手 | 出牌时 | 51 |
| Splash | Common | $3 | 所有打出的牌都参与计分（含其增强/封蜡/版式） | 被动 | 52 |
| Sixth Sense | Uncommon | $6 | 若本回合第一手是**单张 6**：摧毁它并生成 1 张 Spectral（不含 The Soul/Black Hole） | 被动 | 54 |
| Superposition | Common | $4 | 牌型同时含 A 与顺子时生成 1 张 Tarot | 恒定 | 59 |
| Séance | Uncommon | $6 | 打出**同花顺**时生成 1 张随机 Spectral（不含 The Soul/Black Hole） | 恒定 | 66 |
| Riff-Raff | Common | $6 | 选盲注时生成最多 2 个 Common Joker（有槽位才生成） | 选盲注 | 67 |
| Shortcut | Uncommon | $7 | 顺子允许间隔 1 个点数（如 10 8 6 5 3；仍不允许 A 两头接） | 被动 | 69 |
| Vagabond | Rare | $8 | 出牌时金钱 ≤ $4 则生成 1 张 Tarot（需有空消耗品槽） | 恒定 | 71 |
| Midas Mask | Uncommon | $7 | 所有打出并计分的花牌变为 **Gold** 卡（覆盖原增强） | 出牌时 | 76 |
| Luchador | Uncommon | $5 | **卖出**时禁用当前 Boss Blind 效果（须在 Boss 回合内卖） | 被动 | 77 |
| Turtle Bean | Uncommon | $6 | +5 手牌上限，每回合 −1；降到 0 自毁 | 被动 | 80 |
| Hallucination | Common | $4 | 每次打开补充包 **1 in 2** 概率生成 Tarot | 被动 | 85 |
| Juggler | Common | $4 | +1 手牌上限 | 被动 | 87 |
| Drunkard | Common | $4 | 每回合 +1 弃牌 | 被动 | 88 |
| Diet Cola | Uncommon | $6 | **卖出**时生成一个免费的 Double Tag | 被动 | 94 |
| Mr. Bones | Uncommon | $5 | 计分 ≥25% 目标分时免于失败并自毁（不给通关奖励金；牌堆耗尽时不触发） | 被动 | 107 |
| Troubadour | Uncommon | $6 | +2 手牌上限，代价：每回合 −1 手（解锁：连续 5 回合单手通关） | 被动 | 111 |
| Certificate | Uncommon | $6 | 回合开始时加 1 张「随机点数/花色 + 随机封蜡」的牌入手（保留入牌组） | 被动 | 112 |
| Smeared Joker | Uncommon | $7 | 红心=方块、黑桃=梅花（对 Joker 与盲注的花色判定都生效） | 被动 | 113 |
| Showman | Uncommon | $5 | 解除「同一张卡不能重复出现」限制（Joker/Tarot/Planet/Spectral） | 被动 | 121 |
| Blueprint | Rare | $10 | 复制**右侧** Joker 的能力（部分被动/回合末效果不可复制；解锁：通关一局） | 被动 | 123 |
| Merry Andy | Uncommon | $7 | 每回合 **+3 弃牌**，代价 −1 手牌上限（解锁：12 回合内通关） | 被动 | 125 |
| Oops! All 6s | Uncommon | $4 | 所有「标明的概率」翻倍（如 1 in 3 → 2 in 3；解锁：单手 ≥10,000 Chips） | 被动 | 126 |
| Invisible Joker | Rare | $8 | 经过 2 回合后可卖出，复制 1 个随机 Joker（副本去掉 Negative；解锁：全程 Joker ≤4 通关） | 被动 | 137 |
| Brainstorm | Rare | $10 | 复制**最左侧** Joker 的能力（解锁：弃掉一手皇家同花顺） | 被动 | 138 |
| Cartomancer | Uncommon | $6 | 选盲注时生成 1 张 Tarot（解锁：集齐全部 Tarot） | 选盲注 | 142 |
| Astronomer | Uncommon | $8 | 商店内所有 Planet 卡与 Celestial 包价格 → $0（解锁：集齐全部 Planet） | 被动 | 143 |
| Burnt Joker | Rare | $8 | 每回合**首次弃牌**时升级该弃牌牌型 1 级（解锁：累计卖 50 张牌） | 弃牌 | 144 |
| Chicot | Legendary | $20 | 禁用**每一个** Boss Blind 的效果（分数回到 2× 基础） | 选盲注 | 149 |
| Perkeo | Legendary | $20 | 离开商店时，生成 1 张随机消耗品的 **Negative** 副本（不受槽位限制） | 被动 | 150 |
#### 1.3.5 重触发类（Retrigger，6 条）

| 名称 | 稀有度 | 价格 | 效果 | 触发/条件 | 编号 |
|---|---|---:|---|---|---:|
| Mime | Uncommon | $5 | 重触发所有**手中持有**牌的「在手效果」（Steel/Gold/封蜡等） | 手中持有 | 19 |
| Dusk | Uncommon | $5 | 本回合**最后一手**的所有出牌重触发 1 次 | 计分时 | 28 |
| Hack | Uncommon | $6 | 每张打出的 **2/3/4/5** 重触发 1 次 | 计分时 | 36 |
| Seltzer | Uncommon | $6 | 接下来 **10 手**内，所有打出的牌重触发（用尽后自毁） | 计分时 | 102 |
| Sock and Buskin | Uncommon | $6 | 所有打出的**花牌**（J/Q/K）重触发 1 次（解锁：累计打出 300 张花牌） | 计分时 | 109 |
| Hanging Chad | Common | $4 | 本手**第一张**计分牌额外重触发 **2** 次（解锁：用高牌击败 Boss Blind） | 计分时 | 115 |

> 注：重触发不会让 `Red Seal` 再次触发（Red Seal 自身已是一次重触发）；Mime 不重触发「出牌时」的牌面筹码与版式。

#### 1.3.6 经济类（Economy，18 条）

| 名称 | 稀有度 | 价格 | 效果 | 触发/条件 | 编号 |
|---|---|---:|---|---|---:|
| Credit Card | Common | $1 | 允许金钱透支至 **−$20** | 被动 | 20 |
| Delayed Gratification | Common | $4 | 本回合**未使用任何弃牌**时，回合末每剩余弃牌 +$2 | 被动 | 35 |
| Business Card | Common | $4 | 每张计分花牌 **1 in 2** 概率 +$2 | 计分时 | 42 |
| Egg | Common | $4 | 回合末自身**售价 +$3**（可出售套现） | 被动 | 46 |
| Faceless Joker | Common | $4 | 同一时间弃掉 **≥3 张花牌** → +$5 | 弃牌时 | 57 |
| To Do List | Common | $4 | 打出**指定牌型**（每回合更换）→ +$4 | 出牌时 | 60 |
| Cloud 9 | Uncommon | $7 | 回合末，完整牌组中每张 **9** → +$1 | 被动 | 73 |
| Rocket | Uncommon | $6 | 回合末 +$1；每击败 1 个 Boss Blind，支付额 +$2 累加 | 被动 | 74 |
| Gift Card | Uncommon | $6 | 回合末，所有 Joker 与消耗品**售价 +$1**（含自身） | 被动 | 79 |
| Reserved Parking | Common | $6 | 手中每张花牌 **1 in 2** 概率 +$1 | 手中持有 | 82 |
| Mail-In Rebate | Common | $4 | 每弃 1 张**指定点数**的牌 +$5（点数每回合从牌组随机更换） | 弃牌时 | 83 |
| To the Moon | Uncommon | $5 | 每持有 $5 额外 **+$1 利息**（仍受利息上限约束） | 被动 | 84 |
| Golden Joker | Common | $6 | 回合末 +$4 | 被动 | 90 |
| Trading Card | Uncommon | $6 | 每回合**首次弃牌**若只有 1 张：摧毁它并 +$3 | 弃牌时 | 95 |
| Golden Ticket | Common | $5 | 每张计分的 **Gold** 牌 +$4（仅在牌组已有 Gold 牌时出现） | 计分时 | 106 |
| Rough Gem | Uncommon | $7 | 每张计分的**方块**牌 +$1（解锁：牌组 ≥30 张方块） | 计分时 | 116 |
| Matador | Uncommon | $7 | 打出的牌**触发了 Boss Blind 能力**时 +$8（解锁：不用弃牌单手击败 Boss） | 恒定 | 129 |
| Satellite | Uncommon | $6 | 回合末，本局用过的**不同 Planet 卡**每张 +$1（解锁：单局持有 ≥$400） | 被动 | 139 |

### 1.4 覆盖核对（150/150）

| 分组 | 条数 | 说明 |
|---|---:|---|
| 1.3.1 +Chips（含 Chips&Mult 2） | 21 | Chips 19 + Scholar/Walkie Talkie 2 |
| 1.3.2 +Mult（含跨类提示 2） | 35 | Additive Mult 33 + Ancient/Vampire 2（后者属 ×Mult，仅提示不重复计） |
| 1.3.3 ×Mult | 33 | 不含 Ancient/Vampire |
| 1.3.4 Effect | 37 | — |
| 1.3.5 Retrigger | 6 | — |
| 1.3.6 Economy | 18 | — |
| **合计** | **150** | 与 Wiki 声明的 150 一致 ✅ |

### 1.5 与 W3 的 8 个 vanilla Joker 对应关系

> 只陈述事实（名称/稀有度/价格/编号/效果条件），**不评价实现难度、不声称已实现**。触发顺序与"含对子"的边界仍需真游戏实测（`docs/joker-semantics.md` §3.3，📋）。

| W3 目标 | 完整目录位置 | 稀有度 | 价格 | 编号 | 效果与条件（vanilla 事实） |
|---|---|---|---:|---:|---|
| `Joker` | §1.3.2 | Common | $2 | 1 | +4 Mult，无条件 |
| `Jolly Joker` | §1.3.2 | Common | $3 | 6 | +8 Mult，若所出牌**含对子**（含三条/葫芦/四条等超集） |
| `Zany Joker` | §1.3.2 | Common | $4 | 7 | +12 Mult，若所出牌**含三条**（含葫芦等超集） |
| `Sly Joker` | §1.3.1 | Common | $3 | 11 | +50 Chips，若所出牌**含对子** |
| `Wily Joker` | §1.3.1 | Common | $4 | 12 | +100 Chips，若所出牌**含三条** |
| `Half Joker` | §1.3.2 | Common | $5 | 16 | +20 Mult，若所出牌**≤3 张**（不看是否计分） |
| `The Duo` | §1.3.3 | **Rare** | $8 | 131 | ×2 Mult，若所出牌含对子（解锁：通关且全程未打过对子） |
| `The Trio` | §1.3.3 | **Rare** | $8 | 132 | ×3 Mult，若所出牌含三条（解锁：通关且未打过三条） |

**读法提示**：这 8 张里 6 张是 Common、2 张是 Rare；`The Duo`/`The Trio` 的 ×Mult 语义与 6 张 +Chips/+Mult 的线性语义不同，**不能共用同一条实现路径就宣布"覆盖"**。完整目录中还有 142 张未进入 W3 首批目标。另：条件里的"含对子/含三条"按 vanilla 的 **Contains** 关系判定——三条含对子、四条**不**含两对、五条**不**含葫芦（✅ `/w/Jokers`）；**四条/五条是否含 Pair/Three，官方文本未明示，标 ⏳ 待 A2 实测**。

---

## 2. 消耗品（Consumables）

> **来源**：balatrowiki.org 各消耗品单页 `{{Consumable info}}`（`number` / `effect` / `buyprice` / `sellprice` / `unlock` / `type`），2026-11-15，**✅**。分类页：`Category:Tarot Cards`(22)、`Category:Planet Cards`(12)、`Category:Spectral Cards`(18)。

### 2.1 Tarot 卡（22 张）

统一价格：**购买 $3 / 出售 $1** ✅。除特别标注外全部**起始即可获得**（`unlock = Available from start`）。

| # | 名称 | 价格 | 效果 | 目标数 |
|---:|---|---:|---|---:|
| 1 | The Fool | $3 | 生成**上一次使用**的 Tarot 或 Planet 卡（The Fool 本身除外） | — |
| 2 | The Magician | $3 | 将选定牌变为 **Lucky** | 2 |
| 3 | The High Priestess | $3 | 生成最多 2 张随机 **Planet** 卡 | — |
| 4 | The Empress | $3 | 将选定牌变为 **Mult** 卡（+4 Mult） | 2 |
| 5 | The Emperor | $3 | 生成最多 2 张随机 **Tarot** 卡（不含自身） | — |
| 6 | The Hierophant | $3 | 将选定牌变为 **Bonus** 卡（+30 Chips） | 2 |
| 7 | The Lovers | $3 | 将选定牌变为 **Wild** 卡（可当任意花色） | 1 |
| 8 | The Chariot | $3 | 将选定牌变为 **Steel** 卡（在手 ×1.5 Mult） | 1 |
| 9 | Justice | $3 | 将选定牌变为 **Glass** 卡（×2 Mult，1/4 破碎） | 1 |
| 10 | The Hermit | $3 | 金钱翻倍，**上限 +$20** | — |
| 11 | The Wheel of Fortune | $3 | **1 in 4** 概率给随机 Joker 加 Foil/Holographic/Polychrome 版式 | — |
| 12 | Strength | $3 | 选定牌点数 **+1**（A→2，K→A） | 2 |
| 13 | The Hanged Man | $3 | 摧毁选定牌 | 2 |
| 14 | Death | $3 | 选 2 张，把**左**卡完全变为**右**卡（含增强/版式/追加筹码） | 2 |
| 15 | Temperance | $3 | 获得所有 Joker 售价总和，**上限 $50** | — |
| 16 | The Devil | $3 | 将选定牌变为 **Gold** 卡（在手回合末 +$3） | 1 |
| 17 | The Tower | $3 | 将选定牌变为 **Stone** 卡（+50 Chips，无点数/花色） | 1 |
| 18 | The Star | $3 | 将选定牌花色变为 **方块** | 3 |
| 19 | The Moon | $3 | 将选定牌花色变为 **梅花** | 3 |
| 20 | The Sun | $3 | 将选定牌花色变为 **红心** | 3 |
| 21 | Judgement | $3 | 生成 1 个随机 **Joker** | — |
| 22 | The World | $3 | 将选定牌花色变为 **黑桃** | 3 |

> ⏳ 数据瑕疵提示：Wiki 的 `{{Consumable info}}` 中 `The Hierophant` 与 `The Lovers` 的 `number` 字段**都为 7**，与"22 张连续编号"矛盾，疑为 Wiki 数据错误。上表按游戏内图鉴顺序（Hierophant 在 Lovers 之前）排列；**该编号冲突未核实**，标 ⏳。

### 2.2 Planet 卡（12 张）

统一价格：**购买 $3 / 出售 $1** ✅。每张提升对应牌型 1 级；"等级 1 基础值"列即升级起点（同 [data-sources](../data-sources.md) §1 的 vanilla 目标值）。

| # | 名称 | 对应牌型 | 每级增益 | 等级 1 基础值 | 解锁 |
|---:|---|---|---|---|---|
| 1 | Pluto | 高牌 High Card | +1 Mult / +10 Chips | 5 × 1 | 起始 |
| 2 | Mercury | 对子 Pair | +1 Mult / +15 Chips | 10 × 2 | 起始 |
| 3 | Uranus | 两对 Two Pair | +1 Mult / +20 Chips | 20 × 2 | 起始 |
| 4 | Venus | 三条 Three of a Kind | +2 Mult / +20 Chips | 30 × 3 | 起始 |
| 5 | Saturn | 顺子 Straight | +3 Mult / +30 Chips | 30 × 4 | 起始 |
| 6 | Jupiter | 同花 Flush | +2 Mult / +15 Chips | 35 × 4 | 起始 |
| 7 | Earth | 葫芦 Full House | +2 Mult / +25 Chips | 40 × 4 | 起始 |
| 8 | Mars | 四条 Four of a Kind | +3 Mult / +30 Chips | 60 × 7 | 起始 |
| 9 | Neptune | 同花顺 Straight Flush（含皇家） | +4 Mult / +40 Chips | 100 × 8 | 起始 |
| 10 | Planet X | 五条 Five of a Kind | +3 Mult / +35 Chips | 120 × 12 | 本局打出过五条 |
| 11 | Ceres | 同花葫芦 Flush House | +4 Mult / +40 Chips | 140 × 14 | 本局打出过同花葫芦 |
| 12 | Eris | 同花五条 Flush Five | +3 Mult / +50 Chips | 160 × 16 | 本局打出过同花五条 |

### 2.3 Spectral 卡（18 张）

统一价格：**购买 $4 / 出售 $2** ✅（`The Soul`、`Black Hole` 标注"cannot be found in shop"）。

| # | 名称 | 效果 | 备注 |
|---:|---|---|---|
| 1 | Familiar | 随机摧毁手中 1 张牌，加入 **3 张随机带增强的花牌**入手 | 起始 |
| 2 | Grim | 摧毁手中 1 张，加入 **2 张带增强的 A** | 起始 |
| 3 | Incantation | 摧毁手中 1 张，加入 **4 张带增强的数字牌** | 起始 |
| 4 | Talisman | 给选定牌加 **Gold Seal** | 起始 |
| 5 | Aura | 给选定牌加 Foil/Holographic/Polychrome 版式之一 | 起始 |
| 6 | Wraith | 生成 1 个随机 **Rare Joker**，但**金钱归 0** | 起始 |
| 7 | Sigil | 手中所有牌变为**同一随机花色** | 起始 |
| 8 | Ouija | 手中所有牌变为**同一随机点数**，代价 **−1 手牌上限** | 起始 |
| 9 | Ectoplasm | 给随机 Joker 加 **Negative**，代价 −1 手牌上限（每多用 1 次再额外 −1） | 起始 |
| 10 | Immolate | 摧毁手中 5 张随机牌，+$20 | 起始 |
| 11 | Ankh | 复制 1 个随机 Joker，并摧毁其他所有 Joker（副本去掉 Negative） | 起始 |
| 12 | Deja Vu | 给选定牌加 **Red Seal** | 起始 |
| 13 | Hex | 给随机 1 个 Joker 加 **Polychrome**，并摧毁其他所有 Joker | 起始 |
| 14 | Trance | 给选定牌加 **Blue Seal** | 起始 |
| 15 | Medium | 给选定牌加 **Purple Seal** | 起始 |
| 16 | Cryptid | 复制选定牌 **2** 张入手 | 起始 |
| 17 | **The Soul** | 生成 1 个随机 **Legendary Joker**（需有空 Joker 槽） | **商店不可见**；仅在 Spectral/Arcana 包内以 **0.3%** 概率替换某张卡 |
| 18 | **Black Hole** | 所有牌型等级 **+1** | **商店不可见**；仅在补充包内以 0.3% 概率替换（Spectral/Celestial；买了 `Omen Globe` 后 Arcana 也可） |

> 两条硬约束（✅ 来源见 `/w/Sixth Sense`、`/w/Séance`、`/w/Black Hole`）：`Sixth Sense` 与 `Séance` **不能**生成 `The Soul` 或 `Black Hole`；两者的 0.3% 替换只发生在补充包开包时。
---

## 3. Voucher（32 张，16 对「基础 → 升级」）

> **来源**：balatrowiki.org 各 Voucher 单页 `{{Voucher info}}`（`number` / `type` / `effect` / `unlock` / `notes`），2026-11-15，**✅**；价格取自 `/w/The_Shop` §Base cost：**Voucher 统一 $10** ✅。
> 规则：每对只有买了**基础版**才会出现**升级版**；`Blank`→`Antimatter` 是唯一例外（需累计买 Blank 10 次）。升级版都是**解锁条件**，不是"买过基础版"就自动出现。

| # | 基础版 | 效果 | # | 升级版 | 效果 | 升级版解锁条件 |
|---:|---|---|---:|---|---|---|
| 1 | Overstock | 商店随机卡位 **+1**（2→3），并立即补满空位 | 2 | Overstock Plus | 再 **+1**（3→4），立即补满空位 | 在商店累计消费 $2500 |
| 3 | Clearance Sale | 卡与补充包 **25% off** | 4 | Liquidation | **50% off**（Joker 售价同步下降；价格 half-down 取整） | 单局兑换 ≥10 张 Voucher |
| 5 | Hone | Foil/Holo/Polychrome 出现率 **2×** | 6 | Glow Up | **4×**（Joker 上的 Polychrome 实际 7×） | 持有 ≥5 个带 Foil/Holo/Poly/Negative 的 Joker |
| 7 | Reroll Surplus | 重掷 **−$2**（起步 $5→$3） | 8 | Reroll Glut | 再 **−$2**（起步 $1） | 累计重掷 100 次 |
| 9 | Crystal Ball | 消耗品槽 **+1** | 10 | Omen Globe | Arcana 包里可出 **Spectral** 卡（每张 20% 概率替换） | 从补充包累计使用 25 张 Tarot |
| 11 | Telescope | Celestial 包**必含**你最常打的牌型对应的 Planet | 12 | Observatory | 消耗品区内的 Planet 卡，对其对应牌型给 **×1.5**（在 Joker 之后结算） | 从 Celestial 包累计使用 25 张 Planet |
| 13 | Grabber | 每回合 **+1 手**（永久） | 14 | Nacho Tong | 再 **+1 手** | 累计打出 2500 张牌 |
| 15 | Wasteful | 每回合 **+1 弃牌**（永久） | 16 | Recyclomancy | 再 **+1 弃牌** | 累计弃牌 2500 张 |
| 17 | Tarot Merchant | 商店 Tarot 权重 4 → **9.6**（约 14.3%→28.6%） | 18 | Tarot Tycoon | 权重 → **32**（约 57.1%） | 在商店累计购买 50 张 Tarot |
| 19 | Planet Merchant | 商店 Planet 权重 4 → **9.6** | 20 | Planet Tycoon | 权重 → **32**（约 57.1%） | 在商店累计购买 50 张 Planet |
| 21 | Seed Money | 利息上限 **$10** | 22 | Money Tree | 利息上限 **$20** | 连续 10 回合吃满利息 |
| 23 | Blank | **无效果**（唯一用途是凑购买次数） | 24 | Antimatter | Joker 槽 **+1** | 累计兑换 Blank 10 次 |
| 25 | Magic Trick | 商店可买**扑克牌**（$1/张） | 26 | Illusion | 商店扑克牌可带增强/版式/封蜡（**1.0.1o 有 bug：实际不出封蜡**，且不吃 Hone/Glow Up） | 在商店累计购买 20 张扑克牌 |
| 27 | Hieroglyph | Ante **−1**，代价每回合 −1 手 | 28 | Petroglyph | Ante **−1**，代价每回合 −1 弃牌 | 到达 Ante 12 |
| 29 | Director's Cut | 每 Ante 可重掷 **Boss Blind 1 次**，$10/次 | 30 | Retcon | Boss Blind **无限重掷**，$10/次 | 发现 25 种 Blind |
| 31 | Paint Brush | 手牌上限 **+1** | 32 | Palette | 手牌上限 **+1** | 把手牌上限降到 5 张 |

> ⏳ 未能从本次抓取页面确认的细节：`Hieroglyph`/`Petroglyph` 的 Ante 下限（可否到 Ante 0 以下）只在 `/w/Blinds_and_Antes` 的"Ante −1"段有示例推演，**具体下限未作为规则声明**，标 ⏳。

---

## 4. 牌组（15 个）

> **来源**：`Category:Decks by number` 各牌组页 `{{Deck info}}`（`number` / `limit` / `unlock`），2026-11-15，**✅**。

| # | 牌组 | 效果（初始资源/规则差异） | 解锁条件 |
|---:|---|---|---|
| 1 | Red | 每回合 **+1 弃牌** | 起始可用 |
| 2 | Blue | 每回合 **+1 手** | 图鉴发现 ≥20 项 |
| 3 | Yellow | 起始金钱 **+$10**（即 $14） | 图鉴发现 ≥50 项 |
| 4 | Green | 回合末：每剩余手 +$2、每剩余弃牌 +$1；**不获得利息** | 图鉴发现 ≥75 项 |
| 5 | Black | **+1 Joker 槽**，代价每回合 **−1 手** | 图鉴发现 ≥100 项 |
| 6 | Magic | 起始带 Voucher `Crystal Ball` + **2 张 The Fool** | 用 Red 牌组通关（任意难度） |
| 7 | Nebula | 起始带 Voucher `Telescope`，代价 **−1 消耗品槽** | 用 Blue 牌组通关 |
| 8 | Ghost | Spectral 卡可出现在商店；起始带 1 张 `Hex` | 用 Yellow 牌组通关 |
| 9 | Abandoned | 起始牌组**没有花牌**（J/Q/K 全缺，40 张） | 用 Green 牌组通关 |
| 10 | Checkered | 起始牌组为 **26 张黑桃 + 26 张红心** | 用 Black 牌组通关 |
| 11 | Zodiac | 起始带 `Tarot Merchant` + `Planet Merchant` + `Overstock` 三张 Voucher | 任意牌组在 **Red 赌注**以上通关 |
| 12 | Painted | 手牌上限 **+2**，代价 **−1 Joker 槽**（初始 4 槽） | 任意牌组在 **Green 赌注**以上通关 |
| 13 | Anaglyph | 每击败一个 Boss Blind 获得 1 个 **Double Tag** | 任意牌组在 **Black 赌注**以上通关 |
| 14 | Plasma | 计分改为「(Chips+Mult)/2 再平方」；**盲注目标 ×2** | 任意牌组在 **Blue 赌注**以上通关 |
| 15 | Erratic | 起始 52 张牌的点数与花色**全部随机** | 任意牌组在 **Orange 赌注**以上通关 |

> 另：`Challenge Decks`（20 个挑战牌组）只能使用 White 赌注，**不属于 15 个常规牌组**，本表不含（✅ `/w/Decks`）。

---

## 5. 赌注（8 档）

> **来源**：`Category:Stakes by number` 各赌注页 `{{Stake info}}`（`number` / `description` / `unlocked_deck`），2026-11-15，**✅**。
> 规则：**每档赌注叠加之前所有档的修正**；每副牌组独立按顺序解锁（先用该牌组赢 White 才解锁 Red，依此类推）。

| # | 赌注 | 新增修正（含此前所有档） | 该档首次通关解锁的牌组 |
|---:|---|---|---|
| 1 | White | 基础难度，无额外修正 | — |
| 2 | Red | **Small Blind 不给奖励金** | Zodiac |
| 3 | Green | 各 Ante 的目标分**缩放更快**（见 §10.4） | Painted |
| 4 | Black | 商店 **30%** 概率出现带 **Eternal** 贴纸的 Joker（不可出售/不可摧毁） | Anaglyph |
| 5 | Blue | 每回合 **−1 弃牌** | Plasma |
| 6 | Purple | 目标分**再加速缩放**（比 Green 更高，见 §10.4） | —（无牌组） |
| 7 | Orange | 商店 **30%** 概率出现带 **Perishable** 贴纸的 Joker（**5 回合后失效**） | Erratic |
| 8 | Gold | 商店 **30%** 概率出现带 **Rental** 贴纸的 Joker（**每回合 $3**） | —（最高档） |

> 贴纸互斥与叠加（✅ `/w/Card_modifiers#Appearance rates`）：Eternal 与 Perishable **互斥**，二者各 30% → 在 Orange/Gold 有 40% 的 Joker 两者皆无；Rental 独立 30% → Gold 下同时无任何 in-run 贴纸的概率为 40% × 70% = **28%**。
>
> 利息与赌注：**8 档赌注都不改变利息规则**；利息默认**每 $5 得 $1、上限 $5**（✅ `/w/To the Moon`：「limited by the current interest cap ($5 by default)」），上限只能由 `Seed Money`（$10）/`Money Tree`（$20）提升（✅ 两张 Voucher 页）。
---

## 6. Boss Blind（23 常规 + 5 Showdown）+ 2 标准盲注

> **来源**：`Category:Blinds by number` 各盲注页 `{{Blind info}}`（`number` / `type` / `description` / `ante` / `score` / `reward` / `compat-matador`），2026-11-15，**✅**。
> **分数倍率** = 该盲注相对**同 Ante 基础分**的倍数（基础分见 §10.4）。奖励为击败后的现金。

### 6.1 标准盲注（参照，可跳过换 Tag）

| 名称 | 类型 | 分数倍率 | 奖励 | 效果 |
|---|---|---:|---:|---|
| Small Blind | Standard | **1.0×** | $3（Red 赌注起为 $0） | 无特殊效果；可跳过换 1 个 Tag |
| Big Blind | Standard | **1.5×** | $4 | 无特殊效果；可跳过换 1 个 Tag |

### 6.2 常规 Boss Blind（23，最低 Ante 与效果）

| # | 名称 | 最低 Ante | 分数倍率 | 奖励 | 效果（自写概括） |
|---:|---|---|---:|---:|---|
| 3 | The Hook | Any | 2× | $5 | 每打出一手后，随机弃掉手中 **2 张**牌 |
| 4 | The Ox | **6** | 2× | $5 | 若打出**本局最常用牌型**，金钱直接归 **$0**（并列时随机取其一 ⏳） |
| 5 | The House | 2 | 2× | $5 | 本回合**第一手**牌背面朝上 |
| 6 | The Wall | 2 | **4×** | $5 | 目标分为基础分的 **4 倍**（超大盲注） |
| 7 | The Wheel | 2 | 2× | $5 | 每次抽牌有 **1 in 7** 概率背面朝上 |
| 8 | The Arm | 2 | 2× | $5 | 打出牌型的等级 **−1**（永久，结算在计分前；1 级不再降） |
| 9 | The Club | Any | 2× | $5 | 所有**梅花**牌失效（debuffed） |
| 10 | The Fish | 2 | 2× | $5 | 每打出一手后抽到的牌**背面朝上** |
| 11 | The Psychic | Any | 2× | $5 | 每手**必须打满 5 张**，否则不计分 |
| 12 | The Goad | Any | 2× | $5 | 所有**黑桃**牌失效 |
| 13 | The Water | 2 | 2× | $5 | 本回合起始**弃牌数 = 0** |
| 14 | The Window | Any | 2× | $5 | 所有**方块**牌失效 |
| 15 | The Manacle | Any | 2× | $5 | 本回合**手牌上限 −1** |
| 16 | The Eye | **3** | 2× | $5 | 本回合**每种牌型只能打 1 次**（重复则整手不计分） |
| 17 | The Mouth | 2 | 2× | $5 | 本回合**只能打第一手所用牌型**（其他牌型不计分） |
| 18 | The Plant | **4** | 2× | $5 | 所有**花牌**失效（J/Q/K，含 Pareidolia 效果下的牌） |
| 19 | The Serpent | **5** | 2× | $5 | 每次出牌或弃牌后**固定抽 3 张** |
| 20 | The Pillar | Any | 2× | $5 | **本 Ante 内此前打出过**的牌失效 |
| 21 | The Needle | 2 | **1×** | $5 | 本回合**只有 1 手**（目标分不翻倍） |
| 22 | The Head | Any | 2× | $5 | 所有**红心**牌失效 |
| 23 | The Tooth | **3** | 2× | $5 | 每打出 **1 张牌失去 $1**（含未计分牌；可致负债） |
| 24 | The Flint | 2 | 2× | $5 | 牌型的**基础 Chips 与 Mult 减半** |
| 25 | The Mark | 2 | 2× | $5 | 所有**花牌**抽到时背面朝上 |

### 6.3 Showdown Blind（5，仅 Ante 8 / 16 / 24 …）

| # | 名称 | 最低 Ante | 分数倍率 | 奖励 | 效果 |
|---:|---|---|---:|---:|---|
| 26 | Amber Acorn | 8 | 2× | **$8** | 所有 Joker **翻面并随机打乱位置** |
| 27 | Verdant Leaf | 8 | 2× | **$8** | 在**卖出 1 个 Joker 之前**，所有牌失效 |
| 28 | Violet Vessel | 8 | **6×** | **$8** | 目标分为基础分的 **6 倍**（超大盲注） |
| 29 | Crimson Heart | 8 | 2× | **$8** | 每手**随机禁用 1 个 Joker**（不会连续两次同一张，除非只有 1 个） |
| 30 | Cerulean Bell | 8 | 2× | **$8** | 强制**始终选中 1 张牌**（出牌/弃牌后重新随机指定） |

### 6.4 Boss 选择与规避规则

| 规则 | 内容 | 证据 |
|---|---|---|
| 随机池约束 | 只有「出现次数最少」的 Boss 才能被随机选中 → **在全部 Boss 至少出现一次前不会重复** | ✅ `/w/Blinds_and_Antes` |
| Ante 1 特殊 | Ante 1（含更低 Ante）只有 **8 个** Boss 可选 | ✅ 同上 |
| 重掷 | `Director's Cut`（每 Ante 1 次）/ `Retcon`（无限）可重掷 Boss，**$10/次**；Ante 8 及其倍数重掷**必出 Showdown**，其余 Ante **必出常规 Boss** | ✅ 同上 + `/w/Director's Cut`、`/w/Retcon` |
| 禁用效果 | `Luchador`（卖出时）与 `Chicot`（常驻）可关掉 Boss 效果；`The Wall` / `Violet Vessel` 的分数回到 2× 基础，`The Needle` 分数不再提升 | ✅ `/w/Blinds_and_Antes`、`/w/Chicot` |
| 跳过 | **Boss Blind 不可跳过**；Small/Big 可跳过换 1 个 Tag | ✅ 同上 |

---

## 7. Tag（24 个，跳过 Small/Big Blind 时获得）

> **来源**：`Category:Tags` 各 Tag 页 `{{Tag info}}`（`number` / `description` / `ante` / `unlock`），2026-11-15，**✅**。
> "出现 Ante"= 该 Tag 最早可能出现的 Ante（`Any` 表示 Ante 1 起）。

| # | Tag | 出现 Ante | 效果 | 解锁 |
|---:|---|---|---|---|
| 1 | Uncommon Tag | Any | 下一个商店出现 1 个**免费 Uncommon Joker** | 起始 |
| 2 | Rare Tag | Any | 下一个商店出现 1 个**免费 Rare Joker** | 发现 `Blueprint` |
| 3 | Negative Tag | **2+** | 下一个**基础版**商店 Joker 免费且变为 **Negative** | 发现 Negative 版式 |
| 4 | Foil Tag | Any | 下一个基础版商店 Joker 免费且变为 **Foil** | 发现 Foil 版式 |
| 5 | Holographic Tag | Any | 下一个基础版商店 Joker 免费且变为 **Holographic** | 发现 Holographic 版式 |
| 6 | Polychrome Tag | Any | 下一个基础版商店 Joker 免费且变为 **Polychrome** | 发现 Polychrome 版式 |
| 7 | Investment Tag | Any | 击败 Boss Blind 后 **+$25** | 起始 |
| 8 | Voucher Tag | Any | 下一个商店**多 1 张 Voucher** | 起始 |
| 9 | Boss Tag | Any | 立刻**重掷下一个 Boss Blind** | 起始 |
| 10 | Standard Tag | **2+** | 立刻获得并开启 1 个**免费 Mega Standard Pack**（5 选 2） | 起始 |
| 11 | Charm Tag | Any | 立刻获得并开启 1 个**免费 Mega Arcana Pack**（5 选 2） | 起始 |
| 12 | Meteor Tag | **2+** | 立刻获得并开启 1 个**免费 Mega Celestial Pack**（5 选 2） | 起始 |
| 13 | Buffoon Tag | **2+** | 立刻获得并开启 1 个**免费 Mega Buffoon Pack**（4 选 2） | 起始 |
| 14 | Handy Tag | **2+** | 本局**每打出过 1 手牌 +$1** | 起始 |
| 15 | Garbage Tag | **2+** | 本局**每有 1 个未使用弃牌 +$1** | 起始 |
| 16 | Ethereal Tag | **2+** | 立刻获得并开启 1 个**免费 Spectral Pack**（2 选 1） | 起始 |
| 17 | Coupon Tag | Any | 下次进入商店时，**初始出现的卡与补充包全部免费**（不含 Voucher，不含重掷后出现） | 起始 |
| 18 | Double Tag | Any | **复制下一个 Tag**（Double Tag 本身不被复制） | 起始 |
| 19 | Juggle Tag | Any | **下一回合手牌上限 +3** | 起始 |
| 20 | D6 Tag | Any | 下次商店**重掷起步价 $0**（之后每次 +$1） | 起始 |
| 21 | Top-up Tag | **2+** | 生成最多 **2 个 Common Joker**（无贴纸；槽位不足则少生成） | 起始 |
| 22 | Speed Tag | Any | 本局**每跳过 1 个盲注 +$5**（含本次） | 起始 |
| 23 | Orbital Tag | **2+** | 随机一个**牌型 +3 级** | 起始 |
| 24 | Economy Tag | Any | 金钱**翻倍**；若已达 $40 则改为 **+$40** | 起始 |

> ⏳ 未核实：`Double Tag` 与多个 Double Tag 叠加时的精确结算顺序，Wiki 文本只给了示例推演，**未作为规则声明**，标 ⏳。
---

## 8. 卡牌改造：增强 / 封蜡 / 版式 / 贴纸

> **来源**：`/w/Card_modifiers`（结构、出现率、价格影响）+ `Category:Enhancements`(8)、`Category:Seals`(4) 各页 `{{Modifier info}}` + `/w/Jokers`（版式数值），2026-11-15。
> 结构规则 ✅：**扑克牌**可同时带 1 个增强 + 1 个版式 + 1 个封蜡；**Joker** 可带 1 个版式 + 多个贴纸；**消耗品**正常不能带改造（`Perkeo` 生成的 Negative 副本例外）；**Voucher 与补充包**永不带改造。

### 8.1 增强（Enhancements，8 种，仅扑克牌）

| 名称 | 效果 | 来源/常见获得方式 |
|---|---|---|
| Bonus | 计分时 **+30 Chips** | The Hierophant、Standard 包、Illusion 商店 |
| Mult | 计分时 **+4 Mult** | The Empress、Standard 包 |
| Wild | 视为**任意花色** | The Lovers、Standard 包 |
| Glass | **×2 Mult**；计分结束后 **1 in 4** 破碎销毁 | Justice、Standard 包 |
| Steel | **在手时 ×1.5 Mult** | The Chariot、Standard 包 |
| Stone | **+50 Chips**；**无点数/无花色**（不参与组牌型，但总在计分内） | The Tower、Marble Joker、Standard 包 |
| Gold | **回合末仍留在手中** → **+$3** | The Devil、Midas Mask、Standard 包 |
| Lucky | 计分时 **1 in 5 → +20 Mult**；**1 in 15 → +$20**（两次独立判定，可同时触发） | The Magician、Standard 包 |

> 注（✅ `/w/Glass cards`）：重触发不会重掷 Glass 的 1/4 破碎判定；Lucky 的双效果独立 roll，`Lucky Cat` 把"同一次同时触发两个效果"只算 1 次。

### 8.2 封蜡（Seals，4 种，仅扑克牌）

| 名称 | 效果 |
|---|---|
| Gold Seal | 该牌被打出并计分时 **+$3**（每次重触发都再加） |
| Red Seal | 该牌**重触发 1 次**（出牌与在手效果都触发；Joker 不能让它再次触发） |
| Blue Seal | 若回合末仍在手中：生成**本回合最后打出的牌型**对应的 Planet 卡（受消耗品槽限制） |
| Purple Seal | 该牌被**弃掉**时生成 1 张 Tarot 卡（需有空消耗品槽） |

### 8.3 版式（Editions，5 种，含 Base）

| 名称 | 效果 | 备注 |
|---|---|---|
| Base | 无附加效果 | 所有卡默认状态 |
| Foil | **+50 Chips** | 提高购买价与售价 |
| Holographic | **+10 Mult** | 同上 |
| Polychrome | **×1.5 Mult** | 同上；Joker 上的 Polychrome 出现率被 Hone/Glow Up 放大更多（3×/7×） |
| Negative | **+1 对应槽位**（Joker 槽或消耗品槽） | 商店出现率 0.3%；`Perkeo` 可给消耗品加 Negative |

> ✅ **版式加价（edition cost）已取得**（`/w/Card_modifiers#Pricing` 渲染页，2026-11-15）：Joker 与扑克牌的 Foil **+$2** / Holographic **+$3** / Polychrome **+$5** / Negative **+$5**；消耗品只可能带 Negative（+$5，仅 `Perkeo` 生成）。与 [rules.md](rules.md) §7.4 一致。

### 8.4 贴纸（Stickers，in-run 3 种）

| 名称 | 效果 | 出现规则 |
|---|---|---|
| Eternal | 该 Joker **不能被出售或摧毁** | Black 赌注起，商店 Joker **30%** 概率；与 Perishable 互斥 |
| Perishable | **5 回合后失效**（debuffed） | Orange 赌注起，商店 Joker **30%** 概率 |
| Rental | 每回合结束时**支付 $3**；该 Joker 购买价为 **$1** | Gold 赌注起，商店 Joker **30%** 概率；所有 Joker 都兼容 |

> 另：`Stake Sticker`（White…Gold 共 8 种）是**纯展示**，记录该 Joker/牌组在哪个赌注通关，不影响对局数值（✅ `/w/Card_modifiers`）。
> 口径说明：任务描述写「贴纸 4」，而本次抓取到的 **in-run 贴纸只有 3 种**（Wiki：11 种 = 3 in-run + 8 stake）。第 4 项可能指 `Negative` 版式或 Stake Sticker，**未确认 ⏳**；本表按 in-run 3 种列，stake 贴纸见上一段。

### 8.5 改造出现率（随机生成时）

**Joker 版式与贴纸**（✅ `/w/Card_modifiers#Appearance rates`）：

| Voucher | Negative | Polychrome | Holographic | Foil | Eternal | Perishable | Rental |
|---|---:|---:|---:|---:|---:|---:|---:|
| 无 | 0.3% | 0.3% | 1.4% | 2% | 30% | 30% | 30% |
| Hone | 0.3% | 0.9% | 2.8% | 4% | 30% | 30% | 30% |
| Glow Up | 0.3% | 2.1% | 5.6% | 8% | 30% | 30% | 30% |

**扑克牌版式 / 增强 / 封蜡**（仅补充包内口径，✅ 同上）：

| Voucher | Polychrome | Holographic | Foil | 增强 | 封蜡 |
|---|---:|---:|---:|---:|---:|
| 无 | 1.2% | 2.8% | 4% | 40% | 20% |
| Hone | 2.4% | 5.6% | 8% | 40% | 20% |
| Glow Up | 4.8% | 11.2% | 16% | 40% | 20% |

> 注：每个增强/封蜡种类在各自池内**均匀分布**；`Illusion` 商店牌走另一套分布且 1.0.1o 有"不出封蜡"的 bug（见 §3 #26）。

---

## 9. 补充包（Booster Packs，5 类 × 3 尺寸 = 15 种）

> **来源**：`/w/Booster_Packs`（List of Booster Packs 表 + Booster Pack rates 表），2026-11-15，**✅**。
> 规则：每个商店固定提供 **2 个**补充包（**首次**进入商店时其中一个是 Normal Buffoon 包，`Jokerless` 挑战除外）；补充包**不随商店重掷刷新**；价格 **Normal $4 / Jumbo $6 / Mega $8**。

| 类别 | 尺寸 | 价格 | 展示张数 | 可选择数 | 内容 |
|---|---|---:|---:|---:|---|
| Arcana | Normal / Jumbo / Mega | $4 / $6 / $8 | 3 / 5 / 5 | 1 / 1 / **2** | Tarot 卡（立即使用） |
| Celestial | Normal / Jumbo / Mega | $4 / $6 / $8 | 3 / 5 / 5 | 1 / 1 / **2** | Planet 卡（立即使用） |
| Standard | Normal / Jumbo / Mega | $4 / $6 / $8 | 3 / 5 / 5 | 1 / 1 / **2** | 扑克牌（加入牌组，常带改造） |
| Buffoon | Normal / Jumbo / Mega | $4 / $6 / $8 | **2 / 4 / 4** | 1 / 1 / **2** | Joker 卡 |
| Spectral | Normal / Jumbo / Mega | $4 / $6 / $8 | **2 / 4 / 4** | 1 / 1 / **2** | Spectral 卡（立即使用） |

**各类补充包的抽取权重与出现率**（✅ 同上；权重和为 16.97）：

| 类别 | Normal 权重 / 出现率 | Jumbo 权重 / 出现率 | Mega 权重 / 出现率 | 合计权重 / 出现率 |
|---|---|---|---|---|
| Standard | 4 / 17.84% | 2 / 8.92% | 0.5 / 2.23% | 6.5 / **28.99%** |
| Arcana | 4 / 17.84% | 2 / 8.92% | 0.5 / 2.23% | 6.5 / **28.99%** |
| Celestial | 4 / 17.84% | 2 / 8.92% | 0.5 / 2.23% | 6.5 / **28.99%** |
| Buffoon | 1.2 / 5.35% | 0.6 / 2.68% | 0.15 / 0.67% | 1.95 / **8.7%** |
| Spectral | 0.6 / 2.68% | 0.3 / 1.34% | 0.07 / 0.31% | 0.97 / **4.33%** |

> 单包内容"永远按标称张数给满"（"up to" 只是措辞），但同一包内可能出现**重复卡**；补丁后 `Red Card` 在跳过任意补充包时都会 +3 Mult（含 Mega 包已选 1 张后再跳过）。
---

## 10. 随机性与权重（vanilla 事实）

### 10.1 Joker 稀有度

| 项 | 值 | 证据 |
|---|---|---|
| Common / Uncommon / Rare 生成权重 | **70% / 25% / 5%** | ✅ `/w/Jokers`、`/w/The_Shop` |
| Legendary | **商店不出现**；只能由 `The Soul` 生成（Spectral/Arcana 包内每张卡 0.3% 概率） | ✅ `/w/Jokers`、`/w/The_Soul` |
| 同屏去重 | 同名 Joker 不会重复出现（除非持有 `Showman`，或由 `Ankh`/`Invisible Joker` 复制） | ✅ `/w/Jokers` |

### 10.2 商店结构与权重

| 项 | 值 | 证据 |
|---|---|---|
| 每次进入商店 | **2 张随机卡** + **2 个补充包** + **1 张 Voucher** | ✅ `/w/The_Shop` |
| 随机卡权重 | Joker **20** / Tarot **4** / Planet **4** → 约 **71.4% / 14.3% / 14.3%** | ✅ `/w/The_Shop`、`/w/Tarot Merchant` |
| 首次商店保底 | 其中 1 个补充包**固定为 Normal Buffoon Pack**（`Jokerless` 挑战除外）；`Bram Poker` 挑战不刷 Joker | ✅ `/w/Booster_Packs`、`/w/Jokers` |
| 重掷 | 起步 **$5**，每次 **+$1**，进入新商店重置；**不刷新补充包与 Voucher**；Voucher 打完 Boss 后刷新 | ✅ `/w/The_Shop` |
| 重掷降价 | `Reroll Surplus` 起步 $3；`Reroll Glut` 起步 $1；`Chaos the Clown` 首次免费；`D6 Tag` 下次商店起步 $0 | ✅ `/w/The_Shop`、各 Voucher 页 |
| 花色/点数相关卡的当场目标 | `Mail-In Rebate`、`Castle`、`The Idol`、`Ancient Joker` 的目标**按牌组构成加权随机**，每回合更换 | ✅ 各 Joker 页 |
| 补充包内容 | 每局按 seed 有**固定顺序**；同种补充包开包顺序不影响结果 | ✅ `/w/Booster_Packs` |
| 其它 seed 事实 | 种子决定全部随机要素（Wiki Seed 条目，引用 1.0.1o 源码）；本仓库仅在 `docs/data-sources.md` §1 记录为 **✅ 已用于开题报告**，**不声称复刻 RNG** | △ 二手引用（见 [data-sources](../data-sources.md)） |

### 10.3 改造出现率

见 **§8.5**（Joker 版式/贴纸表、扑克牌版式/增强/封蜡表）。要点：默认 Edition 概率很低（Joker Poly 0.3% / Foil 2%），`Hone` 与 `Glow Up` 各放大一档；Black/Orange/Gold 赌注分别给 Eternal/Perishable/Rental **各 30%**。

### 10.4 Ante 目标分（△ 来自版本历史表）

> ⚠️ **证据等级 △**：该表取自 `/w/Blinds_and_Antes` 的 **Update history（1.0.0h / 1.0.1f）** 段落，而非"当前版本渲染表"（该页目标分由 `{{Ante Table}}` 模板生成，本次未展开）。表中为 **1.0.1f 之后的当前值**（`A -> B` 形式表示 1.0.1f 把 A 改为 B）。**1.0.1f 之后未见再次改动**，但**未在 1.0.1o 实机核对**，用于 W3 目标值时需 A2 实测确认。

| Ante | 基础（White / Red / Black / Blue） | Green 及以上 | Purple 及以上 |
|---:|---:|---:|---:|
| ≤ 0 | 100 | 100 | 100 |
| 1 | **300** | 300 | 300 |
| 2 | 800 | 900 | 1,000 |
| 3 | 2,000 | 2,600 | 3,200 |
| 4 | 5,000 | 8,000 | 9,000 |
| 5 | 11,000 | 20,000 | 25,000 |
| 6 | 20,000 | 36,000 | 60,000 |
| 7 | 35,000 | 60,000 | 110,000 |
| 8 | 50,000 | 100,000 | 200,000 |

补充事实（✅ `/w/Blinds_and_Antes`）：
- Small / Big / Boss 的目标分 = 基础分 × **1.0 / 1.5 / 2.0**（`The Wall` 4×、`Violet Vessel` 6×、`The Needle` 1×）。
- **Plasma 牌组**把全部 Ante 目标分**×2**。
- Ante 9+（无尽模式）公式：`需求 = Ante8需求 × (1.6 + (0.75·n)^(1+0.2·n))^n`（n = Ante−8），结果**四舍五入到 2 位有效数字**；n≥2 与表中数值逐项吻合，n=1（Ante 9）原文表 110,000 与公式算得 115,435 有差异 ⏳。
- Ante 39 起分数超出 double 上限（≈1.8e308）→ 显示 `naneinf`，无法通关，是无尽模式上限。

### 10.5 Boss 选择规则

见 **§6.4**（最低 Ante、最少出现次数优先、Ante 1 只有 8 个、重掷规则、不可跳过）。

### 10.6 补充包抽取规则

见 **§9**（权重表，权重和 16.97；Normal/Jumbo/Mega 权重比 4 : 2 : 0.5，Spectral/Buffoon 为 0.6/1.2 : 0.3/0.6 : 0.07/0.15）。

---

## 11. 术语对照

> **注意**：任务要求"与 `rules.md` 保持一致"，但本次工作区内 **`docs/balatro/rules.md` 尚未出现**（另一路产出），因此下表是**本文自用的对照表**，以**英文原名为权威标识**；若 `rules.md` 采用不同译名，**以 `rules.md` 为准并把差异回填本文**（⏳ 待对齐）。

| 英文 | 中文（本文用） | 说明 |
|---|---|---|
| Blind / Small Blind / Big Blind / Boss Blind / Showdown Blind | 盲注 / 小盲注 / 大盲注 / Boss 盲注 / 决胜盲注 | Showdown 只在 Ante 8（及 16/24…）出现 |
| Ante | 底注（回合段） | 每个 Ante = 3 个盲注；含 Ante 0/−1 可能 |
| Stake | 赌注 | 8 档，逐档叠加 |
| Deck | 牌组 | 15 个常规牌组 + 20 个挑战牌组 |
| Joker | 小丑（Joker） | 本文一律保留英文名，避免与"Joker 卡 `Joker`"混淆 |
| Consumable | 消耗品 | Tarot / Planet / Spectral 三类 |
| Voucher | 凭证 | 基础版 → 升级版成对 |
| Tag | 标签 | 跳过 Small/Big Blind 获得 |
| Booster Pack | 补充包 | 5 类 × 3 尺寸 |
| Enhancement | 增强 | 8 种，仅扑克牌 |
| Seal | 封蜡 | 4 种，仅扑克牌 |
| Edition | 版式 | Base/Foil/Holographic/Polychrome/Negative |
| Sticker | 贴纸 | in-run：Eternal/Perishable/Rental；另有纯展示的 Stake Sticker |
| Debuffed | 失效（被禁用） | 效果与版式全部不触发（Stone 无点数花色、Negative 仍 +1 槽） |
| Retrigger | 重触发 | 再结算一次该牌的计分效果 |
| Chips / Mult / XMult | 筹码 / 倍率 / 倍率乘数 | `XMult` 即 ×Mult |
| Hand | 手（出牌次数） | 基础 4 手（△：本次抓取页只以 `+1 手 / −1 手` 表述，未取得单一声明；Blue 牌组 +1、Black 牌组/Blue 赌注 −1） |
| Discard | 弃牌 | 基础 3 次（△：由 `/w/Delayed Gratification`「平均牌组 3 次弃牌」推断；Red 牌组 +1、Blue 赌注 −1） |
| Hand size | 手牌上限 | 默认 **8 张** ✅（`/w/The Manacle`：「若通常手牌上限为 8，则为 7」） |
| Reroll | 重掷 | 商店/Boss 重掷 |
| Interest | 利息 | 每 $5 得 $1，默认上限 $5 |
| Cash out | 结算界面 | 击败盲注后的结算 |
| Sell value | 售价 | `floor(buy_cost/2)`，最低 $1 |

---

## 12. 来源清单

> 抓取方式：`web_fetch`；批量数据用 MediaWiki API（`action=query&generator=categorymembers` 或 `titles=`，只取 `rvsection=0` 即 infobox 段）。**抓取日期：2026-11-15**。

| # | URL | 用途 | 证据 | 抓取日期 |
|---:|---|---|---|---|
| 1 | https://balatrowiki.org/w/Jokers | 150 总数、105/45、稀有度 61/64/20/5、70/25/5、关键词（Contains/Is/Retrigger/Debuffed）、平均价 | ✅ | 2026-11-15 |
| 2 | https://balatrowiki.org/api.php?action=query&generator=categorymembers&gcmtitle=Category:Jokers | 150 个 Joker 单页 `{{Joker info}}`（number/rarity/buyprice/effect/activation/type），分 6 批 `titles=` 抓完 | ✅ | 2026-11-15 |
| 3 | https://balatrowiki.org/w/Blinds_and_Antes | 盲注体系、Ante 表来源（版本历史）、无尽公式、Boss 选择规则、Plasma ×2 | ✅/△ | 2026-11-15 |
| 4 | https://balatrowiki.org/api.php?action=query&generator=categorymembers&gcmtitle=Category:Blinds_by_number | 30 个盲注页 `{{Blind info}}`（分数倍率/最低 Ante/奖励/效果） | ✅ | 2026-11-15 |
| 5 | https://balatrowiki.org/w/Stakes ＋ API `Category:Stakes_by_number` | 8 档赌注效果与解锁牌组 | ✅ | 2026-11-15 |
| 6 | https://balatrowiki.org/w/Decks ＋ API `Category:Decks_by_number` | 15 个牌组效果与解锁条件 | ✅ | 2026-11-15 |
| 7 | API `Category:Tarot Cards` / `Category:Planet Cards` / `Category:Spectral Cards` | 22 / 12 / 18 张消耗品 `{{Consumable info}}` | ✅ | 2026-11-15 |
| 8 | API `Category:Vouchers by number` | 32 张 Voucher（基础/升级、效果、解锁） | ✅ | 2026-11-15 |
| 9 | API `Category:Tags` | 24 个 Tag 效果与出现 Ante | ✅ | 2026-11-15 |
| 10 | API `Category:Enhancements` / `Category:Seals` | 8 种增强、4 种封蜡数值 | ✅ | 2026-11-15 |
| 11 | https://balatrowiki.org/w/Card_modifiers | 改造结构、版式/贴纸规则、**出现率两表**、价格影响（版式加价 ⏳） | ✅/⏳ | 2026-11-15 |
| 12 | https://balatrowiki.org/w/Booster_Packs | 15 种补充包价格/张数/可选数 + 权重与出现率 | ✅ | 2026-11-15 |
| 13 | https://balatrowiki.org/w/The_Shop | 商店结构、随机卡权重、重掷、**买价/售价公式**、基础价表、Voucher $10 | ✅ | 2026-11-15 |
| 14 | https://balatrowiki.org/w/Joker、`/w/Jolly_Joker`、`/w/Zany_Joker`、`/w/Sly_Joker`、`/w/Wily_Joker`、`/w/Half_Joker`、`/w/The_Duo`、`/w/The_Trio` | W3 的 8 个 vanilla Joker 逐卡数值/价格/解锁 | ✅ | 2026-11-15 |
| 15 | https://balatrowiki.org/w/The_Soul、`/w/Black Hole`、`/w/Canio` | 0.3% 替换率、Spectral 不能生成这两张、Legendary 价格 $20 不可购 | ✅ | 2026-11-15 |
| 16 | https://balatrowiki.org/w/Template:Stake_Table、`/w/Template:Blind_Table` | **反证**：数据不在模板里（模板只是 DPL 查询），须回到单页 infobox | ✅ | 2026-11-15 |

### 12.1 本次未能核实的项（⏳ 汇总）

| 项 | 状态 | 影响 |
|---|---|---|
| 版式加价（edition_cost）具体数值 | ⏳ 模板未展开 | §8.3 只给公式不给数值；需要时另抓 `Template:Edition costs table` |
| `The Hierophant` / `The Lovers` 的图鉴编号在 Wiki 中同为 7 | ⏳ 疑 Wiki 数据错 | §2.1 编号列可能有一处偏移 |
| `The Ox` 在「最常用牌型并列」时的选择规则 | ⏳ Wiki 自带 `{{verify}}` | §6.2 #4 |
| `Hieroglyph`/`Petroglyph` 能把 Ante 压到多低（Ante 0/−1 是否为硬下限） | ⏳ 只有示例推演 | §3 |
| 多个 `Double Tag` 叠加的结算顺序 | ⏳ 只有示例 | §7 #18 |
| Ante 目标分是否为 1.0.1o 现值 | △（1.0.1f 历史表） | §10.4，W3 目标值须 A2 实测 |
| `rules.md` 术语表对齐 | ⏳ 该文件本次不存在 | §11 |

### 12.2 使用边界（重申）

- 本文件的事实**只用于 W3 对齐的参考基线**，**不构成对齐证据**；`bench/` 当前为 **L0（未对齐）**，A0–A4 与 12 局终验均未执行（📋）。
- 所有数值若与真游戏冲突，**以真游戏捕获（A2/A4）为准**；冲突记 `E1 env_divergence`（数据质量门禁，非 Agent 失败）。
- 引用本文件时请同时引用 `docs/data-sources.md` §5 的许可边界（CC BY-NC-SA 只取事实、描述自写、不贴图）。






