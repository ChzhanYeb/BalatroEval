# BalatroEval ↔ vanilla Balatro 规则差异映射（L0 现状 → W3 目标）

> 用途：把 [rules.md](rules.md) 记录的原版事实，对照本仓库 `bench/`（提交 `c65fb9b`，W2-v2.1）的实际实现，逐项列出差异与 W3 目标值，供 [plan/01-每周任务.md](../../plan/01-每周任务.md) W3 任务 3–4 直接使用。
> **边界（红线）**：本文是**差异清单**，不是对齐证据。当前规则等级仍是 **L0（未对齐）**；`scenarios/RULES_VERSION` 的 `fidelity_status` 保持 `NOT_VERIFIED`。任何"已对齐/A2 通过"的表述都无效，直到 `docs/engine-fidelity.md` A 表有真游戏实测行。
> **2026-11-17 状态更新**：§1/§4 的 `bench/` 现状列是 **2026-11-15 的 L0 快照**；W3 目标值（§7）已在 `bench/` 实现（见 [../implementation/rules-implementation.md](../implementation/rules-implementation.md) 与 `tests/`），但 A2/A3 真游戏实测仍未执行，因此本文的“目标值”与“现状”不应再混读：**实现 ≠ 验证**。
> 基线：`bench/` `c65fb9b`；vanilla 事实来源见 [rules.md](rules.md) §13 与 [content.md](content.md) §12。
> 版本：2026-11-15 ｜ 状态：📋 全部为待改造项（W3）

---

## 0. 一句话结论

当前引擎是一个**自定义 3 盲注、3 Joker 槽位、无金钱/商店/消耗品/卡牌改造**的确定性计数子集；它缺的不只是数值，而是**原版计分公式（牌型基础 Chips×Mult + 计分牌筛选 + 手牌等级）**与**资源/经济层**。W3 需要改的是 `scoring.py`、`jokers.py`、`engine.py` 三处核心常量与语义，并且必须先用真游戏捕获（A2/A4）证明改造后的分数与资源一致。

---

## 1. 差异总表

