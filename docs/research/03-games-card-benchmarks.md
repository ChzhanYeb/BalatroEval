# 03 · 棋牌博弈 AI 与游戏化 Agent 基准：研究现状调研（BalatroEval 开题报告素材）

> 调研人：res-games（Team A3）｜检索日期：2026-11-12（UTC+8）｜写入范围：仅本文件
> 检索手段：`web_search` + `web_fetch`（arXiv abs 页、会议虚拟站、Zenodo、GitHub、社区 Wiki）
> 核实标记：**✅ 已打开页面核对**（标题/作者/年份/摘要均以页面为准）；**⏳ 仅搜索结果**（URL 可点击，元数据来自检索结果摘要，未逐页打开）

**一句话结论**：牌类 AI 在"竞技求解"方向已高度成熟（CFR 谱系 → 超人级程序），但**"把牌类游戏反过来当作 Agent 评测环境"的工作仍处在早期**；主流 LLM 游戏基准（BALROG、lmgame-Bench、Jericho、NLE、Crafter、ALE 等）几乎全部只输出**标量总分**，既没有 oracle 最优值，也没有步骤级失败归因。Balatro 在学术上**刚刚起步**（arXiv 全库仅 2 条命中，无主会/期刊论文），正是一个"可判定、可算 regret、尚无占位者"的空档。

---

## 1. 分类叙述

### 1.1 不完全信息博弈与牌类 AI：从 CFR 到超人程序

不完全信息博弈的算法主线是反事实 regret 最小化（CFR）家族。Zinkevich 等提出反事实 regret 并证明"最小化反事实 regret 即最小化整体 regret，从而自博弈收敛到 Nash 均衡"，在 limit Texas Hold'em 上把可解规模推到 10^12 状态量级 [1]；此后十余年该家族持续演进，2025 年的工作仍在把折扣/预测型 CFR 变体与神经网络结合以适配更大牌局 [2]。工程化落地由三个标志性系统完成：Libratus 在一对一无限注德州扑克中击败顶级职业选手 [3]，Pluribus 把超人水平扩展到六人桌 [4]，而一对一限注德州扑克则已被"完全求解"（给出了近似 Nash 策略与可利用度上界）[5]；Rubin 与 Watson 的综述系统整理了该领域的抽象、求解与评测口径 [6]。中文/亚洲牌类另有两条重要分支：DouZero 用深度 Monte-Carlo + 动作编码在斗地主上超越既有程序并登顶 Botzone（344 个 AI 中第一）[7]；Suphx 用全局奖励预测、oracle guiding 与运行时策略适配，在 Tenhou 平台达到"高于 99.99% 官方排名人类玩家"的稳定段位 [8]。合作型牌类以 Hanabi 为代表：它把"推断他者信念/意图"（theory of mind）推到前台，并配套开源环境与统一的实验框架 [9]，其"conventions（约定）"问题至今仍是人机协作研究的活跃题材。桥牌方向，Lockhart 等用第三方手写机器人（WBridge5 一类）生成初始数据并作为合作/评测伙伴，在"与自身搭档、与既有机器人搭档、与人类搭档"三种设定下刷新叫牌水平 [10]；更早的 GIB 则是专家级桥牌程序的经典代表 [11]。此外，OpenSpiel [12] 与 RLCard [13] 把上述博弈做成统一 API 的开源环境，提供精确博弈树遍历、最佳响应（best response）与可利用度计算，是"可计算评测"的工程基础设施。

**对本项目的意义**：这一脉给了 BalatroEval 两个可直接借用的方法论基座——(a) 用**可利用度/regret**而非胜率来度量策略质量 [1][5][12]；(b) 用**统一环境 API + 精确博弈树**来保证评测可复算 [12][13]。但也要注意其反面：这些工作全部把"牌"当作**要打败的对手**，没有一个把牌类游戏当作**诊断 Agent 推理失败的探针** [3][4][7][8]。

### 1.2 牌类游戏作为 LLM 能力评测：刚起步，且口径未定

把卡牌游戏系统性地用于 LLM 能力评测，是 2025 年前后才成形、并进入主会视野的方向（检索范围内最早的系统性工作是 2025 年的 NeurIPS 论文）。Wang 等在八款卡牌游戏上系统评估 LLM：结论是"经高质量对局数据监督微调后 LLM 可接近强游戏 AI"，但同时观察到**掌握复杂游戏会损害通用能力**（可用通用指令数据缓解）[14]。lmgame-Bench 则从"能不能用游戏评测 LLM"这一方法论问题切入，指出直接让 LLM 玩游戏做评测会失效，原因有三：**视觉感知脆弱、prompt 敏感、数据污染**，因而需要统一 Gym 风格 API + 轻量感知/记忆脚手架 + 防污染设计，并用 13 个模型验证其区分度 [15]。这两条恰好标出了本项目的位置：卡牌 + LLM 的评测**已被认为有意义**，但现有做法仍以"分数/胜率"为终点，**没有回答"它为什么输"**。

