# references · 引用清单与核验状态

> 本文件统一登记本知识库引用的论文、项目、代码仓库与官方文档。
>
> **核验日期**：2026-11-17（Asia/Shanghai）。
> **核验方式**：通过 arXiv 摘要页/HTML 全文、ACL Anthology、PMLR、NeurIPS/ICLR 官方页、官方 GitHub README 逐条核对。
> **状态图例**：
> - ✅ **已核验**：作者数、年份、venue、链接均从一手页面读到；
> - ⚠️ **部分核验**：元数据已核验，但正文某节（通常是 Limitations）因抓取截断未读到；
> - ❓ **待核验**：仅从二手引用或搜索摘要得到，**不得当作确定事实使用**；
> - 🚫 **不可用**：已知不存在或无法访问，禁止引用。
>
> **纪律**：本表里标 ❓ 的内容，在正文中一律写作"待核验"，不得写成结论。

---

## A. 通用大模型 Benchmark

| # | 名称 | 作者 | 年 | 类型 / venue | 链接 | 状态 | 在本报告中的用途 |
|---|---|---|---|---|---|---|---|
| A1 | GLUE: A Multi-Task Benchmark and Analysis Platform for Natural Language Understanding | Alex Wang 等 6 人 | 2018 | 会议 / **ICLR 2019** | https://arxiv.org/abs/1804.07461 | ✅ | 多任务聚合、宏平均、私有测试集、诊断集（[02](02-classic-benchmarks.md) §2.1.1） |
| A2 | SuperGLUE: A Stickier Benchmark for General-Purpose Language Understanding Systems | Alex Wang 等 8 人 | 2019 | 会议 / **NeurIPS 2019** | https://arxiv.org/abs/1905.00537 | ✅ | 提案制、双基线（BERT + 人类）、等权平均（§2.1.2） |
| A3 | Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models (BIG-bench) | Aarohi Srivastava 等（摘要自述 450 作者 / 132 机构） | 2022 | 期刊 / **TMLR** | https://arxiv.org/abs/2206.04615 | ⚠️ 聚合指标、污染控制、Limitations **未核验** | 众包任务库、抗饱和（§2.1.3） |
| A4 | Holistic Evaluation of Language Models (HELM) | Percy Liang 等 50 人 | 2022 | 期刊 / **TMLR 2023** | https://arxiv.org/abs/2211.09110 | ⚠️ 污染控制与 Limitations **未核验** | 7 指标矩阵、拒绝单一总分（§2.1.4） |
| A5 | Measuring Massive Multitask Language Understanding (MMLU) | Dan Hendrycks 等 7 人 | 2020 | 会议 / **ICLR 2021** | https://arxiv.org/abs/2009.03300 | ⚠️ 附录 B.2 内容 **未核验** | 57 学科、人工收集、加权准确率（§2.1.5） |
| A6 | GPQA: A Graduate-Level Google-Proof Q&A Benchmark | David Rein 等 8 人 | 2023 | 预印本；**venue 待核验** | https://arxiv.org/abs/2311.12022 | ⚠️ §6 Limitations **未核验**；venue 未确认 | Google-proof、专家 vs 非专家、canary（§2.1.6） |
| A7 | Training Verifiers to Solve Math Word Problems (GSM8K) | Karl Cobbe 等 12 人 | 2021 | 预印本；**venue 待核验** | https://arxiv.org/abs/2110.14168 | ✅（摘要+§2–§5；无 Limitations 节） | 多步数学、最终答案判定、1.7% 标注分歧（§2.1.7） |
| A8 | Evaluating Large Language Models Trained on Code (HumanEval / Codex) | Mark Chen 等 58 人 | 2021 | 预印本；**venue 待核验** | https://arxiv.org/abs/2107.03374 | ⚠️ §6 Limitations **未核验** | 164 手写题、pass@k 无偏估计量、执行验证（§2.1.8） |
| A9 | SWE-bench: Can Language Models Resolve Real-World GitHub Issues? | Carlos E. Jimenez 等 7 人 | 2023 | 会议 / **ICLR 2024** | https://arxiv.org/abs/2310.06770 · https://www.swebench.com/ | ⚠️ §7 Discussion **未核验**；榜单站已确认 200 | 三阶段自动构造、% Resolved、仓库隔离（§2.1.9） |

