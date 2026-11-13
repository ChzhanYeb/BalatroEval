# AGENTS.md — BalatroEval 仓库契约速览（`bench/` = L0 训练环境底座）

> **项目正式名**：**BalatroEval**（无副标题）。**定位**：面向大模型 Agent 的**长线规划测试集**——用可判定、可复现的 Balatro 规则子集评测跨回合资源分配、多步决策、长期构建与失败恢复；失败归因仅作**诊断报告层**，不是主定位。
> **当前能力边界**：长线规划四支柱（跨回合资源分配 / 长期构建 / 失败恢复 / 长线指标）**均未覆盖**，见 [README](README.md) 的「定位与当前实现差距」；不得声称已覆盖。
> 给 Agent（以及赶时间的人类）的最小上下文。**展开版见 [程序员手册.md](程序员手册.md)**，冲突时以手册为准；v3.0 决策冲突时以 [plan/详细版/07-真实游戏接入与终验.md](plan/详细版/07-真实游戏接入与终验.md) 为准。
> 阅读顺序：[README.md](README.md)（入口）→ 本文件（契约速览）→ [程序员手册.md](程序员手册.md)（完整手册，v3.0 对齐/终验见 §21）。
> 代码基线：`c65fb9b`（W2-v2.1-2026-11-12），对齐等级 **L0（未对齐）**。仓库根：`C:\WorkData\005.Agent\dsh-agent-eval`（目录名 ≠ 项目名）。
> 历史说明：项目曾用名 **BalatroBench**；旧文档已归档到 [archive/legacy-2026-11-13/INDEX.md](archive/legacy-2026-11-13/INDEX.md)，git 历史提交信息不改写。
> 本文件与手册同时约定：以下内容描述的是**行为契约**，改代码前先读对应章节。

---

## 1. 这是什么

`bench/` 是一个**可重复、可测试的 Balatro 风格子集模拟引擎**（Python，stdlib-only），附带：

- 数据模型（牌 / Joker / 对局状态）
- 自定义子集计分（牌型识别 + 筹码/倍率）
- 状态推进（出牌 / 弃牌 / 商店三选一 / 三盲注）
- 参照策略 O1（精确 argmax）、O2（弃牌 EV 采样）、O3（贪心整局）
- append-only JSONL 轨迹日志
- CLI：`python -m bench {demo,verify,ev}`

**v3.0 定位**：`bench/` 不再是“唯一评测环境”，而是两阶段架构的**第一阶段——L0 训练环境底座**（快、可枚举、可 CI）。真实游戏（Balatro + balatrobot）侧只做 12 局小样本终验（计划 W5，目标 L3），**尚未接入**（📋）。`bridge/realgame.py`、`scenarios/v3/`、`runs/w5-real/` 均**未创建**。

**v4.0 定位**：BalatroEval 是面向大模型 Agent 的**长线规划测试集**；失败归因只作诊断报告层（F1–F3 合规/规则理解、F4 规划、F0 证据不足、E1 数据质量门禁，非 Agent 失败类）。**当前长线四支柱均未覆盖**，不得把 L0 引擎能力写成“长线规划已评测”。

## 2. 这不是什么（红线，任何输出都不得越过）

| ❌ 不得声称 | 事实 |
|---|---|
| 实现了原版 Balatro 计分 | 自定义子集公式；`scenarios/RULES_VERSION` 为 `fidelity_status: NOT_VERIFIED` |
| 8 个 Joker 是原版 Joker | `jc_*/jm_*/jx_*` 是**合成测试夹具** |
| 固定 seed 复现了原版 RNG | 只保证本项目内可复现 |
| 25 测试通过 = 原版兼容 / 已对齐 | 测试只覆盖已实现行为，只证 **L0 自洽** |
| verify 通过 = 计分公式正确 / 已对齐 | 两条路径**共用** `score_hand()` |
| demo 输了 = 引擎有 bug | 贪心策略 + seed + 子集规则下的一次对局结果 |
| 已接入 balatrobot / 已对齐 / 已终验 | 真游戏接入、`scenarios/v3/`、12 局终验**均未执行（📋）** |
| 训练集结果 = 真游戏结果 | 两套环境；环境分歧记 **E1 `env_divergence`**（非 Agent 失败），必须单列 |
| 捕获回放 = 真游戏终验 | 捕获回放只做 A2/A4 分数/回放验证；终验是 Agent 在真游戏跑完 12 局 |
| 真游戏 12 局小样本 = 统计显著 | 只做描述统计 + 95% CI，不做显著性主张 |
| 游戏文件 / mod / `.jkr` 存档 / 含游戏素材截图可以入库 | L8：只提交脱敏状态 JSON、分数、trace、版本清单 |
| **已覆盖跨回合资源分配 / 长期构建 / 失败恢复 / 长线指标** | **四项均未覆盖**（见 README 差距表）；只能写“目标能力，尚未覆盖，登记 W3 机制改造候选” |

