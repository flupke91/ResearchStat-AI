# ResearchStat AI

AI-native statistical analysis and reproducibility platform for scientific research.

Simplified Chinese is the default project language. The canonical Chinese
introduction lives in the root [README.md](../README.md).

[English](README.en.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

V1 implements the complete loop:

```text
AI planning
  -> Protocol binding
  -> Human review
  -> Python/R engines
  -> Cross-engine validation
  -> Audit trail
  -> Publication figures
```

## Core Features

- Protocol Registry: YAML-defined methods, assumptions, posthoc, alpha, missing-data policy, and effect sizes.
- AI Planner: natural language to a structured plan, restricted to registered protocols.
- Human Review: accept or override a recommendation and record the reason.
- Multi Engine: the same request runs on Python and R with cross-validation.
- Validation: NIST StRD, R official datasets, and boundary data with `1e-8` continuous tolerance and `1e-6` p-value tolerance.
- Audit Trail: `analysis_record.json` for every analysis.
- Figure Engine: editable SVG, PDF, and TIFF at 300 DPI, with scatter, boxplot, violin, and survival plots.
- Privacy: field masking, identifier hashing, and temporary-workspace cleanup.
- MCP: stdio, SSE, and streamable-http transports.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[figure,test,mcp]"
```

## Quick Start

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

Exposed tools:

- `list_protocols`
- `plan_analysis`
- `execute_analysis`
- `render_figure`

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe benchmarks\run_performance.py
```

## Documentation

- Project plan: `PROJECT_PLAN.md`
- Research lessons: `docs/RESEARCH_LESSONS.md`
- Open source ecosystem: `docs/ECOSYSTEM.md`
- V1 acceptance: `docs/V1_ACCEPTANCE.md`
- Paper draft: `docs/PAPER.md`
- Beginner tutorial: `docs/TUTORIAL.md`

## License

MIT. See `LICENSE`; third-party licenses are listed in `NOTICE`.
