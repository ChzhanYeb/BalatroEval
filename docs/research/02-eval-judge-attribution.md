# 02 · Agent 自动评测、自动判定与失败归因

> 本笔记服务于 BalatroEval 开题报告的「研究现状」部分（A2 块：自动评测 / 自动判定 / 失败归因）。
> 检索与核对时间：2026-11-12。所有条目均经 web_search / web_fetch 实检，无凭记忆写入的条目。
> **核实状态图例**：
> - ✅ 已用 web_fetch 打开论文页面（arXiv abs / ACL Anthology / 会议论文页）核对题名、作者、年份；
> - △ 已用 web_fetch 打开 arXiv 官方元数据接口（export.arxiv.org/api/query）核对题名、作者、首发年份，但未打开论文版面正文；
> - ⏳ 仅由检索结果间接确认（本文件当前无此类条目，保留该图例以便后续补检）。
>
> 计数：参考文献 34 条，✅ 12 条，△ 22 条，⏳ 0 条。

---

## 1. 分类叙述

### 1.1 可验证 / 规则化评测：从「人写参考答案」到「环境判分」

做法上，这一支的共识是**把评测信号从「文本相似」换成「可执行判定」**：HumanEval 用单元测试判功能正确性（Codex 单次 28.8%，每题采 100 个样本可到 70.2%，并提出 pass@k 的无偏估计量）[2]；SWE-bench 把判分交给仓库自带的测试，用 2,294 个真实 GitHub issue 逼出「改多文件 + 与执行环境交互」的长程行为，当时最好的 Claude 2 仅解决 1.96%[1]；更早的 SQuAD 则把 exact-match / F1 这套「参考答案匹配」范式做到极致，也暴露了它的天花板——答案必须能被字符串规范化对齐[3]。指标上，这一类给出的是成功率、pass@k、EM/F1 这类**可精确复算**的量；τ-bench 进一步把判分做成「对话结束后比对数据库终态与标注目标态」，并引入 pass^k 衡量多次试验的稳定性（gpt-4o 任务成功率 <50%，retail 域 pass^8 <25%）[6]。局限有三：测试/答案集本身是人类写的，写错就错判；判分粒度停在 episode 级（成功/失败），不回答「哪一步错」；且容易过拟合——benchmark 的 holdout 不足会被 agent 用 shortcut 刷穿[30]。在训练侧，同一思想延伸为 verifiable rewards：DeepSeek-R1 用规则可判的奖励（数学答案匹配、代码编译/测试通过）做纯 RL，不需要人类标注推理轨迹，就把反思、验证等行为「激励」出来[4]；后续理论工作把 GRPO 的成功概率（PoS）写成递推式，证明其在正则约束下收敛到高于参考策略的不动点[5]。环境接地（environment-grounded）评测则把「可验证」从单点答案扩展到状态轨迹：AgentBench 用 8 个交互环境评 LLM-as-Agent[7]，AgentBoard 在部分可观测、多轮交互的统一框架里加了一个细粒度 progress rate，把「只报最终成功率」补成「过程推进了多少」[8]。这一支对本项目的直接含义是：**只要环境状态可枚举、动作空间可判合法，主指标就完全可以不依赖任何模型打分**。

### 1.2 LLM-as-a-Judge：能对齐人类偏好，但不能承担「客观正确性」

