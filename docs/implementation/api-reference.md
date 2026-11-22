# API Reference（以实际代码为准）

> 本文件按模块列出公开类/函数。所有签名与实际代码一致（Python 3.11+，`from __future__ import annotations`）。
> 约定：`M`=确定性；`P`=纯函数；`IO`=有文件/网络副作用；`E`=可能抛 `BenchError` 子类。

## 0. 错误码（`bench/errors.py`）

| code | 触发场景 | 抛出类型 |
|---|---|---|
| `BAD_REQUEST` | 参数形状/张数/索引非法 | `InvalidActionError` |
| `INVALID_STATE` | 动作与阶段不匹配（如 done 后出牌、非商店阶段买/卖/reroll） | 同上 |
| `NOT_ALLOWED` | 场景动作种类限制、重复 Joker | 同上 |
| `UNKNOWN_CARD` | 未知卡牌/Joker ID | 同上 |
| `DUPLICATE_CARD` | 同一物理牌/ID 重复 | 同上 |
| `NO_RESOURCE` | 无弃牌次数 / 无手数 / 槽位满 / 钱不够（买或 reroll） | 同上 |
| `EPISODE_DONE` | episode 已结束仍执行动作 | 同上 |
| `UNSUPPORTED_RULE` | 请求排除机制（Boss 效果、未知扩展） | `UnsupportedRuleError` |
| `INTERNAL` | 不变量破坏（代码 bug） | `InternalInvariantError` |
| `AGENT_ERROR` | Agent 未能产出动作 | runner status |
| `TIMEOUT` | episode/模型调用超时 | runner status |

```python
try:
    env.step({"kind": "play", "card_ids": ["c7h", "c7d"]})
except BenchError as exc:
    print(exc.code, exc.message, exc.detail)
```

## 1. 规则声明（`bench/rules_version.py`）

| 名称 | 类型 | 说明 |
|---|---|---|
| `HAND_BASE_SCORE` | `dict[str, tuple[int,int]]` | 12 牌型等级 1 的 `(chips, mult)` |
| `BlindSpec` | frozen dataclass | `index/kind/name/base_score/multiplier/reward_money/effect`；`target` 属性 |
| `ANTE1_BLINDS` | `tuple[BlindSpec,...]` | 300/450/600（奖励 3/4/5） |
| `Ruleset` | frozen dataclass（slots） | 规则声明：版本/牌组/资源/槽位/盲注/**经济常量**/状态列表；`to_dict()`、`signature()`、`blind(i)` |
| `VANILLA_SUBSET_V1` | `Ruleset` | 当前权威实例（`vanilla_1.0.1o_subset_v2`） |
| `STARTING_MONEY` / `HAND_BONUS` / `DISCARD_BONUS` / `INTEREST_PER` / `INTEREST_CAP` | `int` | 经济常量（4 / 1 / 1 / 5 / 5） |
| `SHOP_OFFER_COUNT` / `REROLL_BASE_COST` / `REROLL_INCREMENT` | `int` | 商店常量（2 / 5 / 1） |
| `JOKER_PRICE_BY_RARITY` | `dict[str,int]` | 固定价表（Common 5 / Uncommon 7 / Rare 9 / Legendary 10） |
| `joker_price(joker_or_rarity)` | `-> int` | 买价；未知稀有度抛 `ValueError` |
| `sell_value(joker)` | `-> int` | 卖价 = `max(1, price // 2)` |
| `interest_for(money, ruleset=None)` | `-> int` | `min(money // 5, cap)` |
| `RETIRED_EXTENSIONS` | `tuple[str,...]` | `("free_joker_choice",)`：v2 已退役 |
| `ruleset_for(extension_names)` | `-> Ruleset` | v2 起**拒绝任何扩展**（含已退役项），抛 `ValueError` |

- 确定性：`P`；无副作用；调用方：engine/environment/scenarios/evaluation。
- `Ruleset.to_dict()` 与 `scenarios/rules_v2.json` 必须完全一致（`tests/test_rules_declaration.py`）。

```python
from bench.rules_version import VANILLA_SUBSET_V1
print([b.target for b in VANILLA_SUBSET_V1.blinds])   # [300, 450, 600]
print(VANILLA_SUBSET_V1.signature()[:16])
```

## 2. 领域模型（`bench/model.py`）