### 1.3 游戏作为 Agent 基准：可判定性与真实感的权衡

游戏基准的谱系可以按"可判定性 ↔ 真实感"排开。一端是 ALE/Atari：环境确定、分数精确，但语义贫瘠、且需要 sticky actions 等协议抑制"利用确定性"的退化解 [25][33]。中间是 Crafter（开放世界生存，用**语义化成就**解锁率刻画能力谱）[19]、NetHack Learning Environment（**程序生成 + 随机**、富交互、强调探索与泛化，代价是可复现性与判定难度上升）[18]、Jericho（纯文本交互小说，动作空间是**自由文本**，组合爆炸 + 语言理解 + 常识推理三重困难）[17]、TextWorld（程序化生成文本游戏，自带 ground-truth 通关路径）[23]、ScienceWorld（小学科学任务，0–100 分）[24]、MineRL/Voyager（Minecraft 长程开放任务，用奖励或"独特物品/科技树里程碑"计数）[20][21]、Cradle（GUI 通用计算机控制，任务成功由脚本判定）[22]。另一端是 BALROG：直接复用上述 RL 环境，用**细粒度指标**测 LLM/VLM 的 agentic 能力，并发现"给视觉输入后部分模型反而更差" [16]。把这些基准并列可以看出一个共同设计取向：**为了"真实"，它们容忍了随机性、隐藏信息与不可枚举的动作空间；代价是"成功"只能被定义成一个归一化标量**（进度百分比、成就数、human-normalized score），而标量无法回答"哪一步错了"。

### 1.4 与 Balatro 直接相关的学术工作：**刚刚出现，尚无同行评议主会论文**

这是本次调研最需要精确表述的一节（务必不要在报告里写"完全没有"或"已有大量研究"）：

- **arXiv 全库检索（all fields = "Balatro"，2026-11-12）仅命中 2 条**（检索结果页已打开核对）：
  1. **Periasami, Gupta, Cheng, Rosales. _Reinforcement Learning for the Game of Balatro: A Fast Simulator and Two-Policy Training Approach_. arXiv:2610.39049, 2026.** 明确写"Balatro 上已发表的 RL 结果仍然稀少（Published RL results on the game remain scarce）"；指出三大难点：**约 3000 个状态相关动作、数百步决策且奖励稀疏、抽牌与商店生成普遍随机**；给出 Rust 高速模拟器（用 BalatroBot 对真实客户端做 state-diff 校验）+ 动态合法动作掩码 + "盲注战术策略 / 商店战略策略"双策略 PPO；结果首盲通过率 >99%、平均最大 ante 收敛到 3/8，并把剩余差距定位到**长程战略规划**而非战术出牌。**已接收于 EXAG 2026（AIIDE Workshop on Experimental AI in Games）——是 workshop，不是主会/期刊** [26]。
  2. **Che 等. _DemoEvolve: Demonstration-Guided Harness Evolution under Sparse Feedback_. arXiv:2605.24539, 2026.** 把 Balatro 与 Slay the Spire 2 作为两个长程稀疏反馈评测环境，在 **held-out seeds** 上报告"平均封顶最终轮进度 16.83 → 20.00（Balatro）"。它把 Balatro 当**评测床**而非研究对象，且**只报进度/分数，不做失败归因** [27]。
- **非同行评议来源**：Zenodo 上有一条 2026-10 的**课程研究提案（resource type = Proposal，非论文）**《Jokers in the Machine: Evaluating RL vs. LLM Agent Reasoning in a Complex Roguelike Card Game》，提出扩展开源环境 balatro-gym、训练 PPO 并与 prompt-based LLM Agent 对比，主张"超越胜率"的指标（战术决策质量、协同识别）[28]。它证明社区已在想同一件事，但**不构成同行评议工作**，报告中只能作为"研究动向"引用。
- **开源环境侧**：`balatro-gym`（Gymnasium 接口）[29]、`BalatroBot`（真实客户端自动化接口，被 [26] 用作 state-diff 基准）[26] 已存在，说明"用真实游戏做环境"在工程上可行。
- **结论（可直接写入报告）**：**截至 2026-11-12，未发现以 Balatro 为对象、发表于机器学习/游戏 AI 主会或期刊的同行评议论文；arXiv 仅有 1 篇 Balatro 专项工作（EXAG 2026 workshop）与 1 篇把 Balatro 当评测环境的预印本；主流 LLM 游戏基准（BALROG [16]、lmgame-Bench [15]）的游戏清单中未见 Balatro 类卡牌 Roguelike（据其摘要与项目页判断）。** 因此“Balatro 上的长线规划评测（可判定规则子集）”仍近乎空白，失败归因只是其中的诊断层，不构成独立空白。

### 1.5 游戏环境的可复现性惯例：seed、版本锁定与回放

