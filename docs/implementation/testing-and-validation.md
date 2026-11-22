# 测试与验证

> 本文件记录**实际执行过的**测试与结果；未执行的命令不写成“通过”。
> 时间：2026-11-17 ｜ 环境：Windows 11 / Python 3.15.2 / stdlib-only。

## 1. 如何运行

```powershell
Set-Location C:\WorkData\005.Agent\dsh-agent-eval

# 全量测试
python -m unittest discover -s tests

# 单独模块（示例）
python -m unittest tests.test_w2_rules -v
python -m unittest tests.test_runtime -v

# 语法/导入检查（本机 pycache ACL 受限，需把 pycache 指到可写目录）
$env:PYTHONPYCACHEPREFIX = "$env:TEMP\balatroeval-pycache"
python -m compileall -q bench evaluation scenarios benchmarks bridge/server.py

# 规则/引擎自检
python -m bench rules
python -m bench verify --samples 10 --seed 20261112
python -m bench demo --seed 20261117 --max-steps 50

# 评测链路自检
python -m evaluation batch --scenarios scenarios/dev --agent oracle-greedy --experiment smoke --out runs --no-oracle
python -m evaluation report --run-dir runs/smoke
```

## 2. 测试清单（**124** 项，全部通过）

| 文件 | 用例数 | 覆盖 | 证明什么 / 不证明什么 |
|---|---:|---|---|
| `tests/test_w2_rules.py` | 40 | 12 牌型识别、边界（4K kicker、wheel/Broadway、隐藏牌型）、基础分表、计分牌筛选、golden（7h7d=48；Joker 顺序 288/192；三条+Joker 810；Boss two-pair 744）、8 Joker 条件、contains、无副作用 | 证明**本子集规则实现自洽**；不证明与真游戏一致 |
| `tests/test_environment.py` | 30 | `new_game` 常量、盲注推进、胜负、弃牌、非法动作错误码、快照/还原/哈希、动作 canonical、Environment 接口、场景动作限制、max_steps 截断、工具层 envelope、bridge 无 SDK 可导入 | 证明环境/工具接口与状态语义；不证明真实 MCP 对话 |
| `tests/test_scenarios.py` | 17 | dev 场景加载、JSONL、rules_version 不匹配、Boss 效果拒绝、未知扩展、real_capture 无 capture_id、重复牌、未知字段、动作种类约束 | 证明场景校验 fail-fast |
| `tests/test_runtime.py` | 16 | golden episode（48/regret 0/optimality 1）、discard 决策点、agent_error 隔离、非法动作上限、确定性重放、batch 写入、resume、retry-failed、失败隔离、并发隔离、metrics、trace、HTTP fake transport（缓存/重试/超时） | 证明 runner/trace/metrics/adapter 可用；HTTP 仅 fake transport |
| `tests/test_properties.py` | 9 | 52 张守恒（20 seeds×30 步）、`score=floor(chips×mult)`、trace 末条一致、无副作用、环境隔离、非法动作不改状态、436 动作 code 唯一、动作序列重放同 hash、手牌上限 | 证明不变量；不证明数值与真游戏一致 |
| `tests/test_rules_declaration.py` | 9 | `Ruleset` ↔ JSON 镜像 ↔ `RULES_VERSION`、300/450/600、4/4/8/5、基础分表、8 Joker、excluded 列表、扩展签名 | 证明**声明与代码不漂移** |
| `tests/test_performance_smoke.py` | 3 | 计分 500 次 <2s、env 100 次 reset+step <10s、O1 单次 <0.5s | 防止无意数量级退化；不是基准 |

### 2.1 实测输出（原文摘录）

```text
$ python -m unittest discover -s tests
----------------------------------------------------------------------
Ran 124 tests in 5.5s

OK
```

```text
$ python -m bench verify --samples 10 --seed 20261112
{ "seed": 20261112, "samples": 10, "passed": true,
  "checks": [ {"case":1,"oracle":120,"brute_force":120,"match":true,"candidates":218}, ... ] }
```

```text
$ python -m evaluation run --scenarios scenarios/dev/play-pair-7h7d.json --agent oracle-greedy --experiment cli-pair --out runs
counts: {"completed": 1, "skipped": 0, "total": 1}
summary: mean_reward=48.0, mean_regret=0.0, optimality_rate=1.0, legality_rate=1.0
```

## 3. Golden Tests（数值 + 中间过程）

| 用例 | 牌 | 期望 | 依据 |
|---|---|---|---|
| Pair 等级 1 | 7♥ 7♦ | base 10×2；计分牌 7+7=14；chips 24；**48** | `docs/balatro/rules.md` §5 |
| Joker（+4M）→ The Duo（×2M） | 7♥ 7♦ | (2+4)×2=12 → 24×12 = **288** | 槽位顺序 |
| The Duo → Joker | 7♥ 7♦ | (2×2+4)=8 → 24×8 = **192** | 顺序敏感 |
| 三条 8 + Joker + Jolly | 8♠8♥8♦ | (30+24)=54；(3+4+8)=15 → **810** | contains pair |
| Two Pair AA KK + Joker + Duo | A♠A♥K♦K♣ | (20+42)=62；mult 12 → **744** | Boss 决策点场景 |
| High Card 5 张 | A K Q J 9 | 只计 A：5+11=16 → **16** | 计分牌筛选 |
| Four of a Kind + kicker | 8♠8♥8♦8♣4♠ | 只计 4 张 8：60+32=92；×7 = **644** | kicker 不计 |

