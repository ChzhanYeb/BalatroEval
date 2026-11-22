# 历史归档索引（legacy-2026-11-22）

> **性质**：**2026-11-22 归档**。以下文件描述的是 **W2/L0 时期**的自定义规则集（提交 `c65fb9b`：自定义计分公式、合成 Joker、3 个 Joker 槽位、盲注目标 300/800/2000、4 手/2 弃、25 项测试）。该规则集**已被 2026-11-17 的 vanilla 1.0.1o 严格子集 v1 取代**（Red Deck / White Stake / Ante 1，300/450/600，4 手/4 弃，5 槽，8 个具名 Joker，等级 1 基础 Chips×Mult + 计分牌筛选），实现说明见 [docs/implementation/](../../docs/implementation/README.md)。
> **引用规则**：引用本目录文件时必须注明 **“历史归档（2026-11-22，W2/L0 口径）”**；**不得**把其中的规则常量、测试数量、验收结论当作当前规则或当前验收依据。
> **归档方式**：2026-11-22 用 `Move-Item -LiteralPath` 移入本目录，文件内容未改写；git 历史提交信息不改写。文件内部若有相对链接（例如指向 `engine-fidelity.md` 的链接），是按原路径写的，现在需以原路径（`docs/`）为准解析；本索引不修正归档件内部链接。
> **历史快照（归档时状态）**：`rules_version = vanilla_1.0.1o_subset_v1`，规则 **IMPLEMENTED + TESTED**（124 项测试通过）；与真游戏的对齐（A2/A3）**实测 0 行**，`fidelity_status: NOT_VERIFIED`、`alignment_level: L0`。当前状态已升级为 **v2（计分 + 经济，157 测试）**，以仓库根 README/AGENTS 为准。

## 1. 归档清单

| 文件名 | 原路径 | 归档理由 | 替代文档 |
|---|---|---|---|
| `程序员手册.md` | `程序员手册.md`（仓库根） | W2 v2.1 的完整手册（`c65fb9b` 口径）：§6 自定义计分公式与 `HAND_MULT` 表、§7 合成 Joker 夹具、§8 3 槽位 / 4 手 2 弃 / 300-800-2000、§11 schema 1 日志、§15.5 粗糙点清单；其“当前实现”与验收章节已整体失效 | [docs/implementation/architecture.md](../../docs/implementation/architecture.md)、[rules-implementation.md](../../docs/implementation/rules-implementation.md)、[api-reference.md](../../docs/implementation/api-reference.md) |
| `W2-implementation-report.md` | `docs/W2-implementation-report.md` | W2 交付报告：25/25 单测、`bench/` 11 模块、O1/O2/O3、13 步 demo、218 动作等**W2 时点**数字；规则身份为“自定义子集公式 + 合成 Joker” | [docs/implementation/implementation-status.md](../../docs/implementation/implementation-status.md)、[testing-and-validation.md](../../docs/implementation/testing-and-validation.md)、[README.md](../../README.md) |
| `data-sources-w2.md` | `docs/data-sources-w2.md` | W2 时点的数据来源与复用决策表（“W2 实际如何使用”），含“8 个 Joker 是合成测试夹具”“vanilla 数值是 W3 目标、当前未实现”等已被取代的判断 | [docs/data-sources.md](../../docs/data-sources.md)（当前唯一来源清单）、[docs/implementation/rules-implementation.md](../../docs/implementation/rules-implementation.md) |

## 2. 当前文档入口（先读这些，不要读本目录）

| 入口 | 作用 |
|---|---|
| [README.md](../../README.md) | 项目定位、能力边界、当前实现与差距表 |
| [AGENTS.md](../../AGENTS.md) | 仓库契约速览（规则常量、计分层级、验收命令、红线） |
| [docs/implementation/README.md](../../docs/implementation/README.md) | 实现文档总入口：architecture / rules-implementation / api-reference / data-schema / evaluation-execution / testing-and-validation / performance / implementation-status |
| [scenarios/RULES_VERSION](../../scenarios/RULES_VERSION) | 规则版本与覆盖范围的**人类可读声明**（机器可读权威为 `bench/rules_version.py::VANILLA_SUBSET_V1`） |

规则事实调研（非实现文档）：[docs/balatro/](../../docs/balatro/README.md)；方法论知识库（`docs/agent-evaluation-methodology/`）已于 2026-11-22 移出本项目，不再随仓库分发。

## 3. 不归档的材料（按证据/台账规则保留原位）

| 材料 | 位置 | 为什么不归档 |
|---|---|---|
| 对齐台账 | [docs/engine-fidelity.md](../../docs/engine-fidelity.md) | 仍是**当前**的对齐台账：A/B 表、PENDING 状态、A0–A4 与签核模板都在使用中，只是“当前引擎”一句已更新为 vanilla 子集 v1 口径 |
| 原始证据 | `data/`、`evidence/`、`runs/` | 历史证据与实验产物，只读保留，**不移动、不重命名、不删除**（L5/L8） |
| 规则调研 | `docs/balatro/` | 规则事实与来源登记，仍是当前引用来源（`fidelity_status` 仍为 `NOT_VERIFIED`） |
| 测试 | `tests/` | 代码契约的一部分（当前 124 项），不归档 |

## 4. 关联归档

- [archive/legacy-2026-11-13/INDEX.md](../legacy-2026-11-13/INDEX.md)：旧名 BalatroBench 时期的调研报告与跨文档核查记录。
