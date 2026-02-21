# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Knowledge Graph (MCP Memory)

The memory server contains API signatures and architectural decisions that persist across sessions. **Search memory before re-reading source files** — e.g. `mcp__memory__search_nodes("BuildYaml")` or `mcp__memory__search_nodes("WorkflowManager")`.

## Project Overview

WireViz YAML Generator is a Python library for generating WireViz YAML files and manufacturing documentation (BOM, labels, wiring diagrams) from SQLite electrical design databases. It targets **Python 3.10+** and depends on `wireviz`, `pyyaml`, `pandas`, and `openpyxl`. Current version: 0.1.0.

This is an unreleased library used personally — new features do not need backward compatibility.

## Build & Development Commands

```bash
# Install dependencies (uses uv)
uv sync

# Install in editable mode
uv pip install -e .

# Run all tests
pytest

# Run a single test file
pytest tests/test_buildyaml.py

# Run a specific test
pytest tests/test_buildyaml.py::test_function_name -v

# Type checking
uv run ty check

# Code formatting and linting
uv run ruff check
uv run ruff format
```

## Architecture

### Three-Layer Design

1. **Data Access Layer** (`data_access.py`): SQLite queries via `SqliteDataSource`. Returns raw row models (`NetRow`, `DesignatorRow`, `ConnectorRow`, `CableRow`).
2. **Transformation Layer** (`transformations.py`): Pure functions that transform raw rows into domain models (`Connector`, `Cable`, `Connection`, `BomItem`). No I/O.
3. **Output Layer** (`BuildYaml.py`, `excel_writer.py`): Converts domain models into WireViz YAML dicts and Excel manufacturing documents.

### Orchestration

- `WorkflowManager` (`workflow_manager.py`): Coordinates the pipeline — queries data, transforms, and writes output. Receives `DataSource` via constructor (dependency injection).
- `main.py`: CLI entry point. Loads config, initializes dependencies, runs workflows, invokes WireViz CLI for diagram generation.
- `ReadConfig.py`: Singleton `ConfigLoader` that reads `config.toml` for paths and settings.

### Key Modules

- **`models.py`** — Frozen dataclasses: `Connector`, `Cable`, `Connection`, `BomItem`, `Wire`, and raw DB row models (`NetRow`, `DesignatorRow`, `ConnectorRow`, `CableRow`). All immutable.
- **`transformations.py`** — Pure transformation functions. No I/O operations.
- **`BuildYaml.py`** — YAML dict generation: `connector_to_dict`, `cable_to_dict`, `connection_to_list`, `_clean_dict`.
- **`data_access.py`** — `SqliteDataSource` for database queries.
- **`excel_writer.py`** — Excel/BOM output generation.
- **`workflow_manager.py`** — Pipeline orchestration with dependency injection.
- **`exceptions.py`** — Exception hierarchy: `WireVizError` (base), `ConfigurationError`, `DatabaseError`.

### Design Principles

- **Immutability**: All domain models are frozen dataclasses. Never mutate; always return new instances.
- **Pure core / imperative shell**: Business logic in `transformations.py` is pure. I/O is pushed to boundaries (`main.py`, `data_access.py`, `excel_writer.py`).
- **Dependency injection**: `WorkflowManager` receives its data source via constructor, making it testable.

### Source Layout

Source code lives under `src/` (flat layout, `packages = ["src"]` in pyproject.toml). Tests are in `tests/`.

### Testing

- Tests use **pytest** with **pytest-cov**.
- Test files use `sys.path.insert` to find `src/` modules.
- When changing transformation or YAML generation logic, always run `pytest` and verify tests pass.

### Agent Git Workflow

- After completing each self-contained task, commit using the `commit-commands:commit` skill.
- Use git worktrees (via `superpowers:using-git-worktrees` skill) when starting work that may conflict with another running agent session.
