# 04 · Balatro 生态工程调研：现有项目逐个评估（开题报告「研究现状」素材）

> 调研人：res-balatro（Team B1）｜检索日期：2026-11-12（UTC+8）｜写入范围：仅本文件
> 检索手段：`web_fetch` 直接打开 GitHub 仓库页 / GitHub REST API / `raw.githubusercontent.com` 上的 README / 官方文档站 / 社区 Wiki；`web_search` 仅用于发现候选。**本机 pwsh 不可用，全程未使用 shell。**
> 核实标记：**✅ 已打开页面核对**（README、API 元数据、文档站、Wiki 首页原文为准）；**⏳ 仅搜索结果 / 页面仅标题可读**（未读到正文，报告中不可当事实引用）。
> 事实与推测分离：未特别标注的均为页面原文可核对事实；凡推断均写「推测」。
> **📋 v3.0 更新（2026-11-13）**：本文是 2026-11-12 的调研记录，保留原文不改写。其中“不接入真游戏、只做人工对拍”的结论**已被 v3.0 取代**——v3.0 接入 `coder/balatrobot`（MIT）做**真游戏终验（12 局）与局面捕获**，自建 `bench/` 降为 **L0 对齐训练环境底座**；以 [`plan/详细版/07-真实游戏接入与终验.md`](../../plan/详细版/07-真实游戏接入与终验.md) 与 [`plan/00-项目全貌.md`](../../plan/00-项目全貌.md) 为准。

---

**一句话结论（可直接进报告）**：Balatro 生态已经把**「能操作真游戏」**（balatrobot 三件套 + Lovely/Steamodded 注入链）和**「能算分」**（计算器、模拟库、种子推演）这两件事做得相当成熟，甚至已经存在一个**名称相近**的 LLM 排行榜项目 **`coder/balatrobench`**（外部项目）；但**没有任何项目**把「确定性规则子集 + 固定场景 + oracle 参照 + 可判定的失败归因」这四件事合在一起。最接近的两块拼图——`evanofslack/balatro-rs`（可离线运行的规则引擎）与 `alesha-pro/evalatro`（真游戏 LLM 基准）——都恰好缺「归因」这一层。这既证明了本项目的位置是真空，也意味着**相关工作里必须先说清楚与它的差异**（见 §0）。

---

## 0. 三条先行结论（写报告前务必先读）

### 0.1 外部项目 `coder/balatrobench`（非本项目）

