"""BalatroEval 规则引擎与训练环境（vanilla 1.0.1o 严格子集）。

包内模块（自底向上）：
- ``errors``：统一错误码与异常；
- ``rules_version``：规则声明（唯一机器可读来源）、Ante 1 三盲注、牌型基础分表；
- ``model``：Card / Joker / GameState 值对象与状态摘要；
- ``cards``：标准 52 张牌组、稳定 ID 查找；
- ``hand_eval``：牌型识别、计分牌筛选、contains 关系；
- ``jokers``：8 个具名 vanilla Joker 与条件判定；
- ``scoring``：等级 1 计分（基础 Chips×Mult → 计分牌 → Joker 槽位顺序）；
- ``actions``：Action 值对象、合法动作枚举（218 出牌 + 218 弃牌）；
- ``engine``：状态初始化与转移（play/discard/choose_joker）；
- ``serialize``：完整快照/还原/state_hash；
- ``observation``：Agent 可见 observation + 紧凑文本；
- ``environment``：reset/observe/legal_actions/step/snapshot 的稳定环境接口；
- ``tools``：Agent 工具层（统一错误码，MCP 与本地 runner 共用）；
- ``oracle``：O1 精确局部 argmax / O2 近似 EV / O3 贪心参照；
- ``logging``：旧 L0 日志写入器（LEGACY，未被新链路调用；新轨迹见 evaluation.trace）；
- ``__main__``：``python -m bench {rules,demo,verify,ev}``。

边界（不得越线）：
- 规则实现等级：**IMPLEMENTED**；与真游戏一致性：**NOT_VERIFIED**（A2 0 行）。
- 明确排除：金钱/商店经济、Boss 效果、消耗品、Voucher、补充包、卡牌增强/蜡封/版本、
  多牌组/多赌注、Tag/跳盲、Endless、手牌等级>1、重触发。
- 随机性只来自 ``GameState.rng_state``；不承诺与真游戏同种子同局面。
"""
