# ResearchStat AI 傻瓜式教程

版本：1.0.1  
适用对象：第一次使用统计软件的科研人员、学生，以及希望让 Codex、Claude 等 Agent 自动完成统计分析的开发者。

这份教程假设你：

- 用的是 Windows 电脑。
- 不一定熟悉编程。
- 希望不写复杂代码也能完成统计分析。
- 希望 Agent 能替你规划、执行、画图并留下审计记录。

## 1. 先理解一件事

ResearchStat AI 的完整工作流是：

```text
你说需求
  -> AI 给分析计划
  -> 你确认
  -> Python/R 计算
  -> 交叉验证
  -> 生成结果和审计记录
  -> 生成图表
```

最重要的是：AI 不会偷偷决定用什么统计方法。它会先给你一个 Protocol 推荐，你确认后才会执行。

## 2. 第一次运行

### 2.1 安装 Python

如果电脑还没有 Python：

1. 打开 <https://www.python.org/downloads/>。
2. 下载 Python 3.12 或更高版本。
3. 安装时勾选 `Add Python to PATH`。

检查是否安装成功：

```powershell
python --version
```

### 2.2 安装 ResearchStat AI

打开 PowerShell，进入项目目录：

```powershell
cd D:\opencode\ResearchStat-AI
```

创建虚拟环境并安装：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[figure,test,mcp]"
```

等待安装完成。看到 `Successfully installed` 就说明成功了。

### 2.3 运行自检

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

看到 `passed` 说明环境正常。

## 3. 不写代码的用法：让 Agent 帮你

### 3.1 启动 MCP

ResearchStat AI 本身是为 Agent 使用场景设计的。启动 MCP 服务：

```powershell
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport stdio
```

也可以使用 HTTP：

```powershell
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport streamable-http --port 8000
```

### 3.2 配置到 Claude Desktop / Codex

在 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "researchstat": {
      "command": "D:\\opencode\\ResearchStat-AI\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "researchstat.mcp.cli",
        "--transport",
        "stdio"
      ],
      "cwd": "D:\\opencode\\ResearchStat-AI"
    }
  }
}
```

### 3.3 Agent 使用示例

你可以直接对 Agent 说：

```text
请使用 ResearchStat AI 分析这份数据。
数据列是 group 和 value。
我想比较三种药物对小鼠肿瘤大小的影响。
先给我分析计划，等我确认后再执行。
```

Agent 会依次调用：

1. `list_protocols`：查看可用协议。
2. `plan_analysis`：生成计划。
3. `execute_analysis`：执行分析并生成审计记录。
4. `render_figure`：生成图表。

如果 Agent 推荐了 `one_way_anova_tukey_v1`，你可以回复：

```text
确认，按这个协议执行。
```

如果你希望改用其他方法，可以回复：

```text
不用 t 检验，改用 Welch t 检验，原因是我认为两组方差不齐。
```

Agent 会以 override 形式记录 `(recommended, accepted, reason)`。

## 4. 会一点点 Python 的用法

### 4.1 最小分析示例

新建文件 `my_analysis.py`：

```python
import pandas as pd
from researchstat.workflow import run_analysis_workflow

data = pd.DataFrame({
    "group": ["ctrl"] * 10 + ["trt"] * 10,
    "value": [
        1.2, 2.1, 1.8, 3.0, 2.5,
        1.4, 2.3, 1.9, 2.8, 2.6,
        3.1, 4.2, 3.8, 5.0, 4.5,
        3.4, 4.4, 3.9, 4.8, 4.6,
    ],
})

output = run_analysis_workflow(
    user_input="compare value between two groups",
    data=data,
    outcome="value",
    group="group",
    audit_dir="audit",
)

print(output["result"].model_dump())
```

运行：

```powershell
.\.venv\Scripts\python.exe my_analysis.py
```

执行后，`audit` 目录里会出现一个 `analysis_record.json`。

### 4.2 查看审计记录

```powershell
Get-ChildItem audit\*.json
Get-Content audit\*.json
```

你会看到：

- `analysis_id`
- `user_input`
- `dataset_hash`
- `protocol_id`
- `results`
- `warnings`
- `human_review`

## 5. 生成图表

### 5.1 生成 boxplot

