"""CLI entry point for the ResearchStat AI MCP server."""

from __future__ import annotations

import argparse

from .security import McpWorkspace
from .server import create_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="researchstat-mcp",
        description="Run the ResearchStat AI MCP server.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/mcp")
    parser.add_argument("--workspace", default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    workspace = McpWorkspace(root_dir=args.workspace)
    server = create_server(workspace=workspace)
    if args.transport == "stdio":
        server.run("stdio")
    elif args.transport == "sse":
        server.run(
            "sse",
            host=args.host,
            port=args.port,
            sse_path=args.path,
        )
    else:
        server.run(
            "streamable-http",
            host=args.host,
            port=args.port,
            streamable_http_path=args.path,
        )


if __name__ == "__main__":
    main()
