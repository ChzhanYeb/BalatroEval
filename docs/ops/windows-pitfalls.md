# Windows 环境与真游戏环境坑（运维台账）

> 用途：把“踩过的坑 + 解法”记下来，避免重复浪费。**不含规则**，不改变任何 fidelity 状态。
> 状态：✅ 已实测 ｜ 📋 预期风险（真游戏未安装，根因是推测，实测后才改）

## 1. 已实测（W1/W2，Windows + DSH）

| # | 现象 | 根因 | 解法 | 验证 |
|---:|---|---|---|---|
| 1 | `python -m server` 打印启动日志后长时间不退出 | stdio MCP server 阻塞等客户端输入，属预期行为 | 无需处理；退出用 Ctrl+C | stderr 有日志、stdout 无输出、进程挂起 |
| 2 | `!!js` 表达式里 `require('path')` 报 `ReferenceError` | cordis 求值作用域剥离了 `require` / `import.meta` | 改用 `process.getBuiltinModule('node:path')` | `dsh --profile bench-local --dump-config` 无 “did not activate” 警告 |
| 3 | Python 读重定向产物报 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff` | PowerShell 的 `>` / `Out-File` 默认写 **UTF-16LE（带 BOM）** | 读这类文件用 `encoding="utf-16"`；新产物用 `Out-File -Encoding utf8` 或让程序自己写 | 用 utf-16 打开 JSON 能正常解析 |
| 4 | `python - <<'EOF'` 在 pwsh 报“缺少字符串终止符” | PowerShell 不支持 Bash heredoc（`<<` 是重定向） | 脚本写入临时 `.py` 再执行，或用 `@'…'@` here-string | 临时脚本可正常跑 |
| 5 | 工作区所有命令（含只读）启动即失败：`SetNamedSecurityInfoW failed (Win32 5): grantWrite(…)` | DSH 需要在工作区根补写权限（`WRITE_OWNER` 缺失），Windows 拒绝 → 命令根本没执行 | 用 ACL 诊断/修复脚本给当前用户补完全控制（改动前备份、打印回滚命令），修完重试原命令 | 修复后 `Get-Location`/`git status` 正常；报告 `verification.status=verified` |

## 2. 真游戏环境（📋 全部待实测）

> 依据：07 §4.1、§9；[data-sources.md](../quality/data-sources.md) §5。每条 📋 表示“预期风险”，实测确认后把根因从推测改为事实、验证补成实测记录。

| # | 现象 | 根因（推测） | 解法 | 验证（待实测） |
|---:|---|---|---|---|
| 1 | 无交互桌面（服务/远程/CI）下启动后 `health` 超时、`gamestate` 恒空 | Balatro 是图形程序，需可见窗口与图形上下文；mod 注入依赖游戏进程 | 只在本机有交互桌面时跑真游戏；CI 只跑训练环境与离线校验；无图形即按 07 §6.5 降级 `CAPTURE_REPLAY_ONLY`，不得声称终验通过 | `health` 返回 ok 且 `gamestate.state == SELECTING_HAND` |
| 2 | 注入失败，或 `rpc.discover` 报方法不存在 | 四层版本链不匹配（Balatro 1.0.1o ← Lovely ← Steamodded ← balatrobot） | 锁版本并写 `scenarios/v3/MANIFEST.json`（A0 五元组）；先 `rpc.discover` 校验方法名再调用；不追新，断链优先锁旧版或重跑对齐 | 方法集含 `health/gamestate/start/save/load/play/discard` |
| 3 | 隔一段时间重跑，上一批捕获/回放全部失败 | Steam 自动更新打破 A0 版本链；`.jkr` 与旧版不兼容 | 关闭该游戏自动更新（或断网/备份）；版本一变就当**新批次**重做 A0 与对齐，旧结论标版本、不混表 | 连续两次启动 `build_id` 相同，`load` 同一存档成功 |
| 4 | 连 `127.0.0.1:12346` 被拒，或读到上一次残留实例的状态 | 端口固定；上次进程未退干净或多实例并存 | 启动前查 `Get-NetTCPConnection -LocalPort 12346` 与 `Get-Process -Name Balatro`；保证单实例；重连前清残留 | 启动前端口空闲、启动后 `health` 正常、只有一个实例 |
| 5 | `save` 成功但 `load` 找不到文件，或落到意外目录 | 路径可能相对**游戏进程当前目录**；含空格/中文更易出错；存档位置随安装方式变化 | 一律传**绝对路径**，存档写到仓库外或 `data/realgame/saves/`（不入库）；JSONL 只记脱敏占位；`.jkr` 按 L8 不提交 | 文件确实出现在指定路径，`load` 能恢复同一 `gamestate` |
| 6 | `Stop-Process`/`taskkill` 后端口仍被占用，或残留锁文件 | balatrobot 会拉起游戏子进程，只杀父进程会留下 Balatro 占端口 | 按**进程树**杀（`taskkill /PID <pid> /T /F` 或递归子进程 `Stop-Process`）；杀前确认 PID 属本项目 | 杀树后端口无监听、`Get-Process -Name Balatro` 无残留 |
