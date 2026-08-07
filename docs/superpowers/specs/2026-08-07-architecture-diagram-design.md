# Architecture Diagram Design

## Scope

Create one editable draw.io artifact for the implemented ResearchStat AI V1. The artifact documents both the platform architecture and the user-facing analysis workflow.

## Approved Structure

The `System Architecture` page shows the local privacy boundary and the implemented path through User & Data, AI Planner, Protocol Registry, Human Review Gate, Execution Layer, Python/R engines, Validation, Audit, Figure Engine, reproducible outputs, and CLI/API/MCP integration exits.

The `Analysis Workflow` page shows input, plan, human review, execute, validate, publish, and audit, ending in a reproducible analysis package.

## Constraints

- Diagram reflects implemented V1 modules only.
- It does not imply that Docker, external MCP clients, or future GUI features are fully verified.
- No commercial software internals or reverse-engineered behavior are represented.
