"""Security boundary for the MCP server."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from ..protocols.registry import ProtocolRegistry


class McpSecurityError(ValueError):
    """Raised when MCP input violates a security policy."""


class McpWorkspace:
    def __init__(
        self,
        root_dir: str | Path | None = None,
        max_csv_bytes: int = 10 * 1024 * 1024,
        max_rows: int = 10000,
        max_columns: int = 100,
        registry: ProtocolRegistry | None = None,
    ) -> None:
        self.root = Path(root_dir) if root_dir else Path.cwd() / "mcp_workspace"
        self.root.mkdir(parents=True, exist_ok=True)
        self.audit_dir = self.root / "audit"
        self.figure_dir = self.root / "figures"
        self.audit_dir.mkdir(exist_ok=True)
        self.figure_dir.mkdir(exist_ok=True)
        self.max_csv_bytes = max_csv_bytes
        self.max_rows = max_rows
        self.max_columns = max_columns
        self.registry = registry or ProtocolRegistry.load_default()

    def parse_csv(self, csv_data: str) -> pd.DataFrame:
        encoded = csv_data.encode("utf-8")
        if len(encoded) > self.max_csv_bytes:
            raise McpSecurityError(
                f"CSV exceeds {self.max_csv_bytes} byte limit"
            )
        data = pd.read_csv(io.StringIO(csv_data))
        if len(data) > self.max_rows:
            raise McpSecurityError(
                f"CSV exceeds {self.max_rows} row limit"
            )
        if len(data.columns) > self.max_columns:
            raise McpSecurityError(
                f"CSV exceeds {self.max_columns} column limit"
            )
        return data

    def validate_protocol(self, protocol_id: str) -> str:
        protocol = self.registry.get(protocol_id)
        return protocol.id

    def allowed_protocol_ids(self) -> list[str]:
        return self.registry.ids()