Zheng et al. 的 MT-Bench / Chatbot Arena 是这一支的奠基工作：用强模型当裁判，在 3K 专家投票与 30K 人类偏好对话上验证 GPT-4 judge 与人类一致率 >80%，与人类彼此之间的一致率同量级；同时系统列出位置偏差、冗长（verbosity）偏差、自我增强（self-enhancement）偏差与推理能力不足，并给出交换顺序、CoT、参考引导等缓解手段[9]。G-Eval 把 judge 做成「CoT + 表单填空」的评分流水线，在摘要任务上把与人类的 Spearman 相关推到 0.514，但同时在论文里就点出 judge 对 LLM 生成文本存在偏好[10]。偏差研究随后被做成「攻击面」：仅调换两个回答的出现顺序，就能让 Vicuna-13B 在 80 条 query 中的 66 条上「击败」ChatGPT，作者据此提出多证据校准、位置平衡校准与 human-in-the-loop 校准[12]；自我偏好则被追溯到「自我识别」能力——LLM 能以非平凡准确率认出自己的输出，且微调后自我识别能力与自我偏好强度呈线性相关[13]。可靠性侧有两个关键结论：JudgeBench 用「客观正确性」构造难度对（知识/推理/数学/代码），发现包括 GPT-4o 在内的强模型只略好于随机猜测，说明**以人类偏好为金标准的 judge 评测会高估 judge**[11]；Trust or Escalate 则给出另一条路——让 judge 输出置信度并「选择性评估 + 逐级升级到更强模型」，可以在用户指定的一致率水平上给出**可证明的人类一致率保证**（在 GPT-4 都达不到 80% 一致的 Arena 子集上，用 Mistral-7B 起步也做到 >80% 一致、约 80% 覆盖率）[15]。方法论层面，综述把「如何构建可靠 LLM-as-a-Judge」整理为一致性、偏差缓解、场景适配三条主线，并强调需要标准化[14]；而 The Leaderboard Illusion 从制度侧证明，即使是 Chatbot Arena 这种「人类投票」平台，私有测试、选择性披露与采样不对称（Meta 在 Llama-4 前测了 27 个私有变体；Google/OpenAI 各拿到约 19.2%/20.4% 的全部 battle 数据，83 个开放权重模型合计仅 29.7%）也会系统性扭曲排名[16]。**结论对 BalatroEval 很直接：judge 可以作为「解释器/归因器」，但不能进主指标；且 judge 自身必须被单独评测（κ、偏差探针、弃权率），否则只是一层不可审计的噪声。**

### 1.3 轨迹级 / 过程级评测：把「结果对不对」拆成「每一步对不对」

过程监督是这条线的起点：Let's Verify Step by Step 用 80 万条 step-level 人类标注（PRM800K）训练过程奖励模型，在 MATH 代表子集上把过程监督做到 78%，显著优于结果监督[17]。Agent 侧则把「过程」从推理步扩展到工具调用步：Agent-as-a-Judge 让 agent 去评 agent，在 55 个真实 AI 开发任务、365 条层级化需求的 DevAI 上给出中间反馈，可靠性接近人工评测基线[18]；AgentBoard 用 progress rate 把 episode 切成可比较的推进度[8]；AgentEval 则走「先按应用目的自动生成评判准则，再量化 utility」的路线，在数学与 ALFWorld 任务上验证准则的有效性与稳健性（其代价是准则与打分仍由 LLM 给出，缺少人类闭环）[21]。轨迹级评测真正困难的地方在**错误定位**：TRAIL 建立了一个 agentic trace 的错误分类学，并发布 148 条人工标注轨迹，结果是最强的 Gemini-2.5-pro 在 trace debugging 上只有 11%[19]；AgentRewardBench 用 1,302 条经专家复核的 web agent 轨迹（5 个 benchmark、4 个 LLM）评 12 个 LLM judge，发现没有任何一个 judge 在所有 benchmark 上都好，且常用规则判分**低报**成功率[22]。多智能体侧，MAST 从 150 条轨迹归纳出 14 个失败模式、聚为 3 类（系统设计、智能体间失配、任务验证），在 1600+ 条跨 7 个框架的轨迹上做标注，报告标注者间一致性 κ=0.88，并训练了一个与人工高度一致的 LLM 标注器[20]。这一支的共同短板是：**金标准是人工标注，成本高、规模小（148 / 150 / 1,302 量级），且评测对象是「判定器与人类的一致性」，而不是「判定器与可复算真值的一致性」**——这恰好是本项目想换掉的假设。

### 1.4 失败归因：诊断层方法学依据（非本项目主定位）