```python
from researchstat.figures import FigureKind, FigureRequest, render_analysis_figure

paths = render_analysis_figure(
    FigureRequest(
        kind=FigureKind.BOXPLOT,
        data=data,
        group="group",
        y="value",
        analysis_result=output["result"],
        analysis_id=output["record"].analysis_id,
    ),
    "figures",
)
print(paths)
```

输出：

```text
{
  "svg": "figures/boxplot_figure.svg",
  "pdf": "figures/boxplot_figure.pdf",
  "tiff": "figures/boxplot_figure.tiff",
  "spec": "figures/boxplot_figure_spec.json"
}
```

实际效果示例：

![boxplot](../docs/images/boxplot_preview.png)

### 5.2 生成 scatter

```python
from researchstat.figures import FigureKind, FigureRequest, render_analysis_figure

scatter_data = pd.DataFrame({
    "x": [1.0, 2.0, 3.0, 4.0, 5.0],
    "y": [1.5, 2.1, 3.0, 4.2, 4.9],
})

paths = render_analysis_figure(
    FigureRequest(
        kind=FigureKind.SCATTER,
        data=scatter_data,
        x="x",
        y="y",
    ),
    "figures",
)
```

效果示例：

![scatter](../docs/images/scatter_preview.png)

### 5.3 格式说明

- SVG：可编辑，文字仍是文字对象。
- PDF：适合投稿。
- TIFF：300 DPI，适合期刊。
- `figure_spec.json`：记录图表数据来源、分析结果和渲染参数，可复现。

## 6. Agent 高频场景

### 场景 1：让 Agent 先规划，不直接执行

推荐提示词：

```text
请调用 ResearchStat AI 的 plan_analysis。
不要执行，先告诉我推荐协议和理由。
```

### 场景 2：人工确认后执行

```text
计划我确认了，请用 execute_analysis 执行。
审计记录写到默认目录。
```

### 场景 3：覆盖 AI 推荐

```text
请覆盖推荐协议为 independent_t_test_welch_v1，
原因是我的数据方差不齐。
```

### 场景 4：生成图表

```text
分析完成后，请用 render_figure 生成 boxplot。
```

### 场景 5：复盘审计

```text
列出本次分析的 audit record，并解释每个字段。
```

## 7. 数据要求

上传给 Agent 或 MCP 的数据必须是 CSV 文本，建议：

- 第一行是列名。
- 列名使用英文和简单名称，例如 `group`、`value`、`subject`、`time`。
- 结果变量是数值。
- 分组列是 `A/B/C` 或 `ctrl/trt1/trt2` 这样的类别。
- V1 建议不超过 10000 行。
- 不要上传敏感医疗数据到云端；默认使用本地 MCP。

示例：

```csv
group,value
ctrl,1.2
ctrl,2.1
trt,3.1
trt,4.2
```

## 8. 常见问题

### `Rscript not found`

说明电脑没有安装 R。安装 R 4.4 或更高版本，或者设置：

```powershell
$env:RSCRIPT_PATH = "C:\Program Files\R\R-4.6.1\bin\Rscript.exe"
```

### 测试提示 R 相关测试被跳过

只要安装了 R，测试会自动运行。没有 R 时，Python 引擎仍可使用。

### 图表文字变成路径

SVG 默认已经保留文字对象。不要手动把 `svg.fonttype` 改成 `path`。

### Agent 找不到 MCP 工具

检查 MCP 配置中的 Python 路径是否指向项目里的 `.venv`。

## 9. 使用清单

发布分析前检查：

- [ ] 有明确 Protocol ID。
- [ ] 已通过 Human Review。
- [ ] 有 `analysis_record.json`。
- [ ] 有 `dataset_hash`。
- [ ] 图表有 `figure_spec.json`。
- [ ] 敏感列已脱敏或哈希。
- [ ] 10000 行以内。

## 10. 相关文件

- 项目计划：`PROJECT_PLAN.md`
- V1 验收：`V1_ACCEPTANCE.md`
- 论文稿：`PAPER.md`
- 竞品调研：`RESEARCH_LESSONS.md`
- 开源生态：`ECOSYSTEM.md`
- 英文介绍：`README.en.md`
- 日文介绍：`README.ja.md`
