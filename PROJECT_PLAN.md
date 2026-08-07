# ResearchStat AI 项目计划

> 文档版本：V2  
> 更新日期：2026-08-06  
> 当前状态：V1 发布准备完成  
> 文档定位：V1 的项目边界、架构、模块规格、验收标准与开发路线

## 0. 项目定位

ResearchStat AI 是面向科研场景的 AI 原生统计分析与可复现性平台。它不复制 GraphPad Prism、SPSS 或 Origin 的内部实现，而是基于公开统计公式、标准统计定义和公开参考数据，建立一套可验证、可审计的统计分析工作流。

核心主张：

- 统计可信度优先于功能数量。
- 所有分析必须可复现。
- 所有统计结果必须绑定明确 Protocol。
- AI 只负责规划，不负责数值计算。
- 不逆向工程商业软件，不模拟商业软件内部实现。

## 1. 项目边界

### 1.1 V1 包含

V1 的目标是建立可信统计分析核心，而非完整商业软件替代品。

| 范围 | 说明 |
| - | - |
| AI 分析规划 | 自然语言输入，输出受 Protocol Registry 约束的分析计划 |
| 标准统计协议 | YAML Protocol Registry，统一定义方法、假设、缺失值策略、效应量 |
| Python/R 双引擎 | 同一 Protocol 可在两个引擎执行，并做交叉验证 |
| 审计系统 | 每次分析生成 `analysis_record.json`，记录输入、参数、版本、结果 |
| Figure 生成 | 输出可编辑 SVG、PDF、TIFF |
| 本地运行 | 默认本地处理，数据不上传；支持数据脱敏和临时文件清理 |
| Docker 部署 | 提供可复现的容器运行环境 |

### 1.2 V1 不包含

| 不包含项 | 说明 |
| - | - |
| 完整 Prism 复制 | 不实现商业软件的 GUI、工作流或私有输出格式 |
| SPSS GUI 复制 | 不复制 SPSS 窗口、菜单、Syntax 私有行为 |
| 商业软件逆向兼容 | 不读取或模拟商业软件内部实现 |
| Prism/SPSS/SAS 控制 | 连接器延后到 V3 |
| MCP 封装 | 在核心库、测试体系、审计系统和 Agent 层稳定前不做 MCP |
| Bayesian / mixed model | 延后到 V1.5 |
| 默认云上传 | 敏感数据默认不离开本机 |

### 1.3 兼容性红线

- 所有统计方法必须有公开公式或公共文献依据。
- 所有参考答案必须来自 NIST StRD、R 官方数据集、公开教材案例或人工构造边界数据。
- 任何与商业软件输出的差异，只作为公开统计定义下的等价性讨论，不作为兼容性承诺。

## 2. 架构设计

### 2.1 分层架构

```text
AI Layer
   |
   v
Protocol Layer
   |
   v
Execution Layer
   |
   v
Validation Layer
   |
   v
Audit Layer
   |
   v
Output Layer
```

### 2.2 各层职责

| 层 | 职责 | V1 约束 |
| - | - | - |
| AI Layer | 理解自然语言，生成分析计划 | 只能从 Protocol Registry 中选择协议，不执行计算，不生成统计代码 |
| Protocol Layer | 加载、校验、解析 YAML 协议 | 协议必须通过 schema 校验；缺失字段拒绝执行 |
| Execution Layer | 调用 Python/R 引擎执行标准化分析 | 输入输出为标准化 JSON；记录引擎和库版本 |
| Validation Layer | 假设检查、参考数据校验、跨引擎差异校验 | 超出数值容差视为失败，不允许静默通过 |
| Audit Layer | 生成不可省略的分析记录 | 每次分析必须写 `analysis_record.json` |
| Output Layer | 输出结构化结果和出版级图表 | 图表可复现，SVG 保留文字对象与矢量路径 |

### 2.3 数据流

```text
用户上传数据
  -> 数据规范化和脱敏
  -> 数据集指纹
  -> AI 规划（受限协议选择）
  -> 人工确认计划
  -> Protocol 校验
  -> Python/R 引擎执行
  -> Validation 检查
  -> 结果、图表、审计记录
```

