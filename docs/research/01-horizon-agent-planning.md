# Agent 长程/多步决策与规划能力研究进展（调研备忘 A1）

> 用途：BalatroEval 开题报告「研究现状」第一部分（学术侧）。
> 写作时间：2026-11；检索工具：web_search + web_fetch（本机 pwsh 不可用，全程未使用 shell）。
> 引用约定：方括号 `[n]` 对应第 2 节参考文献编号；✅ = 我实际打开页面核对过标题/作者/年份；⏳ = 仅由检索结果页确认 arXiv 编号，未逐条打开。

---

## 1. 分类叙述

### 1.1 推理—行动交织与测试时搜索：从「一次生成」到「显式搜索」

ReAct 最早把「推理轨迹」与「环境动作」交错生成，在 ALFWorld 与 WebShop 上分别比模仿学习/强化学习基线高出 34% 与 10% 绝对成功率，且只用了一到两个 in-context 示例 [1]。它确立了一个关键形式化：一条可观察的「思考→动作」序列就是评测与分析的最小单元，这也是本项目能够逐步判定合法性、逐步计算 regret 的前提。随后的 Reflexion 把「试错」搬到文本空间，用语言化反思 + 情景记忆替代权重更新，HumanEval pass@1 达到 91%（论文对比 GPT-4 的 80%）[2]；Self-Refine 则在同一轮内做「生成—自我反馈—重写」，在 7 个任务上平均绝对提升约 20% [3]。这两条路线的共同点是**把改进寄托于模型自身的判断**，而这正是最脆弱的一环：后来的对照实验显示，在推理任务上不给外部反馈的「内在自纠正」不仅无效，甚至会掉点 [35]。Tree of Thoughts 把 token 级左到右解码扩展成 thought 级的搜索与回溯，在 Game of 24 上把 GPT-4 的成功率从 CoT 的 4% 拉到 74% [5]；LATS 进一步把 MCTS、LM 价值函数与自反思统一起来，HumanEval 92.7%、WebShop 平均 75.9 且完全免梯度 [6]。这一脉的贡献是证明了「测试时计算可以换性能」，局限则非常明确：搜索需要环境可回滚、可重放，并且依赖一个未必可靠的「思考评估器」。对本项目而言，这恰恰是机会——我们的环境规则确定、状态可精确重放，因此「用 oracle 搜索得到的最优动作」是**可计算的真值**，而不是靠模型自评出来的近似值 [6][7]。

### 1.2 分解—规划—验证：把「规划」外置给确定性组件

Plan-and-Solve 先用「先制定计划、再按计划执行」的两段式 prompt 提升零样本 CoT 的稳定性 [4]，但它只解决了「先想后做」的表述问题，没有解决计划是否成立。ReWOO 把规划与观察解耦，先一次性生成完整计划再批量取观测，以降低 token 消耗与重复调用为目标 [10]；DEPS 面向开放世界任务，用「描述—解释—计划—选择」把高层目标拆成可执行的子目标迭代推进 [8]；ADaPT 则按需递归分解，只在子任务确实超出模型能力时才继续往下拆 [9]。这三者的共同思想是：**规划质量应该由子目标是否可达、是否可执行来检验**，而不是由计划文本是否好看来判断。LLM-Modulo 把这一思想推到立场论文的高度：作者认为自回归 LLM 无法可靠地做规划或自我验证，正确形态是让 LLM 充当「通用近似知识源」，由外部基于模型的验证器做紧耦合的双向校验 [7]。这一判断对本项目是直接支撑——我们不是在「让模型学会打牌」，而是在构造一个外部验证器可判定的环境，把模型的规划能力变成可核对的命题 [7][9]。

### 1.3 具身与程序化行动：可执行性本身是一种约束

SayCan 用技能的价值函数（affordance）去约束语言模型的提议，让「说得出」的动作同时是「做得到」的动作，从而在真实移动机械臂上完成长程抽象指令 [11]；Inner Monologue 进一步把环境反馈（成功检测、场景描述）回灌进模型的「内心独白」，形成闭环规划 [12]。ProgPrompt 把动作空间写成 Python 风格的函数签名与前置条件，让「计划」直接成为可解析、可静态检查的程序 [13]；Voyager 把这一思路推到极致，用自动课程 + 不断增长的**可执行代码技能库** + 环境反馈/执行错误驱动的迭代改写，在 Minecraft 上取得 3.3 倍独特物品、2.3 倍移动距离、解锁科技树快 15.3 倍的成绩 [14]。这一脉最重要的方法论启示不是「写得像代码」，而是：**一旦动作被形式化为有限、带前置条件的操作集合，合法性就从「感觉合理」变成「可判定」**。Voyager 的自验证之所以有效，也是因为它验证的是执行结果与执行错误，而不是模型对自己的评价 [14][35]。局限在于，这些系统大多在「动作空间已经给定、物理/规则引擎已经写好」的前提上工作，能力评估仍以终局任务完成度为主，缺乏对「哪一步开始错」的细粒度归因。

