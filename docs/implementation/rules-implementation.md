# 规则实现：vanilla 1.0.1o 严格子集 v1

> 规则权威：`bench/rules_version.py::VANILLA_SUBSET_V1`（机器可读）+ `scenarios/RULES_VERSION`（人类可读）+ `scenarios/rules_v1.json`（JSON 镜像，测试断言一致）。
> **状态**：IMPLEMENTED + TESTED（单测）；**VERIFIED = 否**（A2/A3 真游戏实测 0 行，`fidelity_status=NOT_VERIFIED`）。

## 1. 规则版本与配置

| 项 | 值 | 来源/说明 |
|---|---|---|
| rules_version | `vanilla_1.0.1o_subset_v1` | 本实现 |
| 目标游戏版本 | `1.0.1o` | plan/00、docs/balatro |
| 牌组 / 赌注 | Red Deck / White Stake | W3 目标配置 |
| Ante | 1（`max_ante=1`） | 只覆盖 Ante 1 |
| 盲注目标 | Small **300** / Big **450** / Boss **600** | 基础 300 × 1 / 1.5 / 2 |
| 手 / 弃 | **4 / 4** | 基础 4/3；Red Deck +1 弃 |
| 手牌上限 | 8 | vanilla 基础值 |
| Joker 槽位 | 5 | vanilla 基础值 |
| 单次出牌/弃牌 | 1–5 张 | — |
| 商店 | 默认关闭 | `shop_enabled=False`；`free_joker_choice` 为显式扩展 |
| Boss 效果 | 未实现 | 仍按 600 分目标；场景请求效果会被拒绝 |

**旧 L0 的 `TARGETS=(300,800,2000)` 已删除**：那是 Ante 1/2/3 的基础分，不是同一 Ante 的三盲注。

## 2. 一局流程（engine）

```text
new_game(seed) → Small Blind（target 300，4 手/4 弃，8 张手牌）
  play/discard ... 达标
    ├─ 非最后盲注 且 shop_enabled=False → 自动 _start_blind(下一盲注)
    ├─ 非最后盲注 且 shop_enabled=True  → phase=shop（3 选 1 或跳过）
    └─ 最后盲注（Boss）达标 → done + win
  未达标且 hands_left==0 → done + loss
```

### 2.1 转移规则

| 动作 | 规则 | 实现 |
|---|---|---|
| `play` | 1–5 张；消耗 1 手；计分后补牌到 8；打出的牌入弃牌堆；再判达标/失败 | `engine.play` |
| `discard` | 1–5 张；消耗 1 弃；补牌到 8；弃牌入弃牌堆；不判阶段 | `engine.discard` |
| `choose_joker` | 仅 `shop_enabled`；index 或 None（跳过）；随后进入下一盲注 | `engine.choose_joker` |
| 补牌 | 先抽 `deck`；空则把 `discard_pile` 洗回（消耗 RNG 并写回 `rng_state`）；两堆皆空则少抽 | `engine._draw` |
| 补牌时机 | 先移除打出的牌 → 补牌 → 打出的牌进弃牌堆 | 同一次转移内不会抽回刚打出的牌 |

### 2.2 换盲注

进入下一盲注时：
1. 上一盲注剩余手牌 → 弃牌堆；
2. `blind_idx/kind/target/boss_effect` 切换到该盲注；
3. `total_score=0`；`hands_left=4`；`discards_left=4`；清空 `shop_options`；
4. 补满 8 张手牌（必要时洗回弃牌堆）；
5. `phase='play'`，`outcome=None`。

> **未验证**：vanilla 跨盲注手牌/牌堆的精确处理（是否重洗、剩余手牌去哪）未做真游戏实测，标 `unverified: cross_blind_hand_redraw_policy`。

## 3. 计分流水线（`bench/scoring.py`）