### 2.4 目标目录结构

```text
ResearchStat-AI/
  PROJECT_PLAN.md
  pyproject.toml
  src/researchstat/
    protocols/        # Protocol 定义、加载、校验
    engines/          # Python/R 引擎适配器
    validation/       # 参考数据、容差、跨引擎验证
    audit/            # 审计记录
    privacy/          # 脱敏、临时文件清理
    figures/          # 图表渲染
    planner/          # AI 规划器
    api/              # 本地 API 与 CLI
  r_engine/           # R 脚本或 R 包
  tests/
    unit/
    reference/
    cross_engine/
    boundary/
  benchmarks/
  docker/
  examples/
```

### 2.5 技术选型

基础技术：

| 组件 | 选型 | 理由 |
| - | - | - |
| 语言 | Python 3.12+ | 生态成熟，便于 Agent、API、审计集成 |
| R 引擎 | R 4.4+，优先 base `stats` | 减少第三方包引入的版本漂移 |
| Python 统计 | `scipy`、`statsmodels`、`numpy`、`pandas` | 覆盖 V1 方法，结果可复现 |
| 图表 | Python：`matplotlib` + `seaborn` + `statannotations` + `SciencePlots`/`cnsplots`；R：`ggplot2` + `ggpubr`/`ggprism` | 复用成熟开源渲染栈，不自研绘图引擎 |
| 配置 | YAML + Pydantic | Protocol 人类可读，运行时强校验 |
| API | FastAPI + CLI | 本地集成边界，暂不做完整 GUI |
| 测试 | `pytest`、`hypothesis` | 参考校验与边界测试 |
| 部署 | Docker | 固定 Python/R 版本，保证可复现环境 |

### 2.6 开源复用策略

1. 优先复用成熟开源库，自研只负责协议、审计、验证、AI 规划和结果编排。
2. 所有复用依赖必须记录许可证、版本和出处，并保存 NOTICE。
3. 依赖许可证会影响整体分发方式时，必须经合规确认后再锁定。
4. 允许借鉴公开主题和公开统计约定，禁止逆向商业软件内部实现。
5. 每个候选依赖必须先通过测试再进入 V1 正式依赖。
6. 详细调研结果维护在 `docs/ECOSYSTEM.md`。

### 2.7 竞品调研与差异化

已调研 AStats、cross-tool-statistical-verification、rmcp、AutoML Stat MCP、MedStat、JASP/jamovi，完整清单见 `docs/RESEARCH_LESSONS.md`。

V1 核心差异化：

- AI Planner 只能从 Protocol Registry 选择协议，所有计划、修改和执行都进入审计。
- Validation 由 Protocol 决定必须验证的统计量，不使用用户手工声明。
- R 引擎使用子进程隔离，V1 只维护 V1 方法所需的小型 R 包清单。
- 本地默认、数据零上传、临时文件清理和权限控制。
- MCP 只作为后期集成出口，不作为 V1 核心。

## 3. 开发路线

```text
V1 可信统计分析核心
  -> V1.5 更多统计方法
  -> V2 公开统计协议兼容模式
  -> V3 商业软件连接器
```

### 3.1 V1

建立可信统计分析核心，覆盖：

- Protocol Registry
- Python/R 双引擎
- 参考数据与跨引擎验证
- 审计系统
- 专业软件级 Figure
- AI 分析规划
- 数据隐私与 Docker 部署

V1 交付形态：本地 Python 库 + CLI + 本地 API。不提供完整 GUI，不提供 MCP 封装。

V1 还必须交付专业软件级作图能力，复用开源绘图栈而非自研渲染器。

### 3.2 V1.5

增加：

- Bayesian 分析
- mixed model
- 更多非参数与生存分析方法
- 更完整的 AI 规划能力

### 3.3 V2

增加：

- GraphPad-style 公开协议工作流，基于公开统计定义，不复制商业软件
- 更完整的报告模板
- 可能引入 MCP 封装，前提是核心库、测试体系、审计系统和 Agent 层已稳定