### 1.4 评测基准：从终局成功率走向过程指标

这一批基准可以按「可复现性 × 信号粒度」分成六个子类；每一子类都值得单独对照，因为本项目的定位正是「高可复现 + 细粒度可判定信号」这个空格。

#### 1.4.1 交互式与具身环境

ALFWorld 提供文本抽象与具身执行对齐的家庭任务环境，长期是长程交互任务的标准小环境，ReAct 在此取得的增益后来被反复当作「交互式长程」的基线对照 [1][20]；ScienceWorld 用交互式科学实验把多步操作与常识推理结合起来 [21]；TextCraft 是文本版 Minecraft 合成环境，动作空间只有 inventory/craft/get 三类，天然适合作为「多步依赖」的最小测试台 [15]。这一子类的价值在于动作空间有限、状态可枚举，因而**理论上**可以做过程判定；但现有工作基本只报终局成功率，把过程信息浪费掉了。TextCraft 的原始论文出处我未能确认（见 4.C），引用时需降级处理。

#### 1.4.2 网页与桌面

WebArena 用四个真实站点域构造功能正确性判定，最佳 GPT-4 agent 端到端成功率仅 14.41%，而人类为 78.24% [17]；VisualWebArena 把视觉接地引入同一范式 [18]；OSWorld 把任务搬到真实操作系统与桌面应用 [19]。这一子类的优点是判定客观（终局数据库状态或功能正确性），因此结论可信；缺点是只剩一个 0/1 的终局信号，无法回答「从第几步开始走偏」。另外 OSWorld 这类高自由度环境的复现成本很高，跨论文比较时方差主要来自环境而非模型。

#### 1.4.3 任务与工具域

τ-bench 用「用户（由 LM 模拟）—agent—领域 API」的动态对话，通过比对终局数据库状态与标注目标状态来判分，并提出 pass^k 度量行为一致性：即便 gpt-4o 这类函数调用 SOTA 成功率也不到 50%，零售域 pass^8 不足 25% [22]；WebShop 提供真实商品与自然语言指令的购物环境 [23]；GAIA 用需要多步工具与检索的真实问题考察通用助手 [24]；TravelPlanner 用 1225 条意图、约 400 万条记录的多约束行程规划，GPT-4 成功率仅 0.6%，失败集中在「跑题、工具选错、多约束跟踪不住」[25]。这四条工作合起来说明：一旦任务需要多约束同时成立，成功率会断崖式下跌，且下降不是均匀的——它集中在约束交互处。局限是它们只能给出「哪些约束没满足」，不能给出「哪一步决策导致约束失效」。

#### 1.4.4 规划与游戏

PlanBench 借用国际规划竞赛的域与任务，直接测「计划生成」而非常识问答，结论是当前模型在关键规划能力上表现相当有限 [26]；Jericho 以交互小说提供长程、稀疏奖励的文本决策环境 [29]；NetHack Learning Environment 是出了名的高难度长程探索/策略环境 [30]；Crafter 用开放世界生存任务提供「能力谱」式的多指标评估 [31]；MineDojo 用互联网规模知识支撑开放式具身 agent [32]；BALROG 把多个游戏环境统一到一个 agent 基准里，设计细粒度进度指标，并发现模型在提供视觉表征后反而变差 [28]。游戏是长程决策最自然的试验场，BALROG 与本项目最为同域；但它的进度指标来自对「离目标多远」的估计，没有 oracle 分数，也没有把失败拆成「非法 / 算错 / 幻觉 / 规划不足」四类。这正是本项目相对游戏类基准的差异化位置。

#### 1.4.5 代码域（作为长程任务的极端对照）

SWE-bench 用 2294 个真实 GitHub issue 构造需要跨函数、跨文件协调的修复任务，最强模型当年只能解决 1.96% [33]。它的判定是「测试是否通过」，属于天然可验证的一类，因此在方法论上与本项目同源（oracle-based）；区别在于其验证只在终局发生，中间步骤完全不可判定，而本项目的规则环境可以逐步验证。把 SWE-bench 放进综述的意义是证明：长程能力的瓶颈跨域存在，不是某个环境的偶然现象。

#### 1.4.6 过程化评测的先行者

AgentBoard 明确提出「只看终局成功率信息量太少」，给出细粒度的 progress rate 与配套分析工具 [27]；BALROG 的进度指标思路与之相同 [28]。这两者是本课题最直接的方法论先驱：它们已经把「过程」当成一等公民。但它们的 progress 仍依赖人工或模型标注的子目标分解，本质上是对「离终点多远」的**估计**；本项目可以用可枚举的分数 oracle 把同一个量变成**精确值**，从而把「进度」从估计升级为测量。