Who&When 是这一块的标杆：它把「哪个 agent、哪一步该为失败负责」形式化为一个新任务，发布 127 个多智能体系统的失败日志与细粒度标注，并评测三类自动归因方法，最好的方法在 agent 级只有 53.5% 准确率、在**步级只有 14.2%**，部分方法低于随机，连 o1 / DeepSeek-R1 都达不到可用水平[23]。这组数字是整块领域最重要的事实：**用 LLM 读轨迹做根因定位，当前基本不可用**。AgentDebug 换了个方向：先建 AgentErrorTaxonomy（memory / reflection / planning / action / system 五层模块化分类），再在 ALFWorld、GAIA、WebShop 上构建系统化标注的 AgentErrorBench，用「隔离根因 + 给纠正反馈」的调试框架把 all-correct 准确率提升 24%、步级准确率提升 17%，反馈还带来 26% 的相对任务成功率提升，并蒸馏出 4B 的 AgentDebugger[24]——它证明了**分类学 + 数据管线**比单点 prompt 更有效，但判定仍由模型完成。因果/信用分配侧，最新工作把 Shapley 合作博弈归因与过程奖励模型结合：成功时用 Shapley 把系统级结果分摊到 agent 与 message，失败时用「首次错误定位」构造修复感知的偏好信号，产出局部、带符号、信用守恒的训练信号——但作者明确声明这是概念性工作、**实证验证留给未来**[25]。错误传播侧，「幻觉雪球」把多 agent 流水线中的错误演化建模成四状态一阶马尔可夫过程（Raw Fact → Derived → Narrative → Invisible），实测每道边界的逃逸概率为 24.6% / 48.3% / 89.3%，346 次注入幻觉中 gpt-4o 的检出率从 Stage 1 的 72.0% 降到 Stage 4 的 50.9%，而「在边界处设闸门」把存活率从 58.4% 降到 16.2%（Cohen's h = −0.911）[26]。它给本项目的启示很具体：**归因不只回答「谁错了」，还要回答「错在第几个状态转移上、还能不能被抓到」**。

### 1.5 评测方法论与效度：指标之外的「元问题」

HELM 确立了「多指标 × 多场景 × 标准化」的报告范式：7 个指标（accuracy、calibration、robustness、fairness、bias、toxicity、efficiency）× 16 个核心场景，30 个模型在 42 个场景上 dense benchmark，把核心场景覆盖率从平均 17.9% 提到 96.0%[27]；BIG-bench 则用 204 个任务、450 位作者、132 家机构证明「众包大规模任务集」可行，并给出「性能随规模平滑提升 vs 在某临界规模突变」的区分[28]。效度侧有五类必报项。其一是**污染**：仅做 n-gram 匹配的去污染不够，同义改写/翻译就能绕过，且实测 RedPajama-Data-1T 与 StarCoder-Data 中 HumanEval 的重叠达 8–18%[29]。其二是**成本**：AI Agents That Matter 指出 agent benchmark 只盯 accuracy，导致 SOTA agent 又贵又复杂、社区对「精度来自哪里」得出错误结论，并额外指出 holdout 不足与评测不可复现两个系统性问题，主张把 cost 与 accuracy 联合优化[30]。其三是**统计**：Adding Error Bars to Evals 把评测视为从超总体抽样的实验，给出误差棒、两模型差异检验与实验设计的公式，核心建议是报告置信区间而非点估计[31]。其四是**可复现**：对 255 篇论文的手工复现实验表明「放出代码 ≠ 可复现」[32]。最后是 Goodhart 风险：reward hacking 有形式化定义（proxy 的期望回报上升永不会降低 true 回报才叫 unhackable，而在全部随机策略集合上只有常数奖励满足），说明**任何代理指标都天然可被优化穿**[33]；reward model 过优化的缩放律则给出「优化越狠、真实分数先升后降」的函数形式与参数依赖[34]。对本项目而言，这五条共同构成一张「必须报告的清单」：主指标要给 CI、要报成本、要给 holdout/污染检查、要固定版本与随机性、要说明指标为何不易被刷。

---

## 2. 参考文献表

> 格式：`N. 作者. *Title*. Venue/arXiv:ID, Year. URL | 状态 | 一句话（解决了什么 + 与本项目关系）`

### A. 可验证 / 规则化评测