### 3.4 V3

增加商业软件连接器：

- Prism
- SPSS
- SAS

所有连接器只在用户授权环境中调用，不逆向工程商业软件内部实现。

### 3.5 人工 Review Gate

每个阶段完成时必须：

1. 运行全部测试。
2. 更新 `PROJECT_PLAN.md` 中的完成状态、测试结果、已知限制、下一步计划。
3. 暂停，等待人工明确确认。
4. 未经人工确认，禁止自动进入下一阶段。

## 4. 模块规格

### 4.1 Module 1: Statistical Protocol Registry

Protocol Registry 是 V1 的核心模块。每个协议必须唯一标识统计方法、假设、检验参数、缺失值策略和效应量。

示例协议：

```yaml
id: one_way_anova_tukey_v1
version: 1
method: one_way_anova
assumptions:
  observations_independent: true
  normality_checked: true
  variance: equal_variance
posthoc: tukey_hsd
alpha: 0.05
missing_policy: complete_case
effect_size: eta_squared
```

V1 协议清单：

| 协议 ID | 方法 |
| - | - |
| `descriptive_v1` | 连续变量描述统计 |
| `independent_t_test_student_v1` | 独立样本 t 检验，Student 假设 |
| `independent_t_test_welch_v1` | 独立样本 t 检验，Welch 假设 |
| `paired_t_test_v1` | 配对样本 t 检验 |
| `one_way_anova_tukey_v1` | 单因素 ANOVA + Tukey HSD |
| `two_way_anova_v1` | 双因素 ANOVA，V1 默认 Type III SS |
| `mann_whitney_u_v1` | Mann-Whitney U 检验 |
| `kruskal_wallis_dunn_v1` | Kruskal-Wallis + Dunn 事后检验 |
| `pearson_correlation_v1` | Pearson 相关 |
| `spearman_correlation_v1` | Spearman 相关 |
| `linear_regression_v1` | 简单/多元线性回归 |

协议校验规则：

- 协议必须通过 schema 校验。
- 每个结果必须绑定 `protocol_id` 和 `protocol_version`。
- 假设检查结果必须写入输出，不能静默忽略。
- 假设不满足时记录 warning，不自动切换到另一个协议。
- 缺失值策略在 V1 默认使用 `complete_case`，并记录删除行数。

### 4.2 Module 2: Statistical Execution Engine

V1 必须实现的方法：

| 类别 | 方法 |
| - | - |
| Continuous | 描述统计、独立样本 t 检验、配对 t 检验、单因素 ANOVA、双因素 ANOVA、Mann-Whitney、Kruskal-Wallis |
| Correlation | Pearson、Spearman |
| Regression | 线性回归 |

引擎输入输出统一为标准化 JSON。结果字段包括：

- 方法标识
- 统计量
- 自由度
- p 值
- 效应量
- 假设检查结果
- warning
- 引擎与库版本

### 4.3 Module 3: Multi Engine

V1 只实现 Python 和 R 双引擎。

实现方式：

- 默认使用独立 R 子进程 + JSON 通信，避免 Python/R 内存状态耦合。
- R 端使用 V1 方法所需的小型 package allowlist，不开放任意 R 包。
- 临时文件写入受限目录，执行后清理。
- 文件写入需要人工审批，禁止 R 进程访问项目目录之外的路径。
- R 子进程默认无网络访问。
- 每个引擎记录精确版本号，例如 `scipy 1.14.1`、`R 4.4.2`。
- 同一 Protocol、同一输入，必须可在两个引擎执行。
- Prism、SPSS、SAS 在 V1 只保留接口设计，不实现控制逻辑。
- stdio/HTTP transport 只作为后续 MCP 封装的接口设计，不在 V1 实现。

### 4.4 Module 4: Validation Framework

#### 参考数据来源

V1 必须覆盖：

1. NIST Statistical Reference Datasets（StRD）。
2. R 官方 datasets，例如 `iris`、`mtcars`、`PlantGrowth`、`ToothGrowth`、`npk`、`sleep`。
3. 公开统计教材案例数据。
4. 人工构造边界数据，例如单样本组、全相等值、极端离群值、缺失值、非平衡设计。

