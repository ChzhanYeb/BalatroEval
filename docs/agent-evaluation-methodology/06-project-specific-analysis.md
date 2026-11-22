# 06 · 当前项目的方法论映射与风险分析

> 本文只做一件事：**用前面四份文档的方法论，逐条检查 `BalatroEval` 现在的设计，指出哪些结论有证据、哪些没有、哪些必须先修。**
>
> **证据规则**：本文每个状态判断都必须能追到项目文件的具体行或实际代码。凡"文档说 A、代码是 B"的，我**并列写出两者**，不替项目选边。凡未执行的事，一律写"未执行"，不写成"计划中"以外的东西。
>
> 调研时点：2026-11-17。工作树有 17 个未提交修改（`git status`），HEAD 为 `0e403cf`，`AGENTS.md` 声明的基线是 `c65fb9b`——**这三个"版本"并不相同**，见 §6.12 冲突 C6。

---

## 0. 调研期间的仓库变动（必读）

**这次调研进行到一半时，仓库被并发修改了。** 这不是小事：它意味着"当前项目状态"这句话本身需要带时间戳。

| 时点 | 观察到的事实 | 证据 |
|---|---|---|
| **22:18–22:28** | `bench/` 有 11 个 `.py`；`Joker` 是 3 种效果的合成夹具；`scoring.score_hand` 用自定义公式（`7♥7♦` = 14×2 = **28**）；`engine.play(state, card_ids, log_path=...)` 会写 JSONL | 本次调研早期的文件读取 |
| **22:33–22:34** | 新增 `bench/errors.py`、`bench/hand_eval.py`、`bench/rules_version.py`；`bench/model.py`（216→261 行）与 `bench/jokers.py` 被重写为 **8 个具名 vanilla Joker**（带 `condition`/`rarity`/`buy_price`）；`GameState` 改为 `rules_version`/`ante`/`blind_kind`/`boss_effect`/`joker_slots=5`/`discards_left=4` | 文件 mtime：22:33:02 / 22:33:24 / 22:33:43 / 22:34:13 / 22:34:31 |
| **22:35–22:38** | 新增 `bench/serialize.py`（快照/还原/`state_hash`）；`engine.play(state, card_ids)` **不再接受 `log_path`**；没有任何模块 import `logging`（JSONL 写入器已脱钩）；`scoring` 变为 vanilla 口径（`7♥7♦` = (10+7+7)×2 = **48**，kicker 不计分） | `engine.py` 的 `def play` 签名；全仓 `from .logging` 无匹配；实测 `score_hand` |
| **22:45 复核** | 又新增 `bench/environment.py`（reset/observe/legal_actions/step/snapshot）、`bench/observation.py`、`bench/tools.py`（4 个游戏工具 + `reset_episode`，结构化错误码）；`bench/` 共 **18 个 `.py`**。`tests/test_w2_rules.py` **未变**（mtime 仍 11-12），unittest 因模块导入失败只报 1 个 error。`bridge/server.py` **仍只有占位 `get_state`** | 文件列表 + mtime；`bridge/server.py` 的 `@mcp.tool` 只有一处 |
| **22:50 复核** | 新增 `evaluation/` 目录：`agents.py` / `config.py` / `episode_runner.py` / `trace.py`——说明 Runner、Trace、Agent Adapter 已开始实现（内容未逐行核验） | 目录列表 |

**因此，本文件的状态判断分两类**：

1. **不变量**（两个快照都成立，结论稳定）：没有 money/interest 实现、没有 runner/evaluator/metrics/dataset、O1 仍只对 `play` 做局部 argmax、`bridge/server.py` 仍只有占位 `get_state`。
2. **时点事实**（会随重构变化）：模块数量、测试是否通过、计分公式、日志是否落盘、工具层是否成形。凡此类，本文都标"截至 22:38"或"22:45 复核"。

**复核命令**（任何人接手前应先跑）：

```powershell
python -m unittest discover -s tests -v
# 22:38 实测：Ran 25 tests, FAILED (errors=7)；22:45 复核：测试模块导入失败，只报 1 个 error
python -m bench demo --seed 20261112 --max-steps 50 --log $env:TEMP\demo.jsonl
# 22:38 预期会失败：__main__ 仍传 log_path=，而 engine.play 已不接受该参数
```

> **这一节本身就是一条方法论结论**：`AGENTS.md` 要求"改完必跑、输出贴原始结果"，而当前中间态**跑不过**。在重构完成前，任何基于代码的能力结论都应暂停；`plan/00` §6 的"W2 已交付、25/25 通过"描述的是 22:18 之前的快照。
>
> **本文引用基准固定为 22:38 快照**（个别处补 22:45 复核）。之后仓库仍在变化，但它**不改变本文的核心结论**（缺 runner/evaluator/metrics、money 仍 excluded、bridge 仍占位）；变的是具体数字与文件数。复核时以当时输出为准。

---

## 6.0 先确认"项目事实"