1. C. E. Jimenez, J. Yang, A. Wettig, S. Yao, K. Pei, O. Press, K. Narasimhan. *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024, arXiv:2310.06770. https://arxiv.org/abs/2310.06770 | ✅ | 用仓库自带测试判分的 2,294 个真实 issue 基准（当时最强模型仅 1.96%）；示范了「判分交给可执行测试」的范式，本项目把这一范式从代码扩展到规则可枚举的卡牌状态机。
2. M. Chen, J. Tworek, H. Jun, et al. *Evaluating Large Language Models Trained on Code*. arXiv:2107.03374, 2021. https://arxiv.org/abs/2107.03374 | ✅ | HumanEval + 单元测试 + pass@k 无偏估计量的源头（单次 28.8%，100 采样 70.2%）；本项目 pass@ 类指标的统计口径直接沿用。
3. P. Rajpurkar, J. Zhang, K. Lopyrev, P. Liang. *SQuAD: 100,000+ Questions for Machine Comprehension of Text*. EMNLP 2016, arXiv:1606.05250. https://arxiv.org/abs/1606.05250 | △ | exact-match / F1 参考匹配范式的代表；用来说明「无环境可判时只能退化为字符串匹配」，反衬本项目为何需要可枚举环境。
4. DeepSeek-AI, D. Guo, D. Yang, et al. *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning*. arXiv:2501.12948, 2025（Nature 645:633–638）. https://arxiv.org/abs/2501.12948 | ✅ | 用纯 RL + 规则可判奖励激励推理，无需人类标注轨迹；支撑本项目「规则化奖励足以驱动/评测长程行为」的合法性。
5. Y. Mroueh. *Reinforcement Learning with Verifiable Rewards: GRPO's Effective Loss, Dynamics, and Success Amplification*. arXiv:2503.06639, 2025. https://arxiv.org/abs/2503.06639 | △ | 把 GRPO 在二值可验证奖励下的成功概率写成递推并证明收敛到高于参考策略的不动点；为「可验证奖励」提供理论依据，也提示二值指标的信息量上限。
6. S. Yao, N. Shinn, P. Razavi, K. Narasimhan. *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains*. arXiv:2406.12045, 2024. https://arxiv.org/abs/2406.12045 | ✅ | 用「数据库终态 vs 标注目标态」判分并引入 pass^k（gpt-4o <50%，retail pass^8 <25%）；是本项目「状态比对式判分 + 多次试验稳定性」的直接方法学参照。
7. X. Liu, H. Yu, H. Zhang, et al. *AgentBench: Evaluating LLMs as Agents*. ICLR 2024, arXiv:2308.03688. https://arxiv.org/abs/2308.03688 | △ | 8 个交互环境评测 LLM-as-Agent，并归纳失败原因（长程推理、决策、指令遵循弱）；提供「环境接地评测」的早期模板。
8. C. Ma, J. Zhang, Z. Zhu, et al. *AgentBoard: An Analytical Evaluation Board of Multi-turn LLM Agents*. NeurIPS 2024 (Oral), arXiv:2401.13178. https://arxiv.org/abs/2401.13178 | △ | 提出细粒度 progress rate，弥补「只看最终成功率」；与本项目 Local Regret 的动机同源，但它是学习式进度估计，本项目是可枚举的最优动作差。

### B. LLM-as-a-Judge 与 judge 偏差

9. L. Zheng, W.-L. Chiang, Y. Sheng, et al. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 D&B, arXiv:2306.05685. https://arxiv.org/abs/2306.05685 | ✅ | 系统刻画 position / verbosity / self-enhancement 偏差，并证明 GPT-4 judge 与人类一致率 >80%；本项目据此把 judge 限定在归因层并强制做偏差探针。
10. Y. Liu, D. Iter, Y. Xu, S. Wang, R. Xu, C. Zhu. *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment*. arXiv:2303.16634, 2023. https://arxiv.org/abs/2303.16634 | ✅ | CoT + 表单填空式评分（摘要 Spearman 0.514），并自曝对 LLM 生成文本的偏好；说明 judge 的「可解释评分表」可以借鉴，但其分数不可作主指标。
11. S. Tan, S. Zhuang, K. Montgomery, et al. *JudgeBench: A Benchmark for Evaluating LLM-based Judges*. ICLR 2025, arXiv:2410.12784. https://arxiv.org/abs/2410.12784 | ✅ | 用客观正确性构造难度对，发现 GPT-4o 等强 judge 仅略好于随机；这是本项目「LLM Judge 不进主指标」最硬的一条文献依据。
12. P. Wang, L. Li, L. Chen, et al. *Large Language Models are not Fair Evaluators*. arXiv:2305.17926, 2023. https://arxiv.org/abs/2305.17926 | △ | 仅交换顺序即可让 Vicuna-13B 在 66/80 题上「击败」ChatGPT，并给出三类校准；本项目任何 pairwise/排序类对比都必须做位置平衡。
13. A. Panickssery, S. R. Bowman, S. Feng. *LLM Evaluators Recognize and Favor Their Own Generations*. arXiv:2404.13076, 2024. https://arxiv.org/abs/2404.13076 | △ | 自我识别能力与自我偏好强度线性相关；据此本项目要求判定器与 actor 不同源/不同模型。
14. J. Gu, X. Jiang, Z. Shi, et al. *A Survey on LLM-as-a-Judge*. arXiv:2411.15594, 2024. https://arxiv.org/abs/2411.15594 | △ | 以「如何构建可靠 judge」为主线整理一致性、偏差缓解与场景适配，并提出 judge 可靠性基准；提供本项目判定器可靠性评估的框架词汇。
15. J. Jung, F. Brahman, Y. Choi. *Trust or Escalate: LLM Judges with Provable Guarantees for Human Agreement*. arXiv:2407.18370, 2024. https://arxiv.org/abs/2407.18370 | △ | 选择性评估 + 级联升级，可在指定一致率上给出可证明保证（>80% 一致、约 80% 覆盖）；本项目的「低置信弃权 → 转人工」机制直接借鉴。
16. S. Singh, Y. Nan, A. Wang, et al. *The Leaderboard Illusion*. arXiv:2504.20879, 2025. https://arxiv.org/abs/2504.20879 | △ | 揭示 Arena 的私有测试、选择性披露与采样不对称（Meta 测了 27 个私有变体；开放权重 83 个模型合计仅 29.7% 数据）；提醒本项目排行榜与判定器都要披露调用与筛选过程。