### 1.5 实证发现：长程失败有结构，且「可靠性」比「能力」更差

第一，**失败随步数累积且集中在后段**。AgentBench 在 8 个环境中系统测试后指出，商用模型与不超过 70B 的开源模型差距显著，且失败的主因被归为「长程推理、决策与指令跟随能力不足」，而非单点知识缺失 [16]；TravelPlanner 的失败分析同样指向「保持任务不跑偏、选对工具、同时跟踪多个约束」这三类长程症状 [25]。第二，**pass@k 会系统性高估可靠性**。τ-bench 用 pass^k（k 次独立试验全部成功的概率）揭示：单次成功率接近 50% 的模型，pass^8 可以低到 25% 以下，说明「会做」与「稳定会做」是两件事 [22]。第三，**小模型在多步任务上退化更严重**，AgentBench 观测到 ≤70B 开源模型在长程环境中的表现与商用模型存在断层，且「用代码数据训练」对不同 agent 任务的影响方向不一致（原文用词为 ambivalent）[16]。第四，**上下文与记忆是独立瓶颈**：Lost in the Middle 发现模型对长上下文中部信息的利用显著劣于首尾（U 型）[34]，而 Reflexion/Voyager 之所以有效，很大程度上是因为它们把「历史」压缩成了反思文本或技能库，而不是把全部轨迹塞回上下文 [2][14]。第五，**自纠正不是免费的**：无外部反馈的内在自纠正会掉点 [35]，这直接否定了「让模型自己判断这一步对不对」的评测/归因方案。第六，**失败需要分类学而不只是率**：MAST 对多智能体系统的失败做了系统归纳与分类，说明「失败模式」本身是可以被结构化标注与统计的对象 [36]。

### 1.6 训练侧：可验证性同时定义了奖励与评测

过程奖励模型（PRM）的经典结论是：对每一步给反馈的过程监督显著优于只对结果给反馈的结果监督，在 MATH 代表性测试子集上达到 78%，并公开了 80 万条步级人工标注 [37]。这与本项目的 oracle 判定器在形式上高度同构——**逐步可判定的环境天然能生产步级标签**，只不过我们的标签来自规则引擎而不是人工。RLVR（可验证奖励强化学习）路线（如 DeepSeek-R1）表明，当奖励信号可以由确定性验证器给出时，纯 RL 就能显著提升多步推理能力 [38]；在 agent 场景，WebRL 用自演化在线课程做 web agent 的 RL 训练 [39]，ArCHer 把多轮交互建模为分层 RL 以处理「轨迹级」信用分配 [40]，FireAct 则证明用少量高质量轨迹做微调就能显著改善 agent 行为（agent 蒸馏的雏形）[41]。这些工作对本项目的意义是双向的：一方面，它们说明「确定性验证器 + 轨迹级信号」是当前训练侧的主流基础设施，我们的环境可以直接复用为 verifier 或 PRM 标注器；另一方面，它们也提示了一个评测风险——**当一个确定性环境被用作训练奖励时，模型可能学到的是这个环境的规则细节，而不是可迁移的规划能力**，因此评测必须使用 held-out 的规则变体或参数扰动 [38][39]。

---

## 2. 参考文献

> 格式：`N. 作者. *Title*. Venue/arXiv:ID, Year. URL | 核实状态 | 一句话：解决了什么 + 与本项目关系`

**A. 推理—行动交织与测试时搜索**

1. Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao. *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023; arXiv:2210.03629. https://arxiv.org/abs/2210.03629 | ✅ | 首次把推理轨迹与动作交错生成，ALFWorld/WebShop 绝对成功率分别 +34%/+10%；本项目把「思考→动作」轨迹作为可逐步判定的最小评测单元。
2. Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, Shunyu Yao. *Reflexion: Language Agents with Verbal Reinforcement Learning*. arXiv:2303.11366, 2023. https://arxiv.org/abs/2303.11366 | ✅ | 用语言化反思 + 情景记忆替代权重更新，HumanEval pass@1 91%；提示我们「跨局重试」会掩盖单局能力，评测须区分「单次」与「k 次重试」。
3. Aman Madaan, Niket Tandon, Prakhar Gupta, et al. *Self-Refine: Iterative Refinement with Self-Feedback*. arXiv:2303.17651, 2023. https://arxiv.org/abs/2303.17651 | ✅ | 同一模型迭代给出自我反馈并改写，7 任务平均绝对提升约 20%；其「自我评价」假设被 [35] 反驳，故不能作为本项目归因依据。
4. Lei Wang et al. *Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models*. arXiv:2305.04091, 2023. https://arxiv.org/abs/2305.04091 | ⏳ | 用「先计划后执行」的两段式提示稳定零样本推理；是本项目「规划不足」失败类在提示层面对照的最小基线。
5. Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths, Yuan Cao, Karthik Narasimhan. *Tree of Thoughts: Deliberate Problem Solving with Large Language Models*. NeurIPS 2023; arXiv:2305.10601. https://arxiv.org/abs/2305.10601 | ✅ | 把解码扩展为 thought 级搜索与回溯，Game of 24 从 4% 提升到 74%；说明「逐步最优 ≠ 终局最优」，支持我们用 Local Regret 而非仅终局胜负刻画能力。
6. Andy Zhou, Kai Yan, Michal Shlapentokh-Rothman, Haohan Wang, Yu-Xiong Wang. *Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models*. arXiv:2310.04406, 2023（v3 2024）. https://arxiv.org/abs/2310.04406 | ✅ | 用 MCTS + LM 价值函数 + 自反思统一推理/行动/规划，HumanEval 92.7%、WebShop 平均 75.9 且免梯度；其树搜索需要可回滚环境，而本项目确定性环境使 oracle 搜索得到的是真值而非近似。

**B. 分解—规划—验证**

7. Subbarao Kambhampati, Karthik Valmeekam, Lin Guan, Mudit Verma, Kaya Stechly, Siddhant Bhambri, Lucas Saldyt, Anil Murthy. *LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks*. ICML 2024; arXiv:2402.01817. https://arxiv.org/abs/2402.01817 | ✅ | 立场论文：LLM 无法可靠自规划与自验证，须与外部模型验证器紧耦合；这是本项目「oracle 判定器 + 归因」方法论最直接的学术依据。
8. Zihao Wang et al. *Describe, Explain, Plan and Select: Interactive Planning with LLMs Enables Open-World Multi-Task Agents*. NeurIPS 2023; arXiv:2302.01560. https://arxiv.org/abs/2302.01560 | ⏳ | 用「描述—解释—计划—选择」迭代拆解开放世界长程目标；其子目标分解粒度可作为本项目场景分层的参照。
9. Archiki Prasad et al. *ADaPT: As-Needed Decomposition and Planning with Language Models*. arXiv:2311.05772, 2023. https://arxiv.org/abs/2311.05772 | ⏳ | 仅在子任务超出能力时递归分解，减少无效规划；对应本项目「规划深度」这一分层维度。
10. Binfeng Xu et al. *ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models*. arXiv:2305.18323, 2023. https://arxiv.org/abs/2305.18323 | ⏳ | 把规划与观测取回解耦，先出完整计划再批量取数；说明「规划」可与「执行」分离度量，支持我们把 plan 质量与 action 质量分开统计。

**C. 具身与程序化行动**

11. Michael Ahn, Anthony Brohan, Noah Brown, et al. *Do As I Can, Not As I Say: Grounding Language in Robotic Affordances*（SayCan）. arXiv:2204.01691, 2022. https://arxiv.org/abs/2204.01691 | ✅ | 用技能价值函数约束 LM 提议的可行动作，使「说得出」等于「做得到」；等价于本项目的 Legality 指标：合法性应作为独立能力轴而非与得分解耦。
12. Wenlong Huang et al. *Inner Monologue: Embodied Reasoning through Planning with Language Models*. arXiv:2207.05608, 2022. https://arxiv.org/abs/2207.05608 | ⏳ | 把成功检测、场景描述等环境反馈回灌进模型的闭环规划；其「反馈质量决定闭环质量」直接对应本项目判定器精度对归因可信度的影响。
13. Ishika Singh et al. *ProgPrompt: Generating Situated Robot Task Plans using Large Language Models*. arXiv:2209.11302, 2022. https://arxiv.org/abs/2209.11302 | ⏳ | 用带前置条件的函数式动作签名生成可解析计划；证明「动作形式化 ⇒ 合法性可判定」，是本项目动作空间设计的直接先例。
14. Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu, Linxi Fan, Anima Anandkumar. *Voyager: An Open-Ended Embodied Agent with Large Language Models*. arXiv:2305.16291, 2023. https://arxiv.org/abs/2305.16291 | ✅ | 自动课程 + 可执行代码技能库 + 执行错误驱动迭代，Minecraft 上 3.3× 独特物品、科技树快 15.3×；其自验证依赖「执行结果」这一可判定信号，支持本项目用确定性判定器替代模型自评。
15. OSU-NLP-Group. *EarlyExperience — `envs/textcraft` 环境实现（TextCraft 文本合成基准的开源实现）*. GitHub, 2024. https://github.com/OSU-NLP-Group/EarlyExperience/blob/main/envs/textcraft/README.md | ⏳ | 文本版 Minecraft 合成任务，动作仅 inventory/craft/get 三类，是「多步依赖」的最小测试台；其原始论文出处我未能确认（见第 4 节），本项目只借用其「小动作空间 × 深依赖链」的设计思路。

