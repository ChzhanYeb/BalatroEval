# 实现状态矩阵

> 状态定义（严格区分）：
> - **NOT_IMPLEMENTED**：没有代码路径；
> - **IMPLEMENTED**：有代码路径，可能未被测试覆盖；
> - **TESTED**：有自动化测试且通过；**只证明代码行为符合本仓库测试**；
> - **VERIFIED**：与真游戏/一手事实实测一致并有证据（A0–A4 签核）。**本次没有任何规则项达到 VERIFIED。**
>
> 结论：**规则与基础设施 = IMPLEMENTED + TESTED；与 vanilla 的一致性 = NOT_VERIFIED（A2/A3 0 行）。**

## 1. 规则能力

| 能力 | 状态 | 证据 |
|---|---|---|
| 规则版本/声明（程序可读 + JSON 镜像 + 文档） | **TESTED** | `bench/rules_version.py`、`scenarios/rules_v1.json`、`tests/test_rules_declaration.py` |
| Red Deck / White Stake / Ante 1 配置 | **TESTED** | `Ruleset`、`tests/test_environment.py`、`test_rules_declaration.py` |
| 三盲注 300 / 450 / 600 | **TESTED** | 同上；旧 300/800/2000 已移除 |
| 4 手 / 4 弃（Red +1） | **TESTED** | `new_game`、`test_environment` |
| 手牌 8 / Joker 槽 5 | **TESTED** | `GameState`、`test_environment` |
| 出牌/弃牌 1–5、补牌、洗回弃牌堆、52 张守恒 | **TESTED** | `engine._draw/_refill`、`test_properties` |
| 9 常规牌型识别 | **TESTED** | `hand_eval`、`test_w2_rules`（12 类） |
| 3 隐藏牌型识别（五条/同花葫芦/同花五条） | **TESTED（代码路径；标准 52 张不可达）** | `test_w2_rules` 用重复牌分类测试 |
| 等级 1 基础 Chips×Mult | **TESTED** | `HAND_BASE_SCORE`、`test_w2_rules` |
| 计分牌筛选（高牌 1 / 对子 2 / 两对 4 / 三条 3 / 四条 4 / 其余 5） | **TESTED** | `scoring_card_indices`、`test_w2_rules` |
| Joker 槽位顺序计分 + 条件不触发记 trace | **TESTED** | `scoring.score_hand`、`test_w2_rules` |
| 8 个具名 Joker 数值/条件 | **TESTED** | `bench/jokers.py`、`test_w2_rules`；数值来源 `docs/balatro/content.md` |
| contains 关系（三条含对子；四条不含两对；五条不含葫芦） | **TESTED** | `hand_contains_types`、`test_w2_rules` |
| 胜负判定（达标优先；手数耗尽判负） | **TESTED** | `engine._after_play`、`test_environment` |
| 跨盲注重置/换手牌 | **TESTED** | `engine._start_blind`、`test_environment` |
| 确定性 RNG / 同 seed 复现 | **TESTED** | `rng.py`、`test_properties`、`test_runtime` |
| 完整快照/还原/state_hash | **TESTED** | `serialize.py`、`test_environment` |
| Ante 1 Boss **仅按目标分**建模 | **IMPLEMENTED + TESTED（策略）** | `boss_effect=None`；场景校验拒绝效果 |
| Boss 具名效果 | **NOT_IMPLEMENTED（排除）** | `Ruleset.excluded: boss_effects`；validator 拒绝 |
| 金钱/利息/商店经济 | **NOT_IMPLEMENTED（排除）** | `excluded`；shop 默认关闭 |
| 免费 3 选 1 Joker（benchmark 扩展） | **TESTED** | `ruleset_for([free_joker_choice])`、`test_environment.choose_joker` 相关、dev 场景 |
| 消耗品/Voucher/补充包/增强/蜡封/版本 | **NOT_IMPLEMENTED（排除）** | `excluded` |
| 多牌组/多赌注/Tag/跳盲/Endless | **NOT_IMPLEMENTED（排除）** | `excluded` |
| 手牌等级 >1 / 重触发 / Blueprint | **NOT_IMPLEMENTED（排除）** | `excluded` |
| 取整方式 / contains 4K-5K 边界 / 跨盲注 hand 处理 | **IMPLEMENTED（候选口径），UNVERIFIED** | `Ruleset.unverified` |
| 与真游戏单步分数一致（A2） | **NOT_VERIFIED** | 0 行实测；`docs/engine-fidelity.md` PENDING |

## 2. 环境与工具

| 能力 | 状态 | 证据 |
|---|---|---|
| `Environment.reset/observe/legal_actions/step/snapshot/restore/is_terminated/is_truncated` | **TESTED** | `bench/environment.py`、`test_environment` |
| Observation（不含牌堆顺序/oracle）+ 紧凑文本 | **TESTED** | `observation.py`、`test_environment`、`test_runtime` |
| Action canonical code / from_dict / 1–5 张校验 | **TESTED** | `actions.py`、`test_environment` |
| 场景动作种类限制（play/discard 决策点） | **TESTED** | `Environment._allowed`、`test_environment` |
| 统一错误码（11 个）与工具 envelope | **TESTED** | `errors.py`、`tools.py`、`test_environment` |
| MCP 薄壳（5 工具注册） | **IMPLEMENTED**；**仅构建验证** | `bridge/server.py`、`bridge/.venv` 下 `build_server()` 成功；未做真实 dsh stdio 会话 |
| 快照 restore 校验 hash | **TESTED** | `serialize.py`、`test_environment` |
| 牌组/Joker ID 校验 | **TESTED** | `cards.py`、`scenarios/validator.py` |