RL/Agent 基准的复现性有一组相对成熟的惯例，本项目应显式对齐。第一，**固定种子 + 多种子报告**：DemoEvolve 已在 held-out seeds 上报告 Balatro 指标 [27]，说明"按 seed 划训练/测试"在该游戏上已被接受；Balatro 本体也存在官方"Seeded Run"机制——**种子（0–8 位大写字母数字，有效种子约 2.3×10^12）决定所有随机要素**，商店/凭证/补充包/Boss 盲注等以"队列"形式由种子预定（社区 Wiki 依据 1.0.1o 源码整理）[30]，这使"固定 seed = 固定牌序与商店序列"成为可验证事实而非口头承诺。第二，**环境版本锁定与实现正确性交叉验证**：Balatro 的 RL 工作用 state-diff 把自建模拟器对齐真实客户端 [26]，这与 ALE 通过模拟器版本固定来保证可比性是同一思路 [25]。第三，**随机性协议显式化**：Atari 基准的经典教训是需要 sticky actions 等协议避免"确定性地被利用" [33]；NLE 则明确以"程序生成 + 随机"为特性，代价是跨 seed 方差必须被报告 [18]。第四，**统计显著性与方差报告**：Henderson 等系统证明 RL 结果对 seed、超参、实现细节高度敏感，"单次运行 + 单点比较"不可信 [31]；NeurIPS 复现性报告则把代码/数据/种子/日志的提交规范制度化 [32]。第五，**episode 可回放**：Who&When 类工作把"失败日志 + 步骤级标注"作为归因的数据前提 [34]，对应到本项目即"每局可重放 + 每步可定位"。

**对本项目的意义**：BalatroEval 的"seed 固定 + RNG/环境版本锁定 + 全轨迹回放"不是额外工程负担，而是上述惯例的直接落地；而且 Balatro 的种子机制让"同一起手、同一商店序列"在**真实游戏语义**下成立，比人为造一个确定性环境更有说服力 [30]。

---

## 2. 参考文献表（34 条；✅ = 已打开页面，⏳ = 仅搜索结果）

> 格式：`N. 作者. *Title*. Venue/arXiv:ID, Year. URL | 核实状态 | 解决了什么 + 与本项目关系`

### A. 不完全信息博弈与牌类 AI（CFR 谱系 / 竞技求解）

