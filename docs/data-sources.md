# BalatroEval 数据来源与许可清单（v3.0）

> 目的：落实 `plan/00-项目全貌.md` 决策 D14——**任何进入规则子集的数值都必须能追溯到来源，任何进入仓库的内容都必须许可清晰**。
> 原则：**数值可引，文本自写；设计可借鉴，代码不复制。**
> 版本：v3.0-2026-11-13 ｜ 状态：📋 初始清单（W2 起按实际使用逐条补齐"是否已落地"；v3.0 新增真游戏运行栈与 vanilla 数值来源）
> v3.0 变更：① 新增真游戏运行栈（balatrobot / Lovely / Steamodded）；② 新增 vanilla 牌型基础 Chips×Mult、盲注目标、8 个具名 Joker 的数值来源；③ 旧表述"不接入真游戏"改为 **"W2 未接入；v3.0 规划接入，只做终验/捕获"**（📋 未执行）；④ 新增"游戏文件/存档/截图不入库"条目。
> 依据：`plan/详细版/07-真实游戏接入与终验.md` §4.1、§8

## 1. 规则数值（只取不可版权的事实）

| 数据 | 来源 | 许可 | 用法 | 状态 |
|---|---|---|---|---|
| 牌型基础分与升级曲线 | `balatrowiki.org`（Poker hands） | CC BY-NC-SA 3.0 | 只取数值，描述自写 | 📋 |
| **vanilla 牌型基础 Chips×Mult（等级 1）**：高牌 5×1 / 对子 10×2 / 两对 20×2 / 三条 30×3 / 顺子 30×4 / 同花 35×4 / 葫芦 40×4 / 四条 60×7 / 同花顺 100×8 | `balatrowiki.org`（Poker hands） | CC BY-NC-SA 3.0 | 只取数值；W3 计分改造的目标值（当前未实现 📋） | 📋 |
| **计分牌筛选规则**：高牌只计最高 1 张 / 对子 2 张 / 两对 4 张 / 三条 3 张 / 顺子·同花·葫芦·同花顺 5 张 / 四条 4 张 | `balatrowiki.org`（Poker hands）+ 真游戏实测 | CC BY-NC-SA 3.0 / 实测 | 只取事实；边界以真游戏捕获为准（📋 待 A2 验证） | 📋 |
| 盲注目标分（旧写 300 / 800 / 2000） | `balatrowiki.org`（Blinds & Antes） | CC BY-NC-SA 3.0 | 只取数值 | 📋 |
| **Ante 1 盲注目标（白注 + Red Deck）：Small 300 / Big 450 / Boss 600** | `balatrowiki.org`（Blinds & Antes） | CC BY-NC-SA 3.0 | 只取数值；W3 流程改造的目标值（当前引擎仍是 300/800/2000 📋） | 📋 |
| **牌组与赌注事实**：Red Deck（+1 弃牌）/ White Stake / 初始 8 张 / 4 手 / 基础 5 Joker 槽位 | `balatrowiki.org`（Decks、Stakes）+ 真游戏 `start` 实测 | CC BY-NC-SA 3.0 / 实测 | 只取事实；W3 对齐目标（当前引擎 3 槽位、4 手/2 弃 📋） | 📋 |
| **8 个具名 vanilla Joker 的数值与条件**（Joker +4 Mult / Jolly +8 Mult / Zany +12 Mult / Sly +50 Chips / Wily +100 Chips / Half +20 Mult / The Duo ×2 Mult / The Trio ×3 Mult） | `balatrowiki.org`（各 Joker 页面） | CC BY-NC-SA 3.0 | 只取名称/数值/条件等不可版权事实；触发顺序必须实测，不得照 Wiki 断言 | 📋 目录见 [joker-semantics.md](joker-semantics.md) §2 |
| Joker 效果数值（+chips / +mult / ×mult） | `balatrowiki.org`、`Balatro HQ` | CC BY-NC-SA / 站点未明示 | 只取数值，行为语义对照 smods 文档 | 📋 |
| 稀有度、卡牌池规模（150 jokers / 32 vouchers 等） | `Balatro HQ`、`BalatroLab` | 站点未明示 | 仅作数据完整性核对，不搬运 | 📋 |
| 种子机制（种子决定全部随机要素） | `balatrowiki.org`（Seed 条目，引用游戏 1.0.1o 源码） | CC BY-NC-SA 3.0 | 仅作事实说明，不声称复刻 | ✅（已用于开题报告） |

> 注：v3.0 的训练集**不再由引擎生成**，而是"真游戏捕获 + 真游戏 `save`/`load` 反事实回放"；因此上表数值只是实现侧的目标校验，**最终事实以真游戏捕获（A 表）为准**。

## 2. 只借鉴设计、不复制代码的实现