### C. 轨迹级 / 过程级评测

17. H. Lightman, V. Kosaraju, Y. Burda, et al. *Let's Verify Step by Step*. arXiv:2305.20050, 2023. https://arxiv.org/abs/2305.20050 | △ | 80 万条 step-level 标注训练 PRM，过程监督在 MATH 子集达 78%，显著优于结果监督；本项目 step-level 归因的监督信号设计参照其粒度。
18. M. Zhuge, C. Zhao, D. Ashley, et al. *Agent-as-a-Judge: Evaluate Agents with Agents*. arXiv:2410.10934, 2024. https://arxiv.org/abs/2410.10934 | △ | 用 agent 评 agent 给出中间反馈，在 DevAI（55 任务 / 365 条层级需求）上接近人工评测；说明「过程级判定器」可行，但它仍是模型判定，无法给出确定性证据链。
19. D. Deshpande, V. Gangal, H. Mehta, J. Krishnan, A. Kannappan, R. Qian. *TRAIL: Trace Reasoning and Agentic Issue Localization*. arXiv:2505.08638, 2025. https://arxiv.org/abs/2505.08638 | ✅ | 建立 agentic trace 错误分类学 + 148 条人工标注轨迹，最强模型仅 11%；量化了「LLM 做 trace 级错误定位」的上限，是本项目选择确定性归因的核心反证。
20. M. Cemri, M. Z. Pan, S. Yang, et al. *Why Do Multi-Agent LLM Systems Fail?* arXiv:2503.13657, 2025. https://arxiv.org/abs/2503.13657 | △ | MAST：1600+ 轨迹、7 个框架，归纳 14 个失败模式（3 大类），报告 κ=0.88 并训练高一致 LLM 标注器；本项目 taxonomy 设计与 κ 报告格式的直接样板。
21. N. Arabzadeh, S. Huo, N. Mehta, et al. *Assessing and Verifying Task Utility in LLM-Powered Applications*（框架名 AgentEval）. EMNLP 2024, https://aclanthology.org/2024.emnlp-main.1219/ | ✅ | 按应用目的自动生成评判准则并量化 utility（数学、ALFWorld）；代表「准则自动生成」路线，其缺口正是缺少人类闭环与可复算真值。
22. X. H. Lù, A. Kazemnejad, N. Meade, et al. *AgentRewardBench: Evaluating Automatic Evaluations of Web Agent Trajectories*. arXiv:2504.08942, 2025. https://arxiv.org/abs/2504.08942 | △ | 1,302 条专家复核轨迹、12 个 LLM judge：无单一 judge 全域最优，且规则判分低报成功率；本项目在「规则判分可能漏判」这一点上必须给出对照实验。

### D. 失败归因与信用分配