#### 数值容差

| 指标类型 | 默认容差 | 判定 |
| - | - | - |
| 连续统计量 | relative error < 1e-8 | 超过则失败 |
| p 值 | absolute difference < 1e-6 | 超过则失败 |
| 极小 p 值 | 低于 1e-8 时按相对误差与报告下限联合判定 | 需在测试记录中说明 |

#### Cross Engine Validation

每个方法必须输出 Python vs R 对照结果：

```text
Protocol: one_way_anova_tukey_v1
Python: F=12.34, p=0.00321
R: F=12.34, p=0.00321
Difference: F rel=2.1e-10, p abs=3.0e-11
Status: PASS
```

#### Verification 报告

每个验证必须输出：

- comparison table：逐统计量列出 Python、R、容差、状态。
- verification log：记录验证时间、数据来源、引擎版本。
- methodology statement：说明方法定义和验证依据。

差异分级：

- `error`：超出容差，验证失败。
- `warning`：统计量存在方法学差异但结果仍可解释。
- `info`：合理的方法差异，例如极小数值精度差异，不判失败。

必须明确：Python/R 结果一致只证明实现无关性，不代表分析正确。分析正确性由 Protocol、参考数据和公开统计定义共同保证。

每个 Protocol 必须声明需要验证的统计量清单，不允许用户手工决定验证范围。

### 4.5 Module 5: Audit Trail

每次分析生成 `analysis_record.json`，必须包含：

```json
{
  "analysis_id": "uuid",
  "timestamp": "ISO-8601",
  "user_input": "user prompt or plan confirmation",
  "dataset_hash": "sha256",
  "protocol_id": "one_way_anova_tukey_v1",
  "software_version": "researchstat-ai 0.1.0",
  "library_version": {
    "scipy": "1.14.1",
    "statsmodels": "0.14.2",
    "R": "4.4.2"
  },
  "parameters": {},
  "results": {},
  "warnings": []
}
```

审计要求：

- `dataset_hash` 使用规范化 CSV 的 SHA-256。
- `user_input` 记录用户描述，不记录原始敏感数据。
- 审计记录写入后不可静默覆盖，同一 `analysis_id` 只能追加版本。
- 所有错误必须记录结构化日志。

### 4.6 Module 6: Data Privacy

V1 隐私能力：

- 默认本地运行，无用户确认不上传数据。
- 可选字段级脱敏，脱敏后才进入 AI 规划。
- 临时文件使用后清理，不保留中间敏感副本。
- 本地文件权限控制，API Key 通过环境变量或本地配置提供。
- 未配置外部 LLM 时，AI 规划器降级为规则式协议匹配。
- Project workspace 使用本地文件存储，默认不依赖外部数据库或云存储。

### 4.7 Module 7: Professional Figure Engine

输出格式：

- SVG：可编辑，保留文字对象，保留矢量路径。
- PDF：嵌入字体。
- TIFF：满足出版最低 300 DPI，可配置更高分辨率。

V1 支持图形：

- scatter
- boxplot
- violin
- survival curve

V1 必须达到专业软件级作图能力，包括：

- 期刊级主题、字号、边距、面板间距。
- 色盲安全配色。
- 多面板布局与自动面板标签。
- 显著性标注：星号、p 值、校正 p 值。
- 误差条：SD、SEM、CI，且必须显式标注类型。
- box/violin 上的个体点、散点抖动。
- 相关与回归图的拟合线和置信带。

图表的每个输出必须附带 `figure_spec.json`，记录数据来源、统计方法和渲染参数，确保图表可复现。图形质量通过 golden image 测试和 SVG 可编辑性测试把关，不能只靠人工目检。

### 4.8 Module 8: AI Statistical Planner

输入：自然语言，例如“比较三种药物对小鼠肿瘤大小影响”。

输出：

```text
Experiment type: Animal study
Variable: continuous
Groups: 3 independent groups
Recommended protocol: one_way_anova_tukey_v1
Reason: ...
```