**D. 评测基准**

16. Xiao Liu, Hao Yu, Hanchen Zhang, et al. *AgentBench: Evaluating LLMs as Agents*. ICLR 2024; arXiv:2308.03688. https://arxiv.org/abs/2308.03688 | ✅ | 8 环境系统评测，指出商用与 ≤70B 开源模型差距显著、主因是长程推理/决策/指令跟随不足；为本项目「长程错误累积」提供了最常被引用的经验证据。
17. Shuyan Zhou, Frank F. Xu, Hao Zhu, et al. *WebArena: A Realistic Web Environment for Building Autonomous Agents*. arXiv:2307.13854, 2023. https://arxiv.org/abs/2307.13854 | ✅ | 四域真实站点 + 功能正确性判定，最佳 GPT-4 agent 14.41% vs 人类 78.24%；说明只有终局 0/1 信号时无法定位失败原因，反衬过程指标的必要性。
18. Jing Yu Koh, Robert Lo, Lawrence Jang, et al. *VisualWebArena: Evaluating Multimodal Agents on Realistic Visually Grounded Web Tasks*. arXiv:2401.13649, 2024. https://arxiv.org/abs/2401.13649 | ⏳ | 把视觉接地引入 web agent 评测；提示本项目若要扩展多模态观察，须单独报告「视觉理解错误」而非混入规划失败。
19. Tianbao Xie, Danyang Zhang, Jixuan Chen, et al. *OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments*. arXiv:2404.07972, 2024. https://arxiv.org/abs/2404.07972 | ⏳ | 真实操作系统/桌面应用中的开放式任务基准；代表「高自由度、难复现」一端，与本项目「低自由度、完全可复现」形成方法论对照。
20. Mohit Shridhar, Xingdi Yuan, Marc-Alexandre Côté, Yonatan Bisk, Adam Trischler, Matthew Hausknecht. *ALFWorld: Aligning Text and Embodied Environments for Interactive Learning*. ICLR 2021; arXiv:2010.03768. https://arxiv.org/abs/2010.03768 | ✅ | 文本抽象与具身执行对齐的家庭长程任务环境；是 ReAct 等方法的标配评测场，可作为本项目「短程子任务」参照难度。
21. Ruoyao Wang, Peter Jansen, Marc-Alexandre Côté, Prithviraj Ammanabrolu. *ScienceWorld: Is your Agent Smarter than a 5th Grader?*. arXiv:2203.07540, 2022. https://arxiv.org/abs/2203.07540 | ⏳ | 交互式科学实验环境，要求多步操作与常识推理结合；其「步骤可验证但组合爆炸」的特点与本项目规则子集相似。
22. Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan. *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains*. arXiv:2406.12045, 2024. https://arxiv.org/abs/2406.12045 | ✅ | 提出 pass^k 度量多轮行为一致性；gpt-4o 成功率 <50%、零售域 pass^8 <25%；本项目必须并列报告 pass@k 与 pass^k，否则会高估可靠性。
23. Shunyu Yao, Howard Chen, John Yang, Karthik Narasimhan. *WebShop: Towards Scalable Real-World Web Interaction with Grounded Language Agents*. arXiv:2207.01206, 2022. https://arxiv.org/abs/2207.01206 | ⏳ | 真实商品 + 自然语言指令的购物环境，提供「可达但需多步筛选」的中等长度任务；可作本项目难度梯度中段参照。
24. Grégoire Mialon, Clémentine Fourrier, Craig Swift, et al. *GAIA: A Benchmark for General AI Assistants*. arXiv:2311.12983, 2023. https://arxiv.org/abs/2311.12983 | ⏳ | 需要多步工具调用与检索的真实问题集，人类与最强通用助手差距巨大；代表「概念简单但对 agent 极难」的评测取向。
25. Jian Xie, Kai Zhang, Jiangjie Chen, et al. *TravelPlanner: A Benchmark for Real-World Planning with Language Agents*. ICML 2024; arXiv:2402.01622. https://arxiv.org/abs/2402.01622 | ✅ | 1225 条意图、约 400 万条记录的多约束行程规划，GPT-4 成功率仅 0.6%，失败集中于跑题/工具选错/约束跟踪不住；为本项目「规划不足」子类（约束遗忘、子目标失配）提供了可直接借用的失败描述。
26. Karthik Valmeekam, Matthew Marquez, Alberto Olmo, Sarath Sreedharan, Subbarao Kambhampati. *PlanBench: An Extensible Benchmark for Evaluating Large Language Models on Planning and Reasoning about Change*. NeurIPS 2023 (Datasets & Benchmarks); arXiv:2206.10498. https://arxiv.org/abs/2206.10498 | ✅ | 借用规划竞赛域直接测计划生成而非常识问答，结论是关键规划能力仍很有限；与本项目「用形式化规则而非自然语言描述来检验规划」的取向一致。
27. Chang Ma, Junlei Zhang, Zhihao Zhu, et al. *AgentBoard: An Analytical Evaluation Board of Multi-turn LLM Agents*. NeurIPS 2024; arXiv:2401.13178. https://arxiv.org/abs/2401.13178 | ✅ | 指出「只看终局成功率」信息量不足，提出细粒度 progress rate 与分析工具包；这是与本项目过程指标最接近的工作，但其 progress 依赖标注子目标，是估计值。
28. Davide Paglieri, Bartłomiej Cupiał, Samuel Coward, et al. *BALROG: Benchmarking Agentic LLM and VLM Reasoning On Games*. ICLR 2025; arXiv:2411.13543. https://arxiv.org/abs/2411.13543 | ✅ | 多游戏统一 agent 基准 + 细粒度进度指标，并发现提供视觉表征后部分模型反而更差；与本项目最同域（游戏 + 长程 + 进度指标），差别在于它没有 oracle 分数与失败归因。
29. Matthew Hausknecht, Prithviraj Ammanabrolu, Marc-Alexandre Côté, Xingdi Yuan. *Interactive Fiction Games: A Colossal Adventure*（Jericho）. arXiv:1909.05398, 2019. https://arxiv.org/abs/1909.05398 | ⏳ | 交互小说长期被用作长程、稀疏奖励文本决策环境；其「组合动作空间 + 部分可观测」是本项目规则子集刻意规避的两个难点。
30. Heinrich Küttler, Nantas Nardelli, Alexander H. Miller, et al. *The NetHack Learning Environment*. arXiv:2006.13760, 2020. https://arxiv.org/abs/2006.13760 | ⏳ | 高难度长程探索/策略环境，常被用作 agent 能力的上限压力测试；说明「长程」若不配可判定信号，很难做失败归因。
31. Danijar Hafner. *Benchmarking the Spectrum of Agent Capabilities*（Crafter）. arXiv:2109.06780, 2021. https://arxiv.org/abs/2109.06780 | ⏳ | 用开放世界生存任务提供多维度能力谱而非单一分数；支持本项目「多指标 + 分层」而非单一排行榜的评测设计。
32. Linxi Fan, Guanzhi Wang, Yunfan Jiang, et al. *MineDojo: Building Open-Ended Embodied Agents with Internet-Scale Knowledge*. NeurIPS 2022 (Datasets & Benchmarks); arXiv:2206.08853. https://arxiv.org/abs/2206.08853 | ⏳ | 以互联网规模知识支撑开放式具身 agent 的模拟器与基准套件；其开放性带来的评测方差问题，正是本项目选择「小规则子集」的反面理由。
33. Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, Karthik Narasimhan. *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?*. ICLR 2024; arXiv:2310.06770. https://arxiv.org/abs/2310.06770 | ✅ | 2294 个真实 issue 需跨函数/跨文件协调，当年最强模型仅 1.96%；作为「代码域长程任务」对照，说明长程能力瓶颈跨域普遍存在。