## 3. 依赖分层（只允许上层 import 下层）

| 层 | 模块 | 允许 import 的兄弟模块 |
|---:|---|---|
| L0 | `model.py` | 无 |
| L1 | `cards.py` / `rng.py` / `logging.py` | `model` |
| L2 | `scoring.py` / `jokers.py` | `model` |
| L3 | `actions.py` | `model` |
| L4 | `engine.py` | `actions, cards, jokers, logging, model, rng, scoring` |
| L5 | `oracle.py` | `actions, engine, model, scoring` |
| L6 | `__main__.py` | `actions, engine, model, oracle, scoring` |

【硬约束】只能向下依赖；`engine` **不得** import `oracle`；`model` 不 import 兄弟模块。

## 4. 不可不知的契约

**计分**（`scoring.score_hand`）：

```
chips = Σ 点数筹码(A=11, J/Q/K=10, 其余=点数)          # 没有牌型基础 Chips
mult  = HAND_MULT[牌型]                                # 自定义表：SF12/4K10/FH8/FL6/ST5/3K4/2P3/P2/HC1
按【槽位顺序】逐个应用 Joker：add_chips +v；add_mult +v；mul_mult ×(v/100)
final = floor(chips × mult)                            # Fraction 精确运算，只 floor 一次
```

- 顺序敏感：`+4Mult → x1.5` = 126，`x1.5 → +4Mult` = 98（基于 7♥7♦）。
- 新增效果 kind 必须**两处登记**：`PHASE_BY_KIND` + `EFFECT_DISPATCH`；`G.jokers/before/individual` 只是自定义标签，不等于 SMODS 语义。

**流程**（`engine`）：

- 常量：52 张牌、初始 8 张、每盲注 4 出牌 / 2 弃牌、3 盲注、目标 300/800/2000、最多 3 个 Joker。
- 阶段：`play` →（达标）`shop` →（选 Joker 换盲注）`play` → … → `done`（`win`/`loss`）。
- 每次转移：`deepcopy` 状态 → 改副本 → `steps+1` → 写日志；**从不修改入参**。
- 换盲注六件事：加 Joker、`blind_idx+1`、换 `target`、`total_score=0`、资源重置 4/2、清 shop/outcome。
- 顺序不变式：只有牌堆空才洗弃牌堆（洗牌消耗 RNG 并写回 `rng_state`）；出牌在**补牌之后**才进弃牌堆。
- 守恒：`len(hand)+len(deck)+len(discard_pile) == 52`。

**动作**：8 张手牌 ⇒ 恒 218 个合法动作（`C(8,1..5)`）。`card_ids` 是稳定身份（如 `c7h`），`label`（`7h`）仅供展示；`card_ids` **不排序**。

**日志**：JSONL，`schema_version: 1`，字段 `state_before/action/score_delta/score_details/state_after`；只追加；`deck` 与 `discard_pile` 只有计数。

**v3.0 对齐契约（规划，尚未执行；详见 [07](plan/详细版/07-真实游戏接入与终验.md) §3 与手册 §21）**：

- **A0–A4**：A0 版本锁定（`game_version`/`build_id`/`deck`/`stake`/依赖版本写入 `scenarios/v3/MANIFEST.json`）；A1 状态/动作 schema 映射（`gamestate`↔`GameState`，动作绑定稳定卡牌 id + 下标快照）；A2 单步分数一致（`engine_score == real_score`）；A3 规则子集（已实现的与 vanilla 1.0.1o 一致，未实现的在 `RULES_VERSION.excluded` 明列）；A4 场景来源与回放（`origin: real_capture | real_counterfactual` + `capture_id` + 验证证据）。
- **L0–L3 对齐等级**：L0 未对齐（当前 W2）/ L1 分数对齐 / L2 规则子集对齐（W3 目标）/ L3 真游戏终验通过（W5 目标）。
- **诊断报告层（v4.0）**：F1–F3 属合规/规则理解诊断，F4 属规划诊断（heuristic），F0 为证据不足；**E1 `env_divergence` 是数据质量门禁，不是 Agent 失败类**，单独统计、不进 Agent 失败率。失败归因是诊断层，不是项目主定位或第一创新点。
- **红线**：当前是 **L0**；W2 的 25 测试/`verify`/`demo` 只证自洽，不能写成 A2/A3 对齐证据，更不能写成 L3 终验证据。

## 5. 验收命令（改完必跑，输出要贴原始结果）

