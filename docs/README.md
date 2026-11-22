# docs 索引

> 文档分 4 类 + 1 个历史区。**新增文档必须归入下表目录并在本表登记**；过期文档移到 `archive/legacy-<日期>/` 并更新其 INDEX，不要直接删。

| 目录 | 装什么 | 从哪读起 |
|---|---|---|
| [**quality/**](quality/) | **凭什么相信这个环境**：对齐台账（能不能说已对齐）、来源与许可（数字从哪来、能不能用）、Joker 口径（怎么实现的、哪条未验证） | [engine-fidelity.md](quality/engine-fidelity.md) |
| [**implementation/**](implementation/) | **现在怎么实现的**：架构、规则、API、数据 Schema、执行、测试、性能、状态矩阵 | [README.md](implementation/README.md) |
| [**balatro/**](balatro/) | **原版事实调研**：规则、内容、设计分析、引擎差距映射（只取事实，不是对齐证据） | [README.md](balatro/README.md) |
| [**ops/**](ops/) | **环境与运维**：Windows/DSH/真游戏环境的坑与解法 | [windows-pitfalls.md](ops/windows-pitfalls.md) |
| [**research/**](research/) | 学术与生态调研（背景调研材料，**历史证据不改写**） | [README.md](research/README.md) |

## 三个约定

1. **状态口径统一**：`IMPLEMENTED`（有代码）/ `TESTED`（有测试）/ `VERIFIED`（与真游戏实测一致，需 A0–A4 签核）。未验证的不得写成已验证。
2. **单一事实来源**：规则范围看 `scenarios/RULES_VERSION`，对齐结论看 [quality/engine-fidelity.md](quality/engine-fidelity.md)，计划看 `plan/`。
3. **归档**：历史材料进 `archive/legacy-<日期>/`，只读、不改写。
