# ResearchStat AI

面向科研场景的 AI 原生统计分析与可复现性平台。

默认简体中文介绍以根目录 [README.md](../README.md) 为准，本页为中文镜像。

[English](README.en.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

V1 已形成完整闭环：

```text
AI 规划
  -> Protocol 绑定
  -> 人工 Review
  -> Python/R 双引擎
  -> 交叉验证
  -> Audit Trail
  -> 出版级 Figure
```

## 核心能力

- Protocol Registry：YAML 定义方法、假设、posthoc、alpha、缺失值策略和效应量。
- AI Planner：自然语言转结构化计划，只能从 Registry 选择协议。
- Human Review：分析前接受或覆盖推荐协议，记录 `(recommended, accepted, reason)`。
- Multi Engine：同一请求可在 Python 和 R 上执行，并做交叉验证。
- Validation：NIST StRD、R 官方 datasets、边界数据，连续统计量容差 `1e-8`，p 值容差 `1e-6`。
- Audit Trail：每次分析生成 `analysis_record.json`。
- Figure Engine：SVG 可编辑、PDF、TIFF 300 DPI，支持 scatter、boxplot、violin、survival。
- Privacy：字段脱敏、标识符哈希、临时目录自动清理。
- MCP：stdio、sse、streamable-http 三种 transport。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[figure,test,mcp]"
```

## 快速开始

不想看代码？先读 [新手教程](TUTORIAL.md)，里面有可以直接复制给 Agent 的话术。

示例数据：`examples/data/tutorial_data.csv`

```python
import pandas as pd
from researchstat.workflow import run_analysis_workflow

data = pd.read_csv("examples/data/tutorial_data.csv")

output = run_analysis_workflow(
    user_input="compare three drugs on mouse tumor size",
    data=data,
    outcome="value",
    group="group",
    audit_dir="audit",
)
print(output["result"].model_dump())
```

## MCP

```powershell
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport stdio
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport streamable-http --port 8000
```

暴露工具：

- `list_protocols`
- `plan_analysis`
- `execute_analysis`
- `render_figure`

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe benchmarks\run_performance.py
```

## 文档

- 项目计划：`PROJECT_PLAN.md`
- 新手教程：`docs/TUTORIAL.md`
- 竞品调研：`docs/RESEARCH_LESSONS.md`
- 开源生态：`docs/ECOSYSTEM.md`
- V1 验收：`docs/V1_ACCEPTANCE.md`
- 论文稿：`docs/PAPER.md`
- 傻瓜式教程：`docs/TUTORIAL.md`

## License

MIT，详见 `LICENSE`。第三方依赖许可证见 `NOTICE`。
