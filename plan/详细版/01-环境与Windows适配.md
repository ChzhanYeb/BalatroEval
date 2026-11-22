# 01 环境与 Windows 适配（v3.0）

> 本文件写**环境事实**（✅ 已验证）、**待验证假设**（⏳）与**已决定的环境规划**（📋）。
> 标记：✅ 已验证 / ⏳ 待验证 / 📋 规划 / 🔁 已被取代。**规划项一律标 📋，不得写成已就绪。**
> 版本：**v3.0-2026-11-13**（上一版 v2.2-2026-11-13）；决策基线：[`07-真实游戏接入与终验.md`](07-真实游戏接入与终验.md)（与本文冲突时以 07 为准）。

> **v3.0 改了什么**：①删除旧结论“真实 Balatro + Lovely/Steamodded/balatrobot **本项目不采用**”；②新增 **§5 真实游戏环境（规划）**：四层依赖、版本锁定、Windows 图形依赖、不可 CI/不可并行、健康检查、失败降级；③新增假设 **A7（真游戏可达性）** 与 **A8（`save`/`load` 回放与单局时长）**；④W1/W2 已验证事实**保留不动**（不得改写）；⑤明确**真游戏终验只在本机跑**，CI 只跑训练环境与离线校验。

---

## 1. 已验证的工程事实（W1 产出）

| 项 | 值 | 证据 |
|---|---|---|
| 操作系统 | Windows 11 原生，**无 WSL** | 全程 PowerShell/CMD |
| 项目根 | `C:\WorkData\005.Agent\dsh-agent-eval` | — |
| Python 解释器 | `.venv\Scripts\python.exe`（3.15.2） | `mcp-overlay.yml` 的 `command` |
| DSH home | `C:\Users\admin\.dsh` | 会话文件位置 |
| CLI 用法 | `dsh --profile <name> [--patch <file>] "task"` | 无 `dsh run`；**`--profile` 不能重复出现** |
| MCP SDK | `mcp==2.3.0` | `.venv` 内 |
| MCP Server | `bridge/server.py`，注册名 `balatro_bridge`，`transport: stdio` | `server.py` |
| MCP 客户端配置 | `bridge/mcp-overlay.yml`（`insert` 一个 `@deepseek-ai/dsh-mcp-client` 条目，`serverName: balatro`） | 已生效于 profile `bench-local` |
| 工具当前状态 | 仅 `get_state()`，返回**硬编码 placeholder** | `server.py` |
| 会话记录 | 每次 headless 运行在 `%USERPROFILE%\.dsh` 下落 `session-<uuid>.json` 与 `session-<uuid>.v4.jsonl.zstd` | `evidence/W1/` |

**W1 已通过的链路**：initialize → tools/list → tools/call → 结果回传 → Agent 正确复述字段 → trace 落盘。

### 1.1 W2 验证到的环境事实（2026-11-13）

| 项 | 值 | 证据 |
|---|---|---|
| 引擎运行方式 | 系统 Python 3.15.2 直接跑 `python -m bench {demo,verify,ev}`，**无第三方依赖**（stdlib only） | `pyproject.toml` 的 `dependencies = []`；实测三命令可跑 |
| 测试命令 | `python -m unittest discover -s tests -v` → 25/25 通过 | `tests/test_w2_rules.py` |
| 复现性 | 同 seed 两次整局 `GameState` 完全相等（含 `rng_state`） | `TestReproducibility` |
| 日志编码 | `bench` 写出的 JSONL 是 **UTF-8**（无 BOM）；PowerShell `>` / `Out-File` 默认重定向出的 `data/*.json` 是 **UTF-16LE**，Python 直读会报 `0xff` 解码错误 | 实测（`data/w2-demo-summary-local-20261112.json` 需 `encoding="utf-16"`） |
| 性能基线 | `verify(10)` 0.6 s；`demo(13 步)` 0.7 s；`ev(K=50)` 约 23–25 s（218 动作 × 50 样本 × 218 组合 ≈ 2.4M 次计分） | 实测 |
| 环境注意 | 本机工作区曾出现 Windows 文件权限导致 DSH 无法写入（`WRITE_OWNER` 缺失），已用 ACL 诊断修复；重启会话后复现时先查权限，不要先怀疑代码 | 会话记录 |

> **v3.0 口径**：以上只证明“**L0 训练环境**可在本机跑通”，**不证明**与 vanilla 对齐，也不证明真游戏可用（见 §5，📋 未验证）。

