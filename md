荣耀 YOYO Agent Memory 槽位路由项目记录
一、项目背景

所在团队主要负责荣耀 YOYO Agent 的 Memory 能力建设。

Agent Memory 的目标，是从用户与 Agent 的日常交互中识别并沉淀具有长期价值的用户信息，例如：

身份信息
地址信息
日程信息
个人属性
兴趣偏好
行为习惯等

这些长期记忆主要服务于两个方向：

信息记忆与提醒
帮助用户记录未来可能需要使用的重要信息。
个性化 Agent 服务
利用历史记忆增强后续任务执行，例如在点外卖、出行、推荐等场景中，根据用户历史偏好提供更加个性化的服务。

因此，该模块本质上是 YOYO Agent 个性化能力的重要基础设施之一。

二、当前项目解决的问题

整个 Memory 系统中定义了约 200+ 个细粒度槽位。

例如：

身份证号
身份证籍贯
家庭地址
公司地址
收货地址
身高
体重
职业
生日
纪念日
日程安排
兴趣偏好等

早期方案可能直接针对 200+ 个槽位进行分类。

当前系统引入了一层 粗粒度分类 / 路由机制：

用户 Query

→ 一级粗分类

→ 七个大类之一

→ 后续细粒度分类

→ 具体 Slot

例如：

用户 Query
   ↓
地址信息
   ↓
家庭地址 / 公司地址 / 收货地址 / 学校地址……

因此，我当前负责的任务可以理解为：

Agent Memory 场景下的一级槽位路由（Hierarchical Slot Routing / Coarse-grained Slot Classification）。

其作用类似于整个 200+ Slot 分类体系前端的一个“索引层”：

先缩小候选空间，再由后续模型完成细粒度分类。

三、目前负责的核心工作
1. 大模型粗分类微调

针对七类一级槽位分类任务，对大语言模型进行 LoRA 微调，提高分类准确率。

目前已知：

Fine-tuning：LoRA
训练数据量：约 4,000～5,000 条
输入形式：User Query
输出形式：Slot Category Label
一级类别数量：7 类

训练形式大致为：

Query → Label

例如：

Query:
我的身份证号码是 XXXX

Label:
身份 / 卡证信息

模型推理时 Prompt 中同时包含七个大类的详细定义。

因此，该任务实际上并非单纯依赖模型参数记忆分类规则，而是：

Prompt 中提供业务规则 + Fine-tuning 学习规则理解与决策模式。

四、训练数据与 Benchmark 构建

训练数据主要通过大模型生成。

首先定义七大分类标准，然后按照固定比例生成不同难度的数据。

例如：

大部分为单标签、明确边界的数据
一部分为多标签、边界模糊或容易混淆的数据

数据生成过程中，会明确描述每个类别的业务定义。

例如：

日程类可能要求包含：

时间
地点
计划
安排等语义
五、数据质量控制

由于训练集与 Benchmark 主要通过 LLM 生成，因此数据质量是整个项目中的核心问题之一。

当前采用：

多模型交叉复核 + 人工分析

基本流程：

模型 A 生成数据
      ↓
模型 B / C / D 独立判断 Label
      ↓
比较多个模型结果
      ↓
结果不一致的数据进入异常集合
      ↓
人工分析 / 清洗

因此，数据构建并不是简单的 LLM Synthetic Data，而是通过多个模型进行交叉验证，提高 Label 的可信度。

这部分可以包装为：

Multi-LLM Cross Validation / Multi-model Consensus Data Filtering

即：

通过多个模型之间的一致性进行数据质量筛选。

六、数据驱动的模型迭代流程

整个微调过程并不是：

生成数据 → 训练 → 结束

而是一个持续迭代流程：

数据生成
   ↓
LoRA Fine-tuning
   ↓
Benchmark Evaluation
   ↓
Bad Case Analysis
   ↓
错误归因
   ↓
