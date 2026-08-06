"""Service functions behind MCP tools."""

from __future__ import annotations

from typing import Any

from ..figures.engine import render_analysis_figure
from ..figures.models import FigureKind, FigureRequest
from ..planner.planner import StatisticalPlanner
from ..workflow.runner import run_analysis_workflow
from .security import McpWorkspace


def list_protocols(workspace: McpWorkspace) -> list[str]:
    return workspace.allowed_protocol_ids()


def plan_analysis(
    workspace: McpWorkspace,
    user_input: str,
    csv_data: str,
    outcome: str | None = None,
    group: str | None = None,
    factor2: str | None = None,
    paired_by: str | None = None,
    predictors: list[str] | None = None,
) -> dict[str, Any]:
    data = workspace.parse_csv(csv_data)
    plan = StatisticalPlanner(workspace.registry).plan(
        user_input=user_input,
        data=data,
        outcome=outcome,
        group=group,
        factor2=factor2,
        paired_by=paired_by,
        predictors=tuple(predictors or ()),
    )
    return plan.model_dump()


def execute_analysis(
    workspace: McpWorkspace,
    user_input: str,
    csv_data: str,
    outcome: str | None = None,
    group: str | None = None,
    factor2: str | None = None,
    paired_by: str | None = None,
    predictors: list[str] | None = None,
    review_action: str = "accept",
    override_protocol_id: str | None = None,
    review_reason: str = "",
) -> dict[str, Any]:
    data = workspace.parse_csv(csv_data)
    if override_protocol_id is not None:
        workspace.validate_protocol(override_protocol_id)
    output = run_analysis_workflow(
        user_input=user_input,
        data=data,
        outcome=outcome,
        group=group,
        factor2=factor2,
        paired_by=paired_by,
        predictors=tuple(predictors or ()),
        review_action=review_action,
        override_protocol_id=override_protocol_id,
        review_reason=review_reason,
        audit_dir=workspace.audit_dir,
        registry=workspace.registry,
    )
    return {
        "plan": output["plan"].model_dump(),
        "review": output["review"].model_dump(),
        "result": output["result"].model_dump(),
        "record": output["record"].model_dump(),
        "record_path": str(output["record_path"]),
    }


def render_figure(
    workspace: McpWorkspace,
    csv_data: str,
    kind: str,
    x: str | None = None,
    y: str | None = None,
    group: str | None = None,
    time: str | None = None,
    survival: str | None = None,
) -> dict[str, str]:
    data = workspace.parse_csv(csv_data)
    request = FigureRequest(
        kind=FigureKind(kind),
        data=data,
        x=x,
        y=y,
        group=group,
        time=time,
        survival=survival,
    )
    paths = render_analysis_figure(request, workspace.figure_dir)
    return {key: str(path) for key, path in paths.items()}