### 1.2 v3.0 目标环境一览（真游戏侧 📋 全部未验证，详见 §4/§5）

| 环境 | 构成 | 状态 | 用途 |
|---|---|---|---|
| 训练/开发环境（ATE） | `bench/`（Python 3.15.2，stdlib only）+ bridge MCP + dsh headless | ✅ 可运行（当前 **L0**，对齐改造 📋 W3） | 对齐改造（W3 → **L2**）后的批量实验（W5，90 局） |
| 真实游戏环境（RGFT） | Balatro 1.0.1o + Lovely + Steamodded + balatrobot（JSON-RPC 2.0 @ `127.0.0.1:12346`） | 📋 未安装、未验证 | 捕获 60 决策点（W3）+ 12 局终验（W5 → **L3**） |

---

## 2. 已验证的两个坑（来自 `docs/windows-pitfalls.md`）

| 现象 | 根因 | 解法 |
|---|---|---|
| `python -m server` 打印启动日志后长时间不退出 | stdio MCP server 阻塞等待客户端输入，属预期行为 | 无需处理，Ctrl+C 退出 |
| dsh 配置的 `!!js` 表达式里 `require('path')` 报 `ReferenceError` | cordis `!!js` 求值作用域剥离了 `require` 与 `import.meta` | 改用 `process.getBuiltinModule('node:path')` |

> 这两条要持续追加。W2 起每遇到一个平台问题，按「现象 / 根因 / 解法 / 验证」四段追加到 `docs/windows-pitfalls.md`；W3 起真游戏侧问题（注入失败、端口占用、存档不兼容）同样追加。

---

## 3. 待验证假设（⏳/📋；v3.0 口径）

| # | 假设 | 为什么重要 | 如何验证 | 状态 |
|---|---|---|---|---|
| A1 | 本地模型端点可用（OpenAI 兼容，如 Ollama / LM Studio） | 没有本地模型就无法跑 A/B 组 | `curl <base>/v1/models` 返回模型列表 | ⏳ |
| A2 | 4B 级模型在 4K 上下文、4 个工具下能稳定产出合规工具调用 | 决定工具 schema 大小与是否要约束解码 | 跑 10 局 smoke，统计解析失败率 | ⏳ |
| A3 | 一个 episode 可以放在**一次** dsh 调用里完成（agent 自循环调用工具直到终局） | 决定 runner 是“一局一次”还是“一决策一次” | 写最小复现：工具返回 `finished=true` 后 agent 是否停止 | ⏳ |
| A4 | 会话 trace 中的工具参数与返回完整可读（不被截断） | 归因依赖原始参数 | 解析 W1 trace，比较长度与原文 | ⏳ |
| A5 | 相同 `--profile` 两次运行互不干扰（会话隔离） | 批量跑批需要隔离 | 并发 2 个 headless，检查 session 目录 | ⏳ |
| A6 | 云端 API key 可用且计费可估 | C 组实验 | 发一次最小请求 | ⏳ |
| **A7**（v3.0 新增） | **真游戏四层依赖在本机可达且可启动**：Steam 正版可用、能注入 Lovely、能加载 Steamodded、balatrobot 能监听 `127.0.0.1:12346` 并返回 `health`/`gamestate` | 决定 W3 能否做真游戏接入与 ATS 捕获；不可达则整轮降级（`CAPTURE_REPLAY_ONLY` / `NOT_VERIFIED`），**不得**声称已对齐或已终验 | W3 第一天按 §5.3 的 6 步健康检查冒烟，结果写入 `scenarios/v3/MANIFEST.json` | 📋 未验证 |
| **A8**（v3.0 新增） | 同一版本下 `save`/`load` 能回放决策点；Ante 1 三盲注能在单局 15 分钟内结束 | 决定反事实变体与 12 局终验的时间可行性 | 捕获 1 局，回放 3 个变体并计时 2 局 | 📋 未验证 |

> **A7 是 v3.0 的最高风险项**：它一旦不成立，v3.0 的外部效度主张必须改成“未执行”。**A3 次之**：如果一次 dsh 调用无法承载一局完整交互，就必须改成“一决策一次调用 + 外部状态机”，runner 复杂度翻倍，**W4 需要重排**（该工作已在 W4 任务 1，受影响可控）。

---

## 4. 环境搭建计划

> **工时归属（v3.0）**：§4.1（0.5h）已随 W2 发生、不另计；§4.2（1h，训练环境）**并入 W4 任务 1**；§4.3（3h 基线，真实游戏）**计入 W3 任务 1**。均不额外增加预算。