| 事实 | 证据 |
|---|---|
| 正式名 BalatroEval；定位"面向大模型 Agent 的长线规划测试集" | [README.md](../../README.md#L1-L3) |
| 四个目标能力：跨回合资源分配 / 多步决策 / 长期构建 / 失败恢复 | [plan/00-项目全貌.md](../../plan/00-项目全貌.md#L48-L55) |
| 四支柱**均未覆盖** | [README.md](../../README.md#L9-L15) 差距表；[scenarios/RULES_VERSION](../../scenarios/RULES_VERSION#L19) `long_horizon_pillars: ... NOT_COVERED` |
| `bench/` **截至 22:38 有 15 个 `.py`**（22:18 时为 11 个；新增 `errors`/`hand_eval`/`rules_version`/`serialize`） | `Get-ChildItem bench -Filter *.py` |
| 测试文件仍是 25 项，但**截至 22:38 有 7 个 error**（测试未跟上 `Joker` 签名变更） | [tests/test_w2_rules.py](../../tests/test_w2_rules.py)；实测 `Ran 25 tests ... errors=7` |
| 文档声明规则等级 L0（自定义公式 + 合成 Joker）；**代码已切到 `vanilla_1.0.1o_subset_v1`**（具名 Joker、5 槽位、基础 chips） | [scenarios/RULES_VERSION](../../scenarios/RULES_VERSION#L21-L24) vs [bench/rules_version.py](../../bench/rules_version.py) |
| 真游戏接入、对齐训练集、终验**均未执行** | [plan/00-项目全貌.md](../../plan/00-项目全貌.md#L192-L197) |

**这七条是本文所有判断的地基。** 注意第 4–6 条：它们说明**文档、代码、测试三者已经不同步**（见 §6.12 C10–C12）。这不影响"未完成项确实未完成"的判断，但意味着任何引用具体行号或具体分数的结论都必须标明快照时间。

---

## 6.1 当前项目试图测量什么能力

`plan/00` 给了四个维度（[§1](../../plan/00-项目全貌.md#L48-L55)）。逐条对照 [03](03-agent-benchmark-design.md) §3.2 的"操作性定义"标准：

| 目标能力 | 文档定义 | 是否有可观测行为定义 | 是否有对应任务 | 判定 |
|---|---|---|---|---|
| **跨回合资源分配** | "跨盲注/跨回合分配有限资源（出牌、弃牌、金钱、商店取舍）" | ⚠️ 部分（"分配"未定义指标） | ❌ 无（金钱/利息/价格被 excluded） | **不可测** |
| **多步决策** | "在一局内做多步 play/discard 决策" | ✅ 有（连续动作序列） | ⚠️ 有 L3（仅盲注内） | **部分可测** |
| **长期构建** | "沿 build 路径做 Joker/卡组协同的长期投资" | ❌ 无（"构建路径"无定义） | ❌ 无（shop 仅免费三选一） | **不可测** |
| **失败恢复** | "失败后重新规划并恢复" | ❌ 无（"恢复"无指标） | ❌ 无 | **不可测** |

**结论**：四个维度里，**只有一个（多步决策）有部分可操作定义与对应任务**，其余三个在机制层就被排除了。

这不是"实现进度落后"，而是**定义与机制不匹配**：
- "跨回合资源分配"需要资源跨回合累积，而 `choose_joker` 每盲注重置 `hands_left`/`discards_left`（[bench/engine.py](../../bench/engine.py) 的 `choose_joker`，截至 22:38 取 ruleset 的 4/4），且 `money`/`interest` 在 `rules_version.py` 的 `excluded` 中，`buy_price` 只作字段声明、不参与规则计算（[bench/rules_version.py](../../bench/rules_version.py)、[bench/model.py](../../bench/model.py#L135)）；
- "长期构建"需要购买/出售/价格，而 shop 只有 `_create_shop_options` 的免费三选一（[bench/engine.py](../../bench/engine.py#L89-L102)）；
- "失败恢复"需要"失败后还能继续"，而 `_after_play` 在 `hands_left==0` 时直接 `done + loss`（[bench/engine.py](../../bench/engine.py#L105-L128)），没有恢复窗口。

> **这一节的方法论要点**：能力定义必须能落到"环境里存在该机制"。机制不存在时，无论指标多精细，都测不到该能力。这是**构念效度（construct validity）**的最低门槛。

---

## 6.2 任务设计能否真正测量目标能力

### 6.2.1 "场景"目前是单决策点，不是 episode

`plan/详细版/03` §1 明确："场景（scenario）= 一个固定的初始局面 + 合法动作集 + oracle，是评测的最小单位"（[plan/详细版/03-评测集与指标.md](../../plan/详细版/03-评测集与指标.md#L15-L24)）。

这个定义对应的是 **contextual bandit（上下文赌博机）**，不是 MDP episode：

| | 单决策点（当前） | episode（长程所需） |
|---|---|---|
| 一次评测 | 1 个状态 + 1 个动作 | 初始状态 + 动作序列 + 终止 |
| 可测指标 | Local Regret、Optimality、Legality | Success、Progress、Recovery、pass^k |
| 能否测"多步" | ❌ | ✅ |

**代码证据**：`bench/` 里没有任何"场景 → episode"的执行器。`__main__.run_demo` 只是用 O1 贪心跑一局**演示**（[bench/__main__.py](../../bench/__main__.py#L62-L96)），它不是 Agent 评测：没有 Agent 输入、没有工具、没有 trace。

### 6.2.2 更严重的问题：在当前机制下，贪心近似最优

这是本文对项目最重要的判断，需要完整论证。

**命题**：在现有规则下，"每次出牌都选当前最高分"的策略，对于"在 4 次出牌内达到目标分"这个目标，近似最优。

**论证**：

1. 目标是一个**阈值**：`total_score >= target` 即通过（[bench/engine.py](../../bench/engine.py#L117)）。超出部分没有任何收益（不加钱、不留存、不换资源）。
2. 资源**每盲注重置**：`hands_left` / `discards_left` 在 `choose_joker` 里按 ruleset 重置（截至 22:38 为 4/4，[bench/engine.py](../../bench/engine.py)）。省下来的出牌次数不会带到下一盲注。
3. 没有跨盲注可累积资源：`GameState` 没有 money/interest 字段，`rules_version.py` 把 `money`/`interest` 列入 `excluded`（[bench/rules_version.py](../../bench/rules_version.py)）；Joker 只能通过免费三选一获得，且不能出售。
4. 因此，"本盲注内每次出牌都最大化当前得分"与"最小化达标所需手数"是同一件事；而不存在"现在少拿分以换取未来更多分"的机制。

**推论 1**：`Local Regret`（单步与 oracle 的差距）在当前机制下，**近似等于整体表现**。这既是好消息（指标有信号），也是坏消息（**它测的是战术，不是规划**）。

**推论 2**：任何"长线规划"主张都不能建立在 Local Regret 上，因为该环境里**最优策略本身就是短视的**。用一句更尖锐的话说：**这个环境不需要规划，所以它测不出规划。**

> **这与项目文档的关系**：`plan/详细版/03` §1.2 已经承认"L3 只是同一盲注内、不跨盲注"，README 也把四支柱标为未覆盖。**本文的判断与文档一致，只是把理由从"场景没建"推进到"机制不支持"。** 这一点对 W3 改造很关键：只加场景不够，必须加**跨阶段可累积的稀缺资源**（见 [03](03-agent-benchmark-design.md) §3.3.4）。

### 6.2.3 L1/L2 场景测的是"规则理解 + 组合搜索"

一个 8 张手牌、218 个候选的单步 argmax（[bench/actions.py](../../bench/actions.py#L9)、[bench/oracle.py](../../bench/oracle.py#L37-L62)），其难度来源是：

1. 是否理解自定义计分公式（chips × mult，`HAND_MULT` 表）；
2. 是否能在 218 个组合里找到最大值（对 LLM 而言是"算 + 比"）；
3. 是否能正确调用工具、传对卡牌 id。

**它不是规划**。而且它有一个隐蔽的效度问题：**oracle 目标是"当前手牌最高分"，但如果最优策略是"弃牌换更好的手牌"，O1 会把弃牌判为 0 分动作**（因为 `best_play` 只对 `play` 枚举，[bench/oracle.py](../../bench/oracle.py#L49-L57)）。于是：

- 一个"会弃牌"的聪明 Agent，如果在这一步选择弃牌，会被记为 `regret = 1`（`actual = 0`）；
- 一个"只会闷头打"的 Agent，反而得分。

**这是目标函数不匹配导致的系统性偏差**，不是实现 bug。项目文档已经规定"Local Regret 仅在 play 决策上定义"（[plan/00](../../plan/00-项目全貌.md#L24)），但**没有规定"在 play 决策点上选择 discard 时如何计分"**的语义边界。`plan/详细版/03` §3.2 的"边界处理"写了"Agent 在该出牌时选择了 discard（合法但零得分）→ 记 actual=0，regret=1"——这条规则**会惩罚正确行为**，需要重新设计（见 P0-3）。

---

## 6.3 当前环境与真实游戏的差异

`scenarios/RULES_VERSION` 的 `excluded` 列了 20+ 项（[L32](../../scenarios/RULES_VERSION#L32)）。下表按"是否影响被测能力"分类，并标出**截至 22:38 代码的实际状态**（注意：代码已开始向 vanilla 子集迁移，文档尚未同步）：

| 差异 | 具体（截至 22:38） | 影响能力 | 影响程度 |
|---|---|---|---|
| 计分口径 | 代码已实现 vanilla 子集：牌型基础 Chips×Mult + 只计计分牌（[bench/rules_version.py](../../bench/rules_version.py#L7)），实测 `7♥7♦`=48；**文档仍写"自定义公式"** | 分数绝对值、策略排序 | **高**（且已造成文档-代码冲突，见 C10） |
| Joker | 代码：8 个**具名 vanilla Joker**（[bench/jokers.py](../../bench/jokers.py)）；文档仍写"合成夹具" | 构建/协同 | 高（C10） |
| 槽位 / 资源 / 目标 | 代码：5 槽位、4 手 4 弃、Small/Big/Boss = 300/450/600（[bench/rules_version.py](../../bench/rules_version.py#L92-L97)、[L184-L187](../../bench/rules_version.py#L184-L187)）；**文档仍写 3 槽位 / 4 手 2 弃 / 300-800-2000** | 难度曲线、资源压力 | 中（C10） |
| 无金钱/利息/价格/reroll | `excluded` 含 `money`/`interest`（[bench/rules_version.py](../../bench/rules_version.py#L223-L224)）；`buy_price` 仅声明不参与计算；shop 仍免费三选一 | **跨回合资源分配** | **致命（该能力仍不可测）** |
| Boss 效果 | `boss_effect` 字段已存在，但效果是否真正生效**待核验**（迁移中） | 适应/恢复 | 待定 |
| 无消耗牌/塔罗/星球 | `excluded` | 构建 | 高 |
| 无卡组改造 | `excluded` | 长期构建 | 高 |
| 不复刻 RNG | 只保证本项目内可复现 | 与真游戏同局面 | 中（已用捕获对齐缓解，但未执行） |

**方法论判断**：

1. 这些差异**不是"实现不完整"那么简单**，它们共同决定"这个环境能测什么"。当前组合（无经济、无构建、无 Boss 效果、资源重置）仍然把"长程"的三个来源去掉了——**即使计分已经 vanilla 化**。
2. 项目已经用"两阶段架构 + A0–A4 对齐契约"来处理差异，思路正确（见 [02](02-classic-benchmarks.md) §2.4.2 结论 2：可复现性来自重置机制）。但**对齐契约解决的是"分数是否一致"，不解决"机制是否存在"**。即使 A2 全过，只要没有 money，就测不到跨回合资源分配。
3. 从 22:38 的改动看，团队正在**先做对齐（vanilla 计分/Joker/参数）**。这在"让分数可信"这条线上是合理的；但它**不会自动带来长线能力覆盖**。两条线要分开算账：对齐等级（L0→L2）与能力覆盖（四支柱）是两个独立进度条，不能用前者替代后者。


---

## 6.4 Oracle 的保证范围

| Oracle | 代码 | 保证 | 不保证 |
|---|---|---|---|
| **O1** `best_play` | [bench/oracle.py](../../bench/oracle.py#L37-L62) | 当前手牌 218 个组合中 `final_score` 最大；同分取枚举首个 | 整局最优；弃牌最优；目标函数换成"通关概率"后仍最优 |
| **O2** `discard_ev` | [bench/oracle.py](../../bench/oracle.py#L76-L130) | 抽样模型下的期望分（K=50，均值/最小/最大） | 与引擎真实发牌一致（**不读 `rng_state`**，把 deck+discard 混池，忽略洗牌顺序） |
| **O3** `greedy_episode` | [bench/oracle.py](../../bench/oracle.py#L152-L187) | 一条近似对局轨迹 | 最优解/上界（`precision="approximate_greedy_not_global_optimum"`） |

**三个具体风险**：

1. **O1 的"最优"是目标函数相关的**。若未来把目标从"本手得分"改成"通关概率"，O1 立刻失效，但代码不会报错——它仍会返回一个"最优"。这是**静默失效**，最危险。
2. **O2 的抽样模型与环境不一致**。`discard_ev` 用 `state.seed ^ blind_idx*1009 ^ steps` 派生独立 RNG（[bench/oracle.py](../../bench/oracle.py#L104-L107)），并显式声明"不读取也不推进引擎的随机数状态"。这意味着 **O2 的 EV 不是引擎真实发牌的期望**，只是"某个抽样模型下的期望"。项目已标注 `approx`，正确；但报告里必须写"K=50 下、该抽样模型下"，不能写"期望值"。
3. **O3 的日志行为已变，但问题换了形式**。`greedy_episode` 仍调 `play()`/`choose_joker()`（[bench/oracle.py](../../bench/oracle.py#L169-L179)），而截至 22:38 `engine.play` 已不接受 `log_path`——所以它**不再污染** `data/episode.jsonl`，但代价是**引擎完全不写 trace**（见 §6.6）。这是"修复一个坑、挖出另一个坑"的典型：日志从"默认写且会污染"变成"根本不写"。

**结论**：O1 是合格的"单步精确 oracle"，O2 是合格的"近似参照"，O3 不是 oracle。三者都不能支撑"长线规划"结论——这不是实现问题，是**定义范围**问题。

---

## 6.5 指标是否与研究目标一致

`plan/详细版/03` §3 把指标分五层（[L126-L137](../../plan/详细版/03-评测集与指标.md#L126-L137)），这个结构是对的。逐层核对"定义 vs 可用性"：

| 层 | 指标 | 定义状态 | 实现状态 | 与目标一致性 |
|---|---|---|---|---|
| ① 合规 | Legality Rate、非法计数 | ✅ 定义清楚 | ❌ 无代码（trace 缺 `isError`） | ✅ 一致（门禁） |
| ② 单步战术 | Local Regret、Optimality、Discard EV Gap | ✅ 定义清楚（含 exact/approx） | ⚠️ O1/O2 可算，但无指标模块 | ✅ 与"战术"一致，❌ 与"规划"不一致 |
| ③ 跨期资源 | 资金/利息/商店收益 | ❌ 仅候选 | ❌ | ❌ 机制不存在，不可测 |
| ④ 长程 | Episode Progress、恢复率、pass^k | ⚠️ Progress 粗；恢复率未定义；pass^k 已取消 | ❌ | ❌ 不可测 |
| ⑤ 诊断 | 首次失败步、F1–F4/F0/E1 | ✅ 设计较完整 | ❌ `bench/attrib.py` 未创建 | ⚠️ 依赖 trace 字段（缺） |

**三个具体不一致**：

1. **主指标是单步的，主张是长程的**。`plan/00` D4 把 Local Regret 定为主指标，同时项目定位是"长线规划测试集"。文档自己已经写明"不得把 Local Regret 写成长线能力证据"（[plan/03 §3.2](../../plan/详细版/03-评测集与指标.md#L150)），但**主指标与主主张之间的鸿沟没有被填补**：③④ 层只有"候选"，没有定义。
2. **"首次失败步"依赖 regret 阈值 0.5**，而 regret 只在 play 决策上有定义。若一局里 Agent 大量弃牌（合法且可能正确），这些步没有 regret，首次失败步会漏掉它们。阈值 0.5 也没有依据（无 pilot 数据支撑）。
3. **`Episode Progress`（通过盲注数/3）取值只有 {0, 1/3, 2/3, 1}**，粒度极粗、方差大，小模型恒 0。文档已承认"不得当主指标"，正确。

---

## 6.6 当前 Trace 能支持哪些诊断

**现状**：存在两套互不兼容的"trace"：

| Trace | 位置 | 字段 | 用途 |
|---|---|---|---|
| 引擎迁移日志 | [bench/logging.py](../../bench/logging.py#L39-L46) | `schema_version / state_before / action / score_delta / score_details / state_after` | 规则自洽、重放（**截至 22:38 已无调用方**） |
| dsh 会话事件流 | `evidence/W1/*.jsonl.zstd` | message / tool call / tool result | Agent 行为 |

**引擎日志缺什么**（对照 [05](05-evaluation-framework-engineering.md) §4.5.2 的 Trace 必需字段）：

| 需要 | 有吗 | 影响 |
|---|---|---|
| **日志本身会不会被写** | ❌ **截至 22:38，没有任何模块 import `logging`**；`engine.play` 已不接受 `log_path` | 跑引擎**不产生任何 trace**（比"字段不足"更严重） |
| `episode_id` / `step_id` | ❌ | 无法把多行日志组成一局 |
| `timestamp` | ❌ | 无法算延迟、无法排序 |
| `observation`（Agent 实际看到的） | ❌ | 无法复现"模型看到了什么" |
| `agent_output`（原始输出） | ❌ | 无法做 F2（声称分数 vs 实际）与 F3（规则幻觉） |
| `parsed_action` vs `action` | ⚠️ 只有编码后的 action | 无法区分"解析错"与"决策错" |
| `action_valid` / `invalid_reason` | ⚠️ 新增了 `errors.py`（结构化错误），但尚未接入 trace | 无法统计 F1 |
| `latency_ms` / `token_usage` | ❌ | 无法做成本/延迟指标 |
| `error` | ⚠️ 有错误类型定义，未落盘 | 无法区分环境错与 Agent 错 |
| `termination_reason` | ❌（只有 `phase`/`outcome`） | 无法区分"输"与"超时/崩溃" |
| `state_hash`（重放校验） | ✅ **新进展**：`serialize.py` 提供 snapshot/restore/`state_hash` | 为 trace 与重放打下基础（尚未接入） |

**结论（22:38）**：

1. **当前跑引擎不会写 trace**：`logging.py` 仍在，但已成为孤岛（无调用方），`engine.play` 去掉了 `log_path` 参数，而 `__main__` 还在传它——**CLI 与引擎签名不匹配，`python -m bench demo` 会直接报 TypeError**。
2. 新增的 `serialize.state_hash()` 是正确方向，但它只提供"状态指纹"，不提供"事件流"；要支持 [05](05-evaluation-framework-engineering.md) §4.5 的诊断，仍缺整条 trace。
3. `plan/详细版/04` 的 F1–F4 判定器依赖 `tool/result.isError`、`assistant_text`、`score_delta`（[plan/04 §3](../../plan/详细版/04-失败归因器.md) 的代码示例），这些字段在引擎侧不存在，只在 dsh 会话流里部分存在。**两套 trace 必须先合并成一套，F1–F4 才可能实现。**

---

## 6.7 统计实验设计是否足够

| 项 | 计划 | 现状 | 判断 |
|---|---|---|---|
| 配对键 | `(scenario_id, capture_id, model_config, prompt, tool_version)` | 仅设计 | ✅ 设计合理（[plan/03 §4.1](../../plan/详细版/03-评测集与指标.md#L226-L227)） |
| 样本量 | 3 组 × 30 场景 = 90 局 | 未跑 | ⚠️ 见下 |
| 功效分析 | 事前做，公式给出 σ_d=0.25、Δ=0.10 → n≈50 | 文档已算 | ⚠️ **算出 50 却仍用 30** |
| 统计方法 | Wilcoxon + McNemar + Holm + bootstrap | 无代码 | ❌ 未实现 |
| 真游戏终验 | 3×4=12 局，只做描述统计 | 未执行 | ✅ 口径正确（不做显著性） |

**最尖锐的矛盾**：`plan/03` §4.2 自己算出了 $n\approx50$（σ_d=0.25, Δ=0.10），并写"v3.0 每组只有 30 场景 < 50 → 事前就按描述统计 + CI 写预注册，不承诺显著性"（[L234-L241](../../plan/详细版/03-评测集与指标.md#L234-L241)）。这个处理是**诚实且正确**的。

但 D10 又写"配对 Wilcoxon + McNemar + Holm 校正"（[plan/00 D10](../../plan/00-项目全貌.md#L160)），D5 的验收是"3 组 × 30 场景"（[L79](../../plan/00-项目全貌.md#L79)）。**"做显著性检验"与"n=30 功效不足"同时出现在计划里**，需要在预注册中二选一：

- 方案 A：主表只报描述统计 + CI + 效应量，不做 p 值主张（与 n=30 匹配）；
- 方案 B：扩到 50+ 场景/组，或接受"只能检测大效应"并在结论里限定。

**另一个被忽略的问题**：30 个锚点 + 30 个反事实变体共享局面，**不是 60 个独立样本**。按 [04](04-metrics-and-statistics.md) §4.4.4，必须用**聚类标准误**（簇 = capture），否则 CI 会偏窄（本报告算例中差 1.81 倍）。

---

## 6.8 程序架构缺什么

对照 [05](05-evaluation-framework-engineering.md) §4.1 的 13 个模块：

| 模块 | 当前（22:45 复核） | 证据 |
|---|---|---|
| Environment | ✅ 有两层：`engine`（规则）+ `environment.py`（会话状态/reset/observe/legal_actions/step/snapshot） | [bench/engine.py](../../bench/engine.py)、[bench/environment.py](../../bench/environment.py) |
| Tool Interface | ⚠️ **层已成形**：`tools.py` 有 4 游戏工具 + `reset_episode` + 结构化错误；但 **MCP 未暴露**（`bridge/server.py` 仍只有 `get_state`） | [bench/tools.py](../../bench/tools.py)、[bridge/server.py](../../bridge/server.py#L21-L41) |
| Observation | ✅ `observation.py`（渲染/投影） | [bench/observation.py](../../bench/observation.py) |
| Dataset / Loader | ❌ 无（`scenarios/v3/` 未创建） | [scenarios/](../../scenarios/) 只有 `RULES_VERSION` |
| Scenario Schema | ⚠️ 只有文档 JSONC | [plan/03 §2](../../plan/详细版/03-评测集与指标.md#L66-L101) |
| Agent Adapter | ❌ 无 | — |
| Model Adapter | ❌ 无（依赖外部 dsh） | — |
| Episode Runner | ❌ 无 | — |
| Trace Recorder | ❌ `logging.py` 已无调用方；`serialize.py` 提供 `state_hash`/快照，但不是事件流 | [bench/logging.py](../../bench/logging.py)、[bench/serialize.py](../../bench/serialize.py) |
| Evaluator | ❌ 无 | — |
| Metrics | ❌ 无 | — |
| Aggregator / Stats | ❌ 无 | — |
| Experiment Manager | ❌ 无 | — |
| Report Generator | ❌ 无（`bench/report.py` 被引用但不存在） | [plan/00 §3](../../plan/00-项目全貌.md#L132) |

**结论（22:45）**：环境与工具两层正在快速成形（`environment.py` / `tools.py` / `serialize.py` / `rules_version.py`），这是正确方向。但**评测闭环仍缺四块**：Dataset/Loader、Runner、Evaluator、Metrics/Aggregator。按 [05](05-evaluation-framework-engineering.md) 的说法：**没有 runner 就没有 episode，没有 evaluator 就没有分数，没有 metrics 就没有结论**。所以现在**仍不可能产出任何 Agent 能力结论**——缺的不是"更难的场景"，而是"把场景跑起来并判分"的那半条流水线。

> **22:50 复核补充**：新增了 `evaluation/`（`agents.py`/`config.py`/`episode_runner.py`/`trace.py`），说明 Runner 与 Trace 已开始实现。本节表格是 **22:45 的状态**；这正好印证 §0 的纪律——在活跃重构期，**任何"缺什么"的判断都必须带时间戳**，否则几小时后就会过期。复核时应以"符号是否存在 + 能否跑通"为准，而不是以本文表格为准。

---

## 6.9 测试体系能否证明评测结果可信

现有 25 项测试（[tests/test_w2_rules.py](../../tests/test_w2_rules.py)）覆盖：牌型识别、计分、Joker 顺序、动作枚举、确定性、RNG 往返。

**但截至 22:38，它们跑不过**：`python -m unittest discover -s tests` 报 `Ran 25 tests ... FAILED (errors=7)`，原因是测试仍用旧的 `Joker("jx", "mul_mult", 150)` 三参数写法，而 `Joker` 已改为 `(jid, name, kind, value, condition, rarity, buy_price)`。22:45 复核时更糟：测试模块**导入即失败**，unittest 只报 1 个 error。这说明**测试没有跟上重构**——正是 [05](05-evaluation-framework-engineering.md) §4.7 所说"评测系统自身也需要被评测"的反面案例：测试与实现脱节时，"测试通过"这个信号本身失效。

**它（在 22:18 快照下）证明了什么**：引擎内部自洽（在已实现行为范围内）。
**它没有证明什么**（对照 [05](05-evaluation-framework-engineering.md) §4.7）：

| 测试类型 | 有吗 | 缺什么 |
|---|---|---|
| Unit | ⚠️ 25 项，但当前 7 个 error | 与实现同步 |
| Integration | ❌ | Loader→Runner→Recorder 的联通 |
| E2E | ❌ | 假模型跑完一局并出指标 |
| Golden | ⚠️ 仅 demo 的期望值（steps=13 等） | 计分口径已变，golden 值需重算 |
| Regression | ⚠️ 部分 | `_draw` 洗牌分支、loss 分支、商店唯一性（AGENTS.md §7） |
| Property-based | ❌ | 守恒律（52 张牌）、regret ∈ [0,1] |
| Determinism | ⚠️ 测试 24（但当前可能受重构影响） | 重构后需重跑 |
| Schema | ❌ | 日志 schema 校验 |
| **负对照** | ❌ | random/oracle/固定错误策略的分数梯度 |
| **Oracle 自洽** | ⚠️ `verify` 只证路径一致 | 与真实得分/上界的一致性 |
| **评测器自身** | ❌ | 无 evaluator 可测 |

**最关键的一条**：项目有 `verify`（O1 vs 独立枚举），这证明"两条搜索路径一致"。但如 [02](02-classic-benchmarks.md) §2.3 *AI Agents That Matter* 所指出的，**评测系统本身需要被审计**：如果 evaluator 把失败判成成功，模型分数会虚高，而单元测试发现不了。当前**没有任何测试覆盖"判分正确性"**，因为没有 evaluator。

---

## 6.10 映射表

| 当前项目模块 | 对应评测方法论 | 当前状态 | 主要风险 | 建议 |
|---|---|---|---|---|
| `bench/engine.py` 状态机 | Environment（[05](05-evaluation-framework-engineering.md) §4.1） | ⚠️ 迁移中：改为 ruleset 驱动，确定性待复验 | 机制仍缺经济/构建，目标能力不可测 | P0：先决定"补机制"还是"改主张" |
| `bench/scoring.py` + `rules_version.py` | 环境规则 + Oracle 基础 | ⚠️ 已切 vanilla 子集（基础 chips、计分牌筛选）；文档仍写自定义（C10） | 文档-代码不一致；历史分数不可比 | P0：同步文档与 golden 值，或回退 |
| `bench/oracle.py` O1 | Exact Oracle（[03](03-agent-benchmark-design.md) §3.5） | ✅ 单步精确（代码未改） | 目标函数与"规划"不匹配；弃牌被记 0 | P0：明确"仅 play 决策"的语义，禁止外推 |
| `bench/oracle.py` O2 | Approximate Oracle | ✅ 有区间 | 抽样模型与引擎不一致 | P1：报告必须带 K 与抽样模型说明 |
| `bench/oracle.py` O3 | Reference Policy | ✅ 可调用 | 引擎已不写日志，O3 无轨迹产物 | P1：接回 recorder 后重测 |
| `bench/actions.py` | Action Space | ✅ 218 动作、稳定 id | `code` 顺序敏感，去重漏等价动作 | P2：canonical 化（排序） |
| `bench/logging.py` + `serialize.py` | Trace Recorder | ❌ logging 已无调用方；serialize 只提供 state_hash | 跑引擎不产生任何 trace | P0：接回 recorder 并扩 schema |
| `bridge/server.py` | Tool Interface | ❌ 只有 `get_state` 占位 | **Agent 无法真正玩**；文档称 4 工具（C1） | P0：实现 4 工具 + 结构化错误码 |
| `tests/` | QA（[05](05-evaluation-framework-engineering.md) §4.7） | ❌ 25 项中 7 个 error（截至 22:38） | 无负对照、无 evaluator 测试；测试与实现脱节 | P0：先修同步，再补 integration/负对照 |
| `scenarios/RULES_VERSION` | Dataset manifest 雏形 | ⚠️ 只有规则声明，且与代码不同步 | 无 dataset 版本、无 hash | P1：升级为 manifest（含 hash/划分） |
| `docs/engine-fidelity.md` | 对齐台账 | ✅ 结构完整 | 全 PENDING | P1：保持；不得提前改状态 |
| `plan/详细版/03` 指标五层 | Metrics 设计 | ⚠️ 只有设计 | ③④ 层无定义、无实现 | P0：先定义 ③④ 或明确"不测" |
| `plan/详细版/04` 归因器 | Diagnosis | ⚠️ 设计完整，未实现 | 依赖不存在的 trace 字段 | P1：等 trace 扩完再做 |
| `plan/详细版/05` 实验 | Experiment Manager | ⚠️ 设计完整，未实现 | n=30 与显著性主张冲突 | P0：预注册二选一 |
| `data/` | 产物 | ⚠️ W2 旧产物（自定义公式时代） | 与新计分口径不可比 | P1：标注口径，勿混用 |

---

## 6.11 优先级建议

### P0（影响评测有效性与正确性，必须先解决）

**P0-0 版本漂移：文档、代码、测试三者不同步（截至 22:38，仓库跑不过自己的验收命令）。**
- 证据：`python -m unittest discover -s tests` → `Ran 25 tests, FAILED (errors=7)`（测试仍用旧 `Joker` 三参数签名）；`__main__` 仍向 `play()` 传 `log_path`，而 `engine.play(state, card_ids)` 已不接受该参数（见 §0 快照表）；`bench/logging.py` 无调用方；`README`/`RULES_VERSION` 仍写 L0 自定义公式，代码已是 `vanilla_1.0.1o_subset_v1`。
- 影响：**当前工作树不可作为任何结论的证据**；任何"已通过/已对齐"的表述都与事实不符；若此时跑实验，产物将无法解释。
- 建议：先冻结重构（提交或 stash），恢复三条验收命令（测试 / demo / verify），再继续。**零方法成本、最高优先级**——它是其他所有 P0 的前置条件。

**P0-1 MCP 暴露未接通，Agent 仍无法被评测。**
- 证据：`bridge/server.py` 只有 `get_state()` 且返回占位数据（`"note": "W1 placeholder state"`，手牌 `["J1","J2","J3"]`，[L21-L41](../../bridge/server.py#L21-L41)）；[evidence/W1/W1-acceptance.md](../../evidence/W1/W1-acceptance.md#L76) 自述"validates the MCP communication … only. It does not yet validate … gameplay control"。
- **进展（22:45 复核）**：`bench/tools.py` 已出现，含 `get_state / play_cards / discard_cards / choose_joker / reset_episode`，并把 `BenchError` 转成结构化错误码——这正是需要的东西，但**尚未在 `bridge/server.py` 暴露**，所以 Agent 侧仍只能看到一个占位工具。
- 影响：G2（≥3 次工具调用的完整 episode）仍无法达成；任何"模型表现"数据都无法产生。
- 建议：把 `bench/tools.py` 接到 `bridge/server.py`，为每个工具声明前置状态 + 统一错误码，非法动作返回 `isError` 而不是抛异常。**这是所有后续工作的前置条件。**

**P0-2 "测长线规划"与"环境无长线机制"矛盾。**
- 证据：`money`/`interest` 仍在 `excluded`，`buy_price` 只声明不计算（[rules_version.py](../../bench/rules_version.py)、[model.py](../../bench/model.py#L135)）；资源每盲注重置；shop 仍免费三选一。
- 影响：Local Regret 只测单步；四支柱不可测；任何"规划"结论都不成立。**注意：vanilla 化不改变这一点**——它改的是"分数像不像原版"，不是"有没有跨期取舍"。
- 建议：二选一，并在文档中明确：
  - (a) **改主张**：把项目定位收窄为"单步战术 + 盲注内多步"，删除/降级"长线规划"表述；
  - (b) **改机制**：增加至少一个跨阶段累积资源（金钱+利息最经济），并同步加场景与指标。
  - 不建议"两者都不改"——那会让文档与能力继续脱节。

**P0-3 弃牌决策的计分语义会惩罚正确行为。**
- 证据：`best_play` 只枚举 `play`（[oracle.py](../../bench/oracle.py#L49-L57)）；`plan/03` 规定"选 discard 记 actual=0, regret=1"（[L198-L203](../../plan/详细版/03-评测集与指标.md#L198-L203)）。
- 影响：在这个环境里，"弃牌换更好手牌"可能是正确的，但会被记为最大 regret；指标方向与能力方向相反。
- 建议：把"决策点"类型分开（play 点 / discard 点），每种用自己的 oracle；或把"选择 discard"从 regret 分母中排除、单列为 `action_type_mismatch`。

**P0-4 Trace 断裂：引擎已不写日志，诊断层无从谈起。**
- 证据：`logging.py` 无调用方；`engine.play` 不再接受 `log_path`；`serialize.py` 只提供 `state_hash`，不提供事件流；`plan/04` 依赖的 `isError`/`assistant_text` 字段不存在。
- 影响：F1–F4 无法判定；Legality、Cost、Latency、首次失败步都无法计算；连"重放"也只剩状态哈希，没有动作序列。
- 建议：先接回一个 recorder（可以是 logging.py 升级版），按 [05](05-evaluation-framework-engineering.md) §4.5.2 的字段实现；`schema_version` 升 2；旧产物标为 v1 只读。

**P0-5 实验规模与统计主张冲突。**
- 证据：`plan/03` §4.2 自算 n≈50（[L234-L241](../../plan/详细版/03-评测集与指标.md#L234-L241)），D5 仍定 30/组（[plan/00 L79](../../plan/00-项目全貌.md#L79)），D10 又要 Wilcoxon+Holm（[L160](../../plan/00-项目全貌.md#L160)）。
- 影响：跑完 30 组后做显著性检验，很可能得到"不显著"，然后被解释成"没有差异"。
- 建议：预注册明确"主表 = 描述统计 + CI + 效应量；不做确证性 p 值主张"，或扩样本。**不要既做检验又不承认功效不足。**

### P1（影响研究质量与结论可信度）

| # | 问题 | 证据 | 建议 |
|---|---|---|---|
| P1-1 | 无人类基线 | 无相关产物 | 让 1–2 人做同样 60 个决策点，得到"人类参照分数"；这是解释模型分数的最低成本手段 |
| P1-2 | 无 hidden test / 污染检测 | 无 `scenarios/v3/`、无 canary | 至少保留 20% 场景不公开；在场景里嵌 canary；报告写"知识先验 vs 污染"的区别 |
| P1-3 | 场景成簇但按独立样本统计 | 30 锚点 + 30 变体共享局面 | 用 capture 作簇做聚类 SE；或主表只用锚点 |
| P1-4 | O2 抽样模型与引擎不一致 | [oracle.py](../../bench/oracle.py#L76-L95) 自述"不读 rng_state、混池" | 报告写"该抽样模型下"；若要精确，改为从 `rng_state` 复现发牌 |
| P1-5 | O3 写默认日志污染证据 | [oracle.py](../../bench/oracle.py#L169-L179) | 暴露 `log_path` 参数，默认 `None` |
| P1-6 | 无 code hash / 重放重算实现 | `bench/` 无 hash/manifest 代码；`bench/report.py` 不存在 | 实现 manifest + 结果文件头 hash + 一条 replay 校验命令 |
| P1-7 | 无 CI | 无 `.github/` | 至少加一个本地 `tools/check.py`：测试 + schema + 重放 |
| P1-8 | 失败归因会把环境问题算成 Agent 错 | 无 E1 判定实现 | E1 必须先于 F1–F4 实现，或至少在报告里单列"疑似环境问题" |
| P1-9 | 声明"25 测试通过"容易被读成"引擎正确" | README 已加限定 | 保持限定；在报告模板里固定写"L0 自洽，不等于对齐" |

### P2（提升可扩展性与工程质量）

| # | 问题 | 建议 |
|---|---|---|
| P2-1 | `CardAction.code` 顺序敏感 | canonical 化（排序 id），并加去重测试 |
| P2-2 | `verify_oracle` 构造可能含重复物理牌 | 用独立牌堆构造 hand，或加断言 |
| P2-3 | 无并发/限流/重试骨架 | 按 [05](05-evaluation-framework-engineering.md) §4.6 实现（asyncio + 令牌桶 + 退避） |
| P2-4 | 目录缺 `configs/ experiments/ metrics/ evaluators/` | 按 [05](05-evaluation-framework-engineering.md) §4.8 建骨架，先空实现 |
| P2-5 | 文档内 `bench/` 模块清单与实际不符 | 以实际文件为准（截至 22:38 为 15 个 `.py`），更新 plan/00 §3 的架构图 |
| P2-6 | 无版本化数据集脚本 | 写 `tools/build_dataset.py` + manifest 生成器 |

---

## 6.12 文档与代码冲突清单（不替项目选边）

> 规则：以下每条都同时给出"文档说"与"代码/事实"，**由项目负责人决定以哪个为准**，本文不自行裁决。
> **注意**：C10–C12 是 22:33 之后的并发改动造成的，属于"重构中间态"，不一定是最终设计。复核时请以重构完成后的提交为准。

| # | 文档说 | 代码/事实 | 影响 | 建议 |
|---|---|---|---|---|
| **C1** | `bridge/server.py` 是"W1 训练环境，4 工具"（[README L97](../../README.md#L97)）；`plan/00` §3 写"4 工具（get/play/discard/choose_joker）… 薄壳：校验 → bench.tools"（[L108-L110](../../plan/00-项目全貌.md#L108-L110)）；D6 同（[L156](../../plan/00-项目全貌.md#L156)） | 实际只有 `get_state()`，返回占位 JSON；无 `bench/tools.py` | G2 无法达成；"Agent 已能交互"的印象不成立 | 二者取一：补实现，或改文档为"1 工具占位" |
| **C2** | `plan/00` §6："W1 MCP 链路 ✅ 已完成并通过验收"（[L189](../../plan/00-项目全貌.md#L189)） | [W1-acceptance.md](../../evidence/W1/W1-acceptance.md#L76) 明确"only validates the MCP communication… does not validate gameplay control" | "已完成"容易被读成"游戏链路可用" | 改为"W1 MCP 通信链路已验收；游戏工具未实现" |
| **C3** | `plan/00` §3 架构图列 `bench/` 含 `scenarios / metrics / attrib / render`（[L114-L118](../../plan/00-项目全貌.md#L114-L118)） | `bench/` 无这四个（22:38 有 `errors/hand_eval/rules_version/serialize`，仍无 metrics/attrib/render） | 读者会以为指标/归因已有代码 | 架构图区分"已实现/规划" |
| **C4** | `plan/00` D13："`bench/report.py` 仍保留两道闸——重放重算 + code hash"（[L132](../../plan/00-项目全貌.md#L132)） | `bench/report.py` 不存在；`serialize.py` 提供了 `state_hash`，但没有重放/报告闸门 | "结果完整性"仍未实现（有零件，无装配） | 删掉"仍保留"，或把它实现为 manifest+replay 命令 |
| **C5** | `plan/03` §7 验收："一条命令跑完主表子集并输出指标表"（[L303](../../plan/详细版/03-评测集与指标.md#L303)） | 无 runner/metrics 模块，无该命令 | 验收项当前不可执行 | 标 📋 并注明依赖 P0-1/P0-4 |
| **C6** | `AGENTS.md`："代码基线：`c65fb9b`（W2-v2.1-2026-11-12）" | HEAD 是 `0e403cf`（2026-11-13）；工作树有 17 个未提交修改；**22:33 之后还有未提交的新文件与重写** | 同一句"基线"可指四个不同快照；复现结论会产生歧义 | 结果文件头写"实际 commit + dirty 标记 + 文件 hash" |
| **C7** | `plan/03` §1.2 把 L3 命名为"**长程**"（[L33](../../plan/详细版/03-评测集与指标.md#L33)） | 同单元格定义是"同一盲注内多次 play/discard … **不跨盲注**"；README 也承认只到"盲注内多步" | 命名与定义冲突，容易被引用成"已测长程" | 改名为"L3 盲注内多步"，把"长程"留给跨盲注 |
| **C8** | `plan/00` D4 主指标 = Local Regret；项目定位 = 长线规划 | `plan/03` §3.2 自己写"不能外推为长线规划能力" | 主指标与主主张不匹配 | 见 P0-2 |
| **C9** | `plan/00` §3："`bench/` 是训练环境唯一规则权威" | ✅ 代码一致（`bridge/server.py` 不 import 规则，`bridge/realgame.py` 未创建） | 无冲突 | 保持；`bridge/realgame.py` 创建时继续遵守 |
| **C10** | README/AGENTS/`scenarios/RULES_VERSION`：规则等级 **L0**、**自定义计分公式**、8 个**合成夹具** Joker、3 槽位、4 手 2 弃、300/800/2000 | 代码已切到 `vanilla_1.0.1o_subset_v1`：8 个**具名 vanilla Joker**、5 槽位、4 手 4 弃、300/450/600、牌型基础 Chips×Mult + 计分牌筛选（[rules_version.py](../../bench/rules_version.py#L92-L97)、[L184-L187](../../bench/rules_version.py#L184-L187)） | 文档描述的环境**已不存在**；历史数字（如 `7♥7♦`=28）与新代码（48）不可比 | 重构完成后统一改文档；在此之前报告必须写"规则版本 = ?" |
| **C11** | 各文档："25/25 测试通过" | 22:38 实测 `Ran 25 tests, FAILED (errors=7)`；测试仍用旧 `Joker` 三参数签名 | "测试全绿"不再成立；CI 若存在会红 | 同步测试与实现，或回退实现 |
| **C12** | `AGENTS.md` 验收命令：`python -m bench demo --log ...`；`plan/00`："JSONL 轨迹" | `engine.play(state, card_ids)` 已无 `log_path`；`__main__` 仍传参 → TypeError；`logging.py` 无调用方 | 验收命令当前不可执行；"有轨迹日志"不成立 | 统一签名，并把 recorder 重新接回 |

---

## 6.13 如果只做三件事

按"每单位工时对结论可信度的提升"排序：

1. **冻结当前重构，恢复可运行状态**（P0-0）。
   提交或 stash 正在进行的 vanilla 化改造，让 `unittest`、`bench demo`、`bench verify` 三条命令重新变绿，并同步 `Joker` 签名与 `play(log_path)`。工作量约半天到一天；收益是"后面所有结论有地基"。**这一步之前，任何实验数据都不该进报告。**

2. **实现 4 个 MCP 工具 + 把异常转成结构化错误**（P0-1）。
   没有它，其他一切都没有数据。工作量约 1–2 天，收益是"从零到能跑一局"。

3. **对"长线规划"做一次书面取舍**（P0-2）。
   要么改机制（加 money/interest），要么改主张（收窄定位）。这是**零代码成本、最高收益**的一步：它决定了后面所有场景、指标、实验是否有意义。

> 这三件事都不需要"设计新 benchmark"，也不需要扩大项目范围。它们只是让**现有的方法论设计**能落地。
> 如果只能做一件：做第 1 件。**一个跑不起来、测试是红的仓库，无法产生任何可信的评测结论。**

---

## 6.14 本章应该掌握什么

1. 用"机制是否存在"判断一个能力能否被测量，而不是用"场景是否够多"。
2. 说明为什么当前环境里的贪心策略近似最优，以及这对 Local Regret 的解释意味着什么。
3. 列出当前 Oracle 三种策略各自保证什么、不保证什么。
4. 指出当前 Trace 断在哪里（不是"字段少"，而是"根本没写"），以及它会阻断哪些指标/诊断。
5. 说明 n=30 与"做显著性检验"之间的矛盾，并给出两种合规处理。
6. 复述 P0 六项，并解释为什么 P0-0（版本同步）与 P0-1（工具层）是其他一切的前置条件。
7. 区分"文档说"与"代码是"，并在冲突时不自行选边；同时给所有状态判断加时间戳。

### 常见误区（本章范围）

| 误区 | 为什么错 |
|---|---|
| "场景建好了就能测规划" | 机制不存在时，场景只是"更复杂的单步题" |
| "Local Regret 是精确的，所以结论可靠" | 精确 ≠ 有效；它精确地测了另一件事 |
| "25 个测试通过 = 引擎可信" | 只证 L0 自洽；且没有 evaluator 测试 |
| "n=30 也能做 Wilcoxon，反正会出 p 值" | 出 p 值不等于有功效；不显著不能解释为无差异 |
| "文档写了 4 工具，应该快实现了" | 文档是目标态；代码是占位态，二者必须分开引用 |
| "加了 hidden set 就解决了污染" | 还要防 oracle 泄漏、prompt 泄漏、模板化 |
| "真游戏 12 局能验证训练集结论" | n=12 只能看方向一致性，不能做显著性 |

---

## 导航

- 上一篇：[05 评测系统架构与工程实现](05-evaluation-framework-engineering.md)
- 下一篇：[07 学习路线](07-learning-roadmap.md)
- 相关：[03 场景与 Oracle 设计](03-agent-benchmark-design.md)、[04 指标与统计](04-metrics-and-statistics.md)
- 返回：[README](README.md)