> 金样测试同时断言 `hand_type`、`base_chips/base_mult`、`scoring_card_ids`、`chips/mult`、`final_score` 与 trace 阶段，不只断言最终数字。

## 4. 边界测试（均已覆盖）

- 三条“包含”对子；四条**不**包含两对；五条**不**包含葫芦；同花葫芦/同花五条包含关系；
- 同花顺优先于同花/顺子；四条优先于葫芦/两对；
- A 低（A2345）与 A 高（10JQKA）；K-A-2-3-4 非法；
- Royal Flush 仅标记 `is_royal_flush`，牌型仍为 Straight Flush；
- 隐藏牌型（五条/同花葫芦/同花五条）代码路径（标准 52 张不可达，用重复牌分类测试）；
- 高牌 5 张只计 1 张；四条带 kicker；对子带 3 张 kicker；
- 非法动作：未知/重复 ID、0 张、6 张、done 后动作、无弃牌、无手数、商店未启用；
- 资源归零、最后一手同时达标（达标优先于判负）、max_steps 截断。

## 5. Property-based（等价性质，无 Hypothesis 依赖）

用固定循环 + 20 个 seed 实现：
- `hand+deck+discard == 52` 在随机 playout 中恒成立；
- `final_score == floor(chips×mult)` 且 ≤ 乘积；
- 转移函数不修改入参状态；
- 两个 Environment 交错推进互不影响；
- 非法动作后 state_hash 不变；
- 8 张手牌 436 个 action code 唯一；
- 同 seed + 同动作序列 ⇒ 同 state_hash。

## 6. 集成 / 并发 / 可靠性

| 项 | 覆盖 | 结果 |
|---|---|---|
| Environment ↔ Rules | `test_environment` 全链路 | ✅ |
| Environment ↔ Oracle | O1 与独立枚举 10/10 | ✅（只证搜索路径一致） |
| Scenario Loader ↔ Environment | dev 场景 6 个全部可 reset | ✅ |
| Episode Runner ↔ Trace | step/start/end schema、hash、decision_metric | ✅ |
| Batch ↔ 并发隔离 | 4 并发任务 trace 的 scenario_id/task_id 对应正确 | ✅ |
| 失败隔离 | 一个 task agent_error，另一个 completed | ✅ |
| 断点续跑 | 第二次 run skipped=全部，results 不新增 | ✅ |
| retry-failed | 只重跑失败项 | ✅ |
| Trace 完整性 | JSONL 可逐行解析，end 行含摘要 | ✅ |
| 确定性 | 同配置重放 action/reward/state_hash 完全一致 | ✅ |

## 7. 新规则替换旧测试的说明（合规）

旧 `tests/test_w2_rules.py` 断言 L0 自定义公式（如 Pair 7h7d = 28、`HAND_MULT` 表、3 槽位）。本次 W3 规则升级明确要求“牌型基础 Chips×Mult + 计分牌筛选 + 300/450/600 + 4/4 + 5 槽 + 8 具名 Joker”（见 `docs/balatro/engine-gap.md`、`plan/01-每周任务.md` W3）。旧断言对应的是被替代的规则版本，因此重写为 vanilla 子集断言，并在文件头记录依据；这不是“为了通过测试而修改期望值”，而是规则版本升级的同步。

## 8. 未验证 / 未覆盖（不得写成已通过）

| 项 | 现状 | 影响 | 建议 |
|---|---|---|---|
| A2 单步分数与真游戏一致 | **0 行实测** | 分数绝对值可能不同（取整/contains/触发时机） | W3 真游戏捕获 + 逐局面 diff |
| A3 规则子集对齐 | 未签核 | 合法动作集/资源语义未对拍 | `docs/engine-fidelity.md` A 表 |
| 最终取整方式 | Wiki 未明写；按 floor 候选 | 某些小数倍率局面可能差 1 | A2 多组 ×1.5 局面 |
| contains 4K/5K vs Pair/Three | structural-superset 口径 | Jolly/Sly/The Duo/Zany 等触发范围可能偏大/偏小 | 真游戏实测条件边界 |
| 跨盲注手牌/牌堆处理 | 本实现自定义（剩余手牌入弃牌堆、补满） | 与 vanilla 可能不同 | A1/A4 捕获 |
| Boss 效果 | 未实现（仅 600 分） | 不能用于 A3 场景 | 后续单独实现 + 金样 |
| 旧日志 `bench/logging.py` | LEGACY，未接入新链路 | 误用会写旧 schema | 新代码用 `evaluation.trace` |
| 真实模型服务 | 未实测（仅 fake transport） | HTTP Adapter 兼容性未知 | 用真实端点做一次 smoke |
| MCP stdio 端到端 | 仅验证 `build_server()` + 工具注册（bridge venv） | 未做真实 dsh 会话 | W4 工具层联调 |

## 9. 验收命令与预期

| 命令 | 预期 | 实测 |
|---|---|---|
| `python -m unittest discover -s tests` | 124 tests OK | ✅ Ran 124 / OK |
| `python -m bench verify --samples 10` | passed=true，每例 218 | ✅ |
| `python -m bench demo --seed 20261117` | 正常 JSON，phase=done | ✅ loss / 4 步 / blind_scores [200] |
| `python -m evaluation batch … --no-oracle` | counts 全 completed/truncated，无异常 | ✅ |
| `python -m compileall -q …` | 无输出/退出 0 | ✅（需 `PYTHONPYCACHEPREFIX`） |
| `python -m benchmarks.bench --quick` | 打印 JSON | ✅（结果见 performance.md） |