---

## B. Agent Benchmark

| # | 名称 | 作者 | 年 | 类型 / venue | 链接 | 状态 | 用途 |
|---|---|---|---|---|---|---|---|
| B1 | AgentBench: Evaluating LLMs as Agents | Xiao Liu 等 22 人 | 2023 | 会议 / **ICLR 2024** | https://arxiv.org/abs/2308.03688 · https://github.com/THUDM/AgentBench | ⚠️ §6 局限未核验；仓库 200 | 8 环境、格式错 vs 动作错、单次运行（[02](02-classic-benchmarks.md) §2.2.2） |
| B2 | AgentBoard: An Analytical Evaluation Board of Multi-turn LLM Agents | Chang Ma 等 | 2024 | 会议 / **NeurIPS 2024 (Oral)** | https://arxiv.org/abs/2401.13178 · https://github.com/hkust-nlp/AgentBoard | ✅ | 9 任务/1013 环境、progress rate、确定性转移（§2.2.3） |
| B3 | BALROG: Benchmarking Agentic LLM and VLM Reasoning On Games | Davide Paglieri 等 | 2024 | 会议 / **ICLR 2025** | https://arxiv.org/abs/2411.13543 · https://github.com/balrog-ai/BALROG | ⚠️ 排行榜聚合权重未核验 | 6 游戏环境、多种子、0–100 进度（§2.2.4） |
| B4 | WebArena: A Realistic Web Environment for Building Autonomous Agents | Shuyan Zhou 等 | 2023 | 预印本；**venue 待核验**（常被引作 ICLR 2024） | https://arxiv.org/abs/2307.13854 · https://github.com/web-arena-x/webarena | ⚠️ Limitations 节未核验 | 812 任务/241 模板、DSL、r_info/r_prog、人类 78.24%（§2.2.5） |
| B5 | OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments | Tianbao Xie 等 | 2024 | 会议 / **NeurIPS 2024** | https://arxiv.org/abs/2404.07972 · https://github.com/xlang-ai/OSWorld | ✅ | 369 任务、VM 快照、getter+episode evaluator、[0,1] 奖励（§2.2.6） |
| B6 | WorkArena: How Capable Are Web Agents at Solving Common Knowledge Work Tasks?（含 BrowserGym） | Alexandre Drouin 等 | 2024 | 预印本（arXiv 注释写 preprint） | https://arxiv.org/abs/2403.07718 · https://github.com/ServiceNow/WorkArena · https://github.com/ServiceNow/BrowserGym | ⚠️ 奖励粒度未核验 | 33 任务/19912 实例、setup/teardown/validate/**cheat**（§2.2.7） |
| B7 | GAIA: a benchmark for General AI Assistants | Grégoire Mialon 等 | 2023 | 预印本；**venue 待核验** | https://arxiv.org/abs/2311.12983 | ⚠️ 官方数据页抓取失败，未能确认解析 | 466 题、准精确匹配、**不评估 trace（作者自述）**（§2.2.8） |
| B8 | τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains | Shunyu Yao 等 | 2024 | 预印本；**venue 待核验** | https://arxiv.org/abs/2406.12045 · https://github.com/sierra-research/tau-bench | ⚠️ 各领域任务数未核验；仓库提示任务已更新，建议用新版 | DB 状态 × 输出子串判定、**pass^k 定义**（§2.2.9） |
| B9 | ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs（ToolBench） | Yujia Qin 等 | 2023 | 会议 / **ICLR 2024 spotlight**（仓库描述） | https://arxiv.org/abs/2307.16789 · https://github.com/OpenBMB/ToolBench | ⚠️ 测试集构成未核验 | 16464 API、ToolEval（LLM judge）、87.1%/80.3% 人类一致性（§2.2.10） |

