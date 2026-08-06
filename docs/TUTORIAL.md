# ResearchStat AI 傻瓜式教程

> 默认简体中文。英文版介绍见 [README.en.md](README.en.md)，日文版见 [README.ja.md](README.ja.md)。

## 这个教程适合谁

适合不想手写统计代码、但想把“自然语言问题”变成“可复现统计结果”的人。

你可以把 ResearchStat AI 当成一个统计助手：你把数据文件路径和你想问的问题发给你的 Agent，Agent 会完成下面的闭环：

```text
理解问题
  -> 推断数据结构
  -> 推荐 Protocol
  -> 等你确认
  -> Python/R 双引擎执行
  -> 交叉验证
  -> 生成审计记录
  -> 输出图表
```

## 5 分钟速通

1. 打开项目目录。
2. 安装依赖。
3. 把下面的“话术”复制给你的 Agent。
4. Agent 给出推荐 Protocol 后，回复“接受”，或者告诉它改成哪个 Protocol。
5. 在审计目录和图表目录查看结果。

## 复制给 Agent 的话术

### 场景 1：三组比较 + 图表

把下面整段发给 Agent：

```text
请用 ResearchStat AI 分析 examples/data/tutorial_data.csv：

1. 我的研究问题是“比较三种药物对小鼠肿瘤大小的影响”。
2. outcome 列是 value，group 列是 group。
3. 先给出推荐 Protocol 和理由，等我确认后再执行。
4. 确认后运行 Python/R 双引擎并做交叉验证。
5. 生成 SVG、PDF、TIFF 图表。
6. 把每次分析写入审计记录。
```

预期结果：

- 推荐 Protocol：`one_way_anova_tukey_v1`
- 输出 boxplot 图和 `analysis_record.json`

### 场景 2：两组比较

```text
请用 ResearchStat AI 分析 examples/data/tutorial_data.csv，
只比较 ctrl 和 trt1 两组，outcome 是 value，group 是 group。
先给推荐 Protocol，我确认后再执行，并生成图表和审计记录。
```

### 场景 3：相关性分析

```text
我有一个包含 x 和 y 两列的数据文件，请用 ResearchStat AI 分析 x 和 y 的相关性，
推荐 Pearson 或 Spearman，说明理由，我确认后再执行，并输出散点图和审计记录。
```

### 场景 4：线性回归

```text
请用 ResearchStat AI 做线性回归：outcome 是 y，预测变量是 x1 和 x2。
先给推荐 Protocol，我确认后运行 Python/R 交叉验证，并输出回归散点图和审计记录。
```

### 场景 5：先脱敏再分析

```text
请用 ResearchStat AI 分析我的数据，但先把 patient_id 列哈希脱敏，
再执行统计分析，审计记录里不能出现原始 patient_id。
```

### 场景 6：人工覆盖推荐

```text
请用 ResearchStat AI 分析数据，推荐 Protocol 后先不要执行。
我会告诉你接受或覆盖；如果覆盖，请把原因写进审计记录。
```

## 快速开始（详细版）

### 1. 环境要求

- Python 3.11+
- R 4.4+（可选，但建议安装，用于 Python/R 交叉验证）
- 你的 Agent 能执行终端命令，例如 Codex、Claude、Cursor 等

### 2. 安装依赖

Windows：

```powershell
cd D:\opencode\ResearchStat-AI
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[figure,test,mcp]"
```

如果没有 R：

```powershell
winget install RProject.R
```

然后安装 R 包：

```powershell
Rscript -e "install.packages(c('jsonlite','car'), repos='https://cloud.r-project.org')"
```

### 3. 手动运行示例

```powershell
.\.venv\Scripts\python.exe examples\workflow_demo.py
```

你会在终端看到类似输出：

```text
Recommended protocol: one_way_anova_tukey_v1
Reviewed protocol: one_way_anova_tukey_v1
Audit record: examples\audit_records\....json
```

### 4. 查看结果

结果会落在这些位置：

| 内容 | 路径 |
| - | - |
| 审计记录 | `examples/audit_records/*.json` |
| 图表 SVG/PDF/TIFF | `examples/figures/` |
| Figure 规格 | `*_figure_spec.json` |

## 你会得到什么

每次分析会得到：

- `plan`：AI 推荐的分析计划
- `review`：你接受或覆盖后的最终 Protocol
- `result`：统计结果，包含统计量、p 值、效应量和假设检查
- `record`：完整的 `analysis_record.json`
- `figure`：可编辑 SVG、PDF、TIFF

## 常见问题

### Agent 说“需要更多信息”

通常是因为它无法确定分组数量或 outcome 列。你在话术里明确写出列名和分组即可。

### 我不想要 Agent 推荐的 Protocol

回复：

```text
不要用这个，改用 independent_t_test_welch_v1，原因：方差不齐。
```

Agent 会把它记录为 `(recommended, accepted, reason)`。

### 我的数据超过 10000 行

V1 性能目标为 10000 行以内，建议先筛选关键列或抽样。

### 我不想把数据发给外部 LLM

AI Planner 默认是离线规则版，不调用外部模型。未配置外部 LLM 时，数据不会外发。

## 更多文档

- 项目计划：[PROJECT_PLAN.md](../PROJECT_PLAN.md)
- V1 验收：[V1_ACCEPTANCE.md](V1_ACCEPTANCE.md)
- 竞品调研：[RESEARCH_LESSONS.md](RESEARCH_LESSONS.md)
- 开源生态：[ECOSYSTEM.md](ECOSYSTEM.md)