| # | 维度 | vanilla 1.0.1o（事实） | `bench/` 现状（L0） | 差异等级 | W3 动作（来源） |
|---:|---|---|---|---|---|
| 1 | 一局范围 | 8 个 Ante × 3 盲注（Small/Big/Boss），Ante 8 Showdown 通关；之后可 Endless | 3 个"盲注"，第 3 个达标即 `win` | **高** | 只做 Ante 1 三盲注（W3 任务 3–4） |
| 2 | 盲注目标 | Ante 1 基础 300；Small ×1=300、Big ×1.5=450、Boss ×2=600（Red Deck / White Stake） | `TARGETS = (300, 800, 2000)` 顺序递增，等于 Ante 1/2/3 的基础分，**不是同一 Ante 的三盲注** | **高** | `TARGETS = (300, 450, 600)`；语义改为 Ante 1 三盲注 |
| 3 | 手/弃资源 | 基础 4 手 / 3 弃；Red Deck **+1 弃**（→ 4 手 / 4 弃）；Blue Stake −1 弃 | `HANDS_PER_BLIND=4`、`DISCARDS_PER_BLIND=2` | **高** | Red Deck 目标值 4/4 |
| 4 | 手牌上限 | 8（可被 Boss/卡牌改变） | `INITIAL_HAND_SIZE=8` | ✅ 同 | 保持；补"手牌上限"独立常量 |
| 5 | Joker 槽位 | 基础 5；可被 Negative 等扩展 | 硬编码 `len(jokers) >= 3` | **高** | 5 槽；槽位上限常量化 |
| 6 | 计分公式 | `chips = 牌型基础 Chips + 计分牌 rank chips + …`；`mult = 牌型基础 Mult`；`score = floor(chips × mult)`（取整方式 ⏳ 待 A2 实测，候选口径 floor）；等级 1 的 9 种牌型有固定基础值 | `chips = Σ 所选牌 rank chips`（**无牌型基础 Chips**）；`mult = HAND_MULT[牌型]`（自定义表） | **高** | 引入牌型基础 Chips×Mult；见 §2 |
| 7 | 牌型基础 Mult | 高牌1 / 对子2 / 两对2 / 三条3 / 顺子4 / 同花4 / 葫芦4 / 四条7 / 同花顺8（隐藏牌型 12/14/16） | 高牌1 / 对子2 / 两对3 / 三条4 / 顺子5 / 同花6 / 葫芦8 / 四条10 / 同花顺12 | **高** | 换成 vanilla 表（等级 1） |
| 8 | 计分牌筛选 | 只有参与牌型的牌计 rank chips；高牌只计最高 **1** 张、对子 2、两对 4、三条 3、顺子/同花/葫芦/同花顺 5、四条 4（可带 1 张不计分牌） | **所选 1–5 张全部计分**，未复刻筛选 | **高** | 实现 `scoring_cards()` 并按牌型筛选 |
| 9 | 手牌等级 | 等级 L≥1，无上限；每级加固定增量（如对子 +15 chips/+1 mult）；Planet 卡升级 | 无等级概念 | **中** | W3 固定等级 1（不实现 Planet） |
| 10 | 计分顺序 | 牌型基础 → 打出牌逐张 → 手中 held/Steel 类 → Joker 从左到右 → 版本/重触发；末尾一次取整 | 牌型基础（仅 mult）→ 所选牌逐张 chips（合并成一条 trace）→ Joker 从左到右 → 末尾一次 floor | **中** | 顺序按真游戏实测确认；先对齐"基础→逐张→Joker→floor" |
| 11 | 牌型集合 | 9 常规 + 3 隐藏（Five of a Kind / Flush House / Flush Five）+ Royal Flush 显示特例 | 仅 9 常规；无隐藏牌型（标准 52 张牌组本身也打不出） | 低（子集内可排除） | `RULES_VERSION.excluded` 明列 |
| 12 | 牌型判定边界 | 四条约 4 张同点；两对/葫芦要求不同点数；A 可高可低；同花/顺子需 5 张 | 优先级 `同花顺→四条→葫芦→同花→顺子→三条→两对→对子→高牌`；A 高/低均支持；同花/顺子/葫芦限 5 张 | ✅ 基本同 | 补"四条含 kicker"与"两对 4 张"金样 |
| 13 | Joker 目录 | 约 150 个具名 Joker，稀有度 Common/Uncommon/Rare/Legendary | 8 个合成夹具（`jc_*`/`jm_*`/`jx_*`），**不是原版 Joker** | **高** | W3 实现 8 个 vanilla Joker（见 [joker-semantics.md](../joker-semantics.md) §2） |
| 14 | Joker 触发条件 | 多数 Joker 带条件（含对子/含三条/出牌张数等）；含"是否含对子"的包含关系 | 夹具全部**无条件**生效；`Joker` 模型无 `condition` 字段 | **高** | 新增 `condition` 字段与包含关系判定 |
| 15 | Joker 顺序 | 从左到右；Blueprint/Brainstorm 复制、重触发等复杂语义 | 严格槽位顺序；无复制/重触发 | 中 | 保留槽位顺序；复杂语义进 `excluded` |
| 16 | 消耗品 | Tarot 22 / Planet 12 / Spectral 18；2 个消耗品槽 | 无 | **高** | `excluded`（Ante 1 子集不实现） |
| 17 | 商店与经济 | 每个盲注后现金结算 → 商店（2 卡 + 2 包 + 1 Voucher）；价格/reroll/利息 | 免费 3 选 1 Joker；无金钱、无价格、无 reroll | **高** | `excluded`（W3 不实现，报告明列） |
| 18 | 卡牌改造 | 8 增强 / 4 封蜡 / 4 版本（+Base）/ debuff / 暗牌 | 无任何卡牌属性 | **高** | `excluded` |
| 19 | 牌组与赌注 | 15 牌组、8 赌注 | 无；固定标准 52 张、无赌注 | 中 | 固定 Red Deck / White Stake 作为目标配置 |
| 20 | 随机性 | 种子决定洗牌/商店/盲注等；Boss 从"出场最少"中抽 | `random.Random(seed)` 洗牌 + 商店无放回抽样；RNG 状态完整写回 | ✅ 自洽（非原版 RNG） | 保持；不声称同种子同局面（D11） |
| 21 | 动作空间 | 8 张手牌时可出/弃 1–5 张（组合数 218） | 同样 C(8,1..5)=218；动作绑定稳定卡牌 id | ✅ 同 | 保持；补 discard 计数一致性测试 |
| 22 | 跨盲注牌堆 | 新盲注重新发满手牌（具体牌堆/弃牌处理以真游戏实测为准 ⏳） | 进入新盲注**沿用同一副手牌与牌堆**，不重发 | 中 | 以 A1/A4 实测确认后决定是否改 |
| 23 | 胜负判定 | 达标即过盲注；手牌用完未达标即败（Mr. Bones 等例外） | 最后一次出牌同时达标且 `hands_left=0` 时判**达标优先**（win/shop） | ✅ 同（无 Mr. Bones） | 保持；记录为子集规则 |