23. S. Zhang, M. Yin, J. Zhang, et al. *Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent Systems*. arXiv:2505.00212, 2025. https://arxiv.org/abs/2505.00212 | ✅ | Who&When：127 个 MAS 失败日志，最优方法 agent 级 53.5%、步级 14.2%，o1/R1 亦不可用；本项目要正面回应的「归因难」基线数字。
24. K. Zhu, M. Tian, B. Li, et al. *AgentDebug: Where LLM Agents Fail and How They can Learn From Failures*. ICML 2026 Workshop (Failure Modes in Agentic AI), 2026, https://icml.cc/virtual/2026/77923 | ✅ | AgentErrorTaxonomy（memory/reflection/planning/action/system 五层）+ AgentErrorBench（ALFWorld/GAIA/WebShop）+ 调试反馈，all-correct +24%、步级 +17%、任务成功率相对 +26%；证明分类学 + 数据管线有效，但判定仍由模型完成。
25. C.-H. Yang, T. Mallick, L. Chen, K. Raghavan, A. Gueroudji, I. T. Foster, R. Thakur. *Who Gets the Reward & Who Gets the Blame? Evaluation-Aligned Training Signals for Multi-LLM Agents*. NeurIPS 2025 LAW Workshop, arXiv:2511.10687. https://arxiv.org/abs/2511.10687 | △ | Shapley 信用分摊 + 首次错误定位，产出局部、带符号、信用守恒的信号；明确声明仅为概念性工作、未做实证验证——这正是本项目可用「可枚举 regret」补上的缺口。
26. P. Singh, B. Pawar. *The Hallucination Snowball: Modeling Error Propagation as State Transitions in Multi-Agent LLM Pipelines*. arXiv:2608.14588, 2026（ICML 2026 FAGEN Workshop）. https://arxiv.org/abs/2608.14588 | △ | 把错误传播建模为四状态一阶马尔可夫过程（逃逸概率 24.6%/48.3%/89.3%），边界闸门把存活率从 58.4% 降到 16.2%；支撑本项目「错误传播链」与「在哪一步还能抓到」的证据链字段设计。

### E. 评测方法论与效度

27. P. Liang, R. Bommasani, T. Lee, et al. *Holistic Evaluation of Language Models*. TMLR 2023, arXiv:2211.09110. https://arxiv.org/abs/2211.09110 | △ | 7 指标 × 16 核心场景 × 30 模型，核心场景覆盖率 17.9%→96.0%；本项目多指标报告表（regret/optimality/legality/成本）的结构参照。
28. A. Srivastava, A. Rastogi, A. Rao, et al. *Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models*. TMLR 2022, arXiv:2206.04615. https://arxiv.org/abs/2206.04615 | △ | 204 任务、450 作者、132 机构的众包基准，区分平滑提升与临界突变；提示本项目任务集要分层设计难度而非追求规模。
29. S. Yang, W.-L. Chiang, L. Zheng, J. E. Gonzalez, I. Stoica. *Rethinking Benchmark and Contamination for Language Models with Rephrased Samples*. arXiv:2311.04850, 2023. https://arxiv.org/abs/2311.04850 | △ | n-gram 去污染可被改写绕过，实测预训练集中 HumanEval 重叠 8–18%；本项目自建规则子集需报告污染检查与一次性 held-out 设计。
30. S. Kapoor, B. Stroebl, Z. S. Siegel, N. Nadgir, A. Narayanan. *AI Agents That Matter*. arXiv:2407.01502, 2024. https://arxiv.org/abs/2407.01502 | ✅ | 指出 agent 评测只看 accuracy、缺 holdout、不可复现三大问题，主张 cost–accuracy 联合优化；本项目必须双报成本与准确率的方法学依据。
31. E. Miller. *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations*. arXiv:2411.00640, 2024. https://arxiv.org/abs/2411.00640 | △ | 把评测视为超总体抽样，给出误差棒、模型差异检验与实验设计公式；本项目所有指标都要带 95% CI 的统计学依据。
32. E. Raff. *A Step Toward Quantifying Independently Reproducible Machine Learning Research*. NeurIPS 2019, arXiv:1909.06674. https://arxiv.org/abs/1909.06674 | △ | 手工复现 255 篇论文，证明「发代码 ≠ 可复现」；本项目把「判定可复现」写成硬性验收项的依据。
33. J. Skalse, N. H. R. Howe, D. Krasheninnikov, D. Krueger. *Defining and Characterizing Reward Hacking*. NeurIPS 2022, arXiv:2209.13085. https://arxiv.org/abs/2209.13085 | △ | 形式化 reward hacking：proxy 期望回报上升永不降低 true 回报才叫 unhackable，而全随机策略集上只有常数奖励满足；支撑「主指标须论证不易被刷」。
34. L. Gao, J. Schulman, J. Hilton. *Scaling Laws for Reward Model Overoptimization*. arXiv:2210.10760, 2022. https://arxiv.org/abs/2210.10760 | △ | 给出优化强度与 gold reward 的过优化曲线及其随参数量的平滑缩放；解释为何用 judge/PRM 当优化目标会退化，而可枚举指标不会。