1. M. Zinkevich, M. Johanson, M. Bowling, C. Piccione. *Regret Minimization in Games with Incomplete Information*. NIPS 2007 (Spotlight). https://nips.cc/virtual/2007/spotlight/639 | ✅ | 提出反事实 regret（CFR）：最小化反事实 regret 即最小化整体 regret，自博弈收敛 Nash；把 limit Hold'em 抽象解到 10^12 状态。**regret 作为策略质量度量**的源头，本项目"oracle 最优 + regret"口径的理论祖先。
2. H. Xu, K. Li, H. Fu, Q. Fu, J. Xing, J. Cheng. *Deep (Predictive) Discounted Counterfactual Regret Minimization*. AAAI 2026; arXiv:2511.08174, 2025. https://arxiv.org/abs/2511.08174 | ✅ | 把折扣/预测型 CFR 变体以 model-free 神经网络方式近似，在大型扑克上更强对抗性。说明 CFR 家族仍在演进，且**演进目标始终是"解得更强"而非"评得更准"**。
3. N. Brown, T. Sandholm. *Superhuman AI for heads-up no-limit poker: Libratus beats top professionals*. Science 359(6374), 2018. https://www.science.org/doi/10.1126/science.aao1733 | ⏳ | 一对一无限注德州扑克击败顶级职业选手，确立"不完全信息博弈超人 AI"范式。（本次未开页核对具体数值，报告中不引用 mbb/g 数字。）
4. N. Brown, T. Sandholm. *Superhuman AI for multiplayer poker*. Science 365(6456), 2019. https://www.science.org/doi/abs/10.1126/science.aay7774 | ⏳ | Pluribus 将超人水平扩展到六人桌（多智能体、非零和近似）。说明**多人牌类评测需要自博弈对手池**，与单 Agent 评测口径不同。
5. M. Bowling, N. Burch, M. Johanson, O. Tammelin. *Heads-up limit hold'em poker is solved*. Science 347(6218), 2015. https://www.science.org/doi/10.1126/science.1259433 | ⏳ | 限注单挑扑克被"求解"，给出近似 Nash 策略与可利用度上界。**"可利用度"是可精确计算的评测指标**，与本项目 regret 口径同构。
6. J. Rubin, I. Watson. *Computer poker: A review*. Artificial Intelligence 175(5–6), 2011. https://dl.acm.org/doi/abs/10.1016/j.artint.2010.12.005 | ⏳ | 系统综述扑克的抽象、求解与评测口径。可作为"牌类 AI 评测传统"的引文锚点。
7. D. Zha, J. Xie, W. Ma, S. Zhang, X. Lian, X. Hu, J. Liu. *DouZero: Mastering DouDizhu with Self-Play Deep Reinforcement Learning*. ICML 2021; arXiv:2106.06135. https://arxiv.org/abs/2106.06135 | ✅ | 深度 Monte-Carlo + 动作编码 + 并行 actor，从零训练数日超越既有斗地主程序，登顶 Botzone（344 个 AI 第一）。说明**牌类动作空间随局面剧烈变化**是核心难点，与 Balatro 的"状态相关合法动作"同构。
8. J. Li, S. Koyamada, Q. Ye, G. Liu, C. Wang, R. Yang, L. Zhao, T. Qin, T.-Y. Liu, H.-W. Hon. *Suphx: Mastering Mahjong with Deep Reinforcement Learning*. arXiv:2003.13590, 2020. https://arxiv.org/abs/2003.13590 | ✅ | 全局奖励预测 + oracle guiding + 运行时策略适配；Tenhou 稳定段位高于 99.99% 官方排名人类玩家。其评测是**统计段位**而非可判定最优值，正是本项目要补的口径。
9. N. Bard, J. N. Foerster, S. Chandar, N. Burch, M. Lanctot, et al. *The Hanabi Challenge: A New Frontier for AI Research*. Artificial Intelligence 280:103216, 2020; arXiv:1902.00506. https://arxiv.org/abs/1902.00506 | ✅ | 提出 Hanabi（2–5 人纯合作 + 不完全信息）作为挑战域，强调心智理论推理，配套开源环境与统一实验框架。**合作型牌类的代表**；其"conventions"问题是 LLM Agent 协作评测的近亲。
10. E. Lockhart, N. Burch, N. Bard, S. Borgeaud, T. Eccles, L. Smaira, R. Smith. *Human-Agent Cooperation in Bridge Bidding*. arXiv:2011.14124, 2020. https://arxiv.org/abs/2011.14124 | ✅ | 用第三方手写人类兼容机器人（WBridge5 一类）产生初始数据与初步评测，结合模仿学习 + 搜索 + 策略迭代，在"自身搭档/与既有 bot 搭档/与人类搭档"三设定下刷新桥牌叫牌 SOTA。**"与固定参照 bot 搭档"是桥牌界评测惯例**，对本项目"固定对手/固定种子"设计有直接借鉴。
11. M. Ginsberg. *GIB: Steps Toward an Expert-Level Bridge-Playing Program*. IJCAI-99. https://www.ijcai.org/Proceedings/99-1/Papers/084.pdf | ⏳ | 专家级桥牌程序的经典实现（蒙特卡洛 + 博弈论叫牌）。桥牌 AI 的历史锚点，说明"不完全信息 + 合作"在牌类中早已是核心难题。
12. M. Lanctot, E. Lockhart, J.-B. Lespiau, V. Zambaldi, S. Upadhyay, et al. *OpenSpiel: A Framework for Reinforcement Learning in Games*. arXiv:1908.09453, 2019. https://arxiv.org/abs/1908.09453 | ✅ | 覆盖完美/不完全信息、单/多智能体、合作/零和/一般和的统一环境与算法库，含学习动态与常用评测指标工具。**"精确博弈树 + best response = 可计算 regret"的工程范本**，本项目判定器可直接对齐其术语。
13. D. Zha, K.-H. Lai, Y. Cao, S. Huang, R. Wei, J. Guo, X. Hu. *RLCard: A Toolkit for Reinforcement Learning in Card Games*. AAAI-20 RL in Games Workshop; arXiv:1910.04376. https://arxiv.org/abs/1910.04376 | ✅ | 统一 API 的卡牌环境集（Blackjack、Leduc、Texas Hold'em、UNO、斗地主、麻将）与设计原则。**牌类基准的"环境标准化"先例**，本项目可类比它来论证"规则子集 + 统一接口"的合理性。

### B. 卡牌游戏 + LLM 评测

14. W. Wang, F. Bie, J. Chen, D. Zhang, S. Huang, E. Kharlamov, J. Tang. *Can Large Language Models Master Complex Card Games?* NeurIPS 2025 (Poster). https://neurips.cc/virtual/2025/loc/san-diego/poster/117059 | ✅ | 在 8 款卡牌游戏上评估 LLM：监督微调后接近强游戏 AI；多游戏并行有正/负迁移；掌握复杂游戏会降低通用能力（可用通用指令数据缓解）。**证明"卡牌 × LLM 评测"已被主会接受**，但其终点仍是分数/能力升降，不做失败归因。
15. L. Hu, M. Huo, Y. Zhang, H. Yu, E. P. Xing, I. Stoica, T. Rosing, H. Jin, H. Zhang. *lmgame-Bench: How Good are LLMs at Playing Games?* arXiv:2505.15146, 2025. https://arxiv.org/abs/2505.15146 | ✅ | 指出"直接把 LLM 丢进游戏"不能构成有效评测（视觉脆弱、prompt 敏感、数据污染），提出统一 Gym 风格 API + 轻量感知/记忆脚手架 + 防污染设计，13 个模型验证区分度。**"基准设计本身是研究对象"的关键引文**，支撑本项目对污染、prompt 方差与判定口径的显式处理。

### C. 游戏作为 Agent 基准

