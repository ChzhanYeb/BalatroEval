# 数据来源与许可清单

> **原则**：数值可引、文本自写；设计可借鉴、代码不复制。任何进入规则子集的数值都必须能追溯到来源，任何进入仓库的内容都必须许可清晰（决策 D14、底线 L7–L9）。
> **当前状态**：规则数值已落地为 **vanilla 1.0.1o 子集 v2（计分 + 经济）**，与真游戏一致性 **未验证**（A2/A3 0 行，L0）；真游戏运行栈 📋 未安装。
> 关联：[engine-fidelity.md](engine-fidelity.md)（对齐台账）· [joker-semantics.md](joker-semantics.md)（Joker 口径）

## 1. 规则数值（只取不可版权的事实）

| 数据 | 来源 | 许可 | 状态 |
|---|---|---|---|
| 牌型基础 Chips×Mult（等级 1）：HC 5×1 / P 10×2 / 2P 20×2 / 3K 30×3 / ST 30×4 / FL 35×4 / FH 40×4 / 4K 60×7 / SF 100×8 | balatrowiki（Poker hands） | CC BY-NC-SA 3.0 | ✅ 已实现；📋 未验证 |
| 计分牌筛选：高牌 1 / 对子 2 / 两对 4 / 三条 3 / 顺子·同花·葫芦·同花顺 5 / 四条 4 | balatrowiki + 真游戏实测 | CC BY-NC-SA / 实测 | ✅ 已实现；📋 未验证 |
| Ante 1 盲注目标：Small 300 / Big 450 / Boss 600（旧口径 300/800/2000 = Ante 1/2/3 基础分，已废弃） | balatrowiki（Blinds & Antes） | CC BY-NC-SA 3.0 | ✅ 已实现；📋 未验证 |
| 牌组与赌注：Red Deck（+1 弃）/ White Stake / 8 张手牌 / 4 手 / 5 Joker 槽 | balatrowiki + `start` 实测 | CC BY-NC-SA / 实测 | ✅ 已实现；📋 未验证 |
| 8 个具名 Joker 的数值与条件（Joker +4M / Jolly +8M / Zany +12M / Sly +50C / Wily +100C / Half +20M / The Duo ×2M / The Trio ×3M） | balatrowiki 各 Joker 页 | CC BY-NC-SA 3.0 | ✅ 已实现；📋 触发语义未实测 |
| **经济数值**：起始 $4、盲注奖励 3/4/5、每手/每弃牌 $1、利息每 $5 得 $1（cap $5）、Joker 价格区间 | balatrowiki（Money / The Shop） | CC BY-NC-SA 3.0 | ✅ 已实现；📋 未验证 |
| 升级曲线（手牌等级 >1）、稀有度权重、浮动价、reroll 曲线 | balatrowiki 等 | CC BY-NC-SA 3.0 | 📋 仍在 `excluded` / 未实现 |
| 种子机制（种子决定全部随机要素） | balatrowiki（Seed 条目） | CC BY-NC-SA 3.0 | ✅ 仅事实说明，不声称复刻 |

> 本项目刻意简化的两点：**价格取稀有度中值**（Common $5 / Rare $9）、**商店候选均匀抽样**；均记 `Ruleset.unverified`，不是“原版经济”。

## 2. 只借鉴设计、不复制代码

| 项目 | 许可 | 借鉴什么 | 不做什么 |
|---|---|---|---|
| `evanofslack/balatro-rs` | **未声明许可** | 穷举动作生成、action mask、逐字节 RNG 思路 | 不复制代码/产物，不引入依赖 |
| `DivvyCr/Balatro-Simulation` | GPL-3.0 | `cardarea × phase` 效果分派、三态随机 | 不复制实现（避免 GPL 传染） |
| `alesha-pro/evalatro` | ISC 声明（仓库无 LICENSE） | 重算校验、code hash、工具注册表单一事实源 | 不复用代码 |
| `coder/balatrobot` | **MIT** | 工具契约、GameState 分层、JSON-RPC 2.0 方法集 | v3.0 接入（📋），只做终验/捕获适配层，不改源码 |
| `lovely-injector` | **MIT** | 运行前置（Lua 注入） | 只记版本，不分发 |
| `Steamodded/smods` + `docs.smods.dev` | **GPL-3.0** | 阶段/区域/回调顺序的语义描述 | 仅本机运行时依赖；不复制/不分发/不并入仓库 |
| `EFHIII/balatro-calculator` | MIT | 第三方抽检（辅助 5 例） | 不作依赖、不集成 |
| `balatrowiki.org` | CC BY-NC-SA 3.0 | 只取数值/名称等事实 | 不搬运文本/表格/图片，描述自写 |