数据清洗 / 边界样本增强
   ↓
重新训练

实际工作中存在大量：

洗数据 → 微调 → 测试 → Bad Case 分析 → 再洗数据 → 再训练

的迭代过程。

因此，该项目真正可以强调的能力并不只是“会 LoRA 微调”，而是：

通过 Error-driven Data Iteration 建立数据—训练—评测—优化闭环。

七、边界样本增强

Bad Case 分析过程中发现，模型非常容易在某些语义边界场景下发生错误。

例如：

Query A

我的身份证号是 123456……

应该归入：

身份 / 卡证信息。

Query B

明天住酒店记得带身份证。

虽然出现了“身份证”关键词，但是 Query 并没有表达用户长期身份属性，因此不应该归入身份信息。

这类 Case 暴露了一个重要问题：

模型可能学习到关键词相关性，而没有真正学习 Slot 的业务决策边界。

因此项目中会：

识别高频误分类场景；
构造边界样本；
增强容易混淆类别的数据；
重新 Fine-tuning；
再通过 Benchmark 验证效果。

这部分可以定义为：

Hard Example / Boundary Sample Mining

即：

利用 Bad Case 主动挖掘模型决策边界，并进行针对性数据增强。

八、关于 CoT / 分类依据监督的思考

目前训练数据形式主要为：

Query → Label

但对于业务规则复杂、类别边界模糊的问题，可以进一步探索：

Query
↓
Classification Rationale
↓
Label

例如：

Query:
明天住酒店记得带身份证。

Reason:
该 Query 虽然出现“身份证”，但并没有描述用户身份证本身的长期属性信息，而是在表达一个临时事件提醒。

Label:
Other / 日程相关类别

这种方式的目的并不是单纯让模型生成长 CoT，而是：

向模型提供显式的决策依据监督（Decision Rationale Supervision）。

核心目标是让模型学习：

为什么属于这个类别，

而不是：

哪个关键词通常对应哪个类别。

不过该方案必须结合线上延迟要求考虑。

九、线上时延约束

当前分类任务存在明确的线上时延要求：

单次请求需要在约 200 ms 内完成。

因此推理阶段不能输出较长的 Chain-of-Thought。

这意味着模型训练策略必须同时考虑：

Accuracy
Latency
Token Generation Cost
Serving Throughput

因此当前更加倾向：

Input Query
↓
Model Decision
↓
Direct Label Output

而非：

Input Query
↓
Long Reasoning
↓
Label

这体现了一个非常重要的算法工程原则：

算法研发不是寻找最复杂或最先进的方法，而是在业务目标、资源约束和模型能力之间寻找最优平衡。

十、Prompt 与 Fine-tuning 的关系

当前推理 Prompt 中会显式给出七个类别及对应业务定义。

因此模型最终能力来自：

Prompt Rule
+
Fine-tuned Parameters

而不是单纯依赖其中任何一个。

当业务规则、Slot 定义或 Prompt 发生明显变化时，当前实践通常也会重新进行 Fine-tuning。

原因在于：

Fine-tuning 过程中模型学习的不只是一个抽象分类任务，还学习了：

特定 Prompt Protocol 下的任务执行模式。

因此：

Prompt 与 Fine-tuned Parameters 应当视为一个联合系统，而不是两个完全独立的模块。

十一、推理性能优化：Prefix / KV Cache

当前使用 vLLM 进行模型推理。

该分类任务存在一个明显特点：

每个请求中约 98% 的 Prompt 都是固定内容：

七个类别定义
分类规则
系统指令

真正变化的只有最后的 User Query。

因此：

固定 Prompt：约 98%
变化 Query：约 2%

如果每个请求都重新执行整个 Prefix 的 Prefill，会产生大量重复计算。

因此项目中考虑利用：

KV Cache / Prefix Cache

缓存固定 Prompt 对应的 KV 状态。