- [`coder/balatrobench`](https://github.com/coder/balatrobench) 存在且活跃：23★（2026-11-12 读数）、MIT、Python、创建 2025-08-21、最近推送 2026-05-19、官网 <https://balatrobench.com/>、数据托管在 [Kaggle: s1m0n38/balatrobench](https://www.kaggle.com/datasets/s1m0n38/balatrobench)。其 README 自述为「**benchmark analysis tool and leaderboard for BalatroLLM runs**」——它**解析 `coder/balatrollm` 产生的对局记录并生成可交互排行榜**，不是评测环境、不是判定器、也不定义场景。
- 也就是说：它做的是**评测结果的展示与横向比较层**，本项目做的是**面向大模型 Agent 的长线规划测试集**（失败归因仅作诊断报告层）。二者可互补，但名称相近、易被混淆。建议在开题报告中显式写一句区分（例如「与 coder/balatrobench 目标不同：后者是排行榜与结果分析工具，本项目是长线规划测试集，失败归因仅作诊断报告层」），否则评审很可能第一反应是「这不是已经有了吗」。**项目正式名已定为 `BalatroEval`，相关工作里说明差异即可。**

### 0.2 任务书里有一处事实需要修正：`WilsontheWolf/balatro-calculator` **不是独立实现**

- 经 GitHub API 核对：该仓库 `fork: true`，`parent = EFHIII/balatro-calculator`，**0★**，创建与最后推送均为 **2024-03-14**（即 fork 后未再维护）。
- 因此「EFHIII 与 WilsontheWolf 的 balatro-calculator（Web + JS）」应改为「EFHIII 的 balatro-calculator（Web + JS）及其一个 0★ fork」。报告里若并列成两个项目，会被懂行的人一眼看穿。

### 0.3 「Jev / TypeSafe」**真实存在**，但不是 Balatro 专用模型，也没有可引用的 Balatro 评测结果

- 存在性可核：OpenRouter 有模型版本页（页面标题 `TypeSafe: Jev model versions`，<https://openrouter.ai/typesafe/jev>）；作者 Juris Savostijanovs 的博客详述了 Balatro 集成架构（2026-09-19，<https://juris-savos.me/blog/jev-plays-balatro>）；另有第三方基准仓库 [`wondertwins/jev-benchmark`](https://github.com/wondertwins/jev-benchmark)（8★，自述「Benchmarks and a playground for **TypeSafe's Jev (System One)** model」）。
- 但：①它是**通用「判别」模型**（输入 state + 一组 typed questions，返回每个选项的校准概率，不生成文本），不是为 Balatro 训练的；②Balatro 侧**只有一篇个人博客 + 一个 30 步 replay demo**，未发现对应开源仓库、无对照实验、无胜率/分数结果；③博客里引用的国际象棋数字（533 vs 403 mean centipawn loss、90 → ~950 Elo）**转引自 `wondertwins/jev-benchmark`**，属二手转述。
- 结论：可以写「存在一类『只判断不生成』的小模型方案，并被个人开发者接入 Balatro 验证可行性」，**不可**写成「已有 Balatro 小模型基准/已有 Balatro 专用小模型」。价格数字（输入 $0.042/MTok 等）本次**未核实，不要引用**。

---

## 1. 分节项目详解（共 26 个项目/资源，另见 §2 清单 32 条）

### 1.1 真游戏控制层（让程序操作正版 Balatro）

#### 1.1.1 `coder/balatrobot` —— 事实标准（JSON-RPC 2.0 + Lua mod）

- **URL**：<https://github.com/coder/balatrobot>｜文档 <https://coder.github.io/balatrobot/>｜API 参考 <https://coder.github.io/balatrobot/latest/api/>
- **作者/维护**：coder 组织（原作为 `besteon/balatrobot`，README 明确致谢 phughesion / besteon / giewev 的初始框架）。**81★ / 24 fork / MIT**，创建 2025-07-03，**最近推送 2026-11-11**（非常活跃，54 个 open issue）。
- **目的**：给正版 Balatro 一个程序化控制面，让外部程序（Bot、RL、LLM）能读全量状态并执行动作。
- **设计原理**：Lua mod 注入游戏后在本机起 HTTP 服务，**JSON-RPC 2.0 over HTTP/1.1，默认端点 `http://127.0.0.1:12346`**，请求体为 `{jsonrpc, method, params, id}`；共 22 个方法（`health / gamestate / rpc.discover / start / menu / save / load / select / skip / buy / pack / sell / reroll / cash_out / next_round / play / discard / rearrange / use / add / screenshot / set`），每个方法都声明 **Required State**（如 `play` 必须在 `SELECTING_HAND`）并返回统一错误码（`BAD_REQUEST / INVALID_STATE / NOT_ALLOWED / INTERNAL_ERROR`）。状态机为 **MENU → BLIND_SELECT → SELECTING_HAND → ROUND_EVAL → SHOP →（SMODS_BOOSTER_OPENED）→ GAME_OVER**。`gamestate` 返回结构化 `GameState`（`hands / round / blinds / jokers / consumables / cards / hand / shop / vouchers / packs`，均为 `Area{count, limit, cards[]}`；每张 `Card` 含 `key/set/label/value/modifier/state/cost`）。动作参数是**手牌索引**（`play{cards:[0,2,4]}`）而非卡牌 id；`add`/`set` 是调试钩子（可直接加 joker、改钱/ante/hands）。
- **效果**：目前是「真游戏控制」的**事实标准**，被 evalatro、Jonathanace 的 RL 环境等直接复用；提供 OpenRPC 描述（`rpc.discover`）与 `llms-full.txt` 文档，对 Agent 友好。局限：必须拥有 Steam 版游戏 + Lovely + Steamodded 四层依赖；有图形界面依赖（非无头）；一局到 Ante 8 需数十分钟，无法批量并行；游戏一更新注入链就可能断。
- **与本项目关系**：**不直接复用，但 API 设计要"借鉴型照抄"**。可借鉴：①方法名与「前置状态校验 + 统一错误码」的设计（我们 MCP 工具的前置条件与错误分类几乎可以一一对应）；②`GameState` 的 `Area/Card` 分层与 `modifier{seal,edition,enhancement}` 字段命名（场景快照 JSON 直接用）；③状态机枚举。**不借鉴**其「索引式动作」——索引在手牌重排/隐藏牌场景下不可复现，我们的动作应按卡牌稳定 id 表达。若最终要做「人工对拍真游戏」，它是唯一省力的接口（可把人工点击变成脚本化回放）。

#### 1.1.2 `coder/balatrollm` —— 官方 LLM 打牌参考实现

- **URL**：<https://github.com/coder/balatrollm>｜文档 <https://coder.github.io/balatrollm/>
- **作者/维护**：coder 组织。**114★ / 14 fork / MIT**，创建 2025-08-08，最近推送 2026-08-09（有 Discussions 与 14 个 open issue）。
- **目的**：用 LLM 驱动 balatrobot 打完整局，作为「LLM 玩 Balatro」的参考基线。
- **设计原理**：README 只说明「bot 分析游戏状态 → 做策略决策 → 通过 BalatroBot API 执行」，并给出 BalatroBot + BalatroLLM = BalatroBench.com 的三件套关系；**其内部策略/提示词/工具注册表细节 README 未展开**（本次未读源码，故不臆测）。
- **效果**：作为上游被 `coder/balatrobench` 的排行榜消费，是「LLM 打 Balatro」的事实基线实现；但它是**生成式 bot**，目标是把牌打好，不产出评价与归因。
- **与本项目关系**：**借鉴（工具设计/循环控制）**，不采用代码。我们对工具集的要求（参数简单、返回可直接判定）与 bot 的要求不同——bot 要「够用的状态摘要」，我们要「可精确复算的全量状态」。

#### 1.1.3 外部项目 `coder/balatrobench`（与本项目无隶属）

- **URL**：<https://github.com/coder/balatrobench>｜<https://balatrobench.com/>｜数据 <https://www.kaggle.com/datasets/s1m0n38/balatrobench>
- **作者/维护**：coder 组织（S1M0N38 为主要作者痕迹）。**23★ / 1 fork / MIT**，创建 2025-08-21，最近推送 2026-05-19。
- **目的**：把 BalatroLLM 的 `runs` 产物解析成可交互排行榜，让不同模型/策略可比。
- **设计原理**：Python CLI（`balatrobench --input-dir runs/v1.0.0`）解析对局记录 → 生成静态站点（`make serve`，默认 8000）→ 可选 WebP 截图与上传 CDN（BunnyCDN）；用 Playwright 做端到端测试；数据（runs/benchmarks）同步发 Kaggle。
- **效果**：已有公开 leaderboard 站点与数据下载，并有媒体报道（[Gigazine 2026-02](https://gigazine.net/news/20260213-balatrobench/)、中文公众号转述——**均 ⏳ 仅搜索结果**）。局限：它是**结果展示层**，不定义环境、不计算 oracle、不做归因；其数据口径完全继承 BalatroLLM（即真游戏 + 真模型 API）。
- **与本项目关系**：**不借鉴实现，但相关工作里说明差异即可**；可作为「本项目做出来后如何对外呈现（排行榜/run viewer）」的产品参照。

#### 1.1.4 `Steamodded/smods` —— mod 框架（事实标准）

- **URL**：<https://github.com/Steamodded/smods>｜文档 <https://docs.smods.dev/>｜旧仓库地址 `Steamopollys/Steamodded`（Lovely README 仍引用旧地址）
- **作者/维护**：Steamodded 组织。**1015★ / 206 fork / GPL-3.0**，创建 2023-12-05，最近推送 2026-11-05。
- **目的**：给 Balatro 提供 mod 加载与内容扩展框架（joker、consumable、blind、tag、voucher、poker hand 等）。
- **设计原理**：Lua 实现的 mod loader/injector，提供 `SMODS.*` 对象体系（`SMODS.Joker / Consumable / Blind / Tag / Voucher / PokerHand / Scoring_Parameter / Scoring_Calculation / Rarity / Edition / Enhancement / Seal`…），核心是**`calculate(self, card, context)` 回调 + context 分派**（`context.cardarea`、`before/individual/repetition/after` 等阶段），并配套 `G` 全局状态、事件管理器、权重系统。文档站列全了对象 API 与「Your First Mod」指南。
- **效果**：Balatro 模组生态的**默认标准**（绝大多数 mod 声明依赖 smods）；它把游戏规则「对象化/可注册化」，等于给出了一份**官方规则语义的半结构化描述**。局限：面向「加内容」，不面向「精确复算某一手的分数」；性能与副作用（动画、随机）不适合做确定性 oracle。
- **与本项目关系**：**不引入（我们不做注入），但 `calculate + context` 的语义必须借鉴**——它正是「一个 joker 在什么阶段、对哪些卡、以什么顺序生效」的社区公认建模，我们 Local Oracle 的效果组合器应与其阶段划分对齐，否则对拍会系统性偏差。数据字段（joker 名称/稀有度/效果文案）可参考，但**文本受 GPL/NC 约束，需自行改写**。

#### 1.1.5 `ethangreen-dev/lovely-injector` —— 运行时 Lua 注入器

- **URL**：<https://github.com/ethangreen-dev/lovely-injector>
- **作者/维护**：ethangreen-dev。**626★ / 81 fork / MIT / Rust**，创建 2024-03-04，最近推送 2026-09-23。
- **目的**：不修改游戏文件即可注入 Lua mod（可反复装卸），是 smods 与 balatrobot 的前置。
- **设计原理**：进程内 Lua API detour + 声明式 patch 系统。patch 文件是 TOML：`[[patches]]` 支持 `pattern`（含 `*`/`?` 通配、`match_indent`）、`regex`（捕获组）、`copy`（整文件追加/前置）、`module`（注入新模块）；按 `priority` 排序注入；`[vars]` 支持占位符替换；调试时把打补丁后的 Lua dump 到 `MOD_DIR/lovely/dump`、日志写 `MOD_DIR/lovely/log`。Windows 用 `winmm.dll`（旧版 `version.dll`），macOS 用 `liblovely.dylib`，Linux 原生/Proton 各有说明。
- **效果**：让 mod 变得「可安装/可卸载/可分发」，是整条控制层依赖链的底座。README 自述 **patch 格式在脱离早期开发前「不保证稳定」**——这直接意味着整条链对版本敏感。
- **与本项目关系**：**不借鉴**（我们不做注入）。它的存在恰恰解释了我们为什么不该接真游戏：**任何评测框架只要依赖它，就被绑定在「游戏版本 × 注入器版本 × mod 版本」的三维矩阵上**，可复现性无从谈起。

#### 1.1.6 `balamod/balamod` —— 另一条已边缘化的注入/反编译路线

- **URL**：<https://github.com/balamod/balamod>（`UwUDev/balamod` 为 4★ fork）｜<https://balamod.github.io>
- **作者/维护**：balamod 组织（UwUDev 主导痕迹）。**162★ / 27 fork / Apache-2.0 / Rust**，创建 2023-12-14，**最近推送 2025-01-11**（已近一年无提交）。
- **目的**：modloader + injector + **反编译器**，支持游戏内代码注入，横跨 Linux/Windows/macOS。
- **设计原理**：Rust 实现，通过反编译 + 注入实现比 Lovely 更激进的「改游戏逻辑」能力；生态里存在一批声明「Require Balamod」的 mod（见 awesome-balatro 的 Balamod 分区）。
- **效果**：曾与 Steamodded 并行，但社区已基本收敛到 **Lovely + Steamodded** 组合（对比：balamod 2025-01 停更，lovely 2026-09 仍在更新）。其反编译能力对「理解原版规则」有价值，但对评测无直接价值。
- **与本项目关系**：**不借鉴**。记录它的意义是说明「注入路线存在多条且互相不兼容」——这正是我们不接真游戏的第二层理由。

#### 1.1.7 `besteon/balatrobot` —— coder 版的原始前身

- **URL**：<https://github.com/besteon/balatrobot>
- **作者/维护**：besteon（原贡献者 phughesion / giewev）。**62★ / 36 fork / 无 LICENSE / Lua**，创建 2024-03-26，**最后推送 2024-04-28**（已停更）。
- **目的**：最早的 Balatro 程序化 API，coder 版即其 fork 演进。
- **设计原理**：Lua mod + RPC，功能面比 coder 版窄（coder 版新增了 OpenRPC、截图、`add/set` 调试、完整 schema、`llms.txt` 文档等——据两版 README/文档对比）。
- **效果**：已不维护；**36 个 fork** 说明它曾是真游戏自动化的事实起点。**与本项目关系**：只用于说明谱系与「社区轮子会分叉」的教训；不采用。

#### 1.1.8 `SleepyG11/HandyBalatro` —— 真游戏加速 mod（控制层的性能补丁）

- **URL**：<https://github.com/SleepyG11/HandyBalatro>
- **作者/维护**：SleepyG11。**155★ / 11 fork / GPL-3.0 / Lua**，创建 2024-08-07，最近推送 2026-11-02。
- **目的**：QoL 快捷键与控制（加速、快速选择等），被 `Jonathanace/Balatro-Gym` 用于把 rollout 提到 **512×** 速度。
- **设计原理**：Lovely/Steamodded 生态内的 Lua mod，直接改交互与动画速度。
- **效果**：证明「用真游戏做 RL/批量评测」的**第一瓶颈是速度**，社区只能靠 mod 打补丁。**与本项目关系**：不引入；它是「我们为什么要自建无动画、无图形、可并行的确定性引擎」的现成论据。

### 1.2 LLM / Agent 评测

#### 1.2.1 `alesha-pro/evalatro` —— **最接近本项目的评测侧对照物**

- **URL**：<https://github.com/alesha-pro/evalatro>｜榜单 <https://evalatro.dev/>｜About <https://evalatro.dev/about>
- **作者/维护**：alesha-pro。**28★ / 4 fork / ISC（package.json）/ TypeScript**，创建 2026-06-13，最近推送 2026-07-09。
- **目的**：把真实 Balatro 变成一个**可重复的 LLM 基准**：模型通过 balatrobot 玩真游戏，每次决策落盘，终局给 0–100 分并上公开排行榜。
- **设计原理**（README 原文可核）：
  - **栈**：Balatro（Steam 正版）+ Lovely + Steamodded + balatrobot mod + `balatrobot` CLI（`:12346`）+ 本仓库 runner；
  - **记分**：`progress = ladder position / (targetAnte × 3) + partial chip credit on the losing blind`；`legality = 1 − illegalMoves / totalMoves`；`score = round(progress × legality × 100, 1)`；**v2 目标为打过 Ante 12**（原版 Ante 8 胜利只是里程碑），只有目标达成才是 100；
  - **防作弊**：服务端用 transcript **重算分数**、拒绝不可能轨迹、按稳定 run hash 去重、用 `npm run codehash` 打「official / community」标签；
  - **工具面**：`src/tools/registry.ts` 同时服务 LLM runner 与 **MCP server**（`npm run mcp`，stdio），保证动作面单一事实源；
  - **附**：SQLite 存储、SSE 实时观战、`bench` 种子矩阵、每局完整 replay（状态/推理/动作/token/成本）。
- **效果**：已经实现了「真实环境 + 公开榜 + 可回放 + 可重算」的完整闭环，是本项目在**评测产品形态**上最值得对标的对手。局限（也是我们的空间）：①只输出**一个总分**，`legality` 只是非法动作**计数**，不分类、不定位；②没有 oracle，也没有「最优动作」真值，因此无法算 regret；③目标是最长局（Ante 12），单局成本高；④强依赖游戏本体与注入链，CI 不可行；⑤算分口径由基准自定（Ante 12 而非官方胜利）。
- **与本项目关系**：**定位上直接对照、方法上重点借鉴、代码上不复用**。借鉴：`progress × legality`（作为辅助指标与合法性下限）、transcript 重算 + code hash 的**可信评测**做法、tool registry 同源服务 LLM/MCP 的工程结构。**不借鉴**：真游戏栈、Ante 12 长局、以及「用总分当唯一结论」。

#### 1.2.2 `proj-airi/game-playing-ai-balatro` —— CV + LLM 路线

- **URL**：<https://github.com/proj-airi/game-playing-ai-balatro>
- **作者/维护**：Project AIRI 团队。**44★ / 2 fork / 无 LICENSE（仓库未声明）/ Jupyter Notebook**，创建 2025-09-21，最近推送 2026-06-10。
- **目的**：不碰游戏内存，用**视觉**（YOLO11n 检测卡牌/UI + RapidOCR/PaddleOCR 读文字）理解画面，再交给 LLM 决策。
- **设计原理**：自标 n<1k 图像（Label Studio），以 YOLO11n 为底座训练实体检测与 UI 检测两个模型（单张 4080Super 16GB，~2000 epochs 收敛），模型与数据集发在 HuggingFace；`pixi` 环境 + 脚本/Notebook 复现；操作层走 UI 自动化（macOS 需辅助功能/录屏权限）。
- **效果**：证明了「视觉接地」可行，但成本高、误差源多（识别错一张牌就全盘皆错），且完全不可判定（无法区分「识别错」与「决策错」）。**与本项目关系**：**不借鉴**（模态不同），但它是最有力的反例论据：**要做「可判定归因」，必须拿到结构化状态，而不是截图**。

### 1.3 环境与 RL

#### 1.3.1 `cassiusfive/balatro-gym` —— 最常被引用的 Gymnasium 封装（但未完成）

- **URL**：<https://github.com/cassiusfive/balatro-gym>
- **作者/维护**：cassiusfive。**42★ / 11 fork / MIT / Python**，创建 2024-03-17，最近推送 2025-07-26。
- **目的**：给 Balatro v1.0.0 提供标准 Gymnasium 接口，便于 RL 训练。
- **设计原理**：`pip install -e .` 后 `gym.make("BalatroGym-v0")`；但 README 里 **Observation / Action / Reward 三节正文全部是 `WIP`**——即 MDP 三要素均未定型。
- **效果**：被 Zenodo 提案（§1.3.3）当作「可扩展的公共起点」引用，说明其符号意义大于可用性；实际接入风险是「接口随时变」。**与本项目关系**：**不采用**（plan 里已定为「≤2h 探针，失败即止损」，本次核对进一步支持该决策）。

#### 1.3.2 `Jonathanace/Balatro-Gym` —— 用真游戏 + balatrobot 做 RL

- **URL**：<https://github.com/Jonathanace/Balatro-Gym>
- **作者/维护**：Jonathanace。**1★ / 0 fork / Apache-2.0 / Python**，创建 2025-11-11，推送 2025-12-01（很新、未成熟）。
- **目的**：面向 TorchRL / Stable Baselines3 的 Gymnasium 环境，附训练与评估脚本。
- **设计原理**：**不自己实现规则**，而是通过 balatrobot API 驱动**活的游戏客户端**做 rollout，并用 HandyBalatro 把速度提到 512×；Todo 明列「observation space 还没考虑复杂手牌嵌入」「缺 `has_flush`、`hands_left` 等特征」「网络还没做多 head 输出处理商店决策」「Installation/Usage 待补」。
- **效果**：演示视频证明「真游戏 + API + 加速 mod」能跑训练循环，但工程完备度低。**与本项目关系**：不采用；它的价值是给出「真游戏 RL 的速度上限」这一经验数据点（需要 512× 加速才勉强可训练）。

#### 1.3.3 `Jokers in the Machine`（Zenodo 提案）—— 社区已在想同一件事

- **URL**：<https://zenodo.org/records/23513044>（DOI `10.5281/zenodo.23513044`）
- **作者/状态**：Jessenth Ebenezer Sankar（NYU），2026-10-20 发布，**resource type = Proposal（课程研究提案，非论文、无同行评议）**，CC BY-4.0；36 views / 18 downloads（页面读数）。
- **目的**：提出「扩展现有 balatro-gym、训练 PPO、并与 prompt-based LLM Agent 对比，用超越胜率的指标（战术决策质量、协同识别）刻画两种范式的失败模式」。
- **设计原理**：把 Balatro 视为「短程战术 + 长程战略」双重压力的测试床；对比 RL 与 LLM；指标不止 win rate。
- **效果**：**只是提案**，无实验、无结果、无代码。**与本项目关系**：**最强的「空白佐证」**——它论证了「需要超越胜率的指标」这件事已被社区明确提出，但至今无人交付；报告中只能写「已有研究提案指出该需求」，**不可写成已有成果**。

#### 1.3.4 `evanofslack/balatro-rs` —— **工程上最接近「自建规则引擎」的公开实现**

- **URL**：<https://github.com/evanofslack/balatro-rs>
- **作者/维护**：evanofslack。**15★ / 12 fork / 未声明 LICENSE（API `license: null`）/ Rust（含 PyO3）**，创建 2024-11-30，最近推送 2026-10-21。
- **目的**：一套可离线运行的 Balatro 工具箱 crate：「rules engine + move generator for simulation/RL」「real save-file 解析」「**byte-accurate port of the game's actual seed/RNG algorithm**」「TUI/CLI」。
- **设计原理**：Rust workspace 拆分——`core`（`balatro-rs`：计分、出牌/弃牌、盲注、商店、joker/tarot/planet/spectral）、`balatro-types`（纯数据词汇）、`balatro-jkr`（`.jkr` 存档编解码）、`balatro-profile`（读真实存档）、`balatro-seed`（**逐字节对齐原版 RNG**）、`balatro-storage`、`cli`/`tui`、`pylatro`（PyO3 绑定）。核心 API 是 `Game::gen_actions()`（穷举当前合法动作）与 `gen_action_space()`（**固定大小 binary action mask**，给 RL 用稳定形状）。覆盖：牌型识别与计分、出/弃/重排、盲注通过失败与胜负、金钱利息、ante 1–8、买卖/使用 joker 与消耗品、增强/版本/印章生效、Boss 盲注、凭证；**joker 覆盖 74/150**；明确缺 **skip tags、其他牌组、其他赌注**。附带 replay 录制/回放（`--record`/`--replay`）与离线算分（`cargo run -p balatro-rs --bin calc -- score state.json`）。
- **效果**：这是**目前公开世界里最接近本项目「自建引擎」的那一块**：它已经证明「离线、确定性、可枚举动作、可绑 Python」在工程上成立；但它是**库**不是**评测框架**——没有固定场景集、没有 oracle 参照的最优动作、没有失败分类、没有 MCP 工具层、没有与真游戏的公开对拍报告。局限还包括：无 LICENSE（**不能直接拷代码**）、joker 只做了一半、无 skip tags/多牌组。
- **与本项目关系**：**设计上最值得对标（不是复制）**。借鉴四件套：①**穷举 move generator**（正是我们「出牌组合 ≤218 可枚举」的同构实现）；②**固定大小 action mask**（MCP 工具若要与 RL 共用动作面，这是唯一稳定形状）；③**逐字节复刻 RNG**（若我们要「固定 seed = 固定局面」，这是做法参照）；④**PyO3 绑定**（引擎与评测器分语言时最省事的桥）。**风险**：无 license（法律上不可复用，只能独立重写）；Rust + 74/150 joker 覆盖意味着「拿来即用」是幻觉。

### 1.4 算分 / 求解

#### 1.4.1 `EFHIII/balatro-calculator` —— 精确算分器的标杆

- **URL**：<https://github.com/EFHIII/balatro-calculator>｜站点 <https://efhiii.github.io/balatro-calculator/>
- **作者/维护**：EFHIII。**285★ / 54 fork / MIT / JavaScript**，创建 2024-02-25，最近推送 2026-07-09（仍是同类里最活跃的）。
- **目的**：输入手牌 + joker/牌型等级/抽牌等场景，算**最高分打法**及其得分，也可用来构造「完美一手」。
- **设计原理**：纯前端 HTML/JS（GitHub Pages 托管），把牌型判定、基础 chips×mult、joker 加成与顺序依赖做成可交互表单；内部维护每张 joker 的算分实现与顺序规则（README 只给结论，未给架构细节——**内部实现本次未读源码**）。
- **效果**：社区引用最多、最可信的单点算分器；README 自述「**少数 joker 可能算得不对**」。**与本项目关系**：**不集成，作为第三方对拍参照**（抽检基础牌型与常见 joker 组合 5–10 例，用来给「我们的 oracle 没错」提供外部证据）。注意：它是「求最优打法」的工具，恰好与我们的 Local Oracle 目标同向，但它是交互式网页，不是可编程 API。

#### 1.4.2 `WilsontheWolf/balatro-calculator` —— 实为上述仓库的 fork（见 §0.2）

- **URL**：<https://github.com/WilsontheWolf/balatro-calculator>
- **作者/维护**：WilsontheWolf（fork）。**0★ / 0 fork**，创建与推送均 2024-03-14，`fork: true`，`parent = EFHIII/balatro-calculator`。
- **目的/原理/效果**：与父仓库同构，无独立实现、无后续维护。**与本项目关系**：不采用、不引用；列出来仅用于纠正「两个项目」的误解。WilsontheWolf 本人另有 Balatro 工具（DebugPlus、balatro-save-loader、ScoreImprovements——见 awesome-balatro 列表，**未逐个打开，⏳**）。

#### 1.4.3 `DivvyCr/Balatro-Simulation` —— **Local Oracle 的直接参考实现（Lua 版算分模拟库）**

- **URL**：<https://github.com/DivvyCr/Balatro-Simulation>
- **作者/维护**：DivvyCr。**1★ / 3 fork / GPL-3.0 / Lua**，创建 2024-12-03，最近推送 2025-09-16。README 明确「**不是独立 mod，是给 mod 开发者的库**」。
- **目的**：在游戏内**无副作用地模拟「这一手会得多少分/多少钱」**。
- **设计原理**：把每张 joker 的 `calculate(self, card, context)` **裁剪成纯计算函数**放进 `src/Jokers/`，按 `context.cardarea`（`G.play` / `G.hand` / `G.jokers`）与阶段（`before` / `individual` / `repetition` / `global`）分派；提供 `DV.SIM.add_chips/add_mult/x_mult/add_dollars/add_reps` 等原子算子，以及**随机 joker 的三态** `get_probabilistic_extremes(...)` → 返回 `{min, exact, max}`；`DV.SIM.run()` 返回 `score{min,exact,max}` 与 `dollars{min,exact,max}`。**只覆盖「影响单次出牌分数/金钱」的 joker**（明确不模拟四指、交易卡、大理石、延迟满足等）。
- **效果**：在游戏内可用、被 Divvy's Preview 消费；本质是「**把规则重写成纯函数**」，与我们 Local Oracle 的形态几乎一致，但受制于游戏运行时与 GPL。**与本项目关系**：**借鉴（强烈）**：①效果按 `cardarea × 阶段` 分派的组合模型（可直接映射成我们的 effect 解析器）；②随机性用 `min/exact/max` 三态表达（比单点值更诚实，也天然对应「确定性判定器」的输入）；③「只模拟影响分数的效果」这一裁剪原则（我们的规则子集也应按此收口）。**不复用**：GPL-3.0 + 依赖 Lovely/Steamodded 运行时。

#### 1.4.4 `DivvyCr/Balatro-Preview` —— 游戏内实时分数预言（对拍工具）

- **URL**：<https://github.com/DivvyCr/Balatro-Preview>
- **作者/维护**：DivvyCr。**160★ / 11 fork / GPL-3.0 / Lua**，创建 2024-03-22，最近推送 2025-09-26。
- **目的**：在玩家选中牌时**实时显示预测得分**，本质是把 §1.4.3 的模拟库做成 UI。
- **设计原理**：`DVPreview.lua` 调 `DV.SIM.run()` 并渲染；作者在 README 里反复强调「**限制模拟调用次数**」，说明该模拟在真实运行时是有性能代价的。
- **效果**：160★ 说明「玩家真的需要算分」；它也是**最省力的人工对拍界面**：我们自建引擎的结果可以对着它逐手核对。**与本项目关系**：**不引入（依赖游戏本体），但在人工对拍环节可作为「真游戏侧参照」**；同样受 GPL 约束。

### 1.5 种子 / RNG 与数据

#### 1.5.1 `SpectralPack/Immolate` —— OpenCL 种子搜索器

- **URL**：<https://github.com/SpectralPack/Immolate>（README/awesome 里常见的 `MathIsFun0/Immolate` 会 301 到此处）
- **作者/维护**：SpectralPack 组织（MathIsFun0 主导）。**166★ / 57 fork / C（OpenCL）/ 非标准许可（NOASSERTION）**，创建 2024-01-04，最近推送 2025-04-04。
- **目的**：用 GPU 暴力搜索「满足条件（某 joker/某 tag/某商店序列）的种子」。
- **设计原理**：把原版 RNG 与商店/补充包生成逻辑用 C + OpenCL 重写，按过滤器在 GPU 上并行扫种子空间。
- **效果**：社区种子搜索的底座（Ouija、Balatro4J 等均为其衍生）；它的存在证明「种子内容可**离线精确推演**」。**与本项目关系**：**不引入**（GPU/OpenCL 重依赖、许可不明），但它是「固定 seed ⇒ 固定局面」这一事实的**工程背书**（若种子推演不能离线复现，这些工具就不可能存在）。

#### 1.5.2 `OptimusPi/Ouija` —— Immolate 的 JSON 前端

- **URL**：<https://github.com/OptimusPi/Ouija>
- **作者/维护**：OptimusPi。**9★ / 1 fork / C / 非标准许可**，创建 2025-06-12，最近推送 2025-07-06。
- **目的**：把种子搜索的过滤条件做成 JSON 配置（可视化/可脚本化），降低使用门槛。
- **设计原理**：基于 Immolate 的搜索内核 + JSON 过滤器描述 + 前端。**效果**：小工具，生态位清晰。**与本项目关系**：不引入；若我们要「按条件生成场景种子」，这种「声明式过滤器」的设计值得借鉴。

#### 1.5.3 `balatrohq.com`（Balatro HQ）—— 社区最完整的「真 RNG 种子分析 + 算分」站点

- **URL**：<https://balatrohq.com/>（作者 GitHub：<https://github.com/o98k-ok>）
- **作者/维护**：o98k-ok（个人站，写明「非官方、不隶属 LocalThunk/Playstack」）。页面自述数据对齐 **1.0.1o**。**维护状态：工具与指南仍在更新（站点 2026 年内容），提交频率未能核实。**
- **目的/原理**：①Seed Analyzer——「**replays the game's real RNG, ante by ante**」，逐 ante 列出 Boss/Voucher/商店队列/补充包/传奇 joker；②Shop Replay——按商店样式重放并支持 reroll/开包；③Score Calculator——支持真实卡牌（rank/suit/edition/seal/enhancement）逐张计分、A/B 两套 build 对比、可分享 URL；④**AI Seed Advisor**——把种子分析结果转成 playstyle/推荐阵容/前中后期计划；⑤数据库 278 条（150 jokers / 52 consumables / 32 vouchers / 16 enhancements / 15 decks / 13 hands）。
- **效果**：社区侧「种子确定性 + 精确算分」的**完成度上限**；局限是它是网站不是 API，且其「AI 建议」不可判定（属于内容生成，无真值）。**与本项目关系**：**借鉴（数据/对拍来源）**：①对拍「同一 seed 下我们的商店/牌序是否与真游戏一致」时，它是最快的第三方参照；②它的「数据库条目数」可作为我们数据表完整性检查的清单。**风险**：版权与许可未声明（站点内容不可直接搬运）。

#### 1.5.4 `BalatroLab`（balatrolab.com）—— 双语数据库 + 确定性算分器

- **URL**：<https://balatrolab.com/en>
- **作者/维护**：站点自述由社区维护（awesome-balatro 记为 @Max179）。**维护状态未能核实**（未读到提交记录）。页面自述 **278 条记录**、双语、本地化媒体、确定性算分器、joker 协同查找、解锁追踪、deck builder、seed vault。
- **效果**：与 Balatro HQ 高度重叠的数据站，可作为**交叉核对**（两个独立来源都说 150 jokers / 278 条，说明数据口径稳定）。**与本项目关系**：数据核对备选；不引入。

#### 1.5.5 Kaggle「BalatroBench」数据集

- **URL**：<https://www.kaggle.com/datasets/s1m0n38/balatrobench>
- **作者/状态**：S1M0N38 上传，由 `coder/balatrobench` README 指向；**页面仅标题可读（JS 渲染），内容与许可见 §5 未核实**。
- **效果**：已有 **LLM 真实对局数据（runs / benchmarks）** 可下载。**与本项目关系**：**借鉴（现象级对照）**——若我们要论证「现有评测只给总分」，这批数据是最好的实证素材（可统计其字段里是否存在步骤级失败标签）。**不可直接复用**（格式/许可未核）。

### 1.6 社区知识库

#### 1.6.1 `balatrowiki.org`（Balatro Wiki）

- **URL**：<https://balatrowiki.org/>
- **作者/维护**：社区维护，Weird Gloop 托管；首页自述 **518 篇文章 / 1,017 文件 / 30,984 次编辑**，对齐版本 **1.0.1o-FULL（Friends of Jimbo 4）**，最近编辑 **2026-11-11**；许可 **CC BY-NC-SA 3.0**。
- **目的/原理**：MediaWiki 结构的规则百科：Jokers（按稀有度分页）、Poker hands、Blinds & Antes、Stakes、Card modifiers、Shop、Vouchers、Booster Packs、Tags、Consumables（Tarot/Planet/Spectral）等，条目直接对应游戏对象。
- **效果**：**规则子集最可靠的事实来源**（且标注了游戏版本）。**与本项目关系**：**借鉴（数据来源）**：牌型基础分/升级曲线、盲注目标分、稀有度权重、卡牌效果文本都可据此建表。**风险**：**CC BY-NC-SA** —— 不能把文本/表格直接搬进我们（若为 MIT/Apache）的仓库，也不能商用；正确做法是「读完自己重写描述 + 只取不可版权的事实（数值）」，并在报告里注明来源。

#### 1.6.2 `jie65535/awesome-balatro` —— 生态地图（本次调研的检索入口）

- **URL**：<https://github.com/jie65535/awesome-balatro>（中文版：`blob/Chinese/README-zh_CN.md`）
- **作者/维护**：jie65535。**维护状态：README 里工具条目已更新到包含 Balatro HQ / BalatroLab / Balatro Seed Oracle / Motely 等新项目（说明近期仍在维护）；star 数未能核实（由 raw README 读取，未取 API 元数据）。**
- **目的/原理**：Awesome 式索引，按 **Tools / Mod Loaders / Mods（Require Steamodded / Balamod / Lovely / Other）/ Resources** 分类，每条给一句话说明 + 作者。
- **效果**：社区生态的**全量清单**（本次据此发现 Balatro HQ、BalatroLab、Immolate、Ouija、Motely、Balatro4J、The Soul、Blueprint、Green Needle、Talisman、JokerDisplay 等）。**与本项目关系**：**借鉴（检索与完整性核对）**：写「研究现状」时可用它证明「生态项目很多、但归类后没有归因类工具」；也是避免遗漏同类工作的检查表。

### 1.7 只判断不生成的小模型方案（Jev / TypeSafe）

> 说明：该类方案在生态里**只有一个可核实的个案**，且**没有公开的 Balatro 实现**。能核实的是「模型真实存在 + 有人做过 Balatro 接入」；不能核实的是「有仓库、有结果、有基准」。

#### 1.7.1 TypeSafe **Jev**（System One）+ 个人 Balatro 集成 —— 唯一真实的「只判断不生成」方案

- **URL**：<https://juris-savos.me/blog/jev-plays-balatro>（2026-09-19，作者 Juris Savostijanovs）｜<https://openrouter.ai/typesafe/jev>｜<https://github.com/wondertwins/jev-benchmark>
- **作者/维护**：TypeSafe 提供模型（闭源云服务）；Balatro 集成是**个人博客项目**，未见公开仓库（**该集成代码未能核实**）。`jev-benchmark` 为第三方（wondertwins）仓库，8★、MIT、Python，创建/推送 2026-09-16。
- **目的**：验证「不做生成、只做判断」的模型能否在 Balatro 里承担高频决策。
- **设计原理**（博客原文可核）：Jev「不生成文本」，输入 `state`（一段紧凑文本）+ `questions`（`choice` / `score` / `noul` 三类），**一次并行返回每个选项的校准概率**（OpenRouter Decisions API，`model: ~typesafe/jev-latest`）。Balatro 侧的架构是：`balatrobot JSON-RPC → Python 控制环（hand evaluator 枚举候选并预打分）→ Jev choice → play/discard/use`；**Jev 永远看不到原始卡牌对象、看不到完整 gamestate、看不到全部 218 种组合**，只看到 8–15 个「已预打分的候选」。手牌评估器只算基础牌型分（chips × mult，用当局 hands 等级表），**不模拟 joker/edition/seal/enhancement**（博客自述这是近似）；另有硬编码 **Panic Filter**（最后一手且还有弃牌、最佳估算 < 需求 30% 时，强制只给弃牌选项）。实测仅使用 `choice`，`score`/`noul` 未接入；demo 为 seed `7ZYZ1WFB`、ante 1–4、30 个决策的可回放样本。
- **效果**：**无量化结果**（无对照、无胜率/分数），唯一可引用的是「架构可行 + 一篇详细的失败分析」；博客自己指出最大瓶颈是「算分近似」，并计划改用 `DivvyCr/Balatro-Simulation`。可行性结论、数字、价格均不可当评测证据。
- **与本项目关系**：**方法论直接借鉴，模型坚决不引入**。借鉴三条：①**「精确计算归代码、判断归模型」的分工**（正是我们 Local Oracle + 4 类判定器的哲学）；②**给模型的是「已预打分的候选集」而非原始状态**（我们的场景提示词与工具返回也应如此，既降 token 又消除非法动作）；③**用规则守卫兜住模型系统性错误**（Panic Filter ≈ 我们的「确定性判定器先判、再让模型解释」）。不引入的理由：闭源云 API、与「评测而非打牌」目标相反、且会让项目从「评测框架」漂移成「打牌优化」。

> 其他「judge-only」形态（如各类 reward model / verifier / 小判别器）在 LLM 评测文献里常见，但**未见 Balatro 相关的第二个可核实个案**，故本类只列此一条。

### 1.8 其他值得记录的资源

- **`docs.smods.dev`（Steamodded 文档站）**<https://docs.smods.dev/> ✅：除安装指南外，含 **Calculate Functions、`G` 变量、Game Objects API、`SMODS.Scoring_Parameter` / `SMODS.Scoring_Calculation`、Weight System** 等章节。**与本项目关系：借鉴（规则语义与字段的权威参照）**——我们写规则子集时，joker 的「在哪个阶段、怎么改 chips/mult/dollars」应逐条对照此文档，而不是凭记忆。
- **`balatro-rs` 的衍生科研用法**：`docs/research/03` 已核实的 arXiv:2610.39049（EXAG 2026 workshop）用 **Rust 模拟器 + 对真实客户端做 state-diff 校验 + 动态合法动作掩码 + 双策略 PPO**，与本文件的 `evanofslack/balatro-rs` 互为印证（同一技术路线在学术与开源两侧同时出现）。**报告引用时以 03 文档为准**（本文件未打开该论文）。
- **`The Soul` / `Blueprint` / `Motely` / `Balatro4J` / `Green Needle` / `Balatro Seed Suite` / `BusDash` / `Talisman` / `JokerDisplay` / `DebugPlus`**：均在 awesome-balatro 清单中出现（**⏳ 未逐个打开**）。其中 `Motely`（C# SIMD 种子搜索）、`The Soul`（在线种子分析）、`BusDash`（金注胜率看板）与本项目关系最弱，报告中可只用一句话概括「种子/统计类工具已饱和」，不必逐条展开。

---

## 2. 资源清单（32 条）

> 类型：repo / 文档 / 数据 / 文章。核实：**✅ 已打开页面**（README/API/文档站/Wiki 正文）；**⏳ 仅搜索结果或仅页面标题可读**。
> 星数与日期均为 2026-11-12 通过 GitHub API/页面读数，**仅代表当日**。

1. coder/balatrobot | https://github.com/coder/balatrobot | repo | ✅ | 真游戏 JSON-RPC 2.0 控制面（`:12346`，22 方法，完整 GameState schema），生态事实标准（81★，2026-11 活跃）。
2. coder/balatrollm | https://github.com/coder/balatrollm | repo | ✅ | 官方 LLM 打 Balatro 参考 bot（114★），消费 balatrobot API，是 balatrobench 的上游。
3. coder/balatrobench | https://github.com/coder/balatrobench | repo | ✅ | **与本项目名称相近（外部项目）**的 LLM 排行榜/结果分析工具（23★，balatrobench.com），只做展示不做判定。
4. coder/balatrobot API 参考 | https://coder.github.io/balatrobot/latest/api/ | 文档 | ✅ | 22 个方法的参数/前置状态/错误码 + GameState/Enums，是「工具面 schema」的最佳模板。
5. Steamodded/smods | https://github.com/Steamodded/smods | repo | ✅ | Balatro mod 框架（1015★，GPL-3.0），`SMODS.*` 对象 + `calculate(context)` 语义的社区标准。
6. docs.smods.dev | https://docs.smods.dev/ | 文档 | ✅ | SMODS API 文档：Calculate Functions、`G`、Scoring_Parameter/Calculation、Weight System；规则语义参照。
7. ethangreen-dev/lovely-injector | https://github.com/ethangreen-dev/lovely-injector | repo | ✅ | 运行时 Lua 注入器（626★，Rust，MIT），TOML patch（pattern/regex/copy/module）；patch 格式自述不稳定。
8. balamod/balamod | https://github.com/balamod/balamod | repo | ✅ | 另一条 modloader/injector/decompiler 路线（162★，2025-01 后停更），生态已收敛到 Lovely+Steamodded。
9. besteon/balatrobot | https://github.com/besteon/balatrobot | repo | ✅ | coder 版的前身（62★，2024-04 停更，36 fork），说明社区轮子会分叉。
10. SleepyG11/HandyBalatro | https://github.com/SleepyG11/HandyBalatro | repo | ✅ | 真游戏加速/QoL mod（155★），被 RL 环境用于 512× rollout，证明真游戏瓶颈在速度。
11. alesha-pro/evalatro | https://github.com/alesha-pro/evalatro | repo | ✅ | 真游戏 LLM 基准（28★，TS，ISC）：`score = progress × legality`、Ante 12 目标、服务端重算 + code hash、MCP 模式。
12. evalatro.dev | https://evalatro.dev/ | 数据 | ⏳ | 公开排行榜站点；仅标题/About 可读（JS 渲染），榜单数值未核实。
13. proj-airi/game-playing-ai-balatro | https://github.com/proj-airi/game-playing-ai-balatro | repo | ✅ | CV+LLM 路线（44★）：YOLO11n 检测卡/UI + OCR + LLM，无结构化状态、不可判定。
14. How I Got TypeSafe's Jev to Play Balatro | https://juris-savos.me/blog/jev-plays-balatro | 文章 | ✅ | 唯一真实的 Jev×Balatro 架构记录：hand evaluator 预打分 + `choice` 问题 + Panic Filter；无量化结果。
15. wondertwins/jev-benchmark | https://github.com/wondertwins/jev-benchmark | repo | ✅ | TypeSafe Jev 的第三方基准/试验场（8★，MIT），含 chess 任务；Balatro 数字为二手转述。
16. TypeSafe: Jev model versions (OpenRouter) | https://openrouter.ai/typesafe/jev | 数据 | ✅ | 模型存在性核验（页面标题可读）；Balatro 集成为个人博客，无公开仓库。
17. cassiusfive/balatro-gym | https://github.com/cassiusfive/balatro-gym | repo | ✅ | Gymnasium 封装（42★，MIT），Observation/Action/Reward 全部 WIP，不宜作依赖。
18. Jonathanace/Balatro-Gym | https://github.com/Jonathanace/Balatro-Gym | repo | ✅ | 用 balatrobot 驱动真游戏做 RL（1★，Apache-2.0），512× 加速，obs/网络未完成。
19. evanofslack/balatro-rs | https://github.com/evanofslack/balatro-rs | repo | ✅ | Rust 规则引擎 + 穷举 move generator + 固定 action mask + 逐字节 RNG + PyO3（15★，**无 LICENSE**）；74/150 jokers，缺 skip tags/多牌组/多赌注。
20. Jokers in the Machine (Zenodo) | https://zenodo.org/records/23513044 | 文章 | ✅ | **课程提案**（非论文）：扩 balatro-gym + PPO vs LLM + 超胜率指标；证明需求存在、无成果。
21. EFHIII/balatro-calculator | https://github.com/EFHIII/balatro-calculator | repo | ✅ | 社区标杆算分器（285★，MIT，JS）；「少数 joker 可能不准」；交互式网页，非 API。
22. WilsontheWolf/balatro-calculator | https://github.com/WilsontheWolf/balatro-calculator | repo | ✅ | **EFHIII 的 fork**（0★，2024-03 后无更新），非独立实现。
23. DivvyCr/Balatro-Simulation | https://github.com/DivvyCr/Balatro-Simulation | repo | ✅ | Lua 算分模拟库（1★，GPL-3.0）：按 `cardarea × 阶段` 分派 effect，随机性用 min/exact/max 三态。
24. DivvyCr/Balatro-Preview | https://github.com/DivvyCr/Balatro-Preview | repo | ✅ | 游戏内实时预测得分（160★，GPL-3.0），人工对拍时最省力的真游戏侧参照。
25. SpectralPack/Immolate | https://github.com/SpectralPack/Immolate | repo | ✅ | OpenCL 种子搜索器（166★，C，非标准许可），证明种子内容可离线精确推演。
26. OptimusPi/Ouija | https://github.com/OptimusPi/Ouija | repo | ✅ | Immolate 的 JSON 过滤器前端（9★），声明式搜索配置的参考。
27. Balatro HQ | https://balatrohq.com/ | 数据 | ✅ | 真 RNG 种子分析（全 8 ante）+ 算分器 + AI Seed Advisor + 278 条数据库，对齐 1.0.1o。
28. BalatroLab | https://balatrolab.com/en | 数据 | ✅ | 双语 278 条数据库 + 确定性算分器 + seed vault；可作数据交叉核对。
29. balatrowiki.org | https://balatrowiki.org/ | 数据 | ✅ | 社区 Wiki（518 篇，1.0.1o-FULL，CC BY-NC-SA），规则/牌型/盲注/稀有度的事实来源。
30. jie65535/awesome-balatro | https://github.com/jie65535/awesome-balatro | 数据 | ✅ | 生态全量清单（Tools/Mod Loaders/Mods）；本次检索入口与遗漏检查表。
31. Kaggle: BalatroBench | https://www.kaggle.com/datasets/s1m0n38/balatrobench | 数据 | ⏳ | BalatroLLM runs/benchmarks 数据下载；页面仅标题可读，字段与许可未核。
32. BalatroBench 媒体报道（Gigazine 2026-02） | https://gigazine.net/news/20260213-balatrobench/ | 文章 | ⏳ | 说明该基准已有公众关注度；内容未读，只作「存在媒体覆盖」的旁证。

> 说明：上表 32 条中 ✅ 29 条、⏳ 3 条；正文详解覆盖其中 26 个项目/资源（1.1–1.7 及 1.8 的文档站）。若报告只允许 ≤25 条，建议保留 1–7、11、19、21、23–24、27–30。

---

## 3. 生态空白（8 条，可直接改写成「研究空白」段落）

1. **没有「无需游戏本体」的确定性评测环境。** 现有两条路：绑真游戏（balatrobot 栈 / evalatro / Jonathanace）或只做局部（算分器、模拟库、种子工具）。前者不可 CI、不可并行、受版本链支配；后者不构成「从状态到动作到结果」的完整可运行环境。**没有第三条路（完整规则子集 + 固定场景）被公开实现。**
2. **没有失败归因层。** 所有评测的终点都是标量：evalatro 的 `progress × legality`、balatrobench 的排行榜、RL 的训练曲线、Zenodo 提案的「超胜率指标」。**非法动作只被计数（legality），不被分类，更不被定位到具体步**。全生态找不到「把一局失败拆成 N 类可判定原因」的公开实现。
3. **没有固定场景集（scenario suite）。** evalatro 有 seed matrix，但目标是跑完整局；balatro-rs 有 `gen_actions()`，但没有「预置 60 个单点决策局面 + 每个局面的 oracle 最优动作」这种东西。**「单步可判定」这一粒度在生态里是空白。**
4. **没有 oracle 驱动的过程指标。** 没有人算 regret、best-action match、oracle 分差；现有指标全是终局/进度。而这是规则确定环境最该有的指标（成本低、可解释、可归因）。
5. **规则实现之间没有一致性基准（conformance suite）。** 各实现覆盖互相矛盾：EFHIII「少数 joker 不准」、Divvy SIM「只覆盖影响分数的 joker 且刻意不模拟四指/交易卡」、Jev 的 hand_eval「不模拟 joker/edition/seal」、balatro-rs「74/150 jokers」、smods 面向扩展而非复算。**没有任何公开的「同一局面、N 个实现、结果对比」测试集。**
6. **没有统一的 action / state schema。** balatrobot 用**手牌索引**（`play{cards:[0,2]}`），balatro-rs 用 **Action 枚举 + 固定 action mask**，smods 用**对象回调**；三者不可互换，导致「跨实现的评测结果不可比」，也让 Agent 工具层每接一个环境就要重写。
7. **MCP / 工具化接口只是副产品。** 只有 evalatro 顺带把 tool registry 暴露成 MCP server；balatrobot 是 HTTP RPC 而非 Agent 工具语义（无 description、无参数校验提示、无 per-tool 示例）。**没有人为「长程决策 Agent 评测」设计过工具集。**
8. **没有可复现的失败数据集 / 标注。** balatro-rs 有 replay 日志但自用；evalatro 有完整 transcript，但那是「LLM 决策日志」，**没有失败类别标签、没有 oracle 对照**。WHO&WHEN（见 `docs/research/03` 文献 [34]）那类「步骤级失败标注」在 Balatro 上不存在。

> 备选第 9 条（如需要）：**评测依赖商业游戏 + Steam 账号 + 3–4 层注入**，违背「基准应可分发、可复现」的社区惯例（对比 ALE/TextWorld 的「环境随基准分发」）。这也是 evalatro 无法被第三方一键复跑的根本原因。

---

## 4. 「可借鉴 / 不借鉴」决策表

| # | 借鉴点 | 来源 | 用在本项目哪里 | 风险 / 注意 |
|---|---|---|---|---|
| 1 | JSON-RPC 方法集 + **Required State 前置校验** + 统一错误码 | balatrobot API | MCP 工具的 `preconditions` 与错误分类（`BAD_REQUEST/INVALID_STATE/NOT_ALLOWED`） | 方法名照抄会让人误以为我们依赖真游戏；应改为工具语义命名 |
| 2 | `GameState / Area / Card / modifier{seal,edition,enhancement}` 字段分层 | balatrobot API | 场景快照 JSON schema、Oracle 输入 | 必须**不用**其「索引式动作」；动作要绑稳定 id 才可复现 |
| 3 | 7 状态状态机（MENU→BLIND_SELECT→…→GAME_OVER） | balatrobot 文档 | 规则子集状态机（可裁掉 `SMODS_BOOSTER_OPENED` 等） | 我们的子集可能不含商店/补充包，需显式声明裁剪边界 |
| 4 | `progress × legality` 记分 + **transcript 服务端重算** + code hash | evalatro | 辅助合法性指标；评测结果的可信性设计（防篡改、可复算） | `legality` 太粗（只计数），主指标必须换成 oracle regret；Ante 12 目标不适用 |
| 5 | tool registry 单一事实源，同时服务 LLM 与 MCP | evalatro | 我们 MCP server 与内部 runner 共用同一动作定义 | 需自行设计「工具返回值可直接判定」的返回结构 |
| 6 | 穷举 move generator + **固定大小 action mask** | balatro-rs | 场景构建、regret 计算、与 RL 共用动作面 | **无 LICENSE，不可拷代码**；只能独立重写；其 74/150 joker 覆盖不可直接继承 |
| 7 | 逐字节复刻原版 seed/RNG | balatro-rs（`balatro-seed`） | 若采用「固定 seed = 固定局面」，这是做法参照 | 子集引擎若不复刻原版 RNG，就不能声称「与真游戏同种子同局面」——**要么复刻，要么改口径** |
| 8 | 效果按 `cardarea × 阶段（before/individual/repetition/global）` 分派；随机性用 `min/exact/max` 三态 | Divvy's Simulation；smods calculate 文档 | Local Oracle 的 effect 组合器与随机性表达 | **GPL-3.0 传染**：只借鉴设计，不拷实现；且它依赖游戏运行时 |
| 9 | 「只模拟影响分数的效果」这一裁剪原则 | Divvy's Simulation | 规则子集边界定义（60 场景的规则覆盖清单） | 裁剪必须写入报告，否则会被质疑「不完整=不忠实」 |
| 10 | 游戏内实时预测分数 | Divvy's Preview | **人工对拍**时作为真游戏侧参照界面 | 依赖游戏本体；只能当验证工具，不能当 oracle |
| 11 | 单点算分器（可交互、可构造完美手牌） | EFHIII calculator | 基础牌型/常见 joker 的第三方抽检（5–10 例） | 它自身「少数 joker 不准」；joker 覆盖与我们子集不同，差异要记录而非强行对齐 |
| 12 | 「精确计算归代码、判断归模型」+ 只给模型「已预打分的候选集」+ 规则守卫（Panic Filter） | Jev × Balatro 博客 | 4 类判定器与 Oracle 的分工；场景提示词构造；判定器先判、模型后解释 | 不引入 Jev；博客中的 chess 数字是二手转述；其 hand_eval 近似不能当对照基线 |
| 13 | 真 RNG 种子分析（逐 ante 的商店/包/Boss/Voucher） | Balatro HQ | 抽检「同 seed 下我们的场景生成是否与真游戏一致」；数据表完整性对照 | 站点无明示许可，仅作参照不可搬运；它是网站非 API |
| 14 | 规则/牌型/盲注/稀有度数据表 | balatrowiki.org | 规则子集的数据表来源（数值事实） | **CC BY-NC-SA**：不能直接搬文本进代码库、不能商用；需自行改写描述 |
| 15 | 生态全量清单与分类法 | awesome-balatro | 研究现状的「生态地图」与遗漏检查表 | 清单本身有滞后，条目需逐个复核（本文件已复核 26 个） |
| 16 | 声明式过滤器（JSON）驱动搜索/场景选择 | Ouija | 若做「按条件挑场景种子」，可借鉴其配置形态 | 其内核是 Immolate（GPU），我们不需要 |
| 17 | 不采用：真游戏 + 注入链（Lovely/Steamodded/balatrobot） | §1.1 全部 | —— | 版本链脆弱、需正版游戏与图形环境、不可 CI/并行；**这是本项目立项前提，不是可选项** |
| 18 | 不采用：Gymnasium 封装（balatro-gym / Jonathanace） | §1.3.1–1.3.2 | —— | MDP 三要素 WIP；真游戏路线速度瓶颈（512× 才可训练） |
| 19 | 不采用：CV 路线（proj-airi） | §1.2.2 | —— | 识别误差与决策误差不可分离，与「可判定归因」直接冲突 |
| 20 | 不采用：Jev 等外部小模型 | §1.7.1 | —— | 闭源云 API、无 Balatro 评测、目标会从「评测」漂移成「打牌优化」 |

---

## 5. 未能核实 / 写作注意（交给 Lead）

**未能核实（不要在报告里写成事实）**

1. `evalatro.dev` 榜单正文：页面 JS 渲染，仅标题可读；**具体分数、模型排名、参赛模型清单均未核实**。
2. Kaggle `s1m0n38/balatrobench` 的**字段结构、样本量、许可证**：仅标题可读。
3. BalatroBench 的媒体报道（Gigazine / 中文公众号 / theneuralfeed）：**仅搜索结果**，未开页；只能写「有媒体报道」并标 ⏳。
4. `coder/balatrollm` 的内部架构（策略、提示词、工具注册表实现）：README 未展开，本次未读源码。
5. `jev` 集成的**代码是否存在**：博客提到 `src/balatrojev/` 等路径，但未发现公开仓库；**Jev 的价格/延迟/上下文长度**（plan 文档里的 $0.042/MTok 等）**未核实，不引用**。
6. `balatrogame.fandom.com`（Fandom 版 Wiki）：**连续 3 次抓取失败**，未打开；本文件改用 `balatrowiki.org`（Weird Gloop 托管，可打开）。若报告需要「两个 Wiki」，需另行核实 Fandom 版状态。
7. `ollezetterstrom/Balatro-gym`：仅搜索结果，未打开；可作为「另有 RL 尝试」的 ⏳ 旁证，不展开。
8. `The Soul / Blueprint / Motely / Balatro4J / Green Needle / Balatro Seed Suite / BusDash / Talisman / JokerDisplay / DebugPlus`：均来自 awesome-balatro 清单，**⏳ 未逐个打开**，只可概括为「种子/统计/展示类工具已饱和」。
9. `coder/balatrobench` 与 `evalatro` 的**实际用户量/榜单规模**：未核实（只有 star 数与公开站点存在性）。
10. `evanofslack/balatro-rs` 的具体测试覆盖与正确性：README 给出功能清单，但**未读测试/未跑**，「74/150 jokers 已实现」是 README 自述。

**写作注意**

1. **相关工作里说明与 `coder/balatrobench` 的差异**（§0.1）：它是排行榜与结果分析工具，本项目是长线规划测试集（失败归因仅作诊断报告层）。这是本次调研最可能被评审第一眼质疑的点。
2. **`WilsontheWolf/balatro-calculator` 是 fork，不是独立项目**（§0.2）。原任务书的表述需修正。
3. **Jev 只能写「存在性 + 方法论」，不能写「已有 Balatro 小模型基准」**（§0.3）。博客中的 chess 数字属二手转述（转引 `wondertwins/jev-benchmark`），不要当独立证据。
4. **`balatro-rs` 无 LICENSE**：报告里可以写「存在可离线运行的公开规则引擎」，但**不能写「可复用其代码」**；我们若重写，须说明「独立实现、设计对标」。
5. **`Divvy's Simulation` / `Preview` 是 GPL-3.0**：只能借鉴设计，不能拷实现（否则我们的仓库也可能被传染）。
6. **Wiki 是 CC BY-NC-SA**：数据表只能取「不可版权的事实（数值）」，描述文本必须自写；报告与仓库都要注明来源。
7. **星数与日期会变**：本文件所有 star/日期均为 **2026-11-12** 读数，写进报告时建议写「截至 2026-11-12」。
8. **与 `docs/research/03` 的分工**：03 负责学术文献（arXiv/会议/Zenodo）与「Balatro 学术占位」的精确表述；本文件负责**工程/生态项目**（仓库、文档、数据站、Wiki）。两者交叉处（arXiv:2610.39049、Zenodo 提案、balatro-gym）**以 03 的口径为准**，本文件不重复论证。
9. **与 `plan/详细版/06-生态调研与复用决策.md` 的一致性**：本文件对 plan 的结论是**加强而非推翻**（不接真游戏、Gym 只做探针、Jev 只取方法论、calculator 只作对拍）；新增的关键信息是：①`coder/balatrobench` 的差异需在相关工作里说明（项目正式名已定为 BalatroEval，不再讨论副标题）；②`evanofslack/balatro-rs` 这一「最接近的自建引擎」存在（plan 里未提及）；③`Divvy's Simulation` 提供了「effect 组合 + 三态随机」的现成设计参照。