16. D. Paglieri, B. Cupiał, S. Coward, U. Piterbarg, M. Wolczyk, A. Khan, et al. *BALROG: Benchmarking Agentic LLM and VLM Reasoning On Games*. ICLR 2025; arXiv:2411.13543. https://arxiv.org/abs/2411.13543 | ✅ | 复用既有 RL 环境（含 NetHack Learning Environment）构造游戏套件，用细粒度指标评估 LLM/VLM；发现部分模型**在有视觉输入时更差**。**最接近本项目定位的基准**，但其"成功"= 各游戏进度/分数的归一化，无 oracle、无归因。
17. M. Hausknecht, P. Ammanabrolu, M.-A. Côté, X. Yuan. *Interactive Fiction Games: A Colossal Adventure*. AAAI 2020; arXiv:1909.05398. https://arxiv.org/abs/1909.05398 | ✅ | 提出 Jericho 环境与文本 Agent 系统研究；指出 IF 游戏同时具备组合动作空间、语言理解、常识推理三重挑战。**"自由文本动作"是不可判定性的极端**，反衬 Balatro 有限动作集的可判定优势。
18. H. Küttler, N. Nardelli, A. H. Miller, R. Raileanu, M. Selvatici, E. Grefenstette, T. Rocktäschel. *The NetHack Learning Environment*. NeurIPS 2020; arXiv:2006.13760. https://arxiv.org/abs/2006.13760 | ✅ | 程序生成、**随机**、富交互、可大规模采样的 roguelike 环境，强调探索/规划/语言条件 RL 与鲁棒泛化。**"真实感↑ ⇒ 可复现性与判定难度↑"的代表**；本项目刻意反其道（规则子集 + 确定性 + 精确分数）。
19. D. Hafner. *Benchmarking the Spectrum of Agent Capabilities*. ICLR 2022; arXiv:2109.06780. https://arxiv.org/abs/2109.06780 | ✅ | Crafter：单环境内用**语义化成就（achievement）解锁**评估广谱能力，而非单一任务奖励。**"用结构化成功信号替代单一标量"的先例**，但成就序列只给能力画像，不指认具体错误决策。
20. W. H. Guss, B. Houghton, N. Topin, P. Wang, C. Codel, M. Veloso, R. Salakhutdinov. *MineRL: A Large-Scale Dataset of Minecraft Demonstrations*. IJCAI 2019; arXiv:1907.13440. https://arxiv.org/abs/1907.13440 | ⏳ | 大规模 Minecraft 人类演示数据集与环境，推动样本高效、开放世界的 Agent 研究。**"人类演示 + 长程任务"评测传统**，其成功判据依赖奖励/人类基线。
21. G. Wang, Y. Xie, Y. Jiang, A. Mandlekar, C. Xiao, Y. Zhu, L. Fan, A. Anandkumar. *Voyager: An Open-Ended Embodied Agent with Large Language Models*. arXiv:2305.16291, 2023. https://arxiv.org/abs/2305.16291 | ⏳ | LLM 驱动的开放世界终身学习 Agent，用**独特物品数/科技树里程碑**度量进展。**"里程碑计数"是一种可判定但粗粒度的成功判据**。
22. J. Weihs, T. Suhr, et al. *Cradle: Empowering Foundation Agents Towards General Computer Control*. arXiv:2403.03186, 2024. https://arxiv.org/abs/2403.03186 | ⏳ | 通用计算机控制（GUI）Agent，跨软件任务；成功由任务脚本/人工设定的完成条件判定。**"真实感最强、可判定性最弱"的一端**：环境不可枚举、成功判定依赖外部脚本。
23. M.-A. Côté, Á. Kádár, X. Yuan, B. Kybartas, T. Barnes, et al. *TextWorld: A Learning Environment for Text-based Games*. arXiv:1806.11532, 2018. https://arxiv.org/abs/1806.11532 | ⏳ | 程序化生成文本游戏，自带 ground-truth 世界状态与通关路径，支持课程学习。**"生成器侧有真值"** 的思路可类比本项目"oracle 侧有真值"。
24. R. Wang, P. Jansen, M.-A. Côté, P. Ammanabrolu. *ScienceWorld: Is your Agent Smarter than a 5th Grader?* EMNLP 2022; arXiv:2203.07540. https://arxiv.org/abs/2203.07540 | ⏳ | 小学科学交互任务集，0–100 分制、任务成功可精确判定。**"精确判定 + 语义任务"的中间态基准**，但无最优策略参照。
25. M. G. Bellemare, Y. Naddaf, J. Veness, M. Bowling. *The Arcade Learning Environment: An Evaluation Platform for General Agents*. JAIR 47, 2013. https://dl.acm.org/doi/10.5555/2566972.2566979 | ⏳ | Atari 2600 评测平台：环境确定、分数精确、协议统一，成为通用 Agent 评测的事实标准。**"确定性 + 精确分数"能支撑大规模可比评测**的最强证据。

### D. Balatro 相关（含空白判定）