> 等级说明：**高** = 影响单步分数或资源语义，必须 W3 改；**中** = 影响跨盲注/长期语义，W3 可固定或延后；**低** = 子集内不可达，写进 `excluded`。

---

## 2. 计分差异详解（同一手牌，两条公式）

以 `7♥ 7♦` 为例，均无 Joker（bench 的 `suit` 编码见 `bench/model.py`）：

| 口径 | 计算 | 结果 |
|---|---|---:|
| vanilla 等级 1 **Pair** | 牌型基础 10 Chips × 2 Mult；计分牌 2 张：7+7=14 Chips → (10+14) × 2 | **48** |
| `bench/` 当前 | 无牌型基础 Chips；chips = 7+7 = 14；mult = `HAND_MULT[PAIR] = 2` → floor(14×2) | **28** |
| vanilla Pair 等级 2 | 基础 (10+15) Chips / (2+1) Mult；+14 → (25+14) × 3 | **117** |
| `bench/` 当前 | 无等级概念 | 28（不变） |

再叠加两个 Joker（vanilla 事实：`Joker` +4 Mult、`The Duo` ×2 Mult；顺序敏感）：

| 槽位顺序 | vanilla（Pair L1，7♥7♦） | `bench/` 合成夹具等价演示 |
|---|---|---|
| `+4 Mult` → `×2 Mult` | (24) × (2+4) × 2 = 288 | floor(14 × 6 × 2) = 168 |
| `×2 Mult` → `+4 Mult` | (24) × (2×2+4) = 192 | floor(14 × (2×2+4)) = 112 |

> 结论：**"顺序敏感"这一结构两边都有，但数值不可比**。因此 `docs/engine-fidelity.md` 的 A2 只能逐局面比对 `engine_score == real_score`，不能靠手算或 Wiki 断言。

### 2.1 计分口径必要条件（W3 实现清单）

1. `chips` 起点 = 牌型基础 Chips（等级 1）；
2. `mult` 起点 = 牌型基础 Mult（等级 1）；
3. 逐张计分牌加 rank chips（A=11、J/Q/K=10、数字=面值），**只加参与牌型的牌**；
4. 逐张应用卡牌改造（W3 无改造 → 跳过）；
5. 按槽位顺序应用 Joker：`+Chips` / `+Mult` / `×Mult`；
6. 中间用精确有理数（`Fraction`）保留，只在末尾取整；**取整方式 ⏳ 待 A2 实测**（候选：floor 一次）；
7. 与盲注 target 比较，达标即过。

> 待真游戏实测确认（⏳）：`×Mult` 中间是否保留小数、held-in-hand 效果与 Joker 的先后、Royal Flush 是否只是显示差异（答案是"仅显示"，见 [rules.md](rules.md) §5）。

---

## 3. 牌型识别差异

| 项 | vanilla | `bench/` | 处理 |
|---|---|---|---|
| 9 常规牌型 | ✅ | ✅ | 保留 |
| 隐藏牌型 3 种 | ✅（需改牌组/消耗品） | ❌ | `excluded`：标准 52 张 + 无消耗品时不可达 |
| Royal Flush | 选择牌时显示为独立牌型，计分等同同花顺 | 无 | `excluded`（仅显示层差异，不影响分数） |
| 四条带 kicker | 4 张同点 + 1 张不计分牌仍成立 | `counts[0]==4` 即成立（kicker 也计 chips，见 §2 差异 8） | 与计分牌筛选一起修 |
| 两对 4 张 | 成立 | `counts.count(2)>=2` 成立 | ✅ |
| 葫芦必须 3+2 | 成立 | `len==5 and counts==[3,2]` | ✅ |
| A 高/低顺子 | 均成立，不能同时 | `_is_straight` 支持 wheel 与 Broadway | ✅ |
| 同花/顺子 5 张 | 成立 | `len(cards)==5` 限定 | ✅ |

---

## 4. 流程 / 资源差异（状态机层）

### 4.1 当前 `bench/` 状态机（事实）