```text
1) evaluate_hand(cards)
     - 牌型识别（12 种，按基础分从高到低短路）
     - 基础 Chips/Mult（等级 1）
     - 计分牌筛选 scoring_indices
     - contains 集合（Joker 条件用）
2) chips = base_chips
   mult  = Fraction(base_mult)
3) chips += Σ(scoring_cards[i].chips)        # A=11, J/Q/K=10, 数字=点数
4) 按 Joker 槽位顺序（左→右）逐项：
     - 条件满足：add_chips → chips += v；add_mult → mult += v；
                  mul_mult → mult *= Fraction(v,100)
     - 条件不满足：只记录 trace(triggered=False)，不改变数值
5) final_score = floor(chips × mult)          # 只在末尾取整
```

**未验证**：最终取整方式与中间小数处理（Wiki 未明写）。本实现按 `floor` 一次作为候选口径，trace 中显式写 `rounding_status=CANDIDATE_FLOOR_UNVERIFIED`。

### 3.1 牌型优先级与基础分（等级 1）

| 优先级 | 牌型 | 基础 Chips | 基础 Mult | 计分牌数 | 备注 |
|---:|---|---:|---:|---:|---|
| 1 | Flush Five 同花五条 | 160 | 16 | 5 | 标准 52 张不可达 |
| 2 | Flush House 同花葫芦 | 140 | 14 | 5 | 标准 52 张不可达 |
| 3 | Five of a Kind 五条 | 120 | 12 | 5 | 标准 52 张不可达（4 花色限制） |
| 4 | Straight Flush 同花顺 | 100 | 8 | 5 | Royal Flush 仅 `is_royal_flush` 标记 |
| 5 | Four of a Kind 四条 | 60 | 7 | 4 | 可带 1 张不计分 kicker |
| 6 | Full House 葫芦 | 40 | 4 | 5 | 必须 3+2 且 5 张 |
| 7 | Flush 同花 | 35 | 4 | 5 | 5 张同花色 |
| 8 | Straight 顺子 | 30 | 4 | 5 | A 可高/低，不可同时 |
| 9 | Three of a Kind 三条 | 30 | 3 | 3 | — |
| 10 | Two Pair 两对 | 20 | 2 | 4 | 两个不同点数对子 |
| 11 | Pair 对子 | 10 | 2 | 2 | 可带最多 3 张不计分牌 |
| 12 | High Card 高牌 | 5 | 1 | 1 | 只计点数最高 1 张 |

计分牌筛选规则（`scoring_card_indices`）：
- 高牌：只计最高 1 张（A 视为最大）；
- 对子 2 / 两对 4 / 三条 3 / 四条 4 / 顺子·同花·葫芦·同花顺 5 / 隐藏牌型 5；
- kicker/未参与牌型的牌**不计** rank chips。

### 3.2 contains（Joker 条件）口径

`CONTAINS_POLICY = "structural_superset_v1"`：基于打出的全部牌做结构判定。

| 判定 | 结果 | 证据状态 |
|---|---|---|
| 三条含对子 | ✅ 是 | docs/balatro 引用 Wiki |
| 四条含两对 | ❌ 否（两对要求两个不同点数） | ✅ Wiki 明示 |
| 五条含葫芦 | ❌ 否（葫芦要求 3+2） | ✅ Wiki 明示 |
| 四条/五条含对子/三条 | 是（结构超集） | **⏳ UNVERIFIED** |
| 同花顺含顺子/同花 | 是 | 结构定义 |

该口径影响 Jolly/Sly/The Duo（含对子）与 Zany/Wily/The Trio（含三条）的触发范围；A2 实测前不得当作已核事实。

## 4. 8 个具名 Joker

| Joker | 稀有度 | 效果 | 条件 | 实现 |
|---|---|---|---|---|
| Joker | Common | +4 Mult | always | add_mult |
| Jolly Joker | Common | +8 Mult | contains_pair | add_mult |
| Zany Joker | Common | +12 Mult | contains_three | add_mult |
| Sly Joker | Common | +50 Chips | contains_pair | add_chips |
| Wily Joker | Common | +100 Chips | contains_three | add_chips |
| Half Joker | Common | +20 Mult | 打出的牌 ≤3 张 | add_mult |
| The Duo | Rare | ×2 Mult | contains_pair | mul_mult(value=200) |
| The Trio | Rare | ×3 Mult | contains_three | mul_mult(value=300) |

