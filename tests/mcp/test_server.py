import anyio

from researchstat.mcp import McpWorkspace, create_server


def test_create_server_registers_tools(tmp_path):
    server = create_server(McpWorkspace(root_dir=tmp_path))

    tools = anyio.run(server.list_tools)

    assert {tool.name for tool in tools} == {
        "list_protocols",
        "plan_analysis",
        "execute_analysis",
        "render_figure",
    }