**E. 实证发现**

34. Nelson F. Liu, Kevin Lin, John Hewitt, et al. *Lost in the Middle: How Language Models Use Long Contexts*. arXiv:2307.03172, 2023. https://arxiv.org/abs/2307.03172 | ⏳ | 发现模型对长上下文中部信息利用显著劣于首尾（U 型）；提示本项目必须固定状态序列化格式并做历史窗口长度消融，否则分数会混入 prompt 效应。
35. Jie Huang, Xinyun Chen, Swaroop Mishra, Huaixiu Steven Zheng, Adams Wei Yu, Xinying Song, Denny Zhou. *Large Language Models Cannot Self-Correct Reasoning Yet*. ICLR 2024; arXiv:2310.01798. https://arxiv.org/abs/2310.01798 | ✅ | 无外部反馈的内在自纠正不仅无效、甚至掉点；这是本项目坚持「确定性判定器而非模型自评」的直接理由。
36. Mert Cemri et al. *Why Do Multi-Agent LLM Systems Fail?*（MAST）. NeurIPS 2025; arXiv:2503.13657. https://arxiv.org/abs/2503.13657 | ⏳ | 系统归纳并标注 LLM 多智能体系统的失败模式，形成可统计的失败分类学；本项目 4 类判定器的互斥性/覆盖率设计可借用其标注一致性做法。

**F. 训练侧（与评测的关系）**