| 项目 | 许可 | 我们借鉴什么 | 我们不做什么 |
|---|---|---|---|
| `evanofslack/balatro-rs` | **未声明许可证** | 穷举动作生成、固定 action mask、逐字节 RNG 的实现思路 | 不拷贝代码、不引入依赖、不在仓库内分发其产物 |
| `DivvyCr/Balatro-Simulation` | GPL-3.0 | `cardarea × phase` 效果分派、`min/exact/max` 三态随机、只模拟影响分数的效果 | 不拷贝实现（避免 GPL 传染） |
| `DivvyCr/Balatro-Preview` | GPL-3.0 | 人工对拍时的界面参照 | 不引入 |
| `alesha-pro/evalatro` | package.json 声明 ISC；仓库无 LICENSE 文件 | 重算校验、code hash、工具注册表单一事实源 | 不复用代码（栈不同） |
| `coder/balatrobot` | **MIT** | 工具契约（前置状态校验 + 统一错误码）、GameState 字段分层、JSON-RPC 2.0 方法集 | **v3.0 接入（📋 未执行）**，只作终验/捕获的适配层；不修改其源码、不把其代码并入本仓库 |
| `lovely-injector`（Lovely） | **MIT** | 运行前置（Lua 注入），只记录版本 | 只记录版本，不分发；不修改 |
| `Steamodded/smods` + `docs.smods.dev` | **GPL-3.0** | 规则语义（阶段/区域/回调顺序）的权威描述 | **仅作运行时依赖**：不复制/不分发其代码，不把 GPL 代码并入本仓库；不写 mod |
| `EFHIII/balatro-calculator` | MIT | 第三方抽检（辅助，5 例） | 不作依赖（网页非 API）、不集成 |
| `balatrowiki.org` | CC BY-NC-SA 3.0 | 只取数值事实（牌型/Joker/盲注/牌组） | 不搬运文本/表格/图片，描述自写 |

> **许可传染边界**：Steamodded（GPL-3.0）与 Balatro 本体（商业软件）**都只是本机运行时**，不是本仓库的依赖或分发物。仓库内的 `bench/`、`bridge/`、`scenarios/`、`evidence/` 均为独立实现或脱敏数据。

## 3. 学术引用

- 论文与预印本：只引用公开可访问的 arXiv / ACL / OpenReview / 会议页面，完整条目见 **历史归档** `archive/legacy-2026-11-13/调研报告.md` 第 8 章（111 条，含可信度标记；引用需注明日期）。
- 不可达来源（Science、ACM DL 等）：只作定性引用，**不引具体数值**。
- 社区 Wiki 与站点：只用于核对游戏事实，**不作为学术引文撑论点**。

## 4. 本仓库自有内容

| 内容 | 许可建议 | 说明 |
|---|---|---|
| `bench/` 代码 | 待定（建议 MIT 或 Apache-2.0） | 独立实现，不含第三方代码 |
| `scenarios/v3/` | 跟随仓库许可 | 📋 由真游戏捕获 + 反事实回放生成（W3）；只含脱敏状态/动作/分数，不含 `.jkr` 存档或游戏素材 |
| 报告与图表 | 跟随仓库许可 | 图表由脚本生成 |

## 5. 合规红线（与 plan 底线 L7–L9 对应）

1. 不把 Wiki 的描述文本贴进代码或报告（只取数值，改写表述）。
2. 不复制 GPL 项目的实现；引用其设计时在报告注明来源。
3. 不引入 `balatro-rs` 的任何代码或产物（无许可证 = 默认保留所有权利）。
4. 任何新增数据源，先在本表登记"来源 / 许可 / 用法"，再落地。
5. **【L8】游戏文件 / mod / `.jkr` 存档 / 含游戏素材的截图不入库**：仓库只保留脱敏后的状态 JSON、分数、trace、版本清单；截图仅放 `evidence/` 且不对外分发。
6. **【L9】不得把"真游戏捕获回放"写成"真游戏终验"**，也不得把"单步分数一致"写成"完整规则一致"。
7. 真游戏适配层（`coder/balatrobot`，MIT）只做 JSON-RPC 调用、字段映射、动作 id↔下标转换、统一错误码；**不写规则、不做分数复算**。

## 5.1 "游戏文件 / 存档 / 截图不入库"明细

| 对象 | 许可 / 性质 | 处理方式 |
|---|---|---|
| Balatro 游戏本体与素材（贴图/音频/字体） | 商业软件 | 只在本机运行；**不提交、不再分发** |
| Lovely（`lovely-injector`）/ Steamodded（`smods`）本体 | MIT / GPL-3.0 | 只记录版本号；**不复制文件、不提交**（GPL 代码禁止并入本仓库） |
| `.jkr` 存档（`save`/`load` 产物） | 游戏生成物，含游戏素材 | 只记录**脱敏路径占位**（如 `data/realgame/saves/<capture_id>-stepNN.jkr`）；文件本身不入库 |
| 截图（`screenshot`） | 含游戏素材 | 只在 `evidence/` 内部留证，不对外分发、不提交到公开仓库 |
| 脱敏状态 JSON / 分数 / trace / 版本清单 | 本项目生成 | ✅ 允许入库（`evidence/W3/align/*.json`、`scenarios/v3/*.jsonl`） |
| `scenarios/v3/MANIFEST.json` | 本项目生成 | ✅ 允许入库（只含版本号/构建号/牌组/赌注等元数据） |


## 6. W2 v2.1 实际实现与核验记录

