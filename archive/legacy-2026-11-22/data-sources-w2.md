# 数据来源与复用决策 — W2（历史版：v2.1，v3.0 追加说明）

> 本文为中文版（原英文版已由本文取代；历史英文版见提交 `c65fb9b`）。
> **历史状态标注**：本文表格记录的是 **W2 v2.1（提交 `c65fb9b`）当时的实际使用情况**，是历史事实，不得改写。
> **v3.0 追加（2026-11-13）**：W2 未接入真游戏；v3.0 规划接入 balatrobot（MIT），只做终验/捕获（📋 未执行）。完整来源清单以 [data-sources.md](data-sources.md) 为准，本文保留 W2 视角。
> 依据：`plan/详细版/07-真实游戏接入与终验.md` §4.1、§8

## 1. W2 v2.1 实际使用情况（历史，不变）

| 来源 | 预期用途 | 本次实现实际如何使用 | 许可 / 复用规则 | 状态（W2 时点） |
|---|---|---|---|---|
| SMODS Calculate Functions | 理解 context／area 概念与计分阶段 | 仅作架构参考；自定义效果元数据另在别处记录 | 未复制任何源代码 | 已审阅；`before` 语义的适用边界记录在 [joker-semantics.md](joker-semantics.md) §3 |
| DivvyCr/Balatro-Simulation | 理解纯函数式计分分派结构 | 仅借鉴设计思路；未复制代码 | 遵守仓库声明的许可（`LICENCE`）；未复制实现 | README 已审阅 |
| Balatro HQ poker-hands | 核对原版基础筹码／倍率与计分事实 | 用于识别原版计分与自定义公式之间的差异 | 仅使用事实；未复制描述文本 | 参考：https://balatrohq.com/poker-hands/ |
| Game Design Lab / Balatro wiki mirror | 交叉核对计分流水线与阶段事实 | 仅作事实参考 | 未复制文本或代码 | https://teemo.dev/game-design/balatro/systems/scoring-engine-chips-mult/ |
| EFHIII/balatro-calculator | 第三方单手抽检（spot-check）候选 | 本环境尚未执行任何实测 | 上游仓库声明 MIT 许可；未复制代码 | 5 项抽检待完成，见 [engine-fidelity.md](engine-fidelity.md) 附录 D |
| evanofslack/balatro-rs | 仅作实现调研 | 未复制代码 | 未确认许可即不得复制代码 | 未用于实现 |
| coder/balatrobot | 未来可能参考的动作／校验 API | 未安装、未调用；本项目不对原版游戏脚本化操作 | 仅借鉴命名 | **W2 未接入**；v3.0 规划接入（MIT），只做终验/捕获 📋 |

## 2. v3.0 规划中的来源（📋 未执行，W3/W5）

> W2 的"未安装 / 不在范围"在 v3.0 改为 **"W2 未接入；v3.0 规划接入"**。以下均**尚未安装、尚未调用**。

| 来源 | 许可 | v3.0 用途 | 边界 | 状态 |
|---|---|---|---|---|
| `coder/balatrobot` | **MIT** | 真游戏 JSON-RPC 控制面（`127.0.0.1:12346`），用于 A2/A4 捕获与 12 局终验 | 不修改源码、不并入本仓库；适配器只做字段映射与 id↔下标转换 | 📋 未安装 |
| Lovely（`lovely-injector`） | **MIT** | 运行前置（Lua 注入） | 只记录版本，不分发 | 📋 未安装 |
| Steamodded（`smods`） | **GPL-3.0** | 运行前置（mod 框架） | **仅作运行时依赖**；不复制/不分发其代码 | 📋 未安装 |
| Balatro（Steam 1.0.1o） | 商业软件 | 真游戏本体，只在本机跑来捕获/终验 | 游戏文件/素材/`.jkr` 存档/截图**不入库**（L8） | 📋 未安装 |

## 3. vanilla 数值来源（W3 对齐目标，📋 未实现）

