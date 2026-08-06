# ResearchStat AI 傻瓜式使用教程

这篇教程假设你基本不会用命令行，按顺序复制命令即可。

## 1. 这是什么

ResearchStat AI 可以帮你完成：

1. 输入一句自然语言，例如“比较三种药物对小鼠肿瘤大小影响”。
2. 自动推荐一个统计协议。
3. 人工确认后，自动用 Python 和 R 做分析。
4. 生成可审计的分析记录。
5. 生成可以投稿用的 SVG、PDF、TIFF 图表。

## 2. 安装

### 2.1 安装 Python

需要 Python 3.11 或更高版本。安装后打开 PowerShell。

### 2.2 下载项目

```powershell
cd D:\
git clone https://github.com/flupke91/ResearchStat-AI.git
cd ResearchStat-AI
```

### 2.3 创建虚拟环境并安装

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[figure,test,mcp]"
```

如果不需要 R，也可以继续使用；R 只用于 Python vs R 交叉验证。

## 3. 最快体验

运行现成示例：

```powershell
.\.venv\Scripts\python.exe examples\workflow_demo.py
```

你会看到类似输出：

```text
Recommended protocol: one_way_anova_tukey_v1
Reviewed protocol: one_way_anova_tukey_v1
Audit record: ...\audit_records\xxxxxxxx.json
```

运行全部测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 4. 用自己的数据

### 4.1 准备 CSV

把你的数据保存成 `data.csv`，例如：

```csv
group,value
ctrl,9.2
ctrl,10.1
trt1,12.4
trt1,13.0
trt2,15.1
trt2,16.4
```

规则：

- 第一行是列名。
- 一列放分组，一列放连续数值。
- 缺失值会按 complete_case 策略自动删除并记录 warning。

### 4.2 运行完整分析

新建 `run_my_analysis.py`：

```python
import pandas as pd
from researchstat.workflow import run_analysis_workflow

data = pd.read_csv("data.csv")
output = run_analysis_workflow(
    user_input="compare value across treatment groups",
    data=data,
    outcome="value",
    group="group",
    audit_dir="my_audit",
)

print(output["plan"].model_dump())
print(output["result"].model_dump())
print("Audit:", output["record_path"])
```

运行：

```powershell
.\.venv\Scripts\python.exe run_my_analysis.py
```

## 5. 生成图表

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

会生成：

- `figures/boxplot_figure.svg`
- `figures/boxplot_figure.pdf`
- `figures/boxplot_figure.tiff`
- `figures/boxplot_figure_spec.json`

## 6. 接入 MCP

### 6.1 启动 stdio

```powershell
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport stdio
```

### 6.2 启动 HTTP

```powershell
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport streamable-http --port 8000
```

### 6.3 Claude Desktop 配置示例

```json
{
  "mcpServers": {
    "researchstat": {
      "command": "D:\\ResearchStat-AI\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "researchstat.mcp.cli",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

启动后可用工具：

- `list_protocols`
- `plan_analysis`
- `execute_analysis`
- `render_figure`

## 7. 常见问题

### Rscript 找不到

安装 R，或设置环境变量：

```powershell
$env:RSCRIPT_PATH = "C:\Program Files\R\R-4.6.1\bin\Rscript.exe"
```

### 网络下载失败

重试安装命令即可。项目本身默认本地运行，不要求连接外部服务。

### 图表文字变方块

把代码中的字体改为系统中已安装的中文字体，例如：

```python
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
```

## 8. 常用命令速查

```powershell
# 安装
.\.venv\Scripts\python.exe -m pip install -e ".[figure,test,mcp]"

# 测试
.\.venv\Scripts\python.exe -m pytest -q

# 性能测试
.\.venv\Scripts\python.exe benchmarks\run_performance.py

# 示例
.\.venv\Scripts\python.exe examples\workflow_demo.py

# MCP stdio
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport stdio
```