后续请求仅对新增 Query Token 进行计算，从而减少 Prefill 开销并降低推理延迟。

这一点与当前 200 ms latency constraint 高度相关。

这部分下周需要进一步确认 vLLM 中实际使用的机制和参数名称。

十二、评测指标

目前模型评测主要关注：

Accuracy
Precision
Recall

每轮模型训练结束后：

在 Benchmark 上推理；
统计各项指标；
提取错误样本；
Bad Case 分类；
判断错误来源；
针对性优化。

后续最好进一步记录：

Macro Precision / Recall / F1
Micro F1
每个类别 Recall
Confusion Matrix

尤其对于类别分布不均衡问题，单纯 Accuracy 可能不足以反映模型真实表现。

十三、项目可以包装出的技术主线

这个项目不建议描述成：

“用 LoRA 调了一个七分类模型。”

更适合定义为：

面向 Agent Memory 的分层槽位路由模型研发与数据驱动优化。

完整技术主线可以描述为：

200+细粒度Memory Slots
          ↓
Hierarchical Slot Routing
          ↓
LLM-based Coarse Classification
          ↓
LoRA Fine-tuning
          ↓
Synthetic Data Construction
          ↓
Multi-LLM Cross Validation
          ↓
Bad Case Analysis
          ↓
Boundary Sample Mining
          ↓
Iterative Fine-tuning
          ↓
Latency Optimization
十四、简历候选描述
Version 1

Agent Memory 分层槽位路由模型优化

面向荣耀 YOYO Agent Memory 场景，参与 200+ 细粒度 Memory Slot 的分层路由方案建设，基于大语言模型实现七类一级槽位分类，并使用 LoRA 进行任务微调；构建约 5K 条训练数据，通过多模型交叉复核提升 Synthetic Data 标签可靠性，并结合 Bad Case 分析开展边界样本挖掘与数据增强，形成“数据构建—微调—评测—错误归因—再训练”的数据驱动优化闭环。

Version 2：偏算法岗

面向 YOYO Agent 长期记忆系统，参与 Hierarchical Slot Routing 模型研发，将 200+ 细粒度 Memory Slots 拆分为一级粗分类与下游细分类任务；基于 LLM + LoRA 完成七类一级路由模型微调，并通过 Multi-LLM Consensus 构建、筛选约 5K 条训练数据，结合 Hard Example Mining 与 Bad Case Analysis 持续优化模型决策边界；针对线上 200 ms 时延约束，探索基于 vLLM Prefix/KV Cache 的重复 Prompt Prefill 优化方案。

十五、项目中值得保留的面试思维
1. 从业务问题到机器学习问题

可以表达为：

应用算法的价值不仅在于模型本身，更重要的是把业务问题转化成一个可定义、可评测、可持续优化的机器学习问题。

这个项目中：

200+ Slot 业务问题
↓
分层分类问题
↓
七分类任务
↓
Benchmark
↓
Fine-tuning
↓
Bad Case
↓
数据增强

就是典型例子。

2. 算法与业务约束的平衡

可以表达为：

算法研发并不是寻找最先进的方法，而是在业务目标、资源约束和模型能力之间寻找最优平衡。

例如：

CoT 可能提高分类推理能力，

但是：

CoT
↓
Generation Tokens ↑
↓
Latency ↑

与 200 ms 线上要求产生冲突。

因此：

最好的离线算法 ≠ 最好的线上算法。

3. 系统级优化思维

模型准确率并不能无限提升。

当 Query 本身具有歧义，例如：

用户表达不足以判断属于哪个 Slot

继续优化分类模型的边际收益可能已经非常低。

此时更合理的方案可能是：

用户 Query
↓
Classifier 无法高置信判断
↓
Agent Clarification
↓
向用户主动确认

因此真正的端到端优化，并不是不断提高单个模型指标，而是：

理解整个 Agent Pipeline 中各模块的职责，寻找当前系统真正的 Bottleneck，并把优化资源投入边际收益最高的环节。