> **补注**：`AI Agents in Depth` 第 7 章（https://bojieli.github.io/ai-agent-book/astro/book/chapter7/）对 τ²-bench 的任务结构、验证器分层、失败归因有逐字段讲解，是很好的中文入门材料；它是**二手资料**，引用具体数字时应回原文。

---

## C. 评测方法、Judge 与统计

| # | 名称 | 作者 | 年 | 类型 / venue | 链接 | 状态 | 用途 |
|---|---|---|---|---|---|---|---|
| C1 | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | Lianmin Zheng 等 13 人 | 2023 | 会议 / **NeurIPS 2023 Datasets & Benchmarks** | https://arxiv.org/abs/2306.05685 · https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge | ✅ | 80 道两轮题、三种 judge 协议、位置偏差 23.8%、85% 一致率（[02](02-classic-benchmarks.md) §2.3.1） |
| C2 | Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference | Wei-Lin Chiang 等 11 人 | 2024 | 会议 / **ICML 2024**（PMLR 235:8359–8388） | https://arxiv.org/abs/2403.04132 · https://chat.lmsys.org | ⚠️ 代码仓未确认（UNVERIFIED） | Bradley–Terry、主动采样省 54%（§2.3.2） |
| C3 | G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment | Yang Liu 等 | 2023 | 会议 / **EMNLP 2023 main**（pp. 2511–2522） | https://arxiv.org/abs/2303.16634 · https://github.com/nlpyang/geval | ✅ | CoT + form-filling、Spearman 0.514、LLM 文本偏好风险（§2.3.3） |
| C4 | JudgeBench: A Benchmark for Evaluating LLM-based Judges | Sijun Tan 等 | 2024 | 会议 / **ICLR 2025** | https://arxiv.org/abs/2410.12784 · https://github.com/ScalerLab/JudgeBench | ⚠️ 题目构成细节未核验 | 客观真值转偏好对、GPT-4o 接近随机（§2.3.4） |
| C5 | AlpacaEval（评测产物） | Xuechen Li 等 8 人 | 2023 | **GitHub artifact（无同行评审论文）** | https://github.com/tatsu-lab/alpaca_eval | ⚠️ 细节来自 README 而非论文 | 805 指令、胜率、冗长偏差（§2.3.5） |
| C6 | Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators | Yann Dubois、Balázs Galambosi、Percy Liang、Tatsunori Hashimoto | 2024 | 会议 / **COLM 2024** | https://arxiv.org/abs/2404.04475 | ✅ | 长度控制、Spearman 0.94→0.98（§2.3.5） |
| C7 | AI Agents That Matter | Sayash Kapoor、Benedikt Stroebl、Zachary S. Siegel、Nitya Nadgir、Arvind Narayanan | 2024 | **预印本；venue 待核验** | https://arxiv.org/abs/2407.01502 · https://github.com/benediktstroebl/agent-evals | ✅（arXiv v1，章节定位按 v1） | 成本控制、Pareto、holdout、捷径（§2.3.6） |
| C8 | Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations | Evan Miller（Anthropic） | 2024 | **预印本** | https://arxiv.org/abs/2411.00640 | ⚠️ §4.2 配对公式细节未逐行核验 | 题目为抽样单位、聚类 SE、重复采样收益递减、bootstrap 通常不必要（§2.3.7、[04](04-metrics-and-statistics.md) §4.4） |
| C9 | AgentRewardBench: Evaluating Automatic Evaluations of Web Agent Trajectories | Xing Han Lù 等 10 人 | 2025 | **预印本** | https://arxiv.org/abs/2504.08942 · https://github.com/McGill-NLP/agent-reward-bench | ✅ | 1302 条专家轨迹、12 judges、规则判定低报成功（§2.3.8） |
| C10 | Large Language Models are not Fair Evaluators | Peiyi Wang 等 | 2023 | 会议 / **ACL 2024 (Long)**（pp. 9440–9450） | https://arxiv.org/abs/2305.17926 · https://github.com/i-Eval/FairEval | ✅ | 位置偏差、66/80 可被翻转（§2.3.9） |
| C11 | LLM Evaluators Recognize and Favor Their Own Generations | Arjun Panickssery、Samuel R. Bowman、Shi Feng | 2024 | 会议 / **NeurIPS 2024** | https://arxiv.org/abs/2404.13076 | ⚠️ 代码未找到（不能断言"未发布"） | 自识别与自偏好线性相关（§2.3.9） |