26. A. V. Periasami, A. Gupta, E. Cheng, I. Rosales. *Reinforcement Learning for the Game of Balatro: A Fast Simulator and Two-Policy Training Approach*. EXAG 2026 (AIIDE Workshop); arXiv:2610.39049, 2026. https://arxiv.org/abs/2610.39049 | ✅ | 首个 Balatro 专项 RL 工作：Rust 模拟器（对真实客户端 state-diff）+ 合法动作动态掩码 + 盲注/商店双策略 PPO；首盲通过率 >99%、平均最大 ante 收敛 3/8，并把差距定位到长程规划。**本项目最直接的前作/对照**：它证明了环境工程可行与任务难度真实，但用训练曲线而非 oracle regret，且无失败归因。
27. L. Che, Y. Yang, P. Lin, X. Cao, C. Wang, X. Wang, J. Su. *DemoEvolve: Demonstration-Guided Harness Evolution under Sparse Feedback*. arXiv:2605.24539, 2026. https://arxiv.org/abs/2605.24539 | ✅ | 用人类演示引导 harness 演化；在 **held-out seeds** 上把 Balatro 平均封顶最终轮进度从 16.83 提到 20.00（另一环境 Slay the Spire 2 从 18.17 到 28.83）。**Balatro 已被当作长程评测环境使用**，且采用 seed 划分协议——但只报标量进度。
28. J. E. Sankar. *Jokers in the Machine: Evaluating RL vs. LLM Agent Reasoning in a Complex Roguelike Card Game*. Zenodo, 2026（resource type = Proposal，**非同行评议**）. https://zenodo.org/records/23513044 | ✅ | 课程研究提案：扩展 balatro-gym、训练 PPO 并与 prompt-based LLM 对比，主张"超越胜率"的战术质量与协同识别指标。**证明"Balatro × Agent 归因"是社区已识别的空白**，但仅为提案，不可当作已有成果引用。
29. cassiusfive. *balatro-gym: Gymnasium Environment for Balatro*（开源仓库）. GitHub, 2024–. https://github.com/cassiusfive/balatro-gym | ✅（仓库页可访问；README 因抓取截断未完整读取） | 提供 Balatro 的 Gymnasium 接口，被 [28] 作为扩展基座。**说明"Balatro 作为 RL 环境"在工程上已有公共起点**。
30. Balatro Wiki. *Seed*（社区 Wiki，条目引用游戏 1.0.1o 源码 `random_string`）. https://balatrowiki.org/w/Seed | ✅（**非学术来源**，用于事实核对） | 记录：种子为 0–8 位大写字母数字（有效种子约 2.3×10^12），**所有随机要素由种子决定**；商店卡牌、凭证、跳过标签、补充包内容、抽牌与 Boss 盲注以"队列"形式由种子预定；Seeded Run 会关闭成就/统计。**"固定 seed ⇒ 固定牌序与商店序列"的可核查依据**，是本项目可复现性设计的现实基础。

### E. 可复现性与评测协议

31. P. Henderson, R. Islam, P. Bachman, J. Pineau, D. Precup, D. Meger. *Deep Reinforcement Learning That Matters*. AAAI 2018; arXiv:1709.06560. https://arxiv.org/abs/1709.06560 | ⏳ | 系统揭示 RL 结果对随机种子、超参、实现细节与评测协议高度敏感，"单次运行单点比较"不可信。**支撑本项目"多 seed + 方差报告"的必需性**。
32. J. Pineau, et al. *Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program)*. JMLR 22, 2021; arXiv:2003.12206. https://arxiv.org/abs/2003.12206 | ⏳ | 把代码、数据、随机种子、实验日志的提交与复核制度化。**基准"可复现"的规范依据**（对应本项目 seed/版本/回放三件事）。
33. M. C. Machado, M. G. Bellemare, E. Talvitie, J. Veness, M. Hausknecht, M. Bowling. *Revisiting the Arcade Learning Environment: Evaluation Protocols and Open Problems for General Agents*. JAIR 61, 2018; arXiv:1709.06009. https://arxiv.org/abs/1709.06009 | ⏳ | 指出确定性环境会被"记住序列"式策略利用，提出 sticky actions 等评测协议与 open problems。**"确定性 ≠ 免费"的关键警示**：本项目需说明为何 Balatro 的确定性不会被退化解利用（对手是规则而非记忆）。

### F. 失败归因（与本项目判定器直接相关）

34. S. Zhang, M. Yin, J. Zhang, J. Liu, Z. Han, J. Zhang, B. Li, C. Wang, H. Wang, Y. Chen, Q. Wu. *Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent Systems*. ICML 2025; arXiv:2505.00212. https://arxiv.org/abs/2505.00212 | ✅ | 提出"自动失败归因"问题与 Who&When 数据集（127 个多智能体系统的失败日志 + 步骤级标注）；最佳方法**定位责任 Agent 53.5%、定位关键错误步仅 14.2%**，部分方法低于随机。**"用 LLM 判官做归因"目前不可用的最强证据**，直接支撑本项目"用规则判定器把归因变成可计算问题"的路线。

---

## 3. 「为什么 Balatro 适合做可判定 Agent 评测」论据清单

> 每条给出文献/事实依据；编号对应第 2 节。

