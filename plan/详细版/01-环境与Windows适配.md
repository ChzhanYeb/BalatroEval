# 01 环境与 Windows 适配（v3.1）

> 标记：✅ 已验证 / ⏳ 待验证 / 📋 规划 / 🔁 已被取代；**规划项一律标 📋**。
> 版本 **v3.1-2026-11-22**（上版 v3.0-2026-11-13）；决策基线 [`07-真实游戏接入与终验.md`](07-真实游戏接入与终验.md)，冲突时以 07 为准。

> **v3.1 变更**：按 2026-11-22 实测校正过时事实（仓库路径 `dsh-agent-eval` → **BalatroEval**；25/25 → **124/124**；`bench/render.py` → **`bench/observation.py`**；W2 自定义子集 → **vanilla 1.0.1o 严格子集 v1**）；删去 W2/W4 时期“0.5h / 1h”计划流水与失效条目；真游戏侧保持 **📋 未安装、未验证**。

---

## 1. 已验证的工程事实（✅ 2026-11-22）

| 项 | 值 |
|---|---|
| 系统 / 仓库根 | Windows 11 原生（**无 WSL**，全程 PowerShell）；`C:\WorkData\005.Agent\BalatroEval`（目录名 = 项目名） |
| 解释器 | 系统 **Python 3.15**（≥3.11 即可）；`bench/` **stdlib-only**（`dependencies = []`） |
| 测试 | `python -m unittest discover -s tests` → **Ran 157 tests / OK**（≈5.5 s） |
| 规则版本 | **`vanilla_1.0.1o_subset_v2`**：Red Deck / White Stake / Ante 1；300/450/600；4 手 / 4 弃；手牌 8；5 Joker 槽；8 具名 Joker；等级 1 基础 Chips×Mult + 计分牌筛选；**经济（$4 起始、奖励 3/4/5、每手/每弃牌 $1、利息 cap $5、2 报价付费商店）**；确定性 RNG；快照/还原 → **IMPLEMENTED + TESTED**（`scenarios/RULES_VERSION`） |
| 对齐等级 | `fidelity_status: NOT_VERIFIED`、`alignment_level: L0`；A2/A3 真游戏实测 **0 行** |
| CLI | `python -m bench {rules,demo,verify,ev}`；`python -m evaluation {run,batch,report,rules}`；`python -m benchmarks.bench --quick` |
| 紧凑状态文本 | 由 **`bench/observation.py`** 提供（≤250 token，`test_render_is_compact`）；**`bench/render.py` 不存在，也不计划创建** |
| MCP | `bridge/server.py` 薄壳（复用 `bench.tools`，stdio，注册名 `balatro_bridge`）；**MCP SDK 只在 bridge 运行时需要**；`bridge/mcp-overlay.yml` 已生效于 `bench-local` |
| 复现性 / 会话 | 同 seed 两次整局 `GameState` 全等（含 `rng_state`）；headless 会话落 `%USERPROFILE%\.dsh`（`session-<uuid>.json` + `.v4.jsonl.zstd`） |
| 性能基线 | `verify(10)` 0.6 s；`demo` <1 s；`ev(K=50)` 23–25 s（≈2.4M 次计分） |

**边界**：以上只证 **L0 训练环境**本机可跑且**自洽**（157 项测试覆盖规则 / 经济 / 环境 / 场景 / runner / 并发 / 断点 / property / 性能 smoke）；**不证**与 vanilla 对齐，**不证**真游戏可用（§5，📋）。长线四支柱：③ 跨回合资源分配**已有载体（money/利息/商店）、缺指标与场景集**；② 长期构建 / ④ 失败恢复 / 长线指标**未覆盖**；单步 Local Regret 仍是唯一主指标层（`evaluation/` 已能算 play 决策的 regret / optimality）。

> **🔁** “25/25 通过 / `tests/test_w2_rules.py` 25 例”是 **W2 历史**（提交 `c65fb9b`）快照，已被 **157 项测试**取代，不得再当验收数。

---

## 2. 已验证的 Windows 坑（`docs/ops/windows-pitfalls.md`）