### 4.1 W2 前（0.5h，✅ 历史）

| 任务 | 命令/动作 | 完成标准 | 状态（2026-11-13） |
|---|---|---|---|
| 确认 Python 依赖 | `.venv\Scripts\python.exe -m pip list` | 有 `mcp`，无需额外包即可跑引擎 | ✅ 已确认；引擎实际用系统 Python 3.15.2 亦可跑 |
| 引擎目录骨架 | 建 `bench/`（`__init__.py`） | 能 `python -c "import bench"` | ✅ 已建（11 个模块） |
| 确认本地模型 | 见 A1 | 端点可达 | ⏳ 未确认（W4 前置） |

### 4.2 W4 前（1h，📋 训练环境侧）

| 任务 | 说明 | 状态 |
|---|---|---|
| 两个 profile | `bench-local`（本地模型）、`bench-cloud`（云端），只差 provider 配置 | 📋 |
| 跑批入口 | 一条命令跑 30 场景主表子集 × 3 组 = 90 局（命令名 📋 待定，形如 `python -m bench.run --suite <main> --model local`） | 📋 |
| 会话归档 | 每局把 `%USERPROFILE%\.dsh` 下对应 session 复制到 `runs/<run_id>/ep<NNN>/` | 📋 |
| 工具层 `get_state` | 依赖 `bench/render.py`（≤250 token 紧凑文本，W2 未实现，结转 W4） | 📋 |

### 4.3 真实游戏环境（W3 前，3h 基线，📋 未执行）

| 任务 | 说明 | 完成标准 |
|---|---|---|
| 安装四层依赖 | Balatro（Steam 正版）→ Lovely → Steamodded → balatrobot；步骤以官方 README 为准，**版本安装当日锁定** | 四层版本齐全并写入 `MANIFEST.json`（A0） |
| 启动与健康检查 | 见 §5.3 六步冒烟（`health` / `rpc.discover` / `gamestate`） | 三步全通，`gamestate` 返回完整状态 |
| 端口与单实例确认 | `127.0.0.1:12346` 被 balatrobot 独占 | 无第二个实例/端口冲突 |
| 失败降级验证 | 人为停止 balatrobot，确认适配器返回统一错误码（`TIMEOUT`/`ADAPTER_ERROR`）而不是静默挂起 | 错误码可复现 |
| 版本清单 | `scenarios/v3/MANIFEST.json` | 含 `game_version`/`build_id`/`deck`/`stake`/`lovely_version`/`smods_version`/`balatrobot_version`/`adapter_version` |

> **工时口径**：`07` §6.1 记录真实游戏 setup 为 **3–5h（含 W3）**；本计划按 **3h 基线**排产。超 3h 从 W3 任务的“对齐台账 2h”里挤（台账可后置到 W4 首日），**超 5h 立即降级**，不挪用对齐与捕获的时间。

### 4.4 已知的环境约束（✅ 实测，训练环境侧）

- **8GB 内存、无独立 GPU**：本地模型以量化小模型（q4）与 CPU/共享显存运行，系统占用已接近上限，**同一时刻只跑一个本地模型进程**；跑批必须串行。
- **MCP 走 stdio**：`stdout` 只能有协议数据，**所有日志必须写 stderr**；Python 侧需 `sys.stdout.reconfigure(encoding="utf-8")`。
- **路径含空格**：调用外部命令一律用参数数组，不用字符串拼接。

---

## 5. 真实游戏环境（📋 规划，v3.0 新增；**尚未安装、尚未验证**）

> 本节只写**已决定的环境规划与已知约束**。所有内容标 📋；执行后按「现象 / 根因 / 解法 / 验证」回填 §2 与本节。决策依据见 [`07`](07-真实游戏接入与终验.md) §4。

### 5.1 四层依赖与版本锁定

| 层 | 作用 | 许可 | 版本口径 | 本项目用法（边界） |
|---|---|---|---|---|
| **Balatro**（Steam 正版） | 真游戏本体 | 商业软件 | 记录基线 **1.0.1o**（另记 `build_id`） | 只在本机运行；**游戏文件/素材不入库、不再分发**（L8） |
| **Lovely**（`lovely-injector`） | Lua 运行时注入 | MIT | 安装当日 release，**锁定** | 运行前置；只记录版本，不分发 |
| **Steamodded**（`smods`） | mod 框架 | GPL-3.0 | 安装当日 release，**锁定** | 运行前置；**不复制/不分发其代码** |
| **balatrobot** | JSON-RPC 2.0 控制面（22 方法，`:12346`） | MIT | 安装当日 release，**锁定** | 适配器唯一入口；**不修改其源码** |