### C-附：指标与统计的原始出处

| 内容 | 出处 | 状态 | 备注 |
|---|---|---|---|
| pass@k 无偏估计量 | Chen et al. 2021（HumanEval）§2.1 Eq.1 | ✅ | $1-\binom{n-c}{k}/\binom{n}{k}$；n=200, k≤100 |
| pass^k 定义 | Yao et al. 2024（τ-bench）§3 | ✅ | $\mathbb{E}[\binom{c}{k}/\binom{n}{k}]$；"all k i.i.d. trials" |
| McNemar 检验 | McNemar 1947（Psychometrika）；通用教科书形式 | ⚠️ 公式为标准形式，未读原始全文 | 只看不一致对 $b,c$ |
| Wilcoxon signed-rank | Wilcoxon 1945；通用教科书形式 | ⚠️ 同上 | 对称性假设 |
| Holm 校正 | Holm 1979（Scandinavian Journal of Statistics） | ⚠️ 步骤已核验为标准 step-down，未读原文 | 控制 FWER |
| rank-biserial（配对） | Cureton 1956（Psychometrika 21(3):287–290）；Kerby 2014 | ⚠️ 存在性/年份已核验，公式为标准形式 | $r=(W^+-W^-)/(W^++W^-)$ |
| Cohen's h | Cohen 1988, *Statistical Power Analysis* (2nd ed.) | ⚠️ 标准公式，未读原书 | $2\arcsin\sqrt{p_1}-2\arcsin\sqrt{p_2}$ |
| Bradley–Terry | Bradley & Terry 1952 | ⚠️ 经 Chatbot Arena 论文间接引用 | 偏好建模 |

---

## D. 官方项目、文档与数据

| # | 名称 | 类型 | 链接 | 状态 | 用途 |
|---|---|---|---|---|---|
| D1 | SWE-bench 官方榜单 | 官方站点 | https://www.swebench.com/ | ✅ 200 | % Resolved 口径 |
| D2 | Chatbot Arena 平台 | 官方平台 | https://chat.lmsys.org | ✅ | 人类偏好评测 |
| D3 | BALROG 排行榜 | 官方站点 | https://balrogai.com | ✅（论文引用） | 跨游戏进度聚合 |
| D4 | AgentRewardBench 项目页 | 官方站点 | https://agent-reward-bench.github.io | ✅（论文引用） | judge 校准 |
| D5 | τ-bench 仓库 | 官方代码 | https://github.com/sierra-research/tau-bench | ✅ 200；README 提示任务更新 | 判定逻辑、pass^k |
| D6 | lm-evaluation-harness | 工业界 harness | https://github.com/EleutherAI/lm-evaluation-harness | ❓ 本报告仅作泛称引用，未逐一核验版本 | harness 组织方式（[07](07-learning-roadmap.md) 阶段 7） |
| D7 | AI Agents in Depth（第 7 章：Agent 的评估） | 技术书（在线） | https://bojieli.github.io/ai-agent-book/astro/book/chapter7/ | ✅ 已抓取正文（有截断） | τ²-bench 解剖、五要素、失败归因、可观测性（二手，需回原文核数） |

> **关于 GitHub 链接的说明**：本报告编写环境的网络对 `github.com` 的访问不稳定。B 组多数仓库已在核验中确认返回 200；A 组论文的代码仓（如 `openai/human-eval`、`hendrycks/test`）**未逐一确认可解析**，引用时请自行复核。