> W2 引擎是 L0：自定义公式 + 合成 Joker。下列 vanilla 数值是 W3 对齐改造的目标，当前**没有实现、没有验证**。只取不可版权的事实（名称/数值/条件），描述自写。

### 3.1 9 种牌型的基础 Chips×Mult（等级 1）

| 牌型 | 基础 Chips | 基础 Mult | 计分牌张数 |
|---|---:|---:|---:|
| High Card（高牌） | 5 | 1 | 1（最高 1 张） |
| Pair（对子） | 10 | 2 | 2 |
| Two Pair（两对） | 20 | 2 | 4 |
| Three of a Kind（三条） | 30 | 3 | 3 |
| Straight（顺子） | 30 | 4 | 5 |
| Flush（同花） | 35 | 4 | 5 |
| Full House（葫芦） | 40 | 4 | 5 |
| Four of a Kind（四条） | 60 | 7 | 4 |
| Straight Flush（同花顺） | 100 | 8 | 5 |

来源：`balatrowiki.org`（Poker hands），CC BY-NC-SA 3.0，只取数值。当前 W2 实现**无基础 Chips**，且倍率表为自定义（SF12/4K10/FH8/FL6/ST5/3K4/2P3/P2/HC1），与上表不同。

### 3.2 盲注目标与牌组/赌注（Ante 1，白注，Red Deck）

| 项 | vanilla 值 | W2 现状 | 状态 |
|---|---|---|---|
| Small Blind 目标 | 300 | 300 | ✅ 数值巧合一致，但**流程不同** |
| Big Blind 目标 | 450 | 800 | ❌ 不同 |
| Boss Blind 目标 | 600 | 2000 | ❌ 不同（Boss 效果不实现，只记录） |
| 每盲注出牌次数 | 4 | 4 | ✅ |
| 每盲注弃牌次数 | 4（Red Deck +1） | 2 | ❌ 不同 |
| Joker 槽位 | 5 | 3 | ❌ 不同 |
| 初始手牌 | 8 | 8 | ✅ |

来源：`balatrowiki.org`（Blinds & Antes、Decks、Stakes）+ 真游戏 `start` 实测（📋 待执行）。

### 3.3 8 个具名 vanilla Joker（目录）

Joker（+4 Mult，无条件）/ Jolly Joker（+8 Mult，含对子）/ Zany Joker（+12 Mult，含三条）/ Sly Joker（+50 Chips，含对子）/ Wily Joker（+100 Chips，含三条）/ Half Joker（+20 Mult，打出 ≤3 张）/ The Duo（×2 Mult，含对子）/ The Trio（×3 Mult，含三条）。

- 完整表格（含来源链接与"待实现"状态）：[joker-semantics.md](joker-semantics.md) §2
- 来源：`balatrowiki.org` 各 Joker 页面，CC BY-NC-SA 3.0，只取名称/数值/条件
- 状态：📋 **全部未实现**；触发顺序必须真游戏实测，不得凭 Wiki 断言
- W2 的 `jc_*` / `jm_*` / `jx_*` 是**合成夹具**，不得进入训练集/主表，W3 需与 vanilla 目录分开命名

## 4. 许可与流程说明（保持有效）

- 本仓库中的效果描述与文档均为自行撰写。
- `bench/jokers.py` 中现有的 8 个 Joker 条目是合成测试夹具（synthetic test fixtures）。其数值是工程默认值，**不是对原版 Joker 数值的声明**。
- 未来版本若要声称与原版 Balatro 达到分数级保真度，必须先记录确切的游戏版本、确切的 Joker 身份与效果，以及所有实测的输入／输出对。不得把待完成的检查表述为已完成。
- v3.0 起，保真度的主门槛是 [engine-fidelity.md](engine-fidelity.md) 的 A 表（真游戏捕获）+ B 表（`save`/`load` 反事实回放）；旧 5 例抽检降为附录 D 辅助证据。
- **游戏文件 / mod 本体 / `.jkr` 存档 / 含游戏素材的截图不入库**（L8）；只提交脱敏状态 JSON、分数、trace、版本清单。
