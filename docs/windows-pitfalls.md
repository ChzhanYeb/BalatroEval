# BalatroEval Windows 环境坑与真游戏环境风险（v3.0）

> 本文记录两类内容：① W1/W2 已实测的 Windows 环境坑（历史事实）；② v3.0 真游戏环境（Balatro + Lovely + Steamodded + balatrobot）的**预期风险**（📋 全部待实测，见文末）。

- 现象：python -m server 打印启动日志后长时间不退出 \
 根因：stdio MCP server 阻塞等待客户端输入，属预期行为 \
 解法：无需处理；需退出时 Ctrl+C \
 验证：stderr 有启动日志、stdout 无输出、进程挂起

- 现象：!!js 表达式里 require('path') 报 ReferenceError: require is not defined \
  根因：cordis !!js 求值作用域剥离了全局 require 和 import.meta \
  解法：改用 process.getBuiltinModule('node:path') \
  验证：dsh --profile bench-local --dump-config 无 "did not activate" 警告

- 现象：Python 读 `data/w2-demo-summary-local-20261112.json` 报 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0` \
  根因：PowerShell 的 `>` / `Out-File` 重定向默认写 UTF-16LE（带 BOM），而 Python `open(..., encoding="utf-8")` 按 UTF-8 解码 \
  解法：读这类文件用 `encoding="utf-16"`；新产物改为 `Out-File -Encoding utf8` 或让程序自己写文件（`bench` 的 JSONL 本身就是 UTF-8） \
  验证：`python -c "import json;print(json.load(open(r'data/w2-demo-summary-local-20261112.json', encoding='utf-16'))['outcome'])"` 输出 `loss`

- 现象：`python - <<'EOF' ... EOF` 在 pwsh 里报 `缺少字符串终止符` / `表达式缺少 ')'` \
  根因：PowerShell 不支持 Bash 的 heredoc（`<<` 是重定向语法），整段被当成命令行解析 \
  解法：把脚本写入临时 `.py` 文件再 `python <file>`，或使用 `@'...'@` here-string 配合管道 \
  验证：`$py = @'...'@; $py | Out-File -Encoding utf8 "$env:TEMP\s.py"; python "$env:TEMP\s.py"` 正常执行

- 现象：工作区内所有命令（含只读 `Get-Location`）启动即失败：`SetNamedSecurityInfoW failed (Win32 5): grantWrite(...)` \
  根因：DSH 需要在工作区根目录补写权限（`WRITE_OWNER` 缺失），Windows 拒绝 → 命令根本没跑起来，与脚本内容无关 \
  解法：用 ACL 诊断/修复脚本为当前用户补全完全控制（改动前备份、打印回滚命令），修完重试原命令 \
  验证：修复后 `Get-Location`、`git status` 正常返回；报告 JSONL 中 `verification.status=verified`

---

## v3.0 真游戏环境（📋 全部待实测）

> **状态说明**：以下 6 条是**预期风险**，不是已验证的事实——真游戏（Balatro + Lovely + Steamodded + balatrobot）尚未安装、尚未运行。每条都标 📋，实测确认后才可把「根因」从推测改为事实、把「验证」补成实测记录。
> 依据：`plan/详细版/07-真实游戏接入与终验.md` §4.1、§9；`docs/data-sources.md` §7。

- 📋 现象：无交互桌面会话（服务、远程无头、CI）下启动 Balatro + balatrobot，游戏不进入可操作状态，`health` 超时或 `gamestate` 恒为空 \
  根因（推测）：Balatro 是图形程序，需要可见窗口与可用的图形上下文；balatrobot 依赖游戏进程内的 mod 注入 \
  解法：只在本机有交互桌面时跑真游戏；CI 只跑 L0 训练环境与离线校验；无图形环境即按 07 §6.5 降级为 `CAPTURE_REPLAY_ONLY`，**不得**声称终验通过 \
  验证（📋 待实测）：`health` 返回 ok 且 `gamestate` 的 `state` 为 `SELECTING_HAND`

- 📋 现象：真游戏启动后 balatrobot 注入失败，或 `rpc.discover` 报方法不存在 \
  根因（推测）：四层版本链不匹配——Balatro `1.0.1o` ← Lovely ← Steamodded ← balatrobot，任一层版本或安装顺序不对都会断链 \
  解法：锁定版本并在 `scenarios/v3/MANIFEST.json`（A0）记录 `game_version`/`build_id`/`lovely`/`smods`/`balatrobot` 五元组；先用 `rpc.discover` 校验方法名再硬编码调用；**不追新**，断链优先锁旧版或重跑对齐 \
  验证（📋 待实测）：`rpc.discover` 返回的方法集包含 `health`/`gamestate`/`start`/`save`/`load`/`play`/`discard`

- 📋 现象：隔一段时间重跑，上一批捕获/回放全部失败 \
  根因（推测）：Steam 自动把 Balatro 升到新版本，打破了 A0 锁定的版本链；`.jkr` 存档与旧版不兼容 \
  解法：关闭该游戏的 Steam 自动更新（或断网/备份），版本一旦变化就当**新批次**重新做 A0 与对齐；旧批次结论标注版本，不与新批次混表 \
  验证（📋 待实测）：连续两次启动记录到相同 `build_id`，`load` 同一 `.jkr` 成功

- 📋 现象：连接 `127.0.0.1:12346` 被拒绝，或连上后读到的是上一次残留实例的状态 \
  根因（推测）：balatrobot 的 JSON-RPC 监听端口固定为 `:12346`；上一次进程未退干净、或同时启动多个游戏实例时端口冲突/串实例 \
  解法：启动前先查端口占用与进程（`Get-NetTCPConnection -LocalPort 12346`、`Get-Process -Name Balatro`）；确认只有一个实例；失败重连前先清理残留 \
  验证（📋 待实测）：启动前端口空闲、启动后 `health` 正常、进程列表中只有一个 Balatro 实例

- 📋 现象：`save` 成功但 `load` 找不到文件，或文件落到意想不到的目录 \
  根因（推测）：`save`/`load` 的路径解析可能相对**游戏进程的当前目录**而非仓库根；路径含空格/中文时更易出错；存档默认位置随安装方式变化 \
  解法：一律传**绝对路径**并把存档写到仓库外或 `data/realgame/saves/`（且该目录不入库）；JSONL 只记脱敏占位路径；`.jkr` 本体按 L8 不提交 \
  验证（📋 待实测）：`save` 后文件确实出现在指定绝对路径，`load` 同一路径能恢复同一 `gamestate`

- 📋 现象：`Stop-Process`/`taskkill` 之后端口仍被占用，或磁盘上残留锁文件导致下次启动失败 \
  根因（推测）：balatrobot 会拉起游戏子进程；只杀父进程会留下 Balatro 子进程继续占用 `:12346` 与存档 \
  解法：按**进程树**杀（`taskkill /PID <pid> /T /F`，或 `Get-CimInstance Win32_Process` 递归子进程后逐个 `Stop-Process`）；杀之前确认 PID 属于本项目的实例，不要误杀其他游戏/Steam 进程 \
  验证（📋 待实测）：杀进程树后 `Get-NetTCPConnection -LocalPort 12346` 无监听、`Get-Process -Name Balatro` 无残留