这属于比较典型的 System-level Engineering Thinking。

十六、下周回公司必须确认的信息
A. Base Model

需要确认：

模型完整名称

是否为 Qwen 系列

参数规模

是否为 MoE

总参数量

Active Parameters

模型架构

Context Length

推理精度：FP16 / BF16 / INT8 / INT4？

为什么选择这个模型？

B. LoRA 配置

需要记录：

LoRA Rank

LoRA Alpha

LoRA Dropout

Target Modules

Learning Rate

Optimizer

Epoch

Batch Size

Gradient Accumulation

Max Sequence Length

Trainable Parameters

Trainable Parameters 占模型总参数比例

单次训练所用 GPU 数量

GPU 型号

显存占用

单次训练耗时

C. Dataset

需要确认：

精确训练数据量

Train / Validation / Test 数量

七个类别各自样本量

是否存在类别不均衡

单标签 / 多标签数据比例

数据生成使用什么模型

三个复核模型分别是什么

Multi-model 一致性规则

不一致数据如何处理

是否存在人工复核

Boundary Sample 占比

D. Evaluation

需要记录：

Fine-tuning 前 Accuracy

Fine-tuning 后 Accuracy

Precision

Recall

F1

Macro / Micro 指标

每类 Recall

Confusion Matrix

最大提升来自哪个类别

最难分类的是哪几个类别

当前 Accuracy 上限大约是多少

主要 Bad Case 类型

这部分是简历中量化结果的核心。

E. Latency / Serving

需要确认：

200 ms 是 TTFT、模型生成延迟还是 End-to-End Latency？

P50 / P95 / P99 哪一个需要小于 200 ms？

Input Token 数量

Output Token 数量

单请求吞吐

并发要求

vLLM 版本

vLLM 中缓存固定 Prompt 使用的机制具体叫什么

是否为 Prefix Caching

是否真正开启

Cache Hit Rate

开启前 Latency

开启后 Latency

GPU 显存增加多少

是否有吞吐提升

F. 为什么采用“七类粗分类 + 细分类”

这个问题非常重要。

需要向业务负责人确认：

之前是否真的直接做 200+ 分类

当时准确率是多少

最大问题是什么

为什么最终选择 Hierarchical Classification

七类是怎么定义出来的

为什么不是 5 类 / 10 类

分层之后具体提升多少

是否同时改善 Prompt 长度 / Token Cost / Latency

是否减少类别混淆

这一部分会直接决定你能不能解释：

为什么这个项目有必要存在。

G. 为什么使用 LLM

建议向同事确认：

是否考虑过 BERT / RoBERTa 等 Encoder 分类模型

是否做过实验

为什么最终使用 LLM

是否因为 Slot Rule 很复杂

是否需要通过 Prompt 动态注入业务规则

是否考虑泛化与需求变化

是否因为已经有统一 LLM Serving Infrastructure

小模型是否测试过

LLM 相对传统模型提升多少

面试官非常可能问：

这就是一个七分类，为什么需要 30B 级 LLM？

这个问题一定要准备。

十七、当前最需要补齐的三个数字

如果只能记三个东西，优先把这三个补齐：

第一：

Baseline → Fine-tuned Model

准确率到底从多少提升到多少。

第二：

模型和 LoRA 参数

到底是哪一个 Base Model，以及实际训练参数规模。

第三：

Latency Optimization

200 ms 的定义是什么，以及 Prefix/KV Cache 到底把延迟从多少降低到了多少。

这三个数字补齐以后，这段经历就会从：

“我做过一次 LLM Fine-tuning”

变成：

“我参与过一个受业务、精度、延迟三重约束的真实 Agent Memory 模型优化项目。”

这才是这段经历最值得呈现的地方。

今天 19:45
张潍久简历.pdf
PDF
帮我总结成一份简历描述  参考这个文件