- 常量：`TARGETS=(300,800,2000)`、`HANDS_PER_BLIND=4`、`DISCARDS_PER_BLIND=2`、`INITIAL_HAND_SIZE=8`、Joker 槽位 3。
- 阶段：`play` →（达标）`shop` →（选 Joker 换盲注）`play` → … → `done`（`win`/`loss`）。
- 商店：3 个候选 Joker，免费选 1；不花钱、不刷新、无补充包。
- 换盲注：加 Joker、`blind_idx+1`、换 `target`、`total_score=0`、资源重置、清 shop/outcome；**手牌与牌堆不重发**。
- 无：金钱、跳过盲注、Tag、Boss 效果、消耗品、Voucher、牌组/赌注、卡牌改造、Endless。

### 4.2 vanilla Ante 1（Red Deck / White Stake）目标状态

| 项 | 目标值 | 来源 |
|---|---|---|
| Ante 1 基础分 | 300 | [Blinds & Antes](https://balatrowiki.org/w/Blinds_and_Antes) |
| Small / Big / Boss | 300 / 450 / 600 | 同上 ×1 / ×1.5 / ×2 |
| 手 / 弃 | 4 / 4（Red Deck +1 弃） | [Decks](https://balatrowiki.org/w/Decks)、[Stakes](https://balatrowiki.org/w/Stakes) |
| 手牌上限 | 8 | [Gameplay rules](https://balatrowiki.org/w/Gameplay_rules) ⏳ 待复核 |
| Joker 槽位 | 5 | [Jokers](https://balatrowiki.org/w/Jokers) ⏳ 待复核 |
| 商店 | 每个盲注后：2 随机卡（Joker 权重 20 / Tarot 4 / Planet 4）+ 2 补充包 + 1 Voucher；reroll 从 $5 起、每次 +$1 | [The Shop](https://balatrowiki.org/w/The_Shop) |
| 现金结算 | 盲注奖励 $3/$4/$5 + 每剩余手牌 $1 + 利息 $1/$5 上限 $5 | [Money](https://balatrowiki.org/w/Money) |

> ⚠️ 关键语义修正：当前 `TARGETS=(300,800,2000)` 容易被误读为"三个盲注"，实际是 **Ante 1/2/3 的基础分**。W3 只做 Ante 1 时，三盲注应为 **300/450/600**，不是 300/800/2000。这个改法同时影响 `blind_idx` 的含义与所有依赖 target 的测试期望。

---

## 5. 内容差异（W3 子集之外，必须写进 `excluded`）

| 内容 | vanilla 规模 | 现状 | W3 处理 |
|---|---|---:|---|
| Joker | 约 150（含 Legendary） | 8 合成夹具 | 只实现 8 个具名 Joker；其余 `excluded` |
| Tarot / Planet / Spectral | 22 / 12 / 18 | 无 | `excluded` |
| Voucher | 32 | 无 | `excluded` |
| Booster packs | 6 类 × 3 尺寸 | 无 | `excluded` |
| 卡牌增强 / 封蜡 / 版本 | 8 / 4 / 4（+Base） | 无 | `excluded` |
| 牌组 / 赌注 | 15 / 8 | 无 | 固定 Red Deck / White Stake |
| Boss 效果 | 23 常规 + 5 Showdown | 无 | `excluded`（Ante 1 仍会出现 Boss，但 W3 只保留目标分，不实现效果） |
| Tag / 跳过盲注 | 全部 | 无 | `excluded` |
| Endless / 挑战牌组 | 有（Endless 底注 9 起；挑战 20 个）；Daily Run **未证实** ⏳ | 无 | `excluded` |

> 注意：即便 W3 只做 Ante 1，**Boss Blind 仍会出现**（Ante 1 有 8 个候选 Boss）。W3 若不复刻 Boss 效果，必须在场景入集时排除带效果的 Boss（或明确记录"该场景不含 Boss 效果"），不得让"含效果的 Boss"悄悄进入训练集。

---

## 6. 动作空间与可复现性

| 项 | vanilla | `bench/` | 结论 |
|---|---|---|---|
| 出牌 | 选 1–5 张，选择即预览牌型 | `C(8,1..5)=218` 个动作，稳定 `card_id` | ✅ 结构同；数值取决于手牌张数 |
| 弃牌 | 选 1–5 张，消耗 1 次弃牌 | 同上 218 | ✅；需确认弃牌张数上限与剩余弃牌次数 |
| 动作身份 | 以卡牌位置/实例为准 | `card_ids` 稳定身份 + 下标快照 | ✅ 可作为 A1 映射基础 |
| 随机性 | 种子决定；有完整 RNG 状态 | `rng_state` 完整写回；同 seed 可复现 | ✅ 本项目内可复现；**不声称**与原版同种子同局面 |
| 日志 | — | append-only JSONL，`schema_version:1` | 保持 |

---

## 7. W3 目标值清单（实现/验收可直接引用）

> 来源：`plan/01-每周任务.md` W3 任务 3–4 + 本文 §2/§4；数值来源见 [rules.md](rules.md) §5/§9。

### 7.1 计分（`bench/scoring.py`）

- [ ] 9 种牌型等级 1 基础 **Chips×Mult**：`5×1 / 10×2 / 20×2 / 30×3 / 30×4 / 35×4 / 40×4 / 60×7 / 100×8`（高牌/对子/两对/三条/顺子/同花/葫芦/四条/同花顺）；
- [ ] 计分牌筛选：高牌 1 / 对子 2 / 两对 4 / 三条 3 / 顺子·同花·葫芦·同花顺 5 / 四条 4；
- [ ] 等级固定 1（不实现 Planet 升级）；
- [ ] 末尾一次取整（候选 floor；⏳ 待 A2 确认），中间精确分数；
- [ ] 金样测试：至少覆盖 9 种牌型 + 4 条 kicker + 高牌 5 张只计 1 张。

### 7.2 资源与流程（`bench/engine.py`）

- [ ] `TARGETS = (300, 450, 600)`（Ante 1 Small/Big/Boss）；
- [ ] 4 手 / 4 弃（Red Deck）；
- [ ] 手牌上限 8；Joker 槽位 5；
- [ ] 换盲注语义：三盲注 = Ante 1 的三个盲注（不是三个 Ante）；
- [ ] 跨盲注手牌/牌堆处理按 A1/A4 实测结果决定（当前"沿用不重发"需标注为子集简化）。

### 7.3 Joker（`bench/jokers.py`）

- [ ] 8 个 vanilla Joker：`Joker` +4 Mult、`Jolly` +8 Mult（含对子）、`Zany` +12 Mult（含三条）、`Sly` +50 Chips（含对子）、`Wily` +100 Chips（含三条）、`Half` +20 Mult（≤3 张）、`The Duo` ×2 Mult（含对子）、`The Trio` ×3 Mult（含三条）；
- [ ] 新增 `condition` 字段；条件不满足时不触发；
- [ ] 合成夹具改名 `synthetic_*` 或移入 `tests/fixtures/`，与 vanilla 目录分命名空间。

### 7.4 显式排除（写入 `scenarios/RULES_VERSION.excluded`）

- Boss 效果、金钱/商店/利息、消耗品、Voucher、补充包、卡牌增强/封蜡/版本、多牌组、赌注、Tag/跳盲、Endless、隐藏牌型、Royal Flush 显示、Blueprint/重触发类 Joker。

---

## 8. 验收映射（改完怎么证明）

| 验收项 | 对应命令/证据 | 说明 |
|---|---|---|
| L0 自洽不回归 | `python -m unittest discover -s tests -v`（25 项） | 改造后测试期望值会变，必须同步更新并说明原因 |
| 计分金样 | 新增 `tests/` 金样用例 | 不能替代 A2；只证明"按本文档的目标值实现" |
| A2 单步分数 | `docs/engine-fidelity.md` A 表 + `evidence/W3/align/` | 真游戏捕获逐局面 `engine_score == real_score` |
| A1 状态映射 | `bench/convert.py` 逐字段 diff 报告 | `gamestate` ↔ `GameState` |
| A3 规则子集 | `RULES_VERSION` 的 `verified_against` / `excluded` | 只在签核后改 `fidelity_status` |
| A4 场景来源 | `scenarios/v3/*.jsonl` 的 `origin` + `capture_id` | 不通过者进 `rejected` 并写原因 |

> 重申：**本文档全部为 📋 待办**。在 A0–A4 签核前，README/报告只能写"L0 自定义子集"，不得写"已对齐 vanilla"。

---

## 9. 维护约定

1. 本文档的 vanilla 列以 [rules.md](rules.md) 为准；`bench/` 现状列必须与代码常量/函数逐项核对（改动后同步）。
2. 任何一项从 📋 改为 ✅，必须同时满足：有来源数值、有金样测试、有 A 表实测行（或明确标注"仅金样，非 A2"）。
3. 发现新差异先登记到 §1 总表，再改代码；不得"顺手修"后不留记录（AGENTS.md §6.6）。
4. 版本变化（游戏/mod）先更新 `scenarios/v3/MANIFEST.json`（A0），再重跑差异表。

---

## 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-15 | 初版：基于 `bench/` `c65fb9b` 与 vanilla 1.0.1o 事实的 23 项差异表 + W3 目标值清单 |