## 3. 学术引用与自有内容

- 论文/预印本只引公开页面（arXiv / ACL / OpenReview / 会议）；111 条完整清单在历史归档 `archive/legacy-2026-11-13/调研报告.md` 第 8 章。不可达来源只作定性引用，不引具体数值。
- `bench/` 为独立实现（许可待定，建议 MIT/Apache-2.0）；`scenarios/v3/`、报告与图表跟随仓库许可；调研文档为自写中文。

## 4. 合规红线（L7–L9）

1. 不把 Wiki 描述文本贴进代码或报告（只取数值，改写表述）。
2. 不复制 GPL 项目实现；引用设计时注明来源。
3. 不引入 `balatro-rs` 的任何代码或产物（无许可证 = 默认保留所有权利）。
4. 新增数据源先在本表登记“来源 / 许可 / 用法”，再落地。
5. **【L8】游戏文件 / mod / `.jkr` 存档 / 含素材截图不入库**：只保留脱敏状态 JSON、分数、trace、版本清单；截图仅放 `evidence/` 且不对外分发。
6. **【L9】不把“捕获回放”写成“真游戏终验”**，不把“单步分数一致”写成“完整规则一致”。
7. 真游戏适配层只做 JSON-RPC、字段映射、动作 id↔下标转换、统一错误码；**不写规则、不复算分数**。

### 4.1 “不入库”明细（L8）

| 对象 | 性质 | 处理 |
|---|---|---|
| Balatro 本体与素材（贴图/音频/字体） | 商业软件 | 只本机运行，不提交、不再分发 |
| Lovely / Steamodded 本体 | MIT / GPL-3.0 | 只记版本号，不复制文件 |
| `.jkr` 存档（`save`/`load` 产物） | 含游戏素材 | 只记脱敏路径占位，文件不入库 |
| 截图 | 含游戏素材 | 只在 `evidence/` 留证，不对外分发 |
| 脱敏状态 JSON / 分数 / trace / 版本清单 | 本项目生成 | ✅ 允许入库 |
| `scenarios/v3/MANIFEST.json` | 本项目生成 | ✅ 允许入库（只含版本/构建/牌组/赌注元数据） |

## 5. 真游戏运行栈（📋 未安装；只作终验/捕获，不做批量主环境）

| 层 | 作用 | 许可 | 本项目用法 |
|---|---|---|---|
| Balatro（Steam 正版，基线 `1.0.1o`） | 真游戏本体 | 商业软件 | 只本机运行，文件/素材不入库 |
| Lovely（`lovely-injector`） | Lua 运行时注入 | MIT | 运行前置，只记版本 |
| Steamodded（`smods`） | mod 框架 | GPL-3.0 | 仅运行时依赖，不复制/不分发 |
| `coder/balatrobot` | JSON-RPC 2.0（`127.0.0.1:12346`） | MIT | 唯一适配层，不改源码 |

边界：真游戏只做**捕获（A2/A4）+ 12 局小样本终验（L3）**；不可达即降级 `CAPTURE_REPLAY_ONLY`，不得声称终验通过。单种子只保证真游戏内可复现，**不承诺与自建引擎同局面**。

## 6. 历史与变更

- W2 v2.1 的核验记录（含 7 行来源表）与 `data-sources-w2.md` 已归档到 `archive/legacy-2026-11-22/`。
- `docs/balatro/` 五份调研的逐页来源在各文档文末清单登记；未取得来源（`Hand_levels`/`Daily_Run` 404、取整方式、逐级增量表）保持 ⏳，未写成 ✅。
- 版本变更见 git 历史；本文件不再维护逐版 changelog。