本节记录 W2 实现阶段实际参考、核验与尚待验证的来源。
状态仅反映当前工程证据，不代表真实 Balatro 对拍已经通过。

| 来源 | 本阶段用途 | 实际使用情况 | 许可与复用边界 | 状态 |
|---|---|---|---|---|
| SMODS Calculate Functions / `docs.smods.dev` | 理解 context、cardarea 和 scoring phase | 用于理解效果分派架构；项目自身的效果元数据另见 `docs/joker-semantics.md` | 仅作架构参考，不复制源代码或文档文本 | 已审阅；`before` 阶段语义的适用边界见 Joker 语义文档 |
| `DivvyCr/Balatro-Simulation` | 参考纯函数计分分派结构 | 借鉴设计思路，没有复制实现 | 原有许可审查见本文件第 2 节；不复制其实现 | README 已审阅 |
| Balatro HQ Poker Hands | 核对原版牌型基础 Chips / Mult | 用于识别原版计分与本项目自定义公式之间的差异 | 仅使用事实，不复制描述文本 | 已用于差异分析；不代表真实游戏对拍通过 |
| Game Design Lab / Balatro Wiki mirror | 交叉核对计分流程与阶段概念 | 作为规则事实参考 | 不复制文本或代码 | 参考记录：<https://teemo.dev/game-design/balatro/systems/scoring-engine-chips-mult/> |
| `EFHIII/balatro-calculator` | 第三方算分抽检 | 尚未取得实际抽检结果 | 不复制代码；网页仅作校验候选 | 5 例抽检待完成，见 `docs/engine-fidelity.md` |
| `evanofslack/balatro-rs` | 离线引擎实现调研 | 当前实现未复制其代码 | 未确认可复用许可，不复制代码或产物 | 仅作研究参考 |
| `coder/balatrobot` | 未来动作与状态校验接口参考 | 本阶段未安装或调用，不执行真实游戏脚本控制 | 仅参考工具契约与命名，**W2 未接入；v3.0 规划接入（MIT）**，只做终验/捕获 | 📋 不在当前实现范围内（W3/W5） |

### 6.1 当前实现的保真度声明

- `bench/jokers.py` 中的 8 个 Joker 是合成测试 fixture，不应描述为原版 Joker 的精确映射。
- 当前计分实现遵循项目规定的自定义公式，不等同于原版 Balatro 完整计分流程。
- `docs/engine-fidelity.md` 已升级为**对齐台账 v3.0**：A 表（真游戏捕获）与 B 表（save/load 反事实回放）为主门槛，旧 20 例人工对拍与 5 例第三方抽检降级为辅助证据（附录 C/D）。
- 在 A0–A4 未签核、A/B 表未实测之前，不得将真实游戏单步分数保真度标记为已通过，也不得修改 `scenarios/RULES_VERSION` 的 `alignment_level` / `fidelity_status`。

## 7. v3.0 真游戏运行栈（📋 未安装、未接入）

> 以下四层是**本机运行时依赖**，不是仓库依赖，不进入 `pyproject.toml`。版本以安装当日 release 为准，写入 `scenarios/v3/MANIFEST.json`（A0）。

| 层 | 作用 | 许可 | 本项目用法 | 状态 |
|---|---|---|---|---|
| Balatro（Steam 正版，基线 `1.0.1o`） | 真游戏本体 | 商业软件 | 只在本机运行；游戏文件/素材不入库 | 📋 未安装 |
| Lovely（`lovely-injector`） | Lua 运行时注入 | **MIT** | 运行前置；只记录版本，不分发 | 📋 未安装 |
| Steamodded（`smods`） | mod 框架 | **GPL-3.0** | **仅作运行时依赖**；不复制/不分发其代码 | 📋 未安装 |
| `coder/balatrobot` | JSON-RPC 2.0 控制面（`127.0.0.1:12346`） | **MIT** | 终验/捕获的唯一适配层；不修改源码、不并入本仓库 | 📋 未安装 |

**关键边界**：

- 真游戏只做**捕获（A2/A4）+ 12 局小样本终验（L3）**，不做批量主环境；不可用即降级为 `CAPTURE_REPLAY_ONLY`，不得声称终验通过。
- `add`/`set` 调试钩子只用于环境自检，**不用于构造训练集主数据**。
- 单种子只保证真游戏内可复现；**不承诺与自建引擎同局面**（D13：captured-state alignment）。

## 8. 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v2.1 | 2026-11-12 | 初始清单；规则数值 + 设计借鉴 + 学术引用 + 自有内容 + 红线 L7 |
| v2.2 | 2026-11-13 | 追加 §6 W2 实际实现与核验记录；明确 8 夹具非原版 |
| **v3.0** | **2026-11-13** | 新增真游戏运行栈（balatrobot/Lovely/Steamodded）、vanilla 牌型基础 Chips×Mult / 盲注目标 / 8 具名 Joker 数值来源；"不接入真游戏"改为"W2 未接入，v3.0 规划接入只做终验/捕获"；新增 L8/L9 与"游戏文件/存档/截图不入库"；§6 旧表保留为历史 |