---

## 3. 判定器设计可借鉴清单（10 条）

1. **主指标与归因器彻底分层，并给出分层理由。** 主指标必须是规则可复算的量（Local Regret / Action Optimality / Legality 由枚举得到），judge 只在归因层出现；理由引用 JudgeBench（judge 在客观正确性上仅略好于随机）[11] 与 TRAIL（11%）[19]、Who&When（步级 14.2%）[23]，三处一起构成「不能让模型判定进主指标」的证据三角。
2. **taxonomy 采用「模块 × 可判定证据」二维设计，而非纯语义分类。** MAST 用 3 大类 14 模式并报告 κ=0.88[20]、AgentDebug 用 5 层模块（memory/reflection/planning/action/system）[24]，共同经验是：**每个类别必须绑定一个能落地的观测证据字段**，否则标注一致性会崩。本项目的 4 类判定器应逐条写明「触发条件 → 证据字段 → 反例（什么情况不算）」。
3. **κ 必须 per-class 报告，并附混淆矩阵与 95% CI；不要只报总体一致率。** MAST 报 κ=0.88 是好的起点[20]，但它是在合并标注上算的；本项目 4 类判定器语义重叠（尤其 miscalculation 与 planning_shortfall）会导致某类 κ 极低而被总体平均掩盖。CI 的算法与报告格式参照 Miller 的超总体抽样框架[31]。
4. **给判定器加「置信度 + 弃权」出口，并报告覆盖率–一致率曲线。** Trust or Escalate 的 selective evaluation 证明：允许 judge 说「不确定」并升级/转人工，才能拿到可证明的一致率保证[15]。本项目对应做法：启发式类（planning_shortfall）默认输出 `suspected` + 置信度，低置信样本进入人工标注集，报告「弃权率 vs κ」而非单点 κ。
5. **step-level 对齐靠确定性重放，不靠 LLM 定位。** Who&When 步级 14.2%[23] 说明 LLM 定位不可依赖；正确做法是记录 `trace_id / step_index / state_hash / action / legal_action_set / expected_score / actual_score`，用同一 seed + 同一动作序列重放到该步，由规则判定该步是否次优。这样「定位」变成可复现的查询而非生成任务。
6. **证据链字段固定 schema 并随结果一起发布。** 借鉴 TRAIL 的分类学[19] 与「幻觉雪球」的状态转移视角[26]：每条归因至少含 `证据类型（规则/枚举/对照）`、`最小反例`（若该步改为最优动作，后续 regret 变化多少）、`传播路径`（该错误影响了哪些后续步）。这直接回应「判定确定、可复现、带证据链」的要求。
7. **位置/顺序/自我偏好三类偏差各设一条硬约束。** pairwise 对比一律双向交换并取平衡位置（Fair Evaluators）[12]；判定器与 actor 不同源（自我偏好）[13]；prompt 中不暴露候选答案的来源/长度（verbosity）[9]。偏差探针结果作为附录指标报告。
8. **多次试验指标用 pass^k 而非单次 pass@1，并区分「能力」与「稳定性」。** τ-bench 的 pass^8 <25%[6] 表明单次成功率会严重高估可用性；本项目对同一初始局面跑 k 次，报告 pass^k、regret 的均值与方差，并用 pass@k 估计量[2]做上界参照。
9. **成本与准确率双报，且把判定器调用成本单列。** AI Agents That Matter[30] 的成本–准确率联合优化应落到表格：token 数、美元成本、墙钟时间，与 Legality/Action Optimality 并列；判定器若被调用，其次数与成本单独一列（否则「不用 judge」的主张无法被验证）。
10. **误判率要拆成 miss 与 false-positive 两个方向，并写进验收标准。** 规则判分可能低报成功（AgentRewardBench[22]），启发式可能误报。验收时对每类判定器报告 precision/recall/F1 与 95% CI，并明确规定「启发式类不得用于否定性结论，只能用于提示人工复核」。

---

## 4. 本项目与已有工作的分界