---

## E. 本仓库内部依据（项目事实来源）

> 这些不是"文献"，是 [06](06-project-specific-analysis.md) 判断项目状态的证据。**行号为调研时点（2026-11-17 22:18–22:38）的快照**；22:33 之后 `bench/engine.py`、`model.py`、`jokers.py`、`scoring.py` 被并发重写，E7–E10 的行号可能已失效，引用时请以符号名（如 `GameState`、`best_play`）为准并复核。项目状态的完整时间线见 [06](06-project-specific-analysis.md) §0。

| # | 文件 | 用途 | 关键位置 |
|---|---|---|---|
| E1 | [README.md](../../README.md) | 定位、差距表、红线、命令 | L1–L3 定位；L9–L15 四支柱差距；L97 工具声明；L174–L191 红线 |
| E2 | [plan/00-项目全貌.md](../../plan/00-项目全貌.md) | 目标、决策 D1–D14、进度 | L48–L55 四能力；L108–L118 架构；L132 `bench/report.py`；L156 D6；L160 D10；L189–L197 进度 |
| E3 | [plan/详细版/03-评测集与指标.md](../../plan/详细版/03-评测集与指标.md) | 场景 Schema、五层指标、统计方案 | L15–L24 场景定义；L33 L3 命名；L66–L101 Schema；L126–L137 五层；L196–L203 regret 边界；L234–L241 功效 |
| E4 | [plan/详细版/04-失败归因器.md](../../plan/详细版/04-失败归因器.md) | F1–F4/F0/E1 定义与判定规则 | §2 分类表；§2.1 E1 边界；§3 判定代码 |
| E5 | [plan/详细版/05-实验与报告.md](../../plan/详细版/05-实验与报告.md) | 实验矩阵、基线、预注册 | §1 90+12 局；§2 基线；§3 指标与统计；§4 预注册 |
| E6 | [scenarios/RULES_VERSION](../../scenarios/RULES_VERSION) | 规则版本、覆盖/排除、对齐等级 | L19 四支柱；L21–L24 L0；L32 `excluded` |
| E7 | [bench/engine.py](../../bench/engine.py) | 规则常量、状态转移 | L29–L32 常量；L105–L128 阶段判定；L247–L248 盲注重置 |
| E8 | [bench/model.py](../../bench/model.py) | 状态字段（无 money） | L124–L170 `GameState` |
| E9 | [bench/oracle.py](../../bench/oracle.py) | O1/O2/O3 及其边界 | L5–L10 边界声明；L37–L62 O1；L76–L130 O2；L152–L187 O3 |
| E10 | [bench/logging.py](../../bench/logging.py) | trace schema 1 | L39–L46 字段 |
| E11 | [bridge/server.py](../../bridge/server.py) | MCP 工具现状 | L21–L41 仅 `get_state` 占位 |
| E12 | [evidence/W1/W1-acceptance.md](../../evidence/W1/W1-acceptance.md) | W1 验收范围 | L76 "does not yet validate … gameplay control" |
| E13 | [tests/test_w2_rules.py](../../tests/test_w2_rules.py) | 25 项测试 | 全文件 |
| E14 | [docs/engine-fidelity.md](../../docs/engine-fidelity.md) | A0–A4 台账 | §2 A 表全 PENDING；§6 签核模板 |
| E15 | [AGENTS.md](../../AGENTS.md) | 契约、红線、已知粗糙点 | §4 契约；§5 验收命令；§7 粗糙点 |

---

## F. 待核验清单（引用时必须标注）