## 3. 评测基础设施

| 能力 | 状态 | 证据 |
|---|---|---|
| Scenario Schema/Loader/Validator | **TESTED** | `scenarios/`、`test_scenarios`（17 项） |
| 单 Episode Runner（同步/异步） | **TESTED** | `evaluation/episode_runner.py`、`test_runtime` |
| 局部 Oracle 指标（regret/optimality，仅 play） | **TESTED** | `oracle.best_play`、`run_episode`、`test_runtime` |
| O2 弃牌 EV（近似） | **TESTED（行为）** | `oracle.discard_ev`、`test_runtime`；必须带 K/抽样模型说明 |
| Trace JSONL schema 2（start/step/decision_metric/end） | **TESTED** | `trace.py`、`test_runtime` |
| 结果 results.jsonl + manifest + code hash | **TESTED** | `config.py`、`test_runtime` |
| Batch 并发执行 | **TESTED** | `batch_runner.py`、`test_runtime` |
| 失败隔离（agent_error/env_error/timeout/invalid limit） | **TESTED** | `test_runtime` |
| 断点续跑 / retry-failed | **TESTED** | `test_runtime` |
| 指标聚合 / bootstrap CI / Markdown 表 | **TESTED** | `metrics.py`、`test_runtime` |
| 模型 Adapter（HTTP + 缓存 + 限流 + 重试 + 超时） | **IMPLEMENTED + TESTED（fake transport）** | `agents.py`、`test_runtime`；**真实服务未实测** |
| 多进程分片 | **NOT_IMPLEMENTED** | 设计说明见 `evaluation-execution.md`；当前单进程 asyncio |
| 模型响应缓存（SQLite） | **TESTED（fake）** | `ResponseCache`、`test_runtime` |
| 成本/token 记录 | **IMPLEMENTED**（Agent usage → trace/result） | `AgentDecision.usage`、`metrics.summarize.usage` |

## 4. 测试与文档

| 项 | 状态 |
|---|---|
| 单元/集成/性质/并发/续跑测试（124） | **TESTED**：`python -m unittest discover -s tests` → Ran 124 / OK |
| Golden 数值（7h7d=48 等） | **TESTED** |
| 规则声明漂移检查 | **TESTED** |
| 性能基准脚本 + 实测数据 | **DONE**：`benchmarks/bench.py`、`docs/implementation/performance.md` |
| 实现文档（9 份） | **DONE**：`docs/implementation/` |
| 与真游戏对齐验证（A0–A4） | **NOT_VERIFIED / 未执行** |

## 5. 明确排除（不实现，不进入训练集）

`money`、`interest`、`shop_economy`、`boss_effects`、`consumables_tarot_planet_spectral`、`vouchers`、`booster_packs`、`card_enhancements`、`card_seals`、`card_editions`、`multi_deck`、`multi_stake`、`tags_and_blind_skip`、`endless_mode`、`hand_levels_gt1`、`retriggers`、`blueprint_brainstorm`、`joker_editions`、`negative_joker_slots`、`held_in_hand_card_effects`、`stone_gold_glass_steel_lucky_cards`。

## 6. 不能宣称的事项（与 README/AGENTS 一致）

1. 不能宣称“与 vanilla 1.0.1o 对齐/已验证/已终验”；当前 `NOT_VERIFIED`。
2. 不能宣称“Boss 效果已实现”；只按目标分建模，效果被排除。
3. 不能宣称“金钱/商店经济/长期构建已实现”。
4. 不能宣称“长线规划四支柱已覆盖”。
5. 不能宣称“O1 是全局最优”；它是当前手牌局部 argmax。
6. 不能宣称“124 测试通过 = 规则与真游戏一致”。
7. 不能把旧 `bench/logging.py` 的 schema 1 当作新 trace；新链路用 `evaluation.trace` schema 2。

## 7. 下一步建议

### P0（先做）
1. **A2/A3 真游戏实测**：W3 捕获 30 锚点 + 30 反事实变体，逐局面比 `engine_score == real_score`；用本实现的 trace `state_hash` 对账。
2. **取整/contains/跨盲注 三项未验证口径**：用真游戏局面做定向实验并写入 `docs/engine-fidelity.md`。
3. **真实模型端点 smoke**：用 `HttpChatAgent` + 真实端点跑 1 个 episode，确认工具 schema/解析/重试/超时；未完成前状态保持“fake-only”。

### P1（可信度）
4. **MCP stdio 端到端**：dsh 连接 `bridge/server.py` 跑 ≥3 次工具调用的 episode，验证工具错误码与 trace。
5. **多进程分片**：按 scenario 分片并行，使 90 局/12 局实验可线性扩展；保持每进程独立 run 目录。
6. **O2 抽样模型修正**：从 `rng_state` 复现真实发牌（或明确只作启发式），报告带 K/seed 派生说明。
7. **Boss 效果子集**：优先实现纯计分型（The Wall 4×、The Needle 1 手）再做 debuff 型；每个效果单独金样。

### P2（工程）
8. 优化 `legal_actions`/`build_observation` 的每步开销（惰性枚举/缓存），减少每步 ~3 ms。
9. Trace 可选批量 fsync（崩溃语义需文档化）。
10. 把 `benchmarks/bench.py` 接入 CI 的 smoke 阈值（防止性能回退）。
11. 将 `results.jsonl` 离线转 Parquet 的脚本（外部依赖，不入库）。
