# Changelog

## Unreleased

### Added

- Detailed Simplified Chinese README with generated figure outputs, audit
  examples, and MCP tool examples.

## 1.0.1 - 2026-08-06

### Fixed

- Golden figure test now uses a cross-platform structural baseline instead of an
  exact SVG hash, so Windows and Linux CI produce stable results.

## 1.0.0 - 2026-08-06

### Added

- Protocol Registry with 11 V1 protocols.
- Python and R statistical execution engines.
- Cross-engine validation with NIST StRD and R official datasets.
- Audit Trail with `analysis_record.json`.
- Human Review accept/override workflow.
- AI Statistical Planner with 15-scenario benchmark.
- Professional Figure Engine with SVG/PDF/TIFF output.
- Privacy masking and temporary workspace cleanup.
- Dockerfile and Docker Compose profiles.
- MCP server with stdio, sse, and streamable-http transports.
- Performance benchmark for 10000 rows.
- Multilingual documentation: English, Simplified Chinese, and Japanese.

### Notes

- Docker image not built on this machine because Docker is unavailable.
- MCP not yet tested against third-party MCP clients.
