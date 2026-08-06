import pandas as pd
import pytest

from researchstat.mcp import McpSecurityError, McpWorkspace


def test_workspace_parse_csv_accepts_valid_data(tmp_path):
    workspace = McpWorkspace(root_dir=tmp_path)
    data = workspace.parse_csv("group,value\nA,1\nB,2\n")

    assert len(data) == 2
    assert list(data.columns) == ["group", "value"]


def test_workspace_rejects_too_many_rows(tmp_path):
    workspace = McpWorkspace(root_dir=tmp_path, max_rows=2)

    with pytest.raises(McpSecurityError):
        workspace.parse_csv("value\n1\n2\n3\n")


def test_workspace_rejects_too_many_bytes(tmp_path):
    workspace = McpWorkspace(root_dir=tmp_path, max_csv_bytes=16)

    with pytest.raises(McpSecurityError):
        workspace.parse_csv("value\n1234567890\n")


def test_workspace_validates_protocol_allowlist(tmp_path):
    workspace = McpWorkspace(root_dir=tmp_path)

    assert workspace.validate_protocol("descriptive_v1") == "descriptive_v1"
    with pytest.raises(Exception):
        workspace.validate_protocol("not_in_registry_v1")