37. Hunter Lightman, Vineet Kosaraju, Yura Burda, et al. *Let's Verify Step by Step*. arXiv:2305.20050, 2023. https://arxiv.org/abs/2305.20050 | ✅ | 过程监督显著优于结果监督，MATH 子集 78%，公开 80 万条步级标注（PRM800K）；与本项目 oracle 逐步判定同构——我们的步级标签来自规则引擎而非人工。
38. DeepSeek-AI. *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning*. arXiv:2501.12948, 2025. https://arxiv.org/abs/2501.12948 | ⏳ | RLVR：奖励可由确定性验证器给出时，纯 RL 即可显著提升多步推理；说明「可验证」同时是训练奖励与评测指标的前提，也提示训练-评测同源会污染结论。
39. Zeqiu Wu et al. *WebRL: Training LLM Web Agents via Self-Evolving Online Curriculum Reinforcement Learning*. ICLR 2025; arXiv:2411.02337. https://arxiv.org/abs/2411.02337 | ⏳ | 用自演化在线课程做 web agent 的在线 RL，缓解长程任务成功信号稀疏；其课程思想可迁移为本文评测的难度分层（长度/分支/前瞻深度）。
40. Yifei Zhou, Andrea Zanette, Jiayi Pan, Sergey Levine, Aviral Kumar. *ArCHer: Training Language Model Agents via Hierarchical Multi-Turn RL*. arXiv:2402.19446, 2024. https://arxiv.org/abs/2402.19446 | ⏳ | 把多轮交互建模为分层 RL，处理轨迹级信用分配；对应本项目「失败发生在第几步」的归因需求。
41. Baian Chen, Chang Shu, Ehsan Shareghi, Nigel Collier, Karthik Narasimhan, Shunyu Yao. *FireAct: Toward Language Agent Fine-tuning*. arXiv:2310.05915, 2023. https://arxiv.org/abs/2310.05915 | ⏳ | 用少量高质量轨迹微调即可显著改善 agent 行为（agent 蒸馏雏形）；其「轨迹数据贵」恰是 oracle 环境可自动产出轨迹的价值所在。

---

## 3. 对本项目的启示

1. **主指标必须是「终局成功率 + oracle Local Regret」双轨，且 regret 要分层报告。** ToT/LATS 已经证明「逐步不优」与「终局失败」不是同一件事 [5][6]；只报成功率会把「一路最优但被一张坏牌翻盘」和「第 3 步就违规」混为一谈。建议按 horizon 长度 / 决策点分支度 / 需要前瞻的深度三个维度分桶报 regret 均值与分位数。
2. **必须报 pass^k 而不只是 pass@k，并额外报「首次失败步」分布。** τ-bench 的 pass^8 < 25%（对应单次成功率近 50%）说明 pass@k 会系统性高估可靠性 [22]；本项目环境确定、可重放，最适合用固定种子做 k 次独立运行，报告 pass^k(k=1,3,5,8) 与失败步直方图。
3. **Legality 与 Optimality 必须拆成两个正交指标，不要合成一个分数。** SayCan 的 affordance 约束与 ProgPrompt 的前置条件检查都说明「可行性」是独立能力轴 [11][13]；AgentBench 也把指令跟随失败与决策失败分开讨论 [16]。合成一个 0–1 分会让「非法但本可最优」与「合法但次优」两类错误不可区分，直接破坏归因。
4. **场景分层按「决策深度 × 分支度 × 约束数量」三轴网格，而不是按游戏场景/角色划分。** TravelPlanner 的 0.6% 主要来自多约束跟踪与工具选择 [25]，BALROG 的进度指标随难度梯度变化明显 [28]，AgentBoard 的 progress rate 也依赖难度分层 [27]；我们的分层应让「规划不足」这一失败类在每一深度层都有可出现样本，否则该类判定器的召回率无法估计。
5. **失败判定器必须报告互斥性、覆盖率与判定器自身的误差。** MAST 的价值在于把失败模式变成可统计、可标注一致的对象 [36]；本项目 4 类判定器中「算分错误」与「规则幻觉」在语义上容易重叠，「规划不足-启发式」又天然带主观性，建议：给出判定优先级（非法 > 算分错误 > 规则幻觉 > 规划不足）、报告判定器间冲突率与人工复核 κ 值，并明确声明「规划不足」类是启发式而非 oracle 判定。
6. **不要用模型自评/自纠正充当判定器或归因器。** 无外部反馈的自纠正在推理任务上会掉点 [35]，LLM-Modulo 也主张 LLM 不能可靠自验证 [7]；本项目的比较优势正是「判定权在 oracle 而非模型」，这一点应写进方法论而非仅写在实现细节里。
7. **上下文与记忆必须作为受控变量，而不是自由发挥。** Lost in the Middle 的 U 型现象 [34] 意味着同一模型在不同历史窗口下分数会有系统性偏差；建议固定状态文本序列化模板、固定历史窗口（并做 0/1/2× 窗口消融）、把「记忆模块」列为可选消融项而非默认配置，否则跨模型比较不公平。
8. **若后续接训练（PRM/RLVR/蒸馏），评测集必须留出 held-out 规则变体。** PRM 与 RLVR 都依赖可验证奖励 [37][38]，我们的 oracle 天然可做 verifier，但一旦环境同时用于训练与评测，模型可能只学了这套规则 [38][39]；建议保留一组「同构但参数/卡牌池不同」的环境变体专门做泛化评测。

