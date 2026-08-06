# ResearchStat AI V1 Acceptance

状态：已通过（发布准备完成）  
日期：2026-08-06  
版本：1.1.0

## 1. Acceptance Checklist

| # | 验收项 | 状态 | 证据 |
| - | - | - | - |
| 1 | Protocol Registry 可加载、校验、查询全部 V1 协议 | 完成 | `tests/protocols` |
| 2 | Python 与 R 双引擎可执行全部 V1 方法 | 完成 | `tests/engine`、`tests/validation` |
| 3 | 参考数据集和边界测试通过 | 完成 | NIST StRD、R official datasets、边界数据 |
| 4 | 所有方法通过 Python vs R 交叉验证 | 完成 | `tests/validation/test_cross_engine.py` |
| 5 | 每次分析生成 `analysis_record.json` | 完成 | `src/researchstat/audit` |
| 6 | Figure 输出 SVG、PDF、TIFF，SVG 文字对象可编辑 | 完成 | `tests/figures` |
| 7 | AI Planner 只能返回 Registry 内有效协议 | 完成 | 15 场景 benchmark 全通过 |
| 8 | 10000 行标准分析时间 < 10 秒 | 完成 | 实测约 0.79 秒 |
| 9 | Docker 部署文件 | 部分完成 | 文件已提供，本机无 Docker 未构建 |
| 10 | PROJECT_PLAN 已更新 | 完成 | `PROJECT_PLAN.md` |
| 11 | 人工 Review Gate | 已通过 | 用户确认发布 |

## 2. P0/P1/P2 状态

| 优先级 | 内容 | 状态 |
| - | - | - |
| P0 | Protocol Registry + AI Planner + Human Review + Python/R 交叉验证 + Audit | 完成 |
| P1 | Professional Figure Engine + 隐私 + Docker | 完成 |
| P2 | MCP 封装 | 完成 |

## 3. 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe benchmarks\run_performance.py
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport stdio
```

## 4. 已知限制

- Docker 镜像未在本机实际构建。
- MCP 已实现 stdio、sse、streamable-http 入口，但未在第三方 MCP 客户端端到端联调。
- AI Planner 当前为确定性规则版本，外部 LLM 后端留待后续版本。
- golden SVG 基线依赖固定 matplotlib 版本。

## 5. 下一步

V1 核心闭环已完成，README、LICENSE、NOTICE、CHANGELOG 和 CI 已生成。下一步是推送到远端仓库并打 `v1.0.0` 标签。
