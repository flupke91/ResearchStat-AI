# ResearchStat AI

面向科研场景的 AI 原生统计分析与可复现性平台。

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

```python
import pandas as pd
from researchstat.workflow import run_analysis_workflow

data = pd.DataFrame({
    "group": ["ctrl"] * 10 + ["trt"] * 10,
    "value": [1.2, 2.1, 1.8, 3.0, 2.5] * 2 + [3.1, 4.2, 3.8, 5.0, 4.5] * 2,
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
- 竞品调研：`docs/RESEARCH_LESSONS.md`
- 开源生态：`docs/ECOSYSTEM.md`
- V1 验收：`docs/V1_ACCEPTANCE.md`

## License

MIT，详见 `LICENSE`。第三方依赖许可证见 `NOTICE`。