**版本锁定规则（A0）**：
1. 同一批实验**不跨版本**；四层版本 + `build_id` + `deck` + `stake` 全部写入 `scenarios/v3/MANIFEST.json`；
2. 游戏/mod 更新导致断链时 **不追新**，先回退到 MANIFEST 记录的版本，或整批重跑对齐；
3. `gamestate` 字段漂移时只按白名单映射，新增字段先出 diff 报告再决定是否纳入（A1）。

### 5.2 已知约束（Windows + 图形依赖）

| 约束 | 事实 | 影响 |
|---|---|---|
| **图形依赖** | 需要 Steam 客户端 + 桌面会话 + 游戏窗口；无头 / 服务 / CI 环境不可用 | **真游戏只在本机跑**；CI 只跑训练环境与离线校验（对齐/重放） |
| **单实例、单端口** | 控制面固定 `127.0.0.1:12346` | **不可并行**；同一时刻只跑一局；12 局终验必须串行 |
| **单局时长** | 5–15 分钟/局（Ante 1 三盲注）；**单局上限 15 分钟** | 12 局 ≈ 4–6h（含重连/失败重跑）；W5 按 **4h 基线**排产，超支先动 W5 机动 1h |
| **版本脆弱** | 游戏/注入链更新即可能断链（RPC 方法名、`gamestate` 字段漂移） | 锁定版本、记录 build、不自动更新；断链即重跑对齐或降级 |
| **存档兼容** | `.jkr` 存档与版本绑定，`save`/`load` 跨版本可能失败 | 变体回放失败 → 该变体进 `rejected`，**不硬凑** |
| **资源竞争** | 8GB 内存、无独显：游戏 + 本地模型同时跑会挤爆 | 终验与本地模型跑批**不同时**；12 局终验期间只跑真游戏 |
| **人工步骤** | Steam 登录/购买/启动属人工步骤 | 不做自动化安装脚本；人工步骤记录到 `evidence/W3/` |

### 5.3 安装与健康检查（📋 W3 第一天，3h 基线）

```text
[安装] Balatro（Steam）→ Lovely → Steamodded → balatrobot（每层记录版本）
[启动] Steam 启动游戏 → 进主菜单 → 确认 Lovely 注入 + Steamodded 加载 → 启动 balatrobot（:12346）
[冒烟] 1) health        → 返回正常
       2) rpc.discover  → 方法表可见（不硬编码过时方法名）
       3) gamestate     → 返回完整状态 JSON（手牌/牌堆/Joker/盲注/目标/资源/阶段）
[锁定] 写 scenarios/v3/MANIFEST.json（A0：四层版本 + build_id + deck + stake + 时间戳）
[降级演练] 停 balatrobot → 适配器应返回 TIMEOUT/ADAPTER_ERROR，不得静默挂起
```

**三步冒烟任一失败即视为 A7 不成立**，按 §5.4 降级，不进入捕获。

### 5.4 失败降级（📋，不可越线）

| 情形 | 处理 |
|---|---|
| 四层中任一层装不上 / 游戏无法启动 / 无图形会话 | 停止真游戏相关任务（W3 任务 1/2/5 中依赖真游戏的部分、W5 任务 3）；**不得**把终验标为通过 |
| 部分可用（只能捕获、不能跑 Agent 终验） | 只做 A2/A4 捕获回放；`fidelity_status: CAPTURE_REPLAY_ONLY`，报告/README 声明“终验未执行” |
| 完全不可达 | `fidelity_status: NOT_VERIFIED`；训练集**不得**退回纯引擎生成；仍可用第三方算分器抽检做辅助证据 |
| `save`/`load` 回放失败 | 该变体进 `rejected` 清单并写原因；锚点仍可入集；报告写“变体覆盖不足” |
| 版本链断裂 | 回退 MANIFEST 记录版本重跑对齐；仍失败则降级 |
| 安装/冒烟超 5h | 立即降级，**不硬撑**（`07` §9） |

> **本机限定**：真游戏终验（12 局）**只在本机跑**，不进 CI、不做并行、不做远程复现；第三方复现只能复现训练环境与离线重放部分（`runs/w5-real/` 提供全量 trace 与版本清单）。