| 现象 | 根因 | 解法 |
|---|---|---|
| `python -m server` 打印启动日志后长时间不退出 | stdio MCP server 阻塞等客户端输入，属预期行为 | 无需处理，Ctrl+C 退出 |
| dsh 配置的 `!!js` 表达式里 `require('path')` 报 `ReferenceError` | cordis `!!js` 求值作用域剥离了 `require` 与 `import.meta` | 改用 `process.getBuiltinModule('node:path')` |
| Python 直读 `data/*.json` 报 `0xff` 解码错误 | `bench` 写 JSONL 用 UTF-8，PowerShell `>` / `Out-File` 重定向出的是 **UTF-16LE** | 读重定向产物用 `encoding="utf-16"`；证据文件由 Python 直接写 |

> 持续追加：新平台问题按「现象 / 根因 / 解法 / 验证」四段写进 pitfalls 文件；真游戏侧（注入失败、端口占用、存档不兼容）同样追加。

---

## 3. 待验证假设（⏳/📋）

| # | 假设（为何重要） | 怎么验证 | 状态 |
|---|---|---|---|
| A1 / A6 | 模型端点可用：本地 OpenAI 兼容端点（Ollama / LM Studio）与云端 API key（没有端点跑不了 A/B/C 组） | `curl <base>/v1/models`；云端发一次最小请求 | ⏳ |
| A2 | 4B 级模型在 4K 上下文、4 个工具下稳定产出合规工具调用（决定 schema 与是否约束解码） | 10 局 smoke 统计解析失败率 | ⏳ |
| A3 | 一个 episode 可放在**一次** dsh 调用里完成（决定 runner 是“一局一次”还是“一决策一次”） | 最小复现：`finished=true` 后 agent 是否停止 | ⏳ |
| A4 / A5 | trace 的工具参数/返回完整可读（归因依赖原文）；同 `--profile` 并发两局互不干扰 | 解析 trace 比对长度；并发 2 个 headless 查 session 目录 | ⏳ |
| **A7** | 真游戏四层依赖本机可达可启动：Steam 正版、Lovely 注入、Steamodded 加载、balatrobot 监听 `127.0.0.1:12346` 并返回 `health`/`gamestate`（决定能否做接入与 ATS 捕获；不可达则整轮降级） | 按 §5.3 冒烟，结果写入 `scenarios/v3/MANIFEST.json` | 📋 未验证 |
| **A8** | 同版本下 `save`/`load` 能回放决策点；Ante 1 三盲注单局 ≤15 min（决定变体与 12 局终验的时间可行性） | 捕获 1 局，回放 3 个变体并计时 2 局 | 📋 未验证 |

> **A7 是最高风险项**：不成立则外部效度主张必须写“未执行”。**A3 次之**：若一次 dsh 调用承载不了一局，就改成“一决策一次 + 外部状态机”，W4 需重排。

---

## 4. 环境现状与约束

### 4.1 训练环境（✅ 已就绪）

| 项 | 现状 |
|---|---|
| 引擎 + CLI | ✅ `python -m bench {rules,demo,verify,ev}`，stdlib-only |
| 评测基础设施 | ✅ `python -m evaluation {run,batch,report,rules}`：单 Episode Runner 同步/异步、Batch Runner 并发、Trace schema 2 JSONL、metrics 聚合 + bootstrap CI、manifest + code hash、断点续跑 / `--retry-failed` |
| 场景层 | ✅ `scenarios/`（`RULES_VERSION`、`rules_v2.json`、schema/loader/validator）+ `scenarios/dev/` **7 个自造开发场景**（含 1 个经济决策点，非 ATS）；**`scenarios/v3/` 60 决策点 📋 未创建** |
| Agent 侧 | ✅ oracle-greedy / random / HTTP Adapter（含缓存）；**HTTP Adapter 仅 fake transport 测试，真实模型端点未跑** ⏳；`bench-local` ✅，`bench-cloud` 📋 |
| 真游戏适配 / MCP 端到端 | 📋 未执行（`bridge/realgame.py` 不存在；MCP stdio 端到端未联调，仅验证 `build_server()`） |
| 结果落盘 | ✅ `runs/<experiment_id>/`（`results.jsonl`、`traces/*.jsonl`、manifest）；真游戏 trace `runs/w5-real/` 📋 不存在 |

### 4.2 已知环境约束（✅ 实测，训练环境侧）