| 名称 | 签名/字段 | 说明 |
|---|---|---|
| `Card(suit:int, rank:int)` | frozen/slots/order | 标准牌；`card_id`/`label`/`rank_label`/`suit_name`/`chips`；`to_dict`/`from_dict` |
| `card_from_id(card_id:str)` | `-> Card` | 解析 `c7h`/`c10s`；非法抛 `ValueError` |
| `Joker(jid, name, kind, value, condition="always", rarity="", buy_price=0)` | frozen/slots | `kind ∈ {add_chips,add_mult,mul_mult}`；`mul_mult` 的 value 为百分之一；`multiplier` 属性 |
| `GameState` | dataclass | 规则身份（rules_version/ante/blind_idx/kind/boss_effect/target/joker_slots/hand_size/shop_enabled）+ 进度 + **经济（money/reroll_cost/last_payout）** + 牌/Joker + seed/rng_state；`deck_total` 属性 |
| `state_summary(state)` | `-> dict` | 紧凑摘要（hand/jokers 完整，deck/discard 只计数，含 money） |

- 构造期校验：suit/rank 范围、kind/condition、资源非负、Joker ≤ 槽位等（`ValueError`）。
- 无副作用；`GameState` 可变，但引擎只修改 `deepcopy` 副本。

## 3. 牌组辅助（`bench/cards.py`）

| 函数 | 返回 | 异常 | 说明 |
|---|---|---|---|
| `standard_deck()` | `list[Card]`（52，固定顺序） | — | 纯/确定 |
| `card_from_stable_id(card_id)` | `Card` | `UNKNOWN_CARD` | 只接受标准 52 张 |
| `cards_by_ids(cards, card_ids)` | `list[Card]`（请求顺序） | `UNKNOWN_CARD`/`DUPLICATE_CARD` | 动作回放基础 |
| `combo_ids(cards)` | `tuple[str,...]` | — | 排序后的稳定键 |
| `remaining_deck(excluded_ids)` | `list[Card]` | `UNKNOWN_CARD`/`DUPLICATE_CARD` | 场景初始化用 |

## 4. 牌型与计分（`bench/hand_eval.py`、`bench/scoring.py`）

```python
def classify_hand(cards: Sequence[Card]) -> HandType
def evaluate_hand(cards: Sequence[Card]) -> HandAnalysis
def scoring_card_indices(cards, hand_type) -> tuple[int, ...]
def hand_contains_types(cards) -> frozenset[HandType]
def is_straight_ranks(ranks: Iterable[int]) -> bool
def score_hand(cards: Sequence[Card], jokers: Sequence[Joker] = ()) -> ScoreResult
```

| 名称 | 说明 | 异常 | 确定性/副作用 |
|---|---|---|---|
| `HandType` | 12 种牌型枚举；`display_name` | — | — |
| `HandAnalysis` | `hand_type/base_chips/base_mult/scoring_indices/scoring_cards/contains/is_royal_flush`；`to_dict()` | — | — |
| `classify_hand` | 牌型识别（张数校验；允许重复牌用于隐藏牌型分析） | `BAD_REQUEST` | P、M |
| `evaluate_hand` | 分类 + 基础分 + 计分牌 + contains；拒绝重复 `card_id` | `BAD_REQUEST`/`DUPLICATE_CARD` | P、M |
| `scoring_card_indices` | 参与计分的下标（见 rules-implementation §3.1） | — | P、M |
| `hand_contains_types` | 结构超集 contains 集合 | — | P、M |
| `ScoreResult` | `analysis/chips/mult/final_score/trace/scoring_card_ids`；`hand_type` 属性；`to_dict()` | — | 不可变 |
| `score_hand` | 完整计分流水线 + trace；**末尾 floor 一次** | `InvalidActionError`；未注册效果 `ValueError` | P、M；不修改入参 |

```python
from bench.model import Card
from bench.scoring import score_hand
r = score_hand([Card(1, 7), Card(2, 7)])      # 7h 7d
assert (r.chips, str(r.mult), r.final_score) == (24, "2", 48)
```

> `Card(1,7)` 是 `suit=1(红心), rank=7`；注意参数顺序是 `(suit, rank)`。

## 5. Joker（`bench/jokers.py`）

| 名称 | 说明 |
|---|---|
| `VANILLA_JOKERS` / `JOKER_CATALOG` | 8 个具名 Joker（tuple） |
| `CATALOG_BY_ID` | `jid -> Joker` |
| `get_joker(jid)` | 未知 ID 抛 `KeyError` |
| `condition_met(joker, analysis, played_card_count)` | 条件判定；`P/M` |