- 数值/名称来自 `docs/balatro/content.md`（Wiki 事实页）；触发时机与与计分牌交互**未实测**。
- `mul_mult` 的 `value` 单位是百分之一（200=×2），trace/JSON 中保留该单位说明。
- 其余 142 个 Joker、Joker 版本、Negative、Blueprint/Brainstorm、重触发全部排除。
- 旧合成夹具（`jc_*`/`jm_*`/`jx_*`）已移出生产目录（仅测试可用自定义 `Joker` 构造）。

## 5. 资源与盲注的边界

| 项 | vanilla 事实 | 本实现 | 状态 |
|---|---|---|---|
| Ante 1 基础分 | 300 | 300 | ✅ 数值 |
| Small/Big/Boss 倍率 | 1 / 1.5 / 2 | 同 | ✅ 数值 |
| 4 手/4 弃 | Red Deck | 同 | ✅ 数值；跨盲注重置 |
| 5 Joker 槽 | 基础 5 | 同 | ✅ |
| 8 手牌 | 基础 8 | 同 | ✅ |
| Boss 效果 | 23 常规 + 5 Showdown 各有机制 | **全部未实现**（仅目标分） | ❌ 排除；场景校验拒绝 |
| 金钱/利息/商店 | 有 | 无（shop 仅显式扩展） | ❌ 排除 |
| 手牌等级 >1 | Planet 升级 | 无（固定等级 1） | ❌ 排除 |
| 牌型筛选例外 | Splash/Four Fingers/Shortcut 等 | 无 | ❌ 排除 |
| 卡牌增强/蜡封/版本 | 有 | 无 | ❌ 排除 |
| 多牌组/多赌注 | 15/8 | 固定 Red/White | ❌ 排除 |

## 6. 显式排除（`Ruleset.excluded`）

`money`、`interest`、`shop_economy`、`boss_effects`、`consumables_tarot_planet_spectral`、`vouchers`、`booster_packs`、`card_enhancements`、`card_seals`、`card_editions`、`multi_deck`、`multi_stake`、`tags_and_blind_skip`、`endless_mode`、`hand_levels_gt1`、`retriggers`、`blueprint_brainstorm`、`joker_editions`、`negative_joker_slots`、`held_in_hand_card_effects`、`stone_gold_glass_steel_lucky_cards`。

**不允许静默忽略**：
- 场景若请求 Boss 效果 → `UnsupportedRuleError`；
- 场景若声明未知扩展 → `UnsupportedRuleError`；
- 工具调用 `choose_joker` 而商店未启用 → `NOT_ALLOWED`；
- 任何未实现机制不得出现在训练集中（由 validator/文档双重约束）。

## 7. 对齐边界与证据

- **已实现的数值**（牌型基础分、Ante 1 目标、4/4、5 槽、8 张、8 Joker 数值）可在 `docs/balatro/rules.md`/`content.md` 找到来源；来源许可为 CC BY-NC-SA，本项目只取事实数值、描述自写。
- **未验证**：单步分数与真游戏一致（A2）、合法动作集一致（A1/A3）、跨盲注行为、取整、contains 4K/5K 边界、Boss 效果缺失。均列在 `Ruleset.unverified` 与 `docs/implementation/testing-and-validation.md`。
- 修改 `verification_status` 的唯一合法路径：`docs/engine-fidelity.md` A/B 表实测 + 签核；本实现未触碰该状态。

## 8. 参考

- 规则事实：[docs/balatro/rules.md](../balatro/rules.md)、[content.md](../balatro/content.md)、[engine-gap.md](../balatro/engine-gap.md)
- 代码：`bench/rules_version.py`、`bench/hand_eval.py`、`bench/scoring.py`、`bench/jokers.py`、`bench/engine.py`
- 测试：`tests/test_w2_rules.py`、`tests/test_environment.py`、`tests/test_rules_declaration.py`