1. **规则完全显式，最优值可定义。** Balatro 的计分是"牌型基础分 × joker 乘区"的确定性算术，无隐藏手牌、无对手 bluff；单人不完全信息仅来自 RNG，而 RNG 可被 seed 固定为确定序列 [30]。因此可以在**给定 seed 下**定义状态价值与最优策略，进而算 oracle 与 regret——这正是 CFR/可利用度传统能在博弈上做精确评测的前提 [1][5][12]，而 Suphx 只能报统计段位 [8]、DouZero 只能报对战胜率与 Botzone 排行榜名次 [7]。
2. **单步动作空间可枚举（本项目规则子集：出牌组合 ≤218 种）。** 可枚举 ⇒ 可做精确 best response、可枚举所有分支算 regret；对比 Jericho 的自由文本动作 [17]、NLE 的组合式物品/方向动作 [18]、Cradle 的 GUI 坐标动作 [22]，这些环境在原理上无法枚举，只能采样估计。Balatro 原版约 3000 个状态相关动作已让 RL 困难 [26]，而"规则子集 + ≤218"是把"可判定"从理想变成工程现实的关键裁剪。
3. **分数是确定性函数，可精确复算，不依赖归一化口径。** BALROG 的成功是各游戏进度/分数的归一化组合 [16]，Crafter 是成就解锁率 [19]，MineRL 是奖励、Voyager 是里程碑计数 [20][21]——这些量都"可读"但**口径由基准作者定义**，跨版本/跨实现易漂移。Balatro 的分数与盲注目标分可直接比对（是否达标是布尔事实），天然适配"精确判定"。
4. **长程资源分配是真实难点，不是人为加戏。** 有限出牌/弃牌次数、金钱与利息、joker 槽位与商店决策构成"短视 vs 规划"的张力；Balatro RL 工作实证显示：把战术与战略拆成双策略后，首盲通过率可 >99%，但**平均最大 ante 仍停在 3/8，剩余差距被定位为长程战略规划** [26]。这说明该环境能稳定产生"局部最优、全局失败"的失败模式——正是失败归因需要覆盖的对象。
5. **现有基准的成功判据普遍缺"可归因"，这是可论证的空白。** 主流基准输出标量（分数/进度/成就数），不指认"哪一步错、错在哪类" [16][17][18][19][25]；连最接近的 Balatro 前作也只做训练指标与人工分析 [26][27]。而"让 LLM 自己当判官做归因"目前能力不足（步骤级 14.2%）[34]。规则可判定的环境让归因从"再训一个判官"变成"按定义检查轨迹"，这是本项目诊断报告层需要回答的问题。
6. **可复现成本低，且可复现性有游戏内建机制背书。** seed 决定全部随机要素与商店队列 [30]；单机、无渲染依赖、无需模拟器分发（对比 ALE 的 ROM 与 sticky actions 协议 [25][33]）。同时 RL 复现性研究要求多 seed + 方差 + 版本锁定 [31][32]，Balatro 的 seed 机制让"同一起手重复 N 次"成为一句可执行的协议，而非统计近似。
7. **已有开源环境与外部校验手段，环境正确性可被交叉验证。** balatro-gym 提供 Gymnasium 接口 [29]；BalatroBot 可驱动真实客户端，[26] 用它对新模拟器做 state-diff 对齐；社区工具可分析种子与路线 [30]。这意味着"我们的规则子集是否忠实于原版"可以被第三方复算，而不是自说自话。
8. **学术占位清晰：已有工作只做了"能玩/能训"，没做"能判/能归因"。** arXiv 全库仅 2 条 Balatro 命中（1 篇 workshop 专项 + 1 篇把 Balatro 当环境的预印本），无主会/期刊同行评议论文，主流 LLM 游戏基准未覆盖该品类 [15][16][26][27]。因此本项目不是在既有基准上做增量调参，而是**首次为该环境建立可判定评测协议，并把失败归因作为诊断层**。

---

## 4. 游戏基准的「成功判据设计」对照表

