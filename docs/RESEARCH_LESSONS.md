# ResearchStat AI 竞品调研与借鉴清单

更新日期：2026-08-06  
状态：已纳入 V1 计划

## 1. AStats

AStats 是与 ResearchStat AI “AI 分析规划”最接近的项目。

值得借鉴：

- 自然语言解析与意图识别。
- 数据结构推断：independent、repeated measures、nested、wide format。
- 推荐前检查假设：Shapiro-Wilk、Levene、样本量是否足够。
- 人工反馈循环：接受、覆盖、解释、修正假设。
- 每次 override 记录为 `(recommended, accepted, reason)`，可形成 DPO 偏好数据。
- 自动生成 Methods 段落。
- 使用 15 个公开/合成数据集做 benchmark。

ResearchStat AI 的差异化：

- AI 只能从 Protocol Registry 选择协议。
- 推荐计划、人工修改和最终执行都必须进入审计记录。
- 数值计算始终由 Python/R 引擎完成，AI 不执行统计代码。

## 2. cross-tool-statistical-verification

该项目的六阶段验证与容差报告结构最值得学。

值得借鉴：

- 数据摄入、变换、一致性检查、可复现性、Python-vs-R 三角验证、报告。
- 每个统计量单独设置容差。
- 输出 comparison table、verification log、methodology statement。
- 明确承认“跨工具一致不等于分析正确”。
- 对合理的方法差异使用 `severity: info`，而不是一律失败。

ResearchStat AI 的差异化：

- Protocol Registry 决定哪些统计量必须被验证，而不是让用户手工声明。
- 跨引擎结果只证明实现无关性，分析正确性由参考数据和统计定义保证。

## 3. rmcp

rmcp 证明了 R 引擎与 MCP 封装的成熟工程做法。

值得借鉴：

- R 通过子进程执行，避免 Python/R 状态耦合。
- package allowlist、文件写入审批、filesystem confinement 等 guardrail。
- 支持 stdio 和 HTTP 两种 MCP transport。

ResearchStat AI 的边界：

- V1 不学 429 个 R 包白名单。
- V1 只维护 V1 方法所需的小型 R 包清单。
- MCP 在核心层稳定后封装，不属于 V1。

## 4. AutoML Stat MCP

该项目的工程化结构值得借鉴。

值得借鉴：

- Project workspace 和本地文件存储。
- Docker Compose profiles。
- 异步任务 + SSE 进度通知。
- 完整的 edge/e2e/security/performance 测试体系。
- 本地默认、无外部依赖的存储模式。

ResearchStat AI 的边界：

- 不复制 51 个工具。
- V1 只保留分析任务、Protocol、审计和 Figure 的最小 API 面。

## 5. MedStat

MedStat 的医学统计产品化思路值得借鉴。

值得借鉴：

- 100% 客户端本地处理，数据零上传。
- 出版级 Table 和 Forest Plot。
- 面向临床研究者的具体方法。

ResearchStat AI 的边界：

- V1 不加入 Firth Logistic Regression、PSM、生存分析等方法。
- 生存分析和 PSM 放 V1.5。

## 6. JASP / jamovi

JASP 和 jamovi 不是代码复用对象，而是 GUI 层透明度参考。

值得借鉴：

- 让用户清楚自己用了什么方法、什么假设、什么效应量。
- 方法数量不是越多越好，透明度优先。

ResearchStat AI 的边界：

- 不复制完整 GUI。
- V1 的 CLI/API 和后续界面都以“方法透明 + 审计可见”为原则。

## 7. V1 差异化矩阵

| 模块 | ResearchStat AI 特色 | 对应借鉴 |
| - | - | - |
| Protocol Registry | YAML 协议，绑定方法、假设、posthoc、alpha、缺失值策略、效应量 | 差异化 |
| AI Planner | 自然语言转结构化计划，只能选择 Registry 内协议 | AStats |
| Human Review | 分析前必须人工确认计划 | AStats |
| Multi Engine | 同一请求跑 Python/R，输出同一 schema | cross-tool verification / rmcp |
| Validation | NIST StRD、R datasets、边界数据，`1e-8` 与 `1e-6` 容差 | cross-tool verification |
| Audit Trail | `analysis_record.json`：数据哈希、库版本、参数、结果、warning | AStats / cross-tool verification |
| Figure Engine | SVG 可编辑、PDF、TIFF 300 DPI、显著性标注、多面板、`figure_spec.json` | MedStat / ggpubr / cnsplots |
| Privacy | 默认本地运行、脱敏、临时文件清理、权限控制 | MedStat |
| Deployment | Docker、CLI/API、10000 行 <10 秒 | AutoML Stat MCP |
| MCP | 核心稳定后再封装 | rmcp / AutoML Stat MCP |

## 8. 落地优先级

P0：

- Protocol Registry
- AI Planner
- Human Review
- Python/R 交叉验证
- Audit

P1：

- Professional Figure Engine
- 隐私
- Docker

P2：

- MCP 封装，只作为集成出口，不作为核心。

## 9. 不照搬

- 不做 429 个 R 包的 MCP 工具平台。
- 不学 JASP/jamovi 的完整 GUI。
- 不让 AI 自由调用统计函数。
- 不把“Python/R 结果一致”当作“分析正确”。