```python
from bench.jokers import CATALOG_BY_ID
from bench.hand_eval import evaluate_hand
from bench.model import Card
analysis = evaluate_hand([Card(0,8), Card(1,8), Card(2,8)])
assert CATALOG_BY_ID["the_trio"].condition == "contains_three"
```

## 6. 动作（`bench/actions.py`）

```python
Action(kind, card_ids=(), hand_indices_snapshot=(), joker_index=None)
Action.code                       # canonical: play:c7d,c7h / choose_joker:buy:0 / choose_joker:leave
Action.to_dict() / Action.from_dict(data)
legal_plays(hand, max_cards=5) -> list[tuple[int,...]]
legal_discards(hand, discards_left, max_cards=5) -> list[tuple[int,...]]
encode_card_action(kind, hand, indices) -> Action
shop_actions(state) -> list[Action]
legal_actions(state, max_play_cards=5, max_discard_cards=5) -> list[Action]
```

- `Action.__post_init__` 校验 kind/张数/重复（抛 `InvalidActionError`）；`sell_joker` 必须带 `joker_index`。
- `legal_actions`：play 阶段 218 出牌 + 218 弃牌（8 张手牌）；shop 阶段返回「买得起的报价 + 每个已拥有 Joker 的卖出 + （钱够时）reroll + 恒可用的离开」；done 返回 `[]`。
- 商店动作码：`choose_joker:buy:{i}` / `choose_joker:leave` / `sell_joker:{i}` / `reroll_shop`。
- `P/M`；不修改 state。

## 7. 引擎（`bench/engine.py`）

| 函数 | 签名 | 返回 | 异常 |
|---|---|---|---|
| `new_game` | `(seed, *, ruleset=VANILLA_SUBSET_V1, hand_ids=None, joker_ids=(), deck_order=None)` | `GameState`（起始 $4） | `BAD_REQUEST`/`UNKNOWN_CARD` |
| `play` | `(state, card_ids)` | `(GameState, ScoreResult)` | `EPISODE_DONE`/`INVALID_STATE`/`NO_RESOURCE`/`BAD_REQUEST`/`DUPLICATE_CARD`/`UNKNOWN_CARD` |
| `discard` | `(state, card_ids)` | `GameState` | 同上（无计分结果） |
| `choose_joker` | `(state, index: int\|None)` | `GameState` | `NOT_ALLOWED`/`INVALID_STATE`/`BAD_REQUEST`/`NO_RESOURCE`（钱不够/槽位满） |
| `sell_joker` | `(state, index: int)` | `GameState` | `INVALID_STATE`（非 shop）/`BAD_REQUEST` |
| `reroll_shop` | `(state)` | `GameState` | `INVALID_STATE`（非 shop）/`NO_RESOURCE` |
| `open_shop` | `(state, ruleset)` | `None`（原地改副本） | — |
| `draw_shop_offers` | `(state, ruleset)` | `None`（原地改副本，消耗 rng） | — |
| `apply_action` | `(state, action: Action)` | `(GameState, ScoreResult\|None)` | 同上 |

- 所有转移：先校验 → `deepcopy` → 修改副本 → 不变量自检（52 张守恒）→ 返回；**入参 state 永不被修改**。
- `IO`：无（不写日志/文件）；`M`：同 state+动作 ⇒ 同结果。
- `choose_joker(i)` 买入后**仍停在 shop**；`choose_joker(None)` 离开商店才进入下一盲注，且 `money` 保留。
- `_blind_payout(state, ruleset)`（内部）返回结算明细并写进 `state.last_payout`：`blind_reward/hand_bonus/discard_bonus/interest/total/money_before/money_after`。

```python
from bench.engine import new_game, play
state = new_game(20261117)
new_state, result = play(state, [state.hand[0].card_id])
assert state.steps == 0 and new_state.steps == 1
```

## 8. 快照与哈希（`bench/serialize.py`）