---

## 4. 证据分级与不确定项

**A. 论文实测（有具体实验数字，可直接引用）**
- ReAct 在 ALFWorld/WebShop 上 +34%/+10% 绝对成功率 [1]；Reflexion HumanEval pass@1 91% [2]；ToT Game of 24 4%→74% [5]；LATS HumanEval 92.7%、WebShop 平均 75.9 [6]；Self-Refine 7 任务平均 +20% 绝对 [3]。
- WebArena 14.41% vs 人类 78.24% [17]；TravelPlanner GPT-4 0.6% [25]；τ-bench gpt-4o <50%、零售 pass^8 <25% [22]；SWE-bench 最强模型 1.96% [33]。
- 过程监督 vs 结果监督、MATH 子集 78%、PRM800K 80 万条 [37]；无外部反馈自纠正会掉点 [35]；AgentBench 商用 vs ≤70B 开源差距与「长程推理主要瓶颈」的归因 [16]。
- Voyager 的 3.3×/2.3×/15.3× 为其自报数据 [14]。

**B. 作者主张 / 立场性结论（非受控实验，引用时应标注为观点）**
- LLM-Modulo「LLM 不能自规划、不能自验证」是 position paper 的核心主张 [7]；PlanBench 的「LLM 规划能力不足」是基准实测，但其外推为「LLM 不会规划」属于作者解释 [26]。
- 第 1.5 节中「失败集中在后段」「pass@k 高估可靠性」是我对多篇论文的综合归纳，其中「集中在后段」缺少跨环境的统一量化证据，TravelPlanner/AgentBench 只提供了定性失败分析 [16][25]。
- 第 3 节全部为我的设计建议（推论），不是文献结论。

**C. 不确定 / 未能核实的部分**
1. **TextCraft 的原始论文出处未确认。** 我只能追溯到开源实现与后续使用它的工作 [15]，故只引用环境实现页并降级为 ⏳；开题报告若需正式引用，建议改引一个明确以 TextCraft 为实验平台的论文，或干脆不引用。
2. **⏳ 条目的作者列表未逐字核对。** 这些条目的标题与 arXiv 编号来自检索结果页（ar5iv / export.arxiv.org / 会议论文集 PDF），URL 按 arXiv 规范格式给出但未逐条打开；第一作者与年份依据检索结果推断，投稿前应逐条打开 abs 页复核。
3. **venue 标注只写有直接证据的。** 仅当 arXiv abs 页的 Comments 字段或检索到的会议论文集页面明确给出会议时，我才写 venue（如 AgentBench ICLR 2024、ToT NeurIPS 2023、TravelPlanner ICML 2024、BALROG ICLR 2025）；其余只写 arXiv，避免误标。
4. **一个必须说明的检索教训：** 我最初凭记忆给 ScienceWorld 填的 arXiv 编号（2203.00504）实际是一篇心电图信号处理论文，打开后才发现错误。因此本文所有 ✅ 条目都是「先打开页面、再写入」，凭记忆的编号一律不采用；这也是我把「打开 abs 页核对」设为硬性流程的原因。
5. **「小模型多步能力退化」的时效性存疑。** AgentBench 的观测基于 2023–2024 年模型 [16]，对 2026 年的开源小模型是否仍成立未知；开题时宜表述为「该现象在 AgentBench 时代被观测到」，而非普适定律。
6. **pass^k 与 Local Regret 的相关性没有文献直接验证。** 二者一个测跨局稳定性、一个测单局决策质量，理论上正交，但缺乏实证；这本身可以作为本项目的一个可检验假设（例如 H：低 regret 的模型 pass^k 更高）。

**D. 检索降级说明**
- 本机 pwsh 不可用，且 web_search 部分查询返回明显无关结果（例如把 TextCraft 检索引向无关的多智能体论文），因此采用「先搜索定位 arXiv 编号 → 再 web_fetch 打开 abs 页核对」的两段式流程；对无法打开或无法定位的条目统一标 ⏳ 并在正文降低断言强度，而不是删掉或凭记忆补全。
