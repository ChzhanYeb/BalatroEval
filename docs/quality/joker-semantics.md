# Joker 语义台账（8 个具名 vanilla Joker）

> **结论**：`bench/jokers.py` 的 8 个具名 Joker 已实现 + 单测覆盖；**触发语义未与真游戏实测**（A2/A3 0 行，`NOT_VERIFIED`）。合成夹具（`jc_*`/`jm_*`/`jx_*`）已移出生产目录，只作历史测试参考。
> 关联：`bench/jokers.py`（实现）· [engine-fidelity.md](engine-fidelity.md)（对齐台账）· `scenarios/RULES_VERSION`（`unverified` 段）

## 1. 目录边界

| 目录 | 身份 | 状态 | 允许用途 | 禁止用途 |
|---|---|---|---|---|
| vanilla 目录（§2） | 具名原版 Joker | ✅ 已实现（未与真游戏验证） | 单测、程序化评测、训练/开发集 | 声称“已对齐/已验证” |
| 合成夹具（历史） | 工程测试构造，**不是原版 Joker** | ⚠️ 已移出生产目录 | 历史回归、夹具构造参考 | 训练集、主表、任何“原版 Joker”表述 |

> **替换铁律**：只有在 (a) 数值与条件有来源链接、(b) 有金样测试或真游戏实测、(c) 已写入 engine-fidelity 的 A 表之后，才可把某个 Joker 标为**已验证**（当前 0 个）。

## 2. 8 个 Joker（数值来自 Wiki 事实页，描述自写）

| # | Joker | 效果 | 触发条件（vanilla 事实，边界待实测） | 类型 |
|---:|---|---|---|---|
| 1 | Joker | +4 Mult | 无条件 | add_mult |
| 2 | Jolly Joker | +8 Mult | 打出的牌含对子（或含对子的更大牌型） | add_mult |
| 3 | Zany Joker | +12 Mult | 打出的牌含三条 | add_mult |
| 4 | Sly Joker | +50 Chips | 打出的牌含对子（同 #2 边界问题） | add_chips |
| 5 | Wily Joker | +100 Chips | 打出的牌含三条 | add_chips |
| 6 | Half Joker | +20 Mult | 打出的牌 ≤3 张 | add_mult |
| 7 | The Duo | ×2 Mult | 打出的牌含对子 | mul_mult |
| 8 | The Trio | ×3 Mult | 打出的牌含三条 | mul_mult |

## 3. 实现口径

- **字段**：`jid`（稳定 id，如 `jolly_joker`）/ `kind`（add_chips / add_mult / mul_mult）/ `value`（mul_mult 用百分之一：200=×2）/ `condition`（always / contains_pair / contains_three / cards_le_3）/ `area` `phase`（本实现自带标签，**不等价** SMODS 上下文）。
- **顺序敏感**：多个 Joker 按槽位从左到右应用；`+4M → ×2` 与 `×2 → +4M` 结果不同（引擎示例 126 vs 98，7♥7♦）。
- **contains 口径**：`structural_superset_v1`——按打出的全部牌结构判定；**4K/5K 是否含 Pair/Three 仍 `UNVERIFIED`**（影响 Jolly/Sly/The Duo/Zany/Wily/The Trio 的触发范围）。
- **算术**：`Fraction` 精确计算，只在末尾 `floor` 一次（候选口径，见 `Ruleset.unverified`）。

## 4. 待真游戏实测的 4 项（📋）

1. **槽位顺序**：多 Joker 同时命中时是否严格从左到右；`+Mult` 与 `×Mult` 是否按槽位混排而非分组。
2. **条件求值时机**：条件在出牌时判定还是计分中判定；是否受计分牌筛选影响。
3. **与牌型基础分的先后**：基础 Chips×Mult 先结算、再逐个 Joker。
4. **取整时机**：中间结果是否取整（vanilla 通常末尾一次，需实测）。

**最小实测集建议**：单 Joker 无歧义对照 → 条件命中/不命中 → `+4M`+`×2` 换序 → 张数阈值（3 张 vs 4 张）→ 加 Chips 与加 Mult 的结算次序。

## 5. 来源与许可

| 来源 | 许可 | 用法 | 边界 |
|---|---|---|---|
| balatrowiki 8 个 Joker 页 | CC BY-NC-SA 3.0 | 只取名称/数值/条件 | 不搬文本、不复制表格、不贴图 |
| `docs.smods.dev`（Calculate Functions） | GPL-3.0（文档） | 理解 context/cardarea 概念 | 不复制文档文本、不引入 GPL 代码 |
| `DivvyCr/Balatro-Simulation` | GPL-3.0 | 借鉴 effect 分派设计 | 不复制代码 |
| 真游戏捕获（balatrobot） | 商业软件 | 后续实测触发顺序与数值 | 游戏文件/存档/截图不入库（L8） |

## 6. 历史

- W2 v2.1 的合成夹具与英文旧版见提交 `c65fb9b` 与 `archive/legacy-2026-11-22/`；生产目录已只用 §2 的具名目录。
