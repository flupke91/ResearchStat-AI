# ResearchStat AI: An AI-Native, Protocol-Bound, and Reproducible Statistical Analysis Platform

## 摘要

统计软件在科研中承担方法选择和结果解释的核心角色，但传统工具普遍存在方法不透明、结果难以复现、AI 辅助分析缺少审计约束等问题。ResearchStat AI 提出一种 AI 原生统计分析与可复现性平台：自然语言分析请求首先被转换为受 Protocol Registry 约束的结构化计划，经过人工评审后，由 Python 和 R 双引擎执行，并接受数值容差交叉验证。每次分析生成完整的 `analysis_record.json`，覆盖数据集指纹、协议、参数、结果、警告和人工评审记录。V1 已实现 11 个标准统计协议、15 个 AI Planner benchmark 场景、87 项自动化测试、NIST StRD 参考数据校验和 10000 行数据约 0.79 秒的分析性能。

关键词：统计可复现性；统计协议；交叉验证；审计系统；AI 规划；MCP

## 1. 引言

GraphPad Prism、SPSS 和 Origin 等商业统计软件为科研用户提供了便利，但其内部实现通常不公开，分析流程难以被自动化审计。另一方面，直接让大型语言模型推荐统计检验并生成代码，容易跳过假设检查、忽略伪重复，并产生不可复现的分析。

ResearchStat AI 的设计目标是：

- 所有统计结果绑定明确 Protocol。
- 所有分析过程可复现、可审计。
- AI 只做规划，数值计算由经过验证的 Python/R 引擎完成。
- 不逆向商业软件内部实现。
- 通过开源生态复用成熟统计和绘图库。

## 2. 系统设计

系统采用分层架构：

```text
AI Layer
  -> Protocol Layer
  -> Execution Layer
  -> Validation Layer
  -> Audit Layer
  -> Output Layer
```

### 2.1 Protocol Registry

Protocol Registry 使用 YAML 定义统计方法、假设、posthoc、alpha、缺失值策略和效应量。V1 内置 11 个协议，覆盖描述统计、独立/配对 t 检验、单/双因素 ANOVA、Mann-Whitney、Kruskal-Wallis、Pearson/Spearman 相关和线性回归。

### 2.2 AI Planner 与 Human Review

AI Planner 解析自然语言，推断数据结构，并只能从 Registry 中选择协议。规划结果必须经过人工评审，支持 accept 和 override。每次 override 记录 `(recommended, accepted, reason)`，可作为后续偏好学习数据。

### 2.3 Multi Engine 与 Validation

同一请求可分别由 Python 和 R 引擎执行，输出统一 schema。Validation Framework 使用 NIST StRD、R 官方 datasets 和边界数据，连续统计量相对误差阈值 `1e-8`，p 值绝对误差阈值 `1e-6`。

### 2.4 Audit Trail

每次分析生成 `analysis_record.json`，包含：

- `analysis_id`
- `timestamp`
- `user_input`
- `dataset_hash`
- `protocol_id`
- `software_version`
- `library_version`
- `parameters`
- `results`
- `warnings`
- `human_review`

### 2.5 Figure Engine 与 Privacy

Figure Engine 使用 `matplotlib`、`seaborn`、`statannotations` 和 `SciencePlots`，输出可编辑 SVG、PDF 和 300 DPI TIFF，并附带 `figure_spec.json`。隐私模块支持字段脱敏、标识符哈希和临时目录自动清理。

### 2.6 MCP

MCP Server 暴露 `list_protocols`、`plan_analysis`、`execute_analysis`、`render_figure` 四个工具，支持 stdio、SSE 和 streamable-http 三种 transport，并包含 CSV 大小限制、Protocol 白名单和工作区隔离。

## 3. 验证结果

### 3.1 自动化测试

当前测试套件共 87 项，覆盖 Protocol Registry、Python/R 双引擎、交叉验证、审计、Human Review、AI Planner、Figure、隐私、MCP 和性能。

### 3.2 参考数据

NIST StRD Norris 线性回归通过认证值校验。R 官方数据集 `iris`、`mtcars`、`PlantGrowth`、`ToothGrowth`、`npk`、`sleep` 已固化为参考测试数据。

### 3.3 交叉验证

所有 V1 方法均通过 Python vs R 交叉验证。例如单因素 ANOVA 输出：

```text
Protocol: one_way_anova_tukey_v1
Python: F=223.92, p=6.35e-20
R: F=223.92, p=6.35e-20
Status: PASS
```

### 3.4 AI Planner Benchmark

15 个公开/合成场景全部通过，覆盖独立/配对比较、单/双因素 ANOVA、相关、回归和描述统计。

### 3.5 性能

10000 行单因素 ANOVA 实测约 0.79 秒，满足 V1 目标 <10 秒。

### 3.6 图表示例

Figure Engine 可从分析结果生成带显著性标注的 boxplot 和带置信带的回归 scatter：

![boxplot](images/boxplot_preview.png)

![scatter](images/scatter_preview.png)

## 4. 讨论

ResearchStat AI 的差异化在于把 AI 规划、Protocol 绑定、双引擎验证、审计和出版级 Figure 组合成完整闭环。当前 AI Planner 为确定性规则版本，外部 LLM 后端留待后续版本；Docker 镜像尚未在本机实际构建；MCP 尚未在第三方客户端端到端联调。

未来工作包括：

- 引入更多统计方法，如 Bayesian analysis 和 mixed model。
- 增加 AI Planner 的 LLM 后端和 DPO 偏好训练。
- 完善 Docker、CI 和第三方 MCP 客户端兼容性。
- 基于用户反馈扩展 Protocol Registry。

## 5. 结论

ResearchStat AI 建立了可验证、可审计的 AI 统计分析核心，为替代传统统计软件提供了一条不依赖商业逆向工程的开放路径。

## 参考文献

- NIST Statistical Reference Datasets. https://www.itl.nist.gov/div898/strd/
- R Core Team. R: A Language and Environment for Statistical Computing.
- SciPy, Statsmodels, Pandas, Matplotlib, Seaborn 官方文档。
- AStats: Agentic AI for Applied Statistical Practitioner Workflows.
- cross-tool-statistical-verification.
- RMCP: R MCP Server.