- **8GB 内存、无独立 GPU**：本地模型为量化小模型（q4）、CPU/共享显存，**同一时刻只跑一个本地模型进程**，跑批必须串行。
- **MCP 走 stdio**：`stdout` 只放协议数据，**日志一律写 stderr**；Python 侧 `sys.stdout.reconfigure(encoding="utf-8")`。
- **路径含空格**：外部命令一律用参数数组，不拼字符串。
- **`__pycache__` ACL 受限**：用 `$env:PYTHONPYCACHEPREFIX = "$env:TEMP\balatroeval-pycache"` 绕行；重启会话后先查权限，别先怀疑代码。

---

## 5. 真实游戏环境（📋 **尚未安装、尚未验证**）

> 本节只写已决定的环境规划与约束，全部标 📋；执行后按「现象 / 根因 / 解法 / 验证」回填 §2 与本节。依据 [`07`](07-真实游戏接入与终验.md) §4。

### 5.1 四层依赖与版本锁定（A0）

| 层 | 作用 / 许可 | 版本 | 边界 |
|---|---|---|---|
| **Balatro**（Steam 正版） | 游戏本体 / 商业软件 | 基线 **1.0.1o** + `build_id` | 只在本机跑；**游戏文件/素材不入库、不再分发**（L8） |
| **Lovely**（`lovely-injector`） | Lua 运行注入 / MIT | 安装当日 release，**锁定** | 运行前置；只记版本，不分发 |
| **Steamodded**（`smods`） | mod 框架 / GPL-3.0 | 安装当日 release，**锁定** | 运行前置；**不复制/不分发其代码** |
| **balatrobot** | JSON-RPC 2.0 控制面（22 方法，`:12346`）/ MIT | 安装当日 release，**锁定** | 适配器唯一入口；**不修改其源码** |

**锁定规则**：同一批实验**不跨版本**，四层版本 + `build_id` + `deck` + `stake` 写入 `scenarios/v3/MANIFEST.json`；上游更新断链**不追新**，回退 MANIFEST 版本或整批重跑对齐；`gamestate` 字段漂移只按白名单映射（A1）。

### 5.2 已知约束（Windows + 图形依赖）

| 约束 | 事实 → 影响 |
|---|---|
| **图形依赖** | 需 Steam 客户端 + 桌面会话 + 游戏窗口；无头 / 服务 / CI 不可用，Steam 登录/购买/启动是人工步骤 → **真游戏只在本机跑**，CI 只跑训练环境与离线校验 |
| **单实例、单端口** | 控制面固定 `127.0.0.1:12346` → **不可并行**，同一时刻只跑一局，12 局终验必须串行 |
| **单局时长 / 资源** | 5–15 分钟/局（Ante 1 三盲注），上限 15 分钟；8GB 内存、无独显，游戏 + 本地模型同跑会挤爆 → 12 局 ≈ 4–6h，按 **4h 基线**排产，终验期间不跑模型 |
| **版本 / 存档脆弱** | 更新即可能断链（RPC 方法名、`gamestate` 字段漂移）；`.jkr` 与版本绑定、跨版本可能 load 失败 → 锁版本；回放失败变体进 `rejected`，不硬凑 |

### 5.3 安装与健康检查（📋 W3 第一天，3h 基线）

```text
[安装] Balatro（Steam 正版）→ Lovely → Steamodded → balatrobot（每层记录版本）
[启动] Steam 启动 → 主菜单 → 确认 Lovely 注入 + Steamodded 加载 → 启动 balatrobot（:12346）
[冒烟] health 正常 → rpc.discover 方法表可见（不硬编码过时方法名）→ gamestate 返回完整状态 JSON
[锁定] scenarios/v3/MANIFEST.json（四层版本 + build_id + deck + stake + 时间戳）
[降级] 停 balatrobot → 适配器返回 TIMEOUT/ADAPTER_ERROR（规划），不得静默挂起
```

**三步冒烟任一失败即 A7 不成立**，按 §5.4 降级、不进入捕获；setup 按 **3h 基线**（`07` §6.1 记 3–5h），超 5h 立即降级。

### 5.4 失败降级（📋，不可越线）