| 函数 | 返回 | 异常 | 说明 |
|---|---|---|---|
| `state_to_dict(state)` | `dict` | — | 完整状态（52 张 IDs + jokers + 资源 + **money/reroll_cost/last_payout** + rng_state）；schema **2** |
| `state_from_dict(data)` | `GameState` | `BAD_REQUEST` | schema 版本/ID/52 张校验；v1 快照被显式拒绝 |
| `state_hash(state)` | `str`(64 hex) | — | 规范化 JSON sha256 |
| `snapshot(state)` | `{"state":..., "state_hash":...}` | — | — |
| `restore(payload)` | `GameState` | `BAD_REQUEST` | 校验 hash |
| `canonical_json(data)` | `str` | — | sort_keys + 紧凑分隔符 |

## 9. Observation / Environment（`bench/observation.py`、`bench/environment.py`）

```python
build_observation(state, ruleset=VANILLA_SUBSET_V1, allowed_action_kinds=None) -> dict
render_observation(observation, max_chars=1000) -> str

class Environment:
    def __init__(self, ruleset=VANILLA_SUBSET_V1, max_steps: int|None=None)
    def reset(self, spec: ResetSpec|None=None, *, seed: int|None=None) -> dict
    def observe(self) -> dict
    def render(self, max_chars=1000) -> str
    def legal_actions(self) -> list[Action]
    def step(self, action: Action|dict) -> StepResult
    def snapshot(self) -> dict
    def restore(self, payload: dict) -> dict
    def is_terminated(self) -> bool
    def is_truncated(self) -> bool
```

- `ResetSpec`：`seed/hand_ids/joker_ids/deck_order/ruleset/allowed_action_kinds/max_steps/blind_idx/total_score/hands_left/discards_left/target/**money**/**shop_open**/scenario_id`。
- `StepResult`：`observation/reward/terminated/truncated/info`（`info` 含 action_code、前后 state_hash、score、**money/money_delta/last_payout**、termination_reason）。
- Observation schema **2**：新增 `economy`（money/利息/上次结算）与 `shop`（报价/价格/是否买得起/reroll 价/卖价/空槽），移除 v1 顶层 `shop_options`。
- 异常：`EPISODE_DONE`（结束后 step）、`INVALID_STATE`（截断后 step）、`NOT_ALLOWED`（场景限制）、规则错误。
- `IO`：无；`M`：同 reset spec + 动作序列 ⇒ 同 observation/hash。
- 调用方：`bench/tools.py`、`evaluation/episode_runner.py`、测试。

```python
from bench.environment import Environment, ResetSpec
env = Environment()
obs = env.reset(ResetSpec(seed=42))
action = next(a for a in env.legal_actions() if a.kind == "play")
result = env.step(action)
print(result.reward, result.terminated, result.info["state_hash_after"][:12])
```

## 10. 工具层（`bench/tools.py`）

```python
GameSession(ruleset=VANILLA_SUBSET_V1, seed=0, env=None)
get_state(session) -> dict
play_cards(session, card_ids) -> dict
discard_cards(session, card_ids) -> dict
choose_joker(session, index: int|None=None) -> dict     # 买（index）或离开（None）
sell_joker(session, index: int) -> dict
reroll_shop(session) -> dict
reset_episode(session, *, seed=None, hand_ids=None, joker_ids=(), blind_idx=None,
              total_score=None, hands_left=None, discards_left=None, target=None,
              money=None, shop_open=False, allowed_action_kinds=None,
              max_steps=None) -> dict
dispatch_tool(session, name, arguments=None) -> dict
TOOL_SPECS: dict[str, dict]   # 名称→描述/JSON schema；MCP 与本地共用（7 个工具）
```

- 返回 envelope：成功 `{"ok": True, "observation":..., "text":..., "reward":..., "terminated":..., "truncated":..., "info":...}`；失败 `{"ok": False, "error": {"code","message","detail"}}`。
- 异常：**不抛出** `BenchError`（统一转换）；未知工具返回 BAD_REQUEST。
- `IO`：无；`M`：同一 session 顺序调用确定。

## 11. Oracle（`bench/oracle.py`）

| 名称 | 说明 | 保真度 |
|---|---|---|
| `best_play(state) -> BestPlay` | 当前手牌 218 组合精确 argmax | **局部**；不评估弃牌/未来 |
| `score_action(state, action) -> ScoreResult\|None` | play 精确分；discard/商店动作返回 None | 精确（play） |
| `discard_ev(state, K=50, seed=None) -> list[DiscardEV]` | 弃牌后下一手 O1 分的 Monte Carlo 均值/min/max | **近似**：不读 rng_state、deck+discard 混池 |
| `greedy_shop_action(state) -> Action` | 商店策略：买得起第一个就买，否则离开（不 reroll/不卖） | 贪心参照，**不**做经济优化 |
| `greedy_episode(state, max_steps=200) -> EpisodeReference` | O1 贪心 + 上述商店策略整局 | 近似参照，不是最优/上界；摘要含 `final_money` |