---

## 6. Windows 通用约定（📋 后续代码必须遵守）

```python
# 统一外部调用：显式参数、UTF-8、无窗口
import subprocess
CREATE_NO_WINDOW = 0x08000000

def run_ps(script: str, timeout: int = 60):
    full = "$ErrorActionPreference='Stop'; chcp 65001 > $null; " + script
    p = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", full],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout,
                       creationflags=CREATE_NO_WINDOW)
    return p.returncode, p.stdout, p.stderr

def kill_tree(pid: int):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True, creationflags=CREATE_NO_WINDOW)
```

七类常见问题与对策（遇到就补进 pitfalls 文件）：

| # | 问题 | 现象 | 对策 |
|---|---|---|---|
| 1 | 控制台编码 | 中文乱码 | `chcp 65001` + 子进程 `encoding="utf-8"` |
| 2 | 退出码语义 | 报错但 `returncode==0` | 脚本内 `try/catch` + 显式 `exit 1`；同时看 stderr |
| 3 | 进程树残留 | kill 父进程后 Python 子进程仍在 | `taskkill /T /F` |
| 4 | 路径空格/反斜杠 | 命令拼接被截断 | 参数数组，不拼字符串 |
| 5 | CRLF | JSON 行尾多 `\r` 解析失败 | `line.rstrip("\r\n")` |
| 6 | 文件锁 | 读到半行 JSON | 只处理以 `}` 结尾的行；重试 3 次 |
| 7 | 长路径 | >260 字符创建失败 | 目录挂在 `C:\WorkData\...` 短路径下 |

### 6.1 网络环境事实（v2.1 新增，✅ 实测）

| 现象 | 影响 | 对策 |
|---|---|---|
| `github.com` 网页直连在部分时段被拒（`fetch failed`，非 404） | 无法用网页核对仓库；从 GitHub 直接 `pip install` 可能失败 | 改用 `api.github.com` 或 `raw.githubusercontent.com`；Python 依赖一律走 PyPI，不装 git 依赖 |
| Science / ACM DL 等学术站点在本机不可达 | 论文数值无法逐页核对 | 只用 arXiv/ACL/OpenReview 核对；不可达来源一律定性引用，不引数字 |

> **v3.0 补充（📋 预期）**：四层依赖的下载来源不同（Steam 商店 / GitHub Releases），**GitHub 直连不稳会直接影响 Lovely 与 balatrobot 的安装**。预案：优先用 `api.github.com` 拉 release 元数据、用镜像或代理下载；**下载失败不阻塞对齐清单的书写**，但阻塞 A7 判定。

> 这两条是调研期间实测，写进文档是为了避免后续再踩：**任何“链接可访问”的结论都要注明是网页、API 还是镜像**。

---

## 7. 明确不在本文件范围内的

- **在 CI / 无头环境运行真实游戏**（明确不做：图形依赖 + 单实例端口 + 版本脆弱，见 §5.2）
- **游戏本体的自动化安装/破解/分发**（Steam 登录与购买属人工步骤；游戏文件不入库，L8）
- **第二份规则实现**（真游戏侧只读 `gamestate` 与动作结果，不写规则；见 `07` §2）
- WSL / Docker / 远程服务器
- 任何 GPU 驱动与 CUDA 配置（本项目不跑训练）
- 真游戏 12 局终验的统计方法（见 `05-实验与报告.md`）与失败归因标签（见 `04-失败归因器.md`）

---

## 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-11-13 | v2.2（历史） | W1/W2 已验证事实登记；记录 UTF-16LE 重定向坑、ACL 权限坑、性能基线；§6 写明“真实游戏 + Lovely/Steamodded/balatrobot 本项目不采用” |
| 2026-11-13 | **v3.0** | **决策同步**：①删除“真实游戏不采用”的旧结论（🔁 已被 v3.0 取代），改为 §5“真实游戏环境（规划）”；②新增四层依赖表 + 版本锁定（A0）+ 图形依赖/不可 CI/不可并行/版本脆弱约束 + 六步健康检查 + 失败降级；③新增假设 **A7 真游戏可达性**、**A8 `save`/`load` 回放与单局时长**；④A3 影响范围由“W3 重排”改为“W4 重排”；⑤工时归属更新（真实游戏 3h 计入 W3 任务 1，训练环境 1h 计入 W4 任务 1）；⑥明确真游戏终验**只在本机跑**；⑦经验事实（W1/W2）保留不改 |