| 基准 / 环境 | 成功定义（原论文口径） | 是否可精确判定 | 是否可归因（是否指认失败步骤/责任） | 依据 |
|---|---|---|---|---|
| **BalatroEval**（本项目） | 相对 oracle 的 regret + 是否达成盲注目标 + 4 类判定器给出的失败类别 | **是**（规则子集，出牌组合 ≤218，分数确定性可算） | **是**（4 类判定器按定义判定，全轨迹可回放） | 本项目设计；方法论对齐 [1][12] |
| Balatro RL（EXAG 2026） | 首盲通过率、平均最大 ante（训练/评测指标） | 是（分数可算），但**未定义最优值** | 部分：作者人工把差距定位到长程规划，**非自动归因** | [26] |
| DemoEvolve（Balatro 用法） | held-out seeds 上的"封顶最终轮进度"均值 | 是（标量可复算） | 否（只报进度变化） | [27] |
| BALROG | 各游戏细粒度指标（进度/分数）组合 | 部分：游戏内量可读，**"成功"阈值由基准定义** | 否（只有总分，无步骤级诊断） | [16] |
| lmgame-Bench | 统一 API 下的游戏分数 + 跨游戏相关性 | 是（分数），但重点是**稳定性/防污染**而非最优性 | 否 | [15] |
| Jericho | 相对 walkthrough 的归一化分数 | 是（游戏分数确定；但动作空间为自由文本） | 否 | [17] |
| NetHack Learning Environment | 游戏分数 / 达成深度（BALROG 等再做归一化） | 是（分数确定），但环境**程序生成 + 随机**，需跨 seed 报告 | 否 | [18] |
| Crafter | 语义化成就解锁率（achievement success rate） | 是（成就为布尔） | 部分：成就序列给能力画像，**不指认错误决策** | [19] |
| MineRL | 奖励 / human-normalized 分数 | 是（奖励可算） | 否 | [20] |
| Voyager | 独特物品数 / 科技树里程碑数 | 是（可计数） | 否 | [21] |
| Cradle | 预设 GUI 任务的完成率 | 部分：依赖任务脚本与外部判定 | 否 | [22] |
| TextWorld | 通关 / 得分（生成器自带 ground-truth） | 是 | 否 | [23] |
| ScienceWorld | 0–100 任务分 | 是 | 否 | [24] |
| ALE / Atari | 游戏分数（常做 human-normalized） | 是（确定性模拟器 + 固定协议） | 否 | [25][33] |
| Hanabi | 合作得分（标准上限 25） | 是（给定牌序与策略后分数确定）；**但博弈最优值未知**（不完全信息合作） | 否（可做 conventions 分析，非步骤归因） | [9] |
| DouZero / RLCard | 对战胜率、Botzone 排名 | 是（单局输赢确定），但**对手池导致高方差** | 否 | [7][13] |
| Libratus / Pluribus | mbb/g（大样本统计 + 置信区间）/ 与职业选手对战胜负 | 是（统计意义下），**单局不可判定好坏** | 否（有可利用度分析，非逐局归因） | [3][4][5] |
| Who&When（归因方法基准） | 责任 Agent 定位准确率、关键错误步定位准确率 | 是（有人工标注真值） | 是（这正是任务本身），但**依赖人工标注、且 LLM 判官仅 14.2%** | [34] |

**表格读法（可直接写进报告）**：横看"是否可精确判定"一列，几乎所有基准都是"是"；但纵看"是否可归因"一列，**除本项目与人工标注的 Who&When 外全部为"否"**。也就是说，游戏基准的成熟度集中在"把成功定义成一个能算的数"，而**"把失败拆成可判定的原因"这一层几乎是空的**——这正是 BalatroEval 的切入点：项目定位是**长线规划测试集**，失败归因只作为**诊断报告层**解释分数、定位错误；这也是第 3 节论据 5 的表格化证据。

---

## 5. 不确定项与写作注意（交给 Lead）

1. **Science / ACM DL 页面本次未逐页打开**（[3][4][5][6][25] 标 ⏳），因此报告中**不要引用任何具体数值**（Libratus/Pluribus 的 mbb/g、对局数、HULHE 的可利用度上界数值等本次均未核对）；只保留定性表述，若必须给数值，请 Lead 先开页核对或改为"见原文"。
2. **Balatro 学术占位的表述必须精确**：正确写法是"截至 2026-11-12，arXiv 全库仅 2 条 Balatro 命中；其中 1 篇为 EXAG 2026（AIIDE Workshop）专项论文，1 篇为把 Balatro 作为评测环境的预印本；未发现主会/期刊同行评议论文"。**不要写"完全没有研究"**（会被 [26][27] 反驳），也不要写"已有较多研究"。
3. **[28] Zenodo 条目类型是 Proposal（课程研究提案）**，只能作为"研究动向/社区需求"引用，不可当作成果；[30] 是社区 Wiki，只能用于核对 seed 机制这一**可外部验证的游戏事实**，不可当作学术引文撑论点。
4. **"≤218 种出牌组合"是本项目环境的工程事实**，文献中不存在该数字；报告中应表述为"本项目规则子集下"，不要归因给任何引文。
5. BALROG 的完整游戏清单我**只核对了摘要与项目页描述**（未见 Balatro），未逐条核对 12 款游戏列表；若报告要写"BALROG 未覆盖卡牌 Roguelike"，建议加限定语"据其摘要与公开游戏列表"。
6. [10] 中 WBridge5 是作为"第三方手写人类兼容 bot"被使用，**该文并未把 WBridge5 本身作为研究对象**；若报告需要"WBridge5 的原始论文"，本次未找到可开页核对的权威出处，建议改用 GIB [11] 或干脆只写"桥牌界以固定强 bot 作为搭档/评测基准"这一惯例。
7. 本文件与 `docs/research/` 下其他文件互不依赖；如需并入开题报告，第 1 节可直接改写为"研究现状 3.x"，第 3、4 节建议整体保留（它们是最能体现本项目差异化定位的两块）。