实现约束：

- AI 只能从 Protocol Registry 中选择协议。
- AI 不执行数值计算，不生成并运行任意统计代码。
- 输出必须经过 schema 校验，非法协议 ID 直接拒绝。
- AI 规划结果进入人工确认流程后才可执行。
- LLM 版本和调用参数写入审计记录。

V1 规划流程：

1. 自然语言解析与意图识别。
2. 数据结构推断：independent、repeated measures、nested、wide format。
3. 假设预检：Shapiro-Wilk、Levene、样本量是否足够。
4. 从 Registry 中选择候选 Protocol。
5. 生成可解释推荐理由。
6. 人工 Review：接受、覆盖、解释、修正假设。
7. 人工确认后才进入执行。

人工反馈要求：

- 每次 override 记录为 `(recommended, accepted, reason)`。
- 偏好数据进入审计记录，未来可形成 DPO 训练数据。
- 支持生成 Methods 段落。
- 建立 15 个公开/合成数据集的 AI Planner benchmark。

## 5. 非功能需求

### 5.1 Performance

- 单用户、10000 行以内数据。
- 单次标准分析目标时间 < 10 秒。
- 建立 benchmark 套件，防止回归。

### 5.2 Reliability

- 所有错误必须记录日志。
- 任何统计失败必须有结构化结果，不允许静默 fallback。
- 跨引擎差异超出容差时，结果状态必须为失败。

### 5.3 Deployment

- 支持 Docker 部署。
- 使用 Docker Compose profiles 区分核心引擎、Figure、测试和示例服务。
- Docker 镜像固定 Python、R、系统依赖版本。
- 容器内非 root 运行，运行时默认无网络。
- 提供健康检查和示例数据验证。
- 异步任务提供 SSE 进度通知，长任务不阻塞 CLI/API。
- 测试体系覆盖 unit、reference、cross-engine、edge、security、performance。

## 6. V1 Definition of Done

1. Protocol Registry 可加载、校验、查询全部 V1 协议。
2. Python 与 R 双引擎可执行全部 V1 方法。
3. 所有参考数据集和边界测试通过，容差符合定义。
4. 所有方法通过 Python vs R 交叉验证。
5. 每次分析生成完整 `analysis_record.json`。
6. Figure 引擎输出 SVG、PDF、TIFF，SVG 文字对象可编辑。
7. AI 规划器只能返回 Registry 内有效协议。
8. 10000 行数据标准分析时间 < 10 秒。
9. Docker 镜像可启动并通过验证流程。
10. `PROJECT_PLAN.md` 已更新完成状态、测试结果、已知限制和下一步计划。
11. 通过人工 Review Gate。

## 7. 已知限制

当前为第一阶段工程规划，尚未进入实现：

- 具体依赖版本尚未锁定。
- R 官方数据集与 NIST StRD 数据的许可和下载方式待确认后固化。
- 双因素 ANOVA 的非平衡设计处理方式需在实现阶段用参考数据验证。
- AI 规划器的外部 LLM 调用默认关闭，避免未经同意的数据外发。
- 本计划不承诺与任何商业软件输出逐项一致。
- 开源依赖和许可证清单需要在进入 Figure Engine 阶段前最终复核并固化。

## 8. 下一步

第七阶段 P2 MCP 封装已完成并通过测试，发布准备文件已生成。V1 功能闭环与发布材料均已完成。

下一步：推送到远端仓库，创建 `v1.0.0` 标签，并生成 PyPI/Docker 发布流水线。

验收依据见 `docs/V1_ACCEPTANCE.md`。

竞品调研见 `docs/RESEARCH_LESSONS.md`，开源生态见 `docs/ECOSYSTEM.md`。

## 9. 阶段记录

### Phase 1: 工程规划

- 状态：完成
- 日期：2026-08-06
- 交付物：本文件
- 测试：规划阶段无代码测试
- 人工确认：已确认，进入 Phase 2

### Phase 2: Protocol Registry