```powershell
Set-Location C:\WorkData\005.Agent\dsh-agent-eval

python -m unittest discover -s tests -v        # 必须：Ran 25 tests / OK
python -m bench verify --samples 10 --seed 20261112   # 必须：passed true, 每例 218 候选
python -m bench demo --seed 20261112 --max-steps 50 --log $env:TEMP\agent-demo.jsonl
# 预期：phase=done, outcome=loss, steps=13, blind_idx=2, total_score_in_current_blind=1430
python -m compileall -q bench                  # 无输出即通过
```

只加注释/文档时，另需证明零行为变更：与 `git show HEAD:<file>` 的 AST（剥掉 docstring）比对一致。

> **范围**：以上命令只覆盖 **L0 训练环境**（既定事实）。它们**不能**替代 A2/A3 对齐验证，也不能替代真游戏终验；对齐命令（`scenarios/v3/`、`bench/align.py`）与终验命令（`bridge/realgame.py`、12 局）📋 尚未提供。

## 6. Agent 硬约束

1. **不许改行为**：注释任务只动 docstring/`#`；不得改表达式、常量、导入、签名、异常消息。
2. **不许伪造验证**：没跑过的命令不许写"通过"。
3. **不许越界**：只改指定文件；不碰 `data/`、`bridge/`、`plan/`；禁止 `git add .` / `commit -a` / `reset --hard` / `clean`。
4. **不许降低保真度表述**：不得把"未验证"写成"已验证"。
5. **库调用传 `log_path=None`**：否则默认写 `data/episode.jsonl`（append，会污染证据）。
6. **发现疑似 bug 不修**：用「注意：」标注并上报，修复需单独任务 + 测试。
7. **真游戏适配器不写规则**：`bridge/realgame.py`（📋 规划）与 `bench/realgame.py`/`convert.py`（📋 规划）只做 JSON-RPC 调用、字段映射、动作 id↔下标转换、统一错误码；规则只有 `bench/` 一份实现，不得在适配器里复算分数或模拟规则。真游戏相关文件（游戏本体、mod、`.jkr` 存档、含素材截图）**不入库**（L8）。

## 7. 已知粗糙点（不要"顺手修"，要单独提交）

完整 15 条见手册 §15.5，以下是高频几项：

- `oracle.greedy_episode` 未暴露 `log_path`，内部 `play()`/`choose_joker()` 用默认值 ⇒ 调 O3 会写 `data/episode.jsonl`；O3 **无 CLI 入口**。
- `greedy_episode` 里有未使用的局部变量 `before_score`。
- `__main__.verify_oracle` 覆盖 `state.hand` 却保留 `new_game` 的 `deck` ⇒ 该状态可能含重复物理牌（只对单步计分校验无影响）。
- 未使用导入：`cards.combinations`、`__main__` 的 `legal_plays/Path/discard/greedy_episode`；无调用方：`model.SUIT_NAMES`、`cards.combo_ids`。
- `actions.CardAction.code` 对入参顺序敏感（去重会漏等价动作）；`model.Card(order=True)` 花色优先排序。
- `scoring.ScoreResult` 的 `__hash__` 实际不可用（`trace` 内含 dict）；`jokers.CATALOG_BY_ID` 遇重复 jid 会静默覆盖。
- `GameState.__post_init__` 校验有限；`rng.decode_state` 不校验内部结构；`_draw` 两堆皆空时静默少发。
- 测试未覆盖：`_draw` 的洗牌分支、loss 分支、商店选项唯一性、CLI、O2/O3 的 golden 值。

## 8. 先读什么

| 你要做的事 | 读 |
|---|---|
| 改计分 | 手册 §6、§14-R1 |
| 加 Joker | 手册 §7、§6.7、§14-R2 |
| 改流程/动作 | 手册 §8、§9、§14-R3 |
| 改日志 | 手册 §11、§14-R4 |
| 判断能否声称保真度 | 手册 §17；默认答案：不能 |
| 判断对齐等级 / 能否声称终验 | 手册 §17、§21、[07](plan/详细版/07-真实游戏接入与终验.md) §3/§6；当前 L0，不得写“已对齐/已终验” |
| 真游戏适配器 / 捕获 / 对齐 / 终验 | [07](plan/详细版/07-真实游戏接入与终验.md) 全文、手册 §21；先确认四层依赖与版本链，失败即降级 `CAPTURE_REPLAY_ONLY` |
| 完整背景 | [README 定位与差距表](README.md)、[engine-fidelity](docs/engine-fidelity.md)、[joker-semantics](docs/joker-semantics.md)、[plan/00 项目全貌](plan/00-项目全貌.md)；W2 实现说明书文件已缺失，历史归档见 [archive/legacy-2026-11-13/INDEX.md](archive/legacy-2026-11-13/INDEX.md) |