| # | 事项 | 当前状态 | 影响 |
|---|---|---|---|
| F1 | BIG-bench 的聚合指标、污染控制、Limitations | ❓ 未获取正文 | [02](02-classic-benchmarks.md) §2.1.3 只做结构性描述 |
| F2 | HELM 的污染控制与 Limitations | ❓ 未获取 | §2.1.4 不评价其污染处理 |
| F3 | GPQA §6 Limitations 内容 | ❓ 未获取 | 只引用摘要级结论 |
| F4 | HumanEval §6 Limitations 内容 | ❓ 未获取 | 只引用摘要级结论 |
| F5 | SWE-bench §7 Discussion | ❓ 未获取 | 只引用 §5 的诊断性发现 |
| F6 | MMLU 附录 B.2 污染讨论内容 | ❓ 只见标题 | 不声称其做了何种去污染 |
| F7 | AgentBench §6 结论/局限 | ❓ 未获取 | 只引用 §2 的"单次运行"与表 2 |
| F8 | WebArena 独立 Limitations 节 | ❓ 未获取 | 只引用 §3.2 的人类成功率 |
| F9 | τ-bench 各领域任务数 | ❓ 未获取 | 不报具体任务数 |
| F10 | WorkArena 每任务奖励是二值还是小数 | ❓ 未获取 | 不声称其有部分分 |
| F11 | BALROG 排行榜跨环境聚合权重 | ❓ 未获取 | 不描述聚合公式 |
| F12 | AgentBench / AgentBoard / WebArena / WorkArena / ToolBench 的种子与重复策略 | ❓ 论文未说明 | 不声称它们"可复现"或"不可复现" |
| F13 | *AI Agents That Matter* 的正式发表 venue | ❓ arXiv 元数据无 venue | 一律标"预印本" |
| F14 | AlpacaEval 1.0 是否有同行评审论文 | ❓ 仅 GitHub `@misc` | 引用时必须写"GitHub artifact" |
| F15 | GPQA / GSM8K / HumanEval 的正式 venue | ❓ arXiv 页无 venue 字段 | 一律标"预印本 / venue 待核验"，**不写成 ICLR/ICML** |
| F16 | 各 GitHub 仓库的可解析性 | ⚠️ 部分已确认 200，部分未确认 | 引用时注明"论文/仓库声明" |
| F17 | 本仓库工作树与 `c65fb9b`/`0e403cf` 的关系 | ✅ 已确认三者不同（见 [06](06-project-specific-analysis.md) C6） | 结果文件必须记录实际 commit + dirty 标记 |

---

## G. 引用格式建议（本知识库内部）

正文引用统一写成：

```text
<作者> et al., <年份>（<venue 或 "预印本">），arXiv:<id>，见 <本文件编号>
```

例：

```text
Chen et al., 2021（预印本），arXiv:2107.03374，见 references.md A8
```

**禁止**：
- 把预印本写成会议论文；
- 只写"某论文指出"而不给编号/链接；
- 引用本表标 ❓ 的内容当作事实；
- 把二手资料（如技术书章节）的数字当作一手数据。

---

## H. 本章应该掌握什么

引用清单不是"参考文献堆"，而是**可追责的证据台账**。使用者应当能够：

1. 说出本项目引用的论文里，哪些是会议论文、哪些是预印本（本表 A/B/C 组的"类型/venue"列）。
2. 区分"已核验""部分核验""待核验"三档，并知道待核验项**不得当作事实**。
3. 对任意一条正文结论，通过编号（如 A8、B8、C8）找到原始出处与用途。
4. 说明为什么 AlpacaEval 1.0 必须写成"GitHub artifact"，为什么 GPQA/GSM8K/HumanEval 只能写"预印本/venue 待核验"。
5. 说出本仓库内部依据（E 组）与外部文献的区别：前者是**项目事实**，后者是**领域知识**，二者不能互相替代。
6. 在新增引用时，先登记本表再在正文引用；若无法核验，写 ❓ 并说明原因。

---

## 导航

- 返回：[README](README.md)
- 方法论：[01](01-evaluation-fundamentals.md) · [02](02-classic-benchmarks.md) · [03](03-agent-benchmark-design.md) · [04](04-metrics-and-statistics.md) · [05](05-evaluation-framework-engineering.md) · [06](06-project-specific-analysis.md) · [07](07-learning-roadmap.md)