| 情形 | 处理 |
|---|---|
| 装不上 / 游戏无法启动 / 无图形会话 | 停止依赖真游戏的任务（W3 相关项、W5 任务 3）；**不得**把终验标为通过 |
| 部分可用（能捕获、不能跑 Agent 终验） | 只做 A2/A4 捕获回放；`fidelity_status: CAPTURE_REPLAY_ONLY`，报告声明“终验未执行” |
| 完全不可达 | `fidelity_status: NOT_VERIFIED`；训练集**不得**退回纯引擎生成；可用第三方算分器抽检作辅助 |
| `save`/`load` 失败或版本链断裂 | 变体进 `rejected` 并写原因；锚点仍可入集；回退 MANIFEST 版本重跑对齐，仍失败则降级 |

> **本机限定**：12 局终验只在本机跑，不进 CI、不并行、不做远程复现；第三方只能复现训练环境与离线重放（`runs/w5-real/` 提供全量 trace 与版本清单）。

---

## 6. Windows 通用约定（📋 后续代码必须遵守）

```python
import subprocess
CREATE_NO_WINDOW = 0x08000000

def run_ps(script: str, timeout: int = 60):
    full = "$ErrorActionPreference='Stop'; chcp 65001 > $null; " + script
    p = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", full],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, creationflags=CREATE_NO_WINDOW)
    return p.returncode, p.stdout, p.stderr
# 杀进程树：subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], creationflags=CREATE_NO_WINDOW)
```

七类常见问题：①中文乱码 → `chcp 65001` + `encoding="utf-8"`；②报错但 `returncode==0` → `try/catch` + 显式 `exit 1`，同时看 stderr；③残留子进程 → `taskkill /T /F`；④路径空格 → 参数数组；⑤CRLF → `line.rstrip("\r\n")`；⑥半行 JSON → 只处理 `}` 结尾行并重试 3 次；⑦长路径 → 挂 `C:\WorkData\...` 短路径。遇到就补进 pitfalls 文件。

### 6.1 网络环境事实（✅ 实测）

- `github.com` 网页直连部分时段被拒（`fetch failed`，非 404）→ 无法网页核对仓库，GitHub 直接 `pip install` 可能失败；改用 `api.github.com` / `raw.githubusercontent.com`，Python 依赖一律走 PyPI。
- Science / ACM DL 等站点本机不可达 → 只用 arXiv/ACL/OpenReview 核对；不可达来源定性引用，不引数字。
- **📋 四层依赖**：Lovely 与 balatrobot 走 GitHub Releases，直连不稳直接影响安装；预案是 `api.github.com` 拉元数据 + 镜像/代理下载。下载失败不阻塞对齐清单，但阻塞 A7 判定；“可访问”结论须注明是网页、API 还是镜像。

---

## 7. 明确不在本文件范围内的

- **CI / 无头环境运行真实游戏**（图形依赖 + 单实例端口 + 版本脆弱，§5.2）；**游戏本体的自动化安装/破解/分发**（人工步骤，文件不入库，L8）
- **第二份规则实现**（真游戏侧只读 `gamestate` 与动作结果，不写规则；`07` §2）
- WSL / Docker / 远程服务器；GPU 驱动与 CUDA 配置（本项目不跑训练）；12 局终验的统计方法（`05-实验与报告.md`）与失败归因标签（`04-失败归因器.md`）

---

## 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-11-13 | v2.2（历史） | W1/W2 事实登记；UTF-16LE 重定向坑、ACL 权限坑、性能基线；曾写“真实游戏不采用” |
| 2026-11-13 | v3.0（🔁 部分被 v3.1 取代） | 改为 §5 真游戏环境规划：四层依赖 + A0 版本锁定 + 图形/端口/版本脆弱约束 + 健康检查 + 失败降级；新增 A7/A8 |
| 2026-11-22 | **v3.1** | ①实测校正：路径 → **BalatroEval**、25/25 → **124/124**、`render.py` → **`observation.py`**、W2 子集 → **`vanilla_1.0.1o_subset_v1`**；②删“W2 前 0.5h / W4 前 1h”计划表，改为现状表；③W1“placeholder 工具 + 链路已通”🔁 改为 `bench.tools` 薄壳 + MCP 端到端 📋；④真游戏侧保持 📋；⑤篇幅压缩 |
| 2026-11-22 | **v3.2** | 经济子集 v2：规则 → `vanilla_1.0.1o_subset_v2`、测试 **157**、场景 7 个（含 `dev-shop-buy-or-bank`）、Obs/Snapshot schema 2、CLI 工具 7 个；对齐等级不变（仍 L0，经济 5 条口径 `unverified`） |