**已被做过、不要重复的**：(a) 用单元测试/可执行判分做 agent 评测（SWE-bench[1]、HumanEval[2]、τ-bench[6]）；(b) 用规则可验证奖励训练推理（DeepSeek-R1[4]）；(c) LLM-as-a-Judge 的偏差刻画与一致性检验（MT-Bench[9]、G-Eval[10]、Fair Evaluators[12]、自我偏好[13]）；(d) agent 轨迹的错误分类学与人工标注集（TRAIL[19]、MAST[20]、AgentDebug[24]）；(e) 「自动失败归因」这一任务本身与其难度量化（Who&When[23]）；(f) agent 评测的效度批判（AI Agents That Matter[30]、Leaderboard Illusion[16]）。**本课题不应再交出一个「新的 agent benchmark」，也不应再交出一份「judge 偏差研究」。**

**仍然空白的四点**：(1) **归因的判定基准**——现有最强方法（Who&When 的 53.5%/14.2%[23]）与最新分类学工作（TRAIL[19]、AgentDebug[24]）的金标准都是人工标注、判定器都是 LLM；没有工作把归因建立在「状态与动作可精确枚举」的环境上，用规则重放给出**确定性、可审计**的根因与最小反例。AgentDebug 已经证明「分类学 + 数据管线」有效但仍未摆脱模型判定[24]，Shapley 归因工作则自认只有概念框架、缺实证[25]——这两点正是可切入的缝。(2) **归因类别与量化指标的耦合**：MAST 是系统级、AgentDebug 是模块级、TRAIL 是通用 trace 级，三者的类别都无法直接对应一个可计算的分数；本项目把 `illegal_action / miscalculation / rule_hallucination / planning_shortfall` 直接挂在 Local Regret 与 Action Optimality 上，使「失败类型 → 指标损失」可换算。(3) **一致性与不确定性的报告规范**在 agent 归因领域普遍缺失：Who&When 只报 accuracy[23]，MAST 报 κ 但不报 per-class CI[20]，错误传播研究用的是效应量而非判定器一致性[26]；本项目按 Miller 的框架给每类判定器报 per-class κ + 95% CI[31]，这一项本身就是可发表的增量。(4) **「LLM Judge 不进主指标」的架构先例**：JudgeBench 论证了 judge 不可靠[11]，Trust or Escalate 给了 judge 的保证式用法[15]，但还没有工作把「规则可枚举主指标 + judge 仅作归因辅助 + κ 校准」做成一个完整、可复现的评测框架；这是本项目最清晰的定位。

---

## 5. 不确定项与待补

1. **AgentDebug 的正式出版信息待确认**：目前核对到的是 ICML 2026 Workshop（Failure Modes in Agentic AI）页面与 OpenReview 入口（forum id VIO4WbZuVW），未见 arXiv 编号；若报告需要 arXiv 引用，需再查一次 OpenReview 页面确认最终版本与作者顺序。
2. **AgentEval 的命名歧义**：任务清单里的「AgentEval」在检索中对应到 Arabzadeh et al. EMNLP 2024《Assessing and Verifying Task Utility in LLM-Powered Applications》（框架自称 AgentEval）[21]；另有一篇同名的多智能体评估框架工作未能核实到可靠页面，故本文件只保留可核实的一篇。若 Lead 需要「AgentEval 作为 MAS 评估框架」的版本，需另行检索确认。
3. **pass@k 的置信区间**：本文件用 HumanEval[2] 的估计量 + Miller[31] 的一般框架组合说明，未找到专门讨论「pass@k 的 CI」的单篇文献；如报告需要更强的引用，建议补检「statistical significance of pass@k」方向。
4. **未覆盖但可能相关的方向**（受篇幅与本文件主题边界限制，留给其他块）：WebArena / OSWorld 类真实环境 benchmark、reward model 的对抗鲁棒性、以及「LLM 自我验证（self-verification）」文献；若 Lead 认为「环境接地」需要更强支撑，可再补 2–3 条。
5. **△ 级条目的正文未经逐页核对**：22 条 △ 条目的题名/作者/年份已由 arXiv 官方元数据接口核对，但摘要之外的具体数字（如某方法的具体提升幅度）未逐页核对正文；报告中若引用精确数值，建议只使用本文件中已标注来源句的数值，或对这些条目再做一次页面级核对。
6. **venue 只保留已核对到的来源**：凡 arXiv 元数据里带 journal_ref / comment（如 ICLR 2024、NeurIPS 2023 D&B、TMLR 2023）或 ACL Anthology / 会议页直接给出的 venue，才写入条目；强度不足以核对 venue 的条目一律只写 arXiv 编号 + 年份，避免把「印象中的会议」写成事实。若开题报告需要完整 venue 字段，请对 10、12、13、15、17、23、34 等条目补一次页面级核对。