- 状态：完成
- 日期：2026-08-06
- 交付物：
  - `pyproject.toml`
  - `src/researchstat/protocols/schema.py`
  - `src/researchstat/protocols/registry.py`
  - `src/researchstat/protocols/data/v1.yaml`
  - `tests/protocols/test_schema.py`
  - `tests/protocols/test_registry.py`
- 测试结果：`15 passed in 1.13s`，Python 3.14.3
- 验收结果：
  - Registry 可加载 11 个 V1 协议。
  - schema 可拒绝非法协议 ID、非法 alpha、非法 posthoc、方法字段冲突。
  - Registry 支持按 method、posthoc、variance 查询，并拒绝重复协议 ID。
- 已知限制：
  - 当前仅实现协议定义、加载、校验和查询，不包含统计执行。
  - 协议字段以 V1 最小集为准，后续扩展方法需要同步扩展 schema。
  - 尚未将协议与执行引擎、审计记录和 AI 规划器绑定。
- 下一步：Python 统计执行引擎 + Figure 渲染原型，等待人工确认。

### Phase 2 Supplement: Open Source Ecosystem Study

- 状态：完成
- 日期：2026-08-06
- 交付物：`docs/ECOSYSTEM.md`
- 关键决策：
  - 绘图不自研渲染器，Python 主路径采用 `matplotlib`、`seaborn`、`statannotations`、`SciencePlots`/`cnsplots`。
  - R 路径采用 `ggplot2`、`ggpubr`/`ggprism`、`patchwork`、`svglite`，但 GPL 依赖需在分发前合规确认。
  - V1 图形验收加入 golden image 测试、SVG 可编辑性测试和出版格式测试。
- 下一步：随 Phase 3 评审一并确认，再进入 Figure Engine 正式实现。

### Phase 3: Python Statistical Execution Engine + Figure Prototype

- 状态：完成
- 日期：2026-08-06
- 交付物：
  - `src/researchstat/engine/models.py`
  - `src/researchstat/engine/python_engine.py`
  - `src/researchstat/figures/prototype.py`
  - `tests/engine/test_python_engine.py`
  - `tests/figures/test_prototype.py`
  - `examples/demo.py`
  - `requirements.lock`
  - `examples/figures/prototype_figure.svg`
  - `examples/figures/prototype_figure.pdf`
  - `examples/figures/prototype_figure.tiff`
- 测试结果：`31 passed`，Python 3.14.3，虚拟环境 `.venv`
- 验收结果：
  - Python 引擎实现全部 V1 方法，并与 `scipy`/`statsmodels` 参考值一致。
  - 每个结果绑定 `protocol_id`，记录引擎和库版本。
  - 假设检查与 warning 已实现，complete_case 缺失策略生效。
  - Figure 原型输出 SVG/PDF/TIFF 和 `figure_spec.json`。
  - SVG 保留可编辑文字对象，TIFF 300 DPI。
- 已知限制：
  - R 引擎尚未实现。
  - Validation Framework 和跨引擎容差校验尚未实现。
  - 双因素 ANOVA 使用 Type III SS，非平衡设计仅给出 warning。
  - Dunn 事后检验默认使用 Holm 校正。
  - Figure 当前为渲染原型，正式 Figure Engine 仍需实现数据绑定和完整主题系统。
- 下一步：R 统计执行引擎 + Validation Framework，等待人工确认。

### Phase 4: R Engine + Validation Framework

- 状态：完成
- 日期：2026-08-06
- 交付物：
  - `r_engine/run_analysis.R`
  - `src/researchstat/engine/r_engine.py`
  - `src/researchstat/figures/engine.py`
  - `src/researchstat/validation/cross_engine.py`
  - `tests/validation/test_cross_engine.py`
  - `tests/validation/test_reference_data.py`
  - `tests/fixtures/validation/nist_norris.dat`
  - `tests/fixtures/validation/r_datasets/`
