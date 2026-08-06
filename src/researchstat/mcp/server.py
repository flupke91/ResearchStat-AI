"""MCP server exposing the ResearchStat AI workflow."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .. import __version__
from . import service
from .security import McpWorkspace


def create_server(
    workspace: McpWorkspace | None = None,
) -> MCPServer:
    workspace = workspace or McpWorkspace()
    server = MCPServer(
        name="researchstat-ai",
        title="ResearchStat AI",
        description=(
            "AI-native statistical analysis with protocol binding, "
            "human review, cross-engine validation, and audit trails."
        ),
        version=__version__,
    )

    @server.tool()
    def list_protocols() -> list[str]:
        return service.list_protocols(workspace)

    @server.tool()
    def plan_analysis(
        user_input: str,
        csv_data: str,
        outcome: str | None = None,
        group: str | None = None,
        factor2: str | None = None,
        paired_by: str | None = None,
        predictors: list[str] | None = None,
    ) -> dict:
        return service.plan_analysis(
            workspace=workspace,
            user_input=user_input,
            csv_data=csv_data,
            outcome=outcome,
            group=group,
            factor2=factor2,
            paired_by=paired_by,
            predictors=predictors,
        )

    @server.tool()
    def execute_analysis(
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
    ) -> dict:
        return service.execute_analysis(
            workspace=workspace,
            user_input=user_input,
            csv_data=csv_data,
            outcome=outcome,
            group=group,
            factor2=factor2,
            paired_by=paired_by,
            predictors=predictors,
            review_action=review_action,
            override_protocol_id=override_protocol_id,
            review_reason=review_reason,
        )

    @server.tool()
    def render_figure(
        csv_data: str,
        kind: str,
        x: str | None = None,
        y: str | None = None,
        group: str | None = None,
        time: str | None = None,
        survival: str | None = None,
    ) -> dict:
        return service.render_figure(
            workspace=workspace,
            csv_data=csv_data,
            kind=kind,
            x=x,
            y=y,
            group=group,
            time=time,
            survival=survival,
        )

    return server
