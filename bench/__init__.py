"""BalatroEval W2 子集引擎包（custom subset engine package）。

职责：实现一个确定性、可复现的简化 Balatro 风格基准环境，供 Agent 规划／评测
实验使用；它只覆盖自定义子集（custom subset），不是原版（not vanilla）复刻。

子模块职责一览：
- model：Card／Joker／GameState 类型化领域模型与日志摘要导出。
- cards：标准 52 张牌组构造、稳定卡牌 ID 查找与组合规范化。
- rng：RNG state 的 JSON 序列化与无损还原（回放保真度的基础）。
- actions：候选动作（candidate action）枚举与 CardAction 编码。
- scoring：牌型判定与自定义子集计分公式，输出 trace 计分轨迹。
- jokers：合成夹具（synthetic fixtures）Joker 目录，非原版具名 Joker。
- engine：状态初始化与状态推进（play／discard／choose_joker）。
- oracle：穷举参照（oracle）与 O1／O2／O3 参照策略，O2／O3 为近似。
- logging：追加式 episode JSONL 日志（schema_version=1）。
- __main__：命令行入口（demo／verify／ev）。

边界／不变量：
- 计分公式省略原版的 hand base chips，且 Joker 为合成夹具；因此本包分数是
  自定义子集成绩，不得与 vanilla 原版分数直接比较，fidelity 结论仅限包内。
- 随机性只能来自 rng 模块保存的完整随机数状态；禁止依赖全局随机源或时间。
- 动作与日志以稳定卡牌 ID 为身份依据；手牌下标只作当次快照。
- 包内导入保持单向、无环：底层为 model 与 rng，cards／actions／scoring／jokers／
  logging 只依赖 model，engine 依赖上述模块，oracle／__main__ 依赖 engine
  （分层与仓库根 AGENTS.md §3 的依赖分层表一致）。

维护提示：改模型字段先看 model.py 与 state_summary 的消费者 logging.py；
改计分公式先看 scoring.py 的模块说明与 tests/test_w2_rules.py；改动作枚举先看
actions.py 的 218 上限断言；改状态推进先看 engine.py 与 test_same_seed_episode。
"""