- 测试结果：`52 passed`，Python 3.14.3，R 4.6.1
- 验收结果：
  - R 引擎实现全部 V1 方法。
  - Python vs R 交叉验证全部通过，连续统计量容差 `1e-8`，p 值容差 `1e-6`。
  - NIST StRD Norris 回归通过认证值校验。
  - R 官方 datasets `iris`、`mtcars`、`PlantGrowth`、`ToothGrowth`、`npk`、`sleep` 已固化为参考数据。
  - Figure 原型已提供正式渲染入口 `render_figure`。
- 已知限制：
  - R 引擎依赖本机 Rscript，未安装 R 的机器会跳过 R 相关测试。
  - Dunn 事后检验在 R 端为公开公式实现，使用 Holm 校正。
  - Spearman 与 Mann-Whitney 的 p 值已统一为与 Python 相同的近似算法。
  - NIST 参考数据目前覆盖线性回归，ANOVA 参考测试依赖 R 官方 datasets。
- 下一步：P0 收尾，等待人工确认。

### Phase 4 Supplement: Competitive Research Lessons

- 状态：完成
- 日期：2026-08-06
- 交付物：`docs/RESEARCH_LESSONS.md`
- 关键决策：
  - AI Planner 借鉴 AStats 的自然语言解析、数据结构推断、假设预检和人工反馈循环。
  - Validation 借鉴 cross-tool verification 的逐统计量容差、comparison table、verification log、methodology statement 和 severity 分级。
  - R 引擎借鉴 rmcp 的子进程隔离和 guardrail 思路，但 V1 只保留小型 package allowlist。
  - 部署和工程结构借鉴 AutoML Stat MCP 的 workspace、Docker Compose profiles、SSE 和测试分层。
  - 隐私和产品化借鉴 MedStat 的本地零上传与出版级输出方向。
- 下一步：进入 P0 收尾，等待人工确认。

### Phase 5: P0 Completion

- 状态：完成
- 日期：2026-08-06
- 交付物：
  - `src/researchstat/audit/records.py`
  - `src/researchstat/review/models.py`
  - `src/researchstat/review/service.py`
  - `src/researchstat/planner/models.py`
  - `src/researchstat/planner/planner.py`
  - `src/researchstat/planner/benchmark.py`
  - `src/researchstat/workflow/runner.py`
  - `tests/audit/test_audit.py`
  - `tests/planner/test_planner.py`
  - `tests/review/test_review.py`
  - `tests/workflow/test_workflow.py`
  - `examples/workflow_demo.py`
- 测试结果：`68 passed`，Python 3.14.3
- 验收结果：
  - 每次分析生成 `analysis_record.json`，包含 `analysis_id`、`dataset_hash`、协议、参数、结果、warnings、plan 和 human_review。
  - Human Review 支持 accept 和 override，override 记录 `(recommended, accepted, reason)`。
  - AI Planner 默认离线运行，只能返回 Registry 内协议，15 个 benchmark 场景全部通过。
  - plan-review-execute-audit 完整工作流可运行并持久化审计记录。
- 已知限制：
  - AI Planner 当前为确定性规则版本，外部 LLM 后端尚未接入。
  - 数据结构推断依赖列名提示和基础类型判断，复杂 wide/nested 数据需要人工修正。
  - audit 记录默认写入本地 JSON，尚未实现加密或数据库存储。
- 下一步：P1 Professional Figure Engine + 隐私 + Docker，等待人工确认。

### Phase 6: P1 Figure Engine + Privacy + Docker

- 状态：完成
- 日期：2026-08-06
- 交付物：
  - `src/researchstat/figures/models.py`
  - `src/researchstat/figures/renderers.py`
  - `src/researchstat/figures/engine.py`
  - `src/researchstat/privacy/masking.py`
  - `docker/Dockerfile`
  - `docker/docker-compose.yml`
  - `.dockerignore`
  - `benchmarks/run_performance.py`
  - `tests/figures/test_engine.py`
  - `tests/figures/test_golden.py`
  - `tests/fixtures/figures/golden_scatter.json`
  - `tests/privacy/test_masking.py`
  - `tests/performance/test_performance.py`