- `best_play` 异常：`INVALID_STATE`（非 play）或 `BAD_REQUEST`（无合法动作）。
- `discard_ev` 异常：`INVALID_STATE`/`BAD_REQUEST`；`P`；不推进引擎 RNG。
- 调用方：`evaluation.agents.OracleGreedyAgent`、`evaluation.episode_runner`（regret）、CLI。

## 12. 评测执行（`evaluation/`）

### 12.1 配置与存储

```python
ExperimentConfig(experiment_id, scenario_paths, agent_id="oracle-greedy",
    agent_params={}, repeats=1, max_steps=None, episode_timeout_s=60.0,
    max_concurrency=4, agent_concurrency=4, retry_attempts=1, retry_backoff_s=0.5,
    max_invalid_actions=3, oracle_enabled=True, trace_fsync=True,
    output_dir="runs", resume=True, retry_failed=False, scenario_max_count=None,
    ruleset=VANILLA_SUBSET_V1)
# 方法：config_hash()（结果相关配置 sha256 前 16 位）、to_dict()

ExperimentStore(config)
# 方法：write_manifest(code_hash, scenarios)、append_result(row)、load_results()、
#       result_index()、completed_task_ids(success_only=True)、trace_path(task_id, episode_index)、invalidate()

compute_code_hash(roots=("bench","evaluation","scenarios"), base_dir=".") -> str
```

- `ExperimentStore`：`IO`（创建 run 目录、写 manifest、append results）；线程锁保护进程内写。
- manifest 冲突（同 experiment 不同 config_hash）抛 `ValueError`。

### 12.2 Agent

```python
AgentDecision(action, raw_output=None, usage={}, error_code=None, error_message=None,
              latency_ms=0.0)   # ok 属性
Agent / AsyncAgent                # 协议：agent_id + decide / decide_async
decide_async(agent, observation, legal_actions) -> AgentDecision
CallableAgent(agent_id, fn)
FirstLegalAgent(agent_id="first-legal")
RandomAgent(seed=0, agent_id="random")
OracleGreedyAgent(agent_id="oracle-greedy", discard_samples=10)
ResponseCache(path=None)          # SQLite；make_key/get/put/close；hits/misses
TokenBucket(rate_per_second, burst=1)  # async acquire()
HttpChatAgent(agent_id, model, *, transport=None, temperature=0.0, max_tokens=256,
              prompt_builder=default_prompt_builder, cache=None, rate_limiter=None,
              max_retries=3, backoff_s=0.5, timeout_s=30.0)
parse_action_text(text) -> Action
default_prompt_builder(observation, legal_actions) -> list[dict]
```

- `OracleGreedyAgent`：play → `best_play`；仅 discard → O2 EV（默认 K=10，较慢）；shop → 买第一个买得起的报价，否则离开（不 reroll、不卖、不为利息存钱）。
- `HttpChatAgent`：缓存键 = 模型+完整请求；限流；超时/重试；解析失败返回 `AGENT_ERROR`/`BAD_REQUEST`；超时返回 `TIMEOUT`。
- `IO`：HTTP（默认 transport 仅读 `BALATROEVAL_LLM_URL`/`KEY` 环境变量）；缓存 SQLite。
- 测试：`tests/test_runtime.py` 用 fake transport 验证缓存/重试/超时；**未对真实模型服务实测**。

### 12.3 Episode / Batch

```python
EpisodeResult(...)                # to_dict()；字段见 data-schema.md
run_episode(scenario, agent, config, store, task_id, *, code_hash="",
            episode_index=0, seed_override=None) -> EpisodeResult
run_episode_async(同上)          # batch 使用
run_batch(scenarios, config, *, agent_factory=None, store=None, code_hash=None,
          max_tasks=None) -> BatchSummary
run_batch_async(同上)
build_tasks(scenarios, config) -> list[Task]
make_task_id(experiment_id, scenario, agent_id, repeat_index, config_hash) -> str
default_agent_factory(config) -> Callable[[Task], Agent|AsyncAgent]
BatchSummary(...).to_dict()
```

