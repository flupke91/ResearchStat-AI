from researchstat.mcp import McpWorkspace
from researchstat.mcp.service import execute_analysis, plan_analysis, render_figure


CSV = "group,value\nA,1\nA,2\nA,3\nB,4\nB,5\nB,6\n"


def test_plan_analysis_service(tmp_path):
    workspace = McpWorkspace(root_dir=tmp_path)

    plan = plan_analysis(
        workspace=workspace,
        user_input="compare value between two groups",
        csv_data=CSV,
        outcome="value",
        group="group",
    )

    assert plan["status"] == "ready"
    assert plan["recommended_protocol_id"] == "independent_t_test_student_v1"


def test_execute_analysis_service_writes_audit(tmp_path):
    workspace = McpWorkspace(root_dir=tmp_path)

    output = execute_analysis(
        workspace=workspace,
        user_input="compare value between two groups",
        csv_data=CSV,
        outcome="value",
        group="group",
    )

    assert output["record"]["protocol_id"] == "independent_t_test_student_v1"
    assert output["record_path"].endswith(".json")


def test_render_figure_service(tmp_path):
    workspace = McpWorkspace(root_dir=tmp_path)

    paths = render_figure(
        workspace=workspace,
        csv_data=CSV,
        kind="boxplot",
        group="group",
        y="value",
    )

    assert paths["svg"].endswith("boxplot_figure.svg")