- 测试结果：`79 passed`，Python 3.14.3
- 验收结果：
  - Figure Engine 可绑定 `analysis_id` 和 `AnalysisResult`，输出 SVG/PDF/TIFF 与 `figure_spec.json`。
  - golden image 测试基于固定 SVG 哈希，消除时间戳和随机 salt 影响。
  - 支持 scatter、boxplot、violin、survival 渲染。
  - 隐私模块支持字段脱敏、标识符哈希和临时目录自动清理。
  - Dockerfile 与 Docker Compose profiles 已提供。
  - 10000 行 ANOVA 实测约 `0.79s`，满足 <10 秒目标。
- 已知限制：
  - 本机未安装 Docker，镜像未实际构建验证。
  - Figure Engine 当前为单面板渲染，多面板仍由 prototype 提供。
  - golden SVG 哈希依赖固定 matplotlib 版本，依赖升级后需重新生成基线。
  - MCP 尚未实现。
- 下一步：P2 MCP 封装 + V1 最终评审，等待人工确认。

### Phase 7: P2 MCP Encapsulation

- 状态：完成
- 日期：2026-08-06
- 交付物：
  - `src/researchstat/mcp/security.py`
  - `src/researchstat/mcp/service.py`
  - `src/researchstat/mcp/server.py`
  - `src/researchstat/mcp/cli.py`
  - `tests/mcp/test_security.py`
  - `tests/mcp/test_service.py`
  - `tests/mcp/test_server.py`
  - `docs/V1_ACCEPTANCE.md`
- 测试结果：`87 passed`，Python 3.14.3
- 验收结果：
  - MCP 暴露 `list_protocols`、`plan_analysis`、`execute_analysis`、`render_figure` 四个工具。
  - 支持 stdio、sse、streamable-http 三种 transport。
  - MCP 安全边界：CSV 大小/行数/列数限制、Protocol 白名单、工作区隔离。
  - plan-review-execute-audit 工作流已封装为 MCP 工具。
- 已知限制：
  - 尚未在第三方 MCP 客户端端到端联调。
  - MCP 服务不持久化会话状态，每次调用独立执行。
- 下一步：等待 V1 最终人工验收，然后进入发布准备。

### Phase 8: V1 Release Preparation

- 状态：完成
- 日期：2026-08-06
- 版本：1.0.0
- 交付物：
  - `README.md`
  - `LICENSE`
  - `NOTICE`
  - `CHANGELOG.md`
  - `.github/workflows/ci.yml`
- 验收结果：
  - README 覆盖安装、快速开始、MCP、测试和文档入口。
  - LICENSE 使用 MIT。
  - NOTICE 记录主要第三方依赖许可证。
  - CHANGELOG 记录 1.0.0 变更。
  - CI 包含 Python、R、测试和性能 benchmark。
- 已知限制：
  - 当前目录不是 git 仓库，未创建 git 提交和标签。
  - 无远端仓库，未推送。
  - Docker 未在本机构建验证。
- 下一步：初始化 git、创建 `v1.0.0` 提交，并推送到远端。

## Phase 9: Architecture Diagram

- Status: completed
- Date: 2026-08-07
- Deliverables:
  - `docs/architecture/ResearchStat-AI-architecture.drawio` (editable two-page draw.io source)
  - `docs/architecture/ResearchStat-AI-architecture.svg` (GitHub preview)
  - `docs/architecture/README.md`
  - multilingual README links in English, Simplified Chinese, and Japanese
- Verification:
  - draw.io XML parsed successfully as standard XML
  - diagram pages cover System Architecture and Analysis Workflow
  - diagram reflects implemented V1 modules and local privacy boundary
- Known limitations:
  - `@next-ai-drawio/mcp-server@latest` could not start in this environment because its published dependency tree is missing `ajv`
  - SVG preview was generated from the same approved layout; opening the `.drawio` source in diagrams.net remains the editable source of truth
- Next step: human review of the architecture diagram before the next project phase

### Architecture homepage placement

- Status: completed
- The root README now renders the SVG architecture diagram in the GitHub homepage content area.
- The editable draw.io source remains linked directly below the preview.