- `run_episode`：同步入口（内部 `asyncio.run`）；在已有事件循环中调用会抛 `RuntimeError`（用 async 版本）。
- `run_batch`：展开任务 → 跳过已记录 → 并发执行 → 结果 append → `BatchSummary`；异常隔离为 `agent_error`/`env_error`。
- `IO`：Trace/Results/manifest 写入；确定性：结果文件受并发影响的是顺序，不是内容。
- 调用方：`evaluation/cli.py`、`benchmarks/bench.py`、测试。

### 12.4 Trace / Metrics

```python
TraceRecorder(path, run_id, task_id, episode_id, *, fsync=True)
# .start(scenario=..., ruleset=..., code_hash=..., config=..., scenario_hash=...)
# .step(step=..., action=..., valid=..., error=..., reward=..., terminated=..., truncated=...,
#       termination_reason=..., state_hash_before=..., state_hash_after=...,
#       observation_text=..., score=..., latency_agent_ms=..., latency_env_ms=...,
#       raw_output=None, usage=None)
# .decision_metric(step=..., action_code=..., oracle_score=..., actual_score=..., regret=...)
# .end(status=..., outcome=..., steps=..., total_reward=..., blinds_cleared=...,
#      blind_scores=..., metrics=..., duration_ms=..., error=None)
read_trace(path) -> list[dict]
trace_summary(events) -> dict

summarize(results) -> dict
group_summaries(results, group_by=("agent_id",)) -> list[dict]
bootstrap_ci(values, statistic=statistics.fmean, n_resamples=1000, confidence=0.95, seed=20261117) -> dict
render_markdown_table(rows, columns=None) -> str
load_results(path) -> list[dict]
```

- `TraceRecorder`：`IO`，append-only；`fsync=True` 提供崩溃安全（性能文档有开销测量）。
- `summarize`：`success_rate/completion_rate/truncation_rate/timeout_rate/error_rate/mean_reward/median_reward/mean_blinds/mean_steps/mean_legality/mean_regret/optimality_rate/mean_final_money/p50/p95 latency/usage`；n<10 只作描述统计。
- `bootstrap_ci`：描述统计，不是显著性检验。

## 13. Scenario（`scenarios/`）

```python
Scenario.from_dict(data) -> Scenario; Scenario.to_dict() -> dict
validate_scenario(scenario, ruleset=VANILLA_SUBSET_V1, *, raw=None) -> None
validate_scenarios(scenarios, ruleset=...) -> None
scenario_from_dict(data, ruleset=...) -> Scenario      # 解析+校验
load_scenario(path, ruleset=...) -> Scenario
iter_scenarios(path, ruleset=...) -> Iterator[Scenario]
load_scenarios(paths, ruleset=...) -> list[Scenario]
scenario_hash(scenario) -> str
to_reset_spec(scenario) -> ResetSpec
write_scenario(path, scenario) -> None
```

- 校验失败抛 `InvalidActionError`（BAD_REQUEST/NOT_ALLOWED）或 `UnsupportedRuleError`；**fail fast**，不静默降级。
- `load_scenarios` 拒绝重复 `scenario_id`。

## 14. CLI

| 命令 | 作用 |
|---|---|
| `python -m bench rules` | 打印 Ruleset JSON + signature |
| `python -m bench demo` | O1 贪心跑一局（stdout JSON） |
| `python -m bench verify` | O1 vs 独立暴力枚举 |
| `python -m bench ev` | 弃牌 EV 抽样 |
| `python -m evaluation run` | 单 episode（`--scenarios --agent --experiment --out`） |
| `python -m evaluation batch` | 批量（`--repeats --max-concurrency --resume/--no-resume --retry-failed --no-oracle`） |
| `python -m evaluation report` | 读取 run 目录 → 分组指标 + Markdown 表 |
| `python -m benchmarks.bench` | 性能基准（`--quick`） |

## 15. 端到端示例

```python
import asyncio
from scenarios.loader import load_scenarios
from evaluation.config import ExperimentConfig
from evaluation.batch_runner import run_batch_async
from evaluation.agents import OracleGreedyAgent

scenarios = load_scenarios("scenarios/dev")
config = ExperimentConfig(
    experiment_id="example-batch",
    scenario_paths=("scenarios/dev",),
    agent_id="oracle-greedy",
    repeats=2,
    max_concurrency=4,
    output_dir="runs",
)
summary = asyncio.run(run_batch_async(scenarios, config))
print(summary.counts, summary.run_dir)
```
