# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Knowledge Graph (MCP Memory)

The memory server contains full API signatures, file locations, constructor parameters, and architectural decisions that persist across sessions.

**Before starting any task**, search memory with 2–3 relevant keywords:

```
mcp__memory__search_nodes("Project")
mcp__memory__search_nodes("HarnessDocCompiler")
mcp__memory__search_nodes("WorkflowManager")
mcp__memory__search_nodes("transformations")
mcp__memory__search_nodes("CsvDataSource")
```

**What's stored:**
- Every public class and module with file paths, constructor signatures, method signatures, and behavior notes
- Domain models with all field names, types, and defaults
- Architecture relations (which classes use/create/delegate to which)
- Design invariants (e.g., sort key shared between `process_cables` and `process_connections`)

**Do NOT re-read source files when memory has the answer.** Memory lookups are faster and preserve context window.

**After completing a task that revealed something non-obvious**, store the insight with `mcp__memory__create_entities` so future sessions benefit.

## API Guide

Full API documentation lives in `docs/API.md`. It covers:

- **Project API** (primary entry point) — constructor parameters, methods (`front_page`, `content_page`, `build`), pipeline overview, usage examples
- **PDF Rendering API** — `HarnessDocCompiler`, `HarnessDocConfig`, page assembly methods
- **Data Sources** — SQLite schema (4 tables), CSV format (required + optional columns), empty-value behavior
- **Domain Models** — all frozen dataclasses with field tables
- **Low-Level API** — `WorkflowManager`, transformation functions, YAML output, Excel output, exceptions

Read `docs/API.md` when you need parameter details or usage patterns beyond what memory provides.

## Project Overview

WireViz YAML Generator is a Python library for generating WireViz YAML files, SVG wiring diagrams, manufacturing documentation (BOM, labels), and PDF harness documents from SQLite or CSV electrical design data. It targets **Python 3.12+** and depends on `wireviz`, `pyyaml`, `pandas`, and `openpyxl`. Optional `typst` dependency for PDF generation. Current version: 0.1.0.

This is an unreleased library used personally — new features do not need backward compatibility.

## Build & Development Commands

```bash
# Install dependencies (uses uv)
uv sync

# Install with PDF support
uv sync --extra pdf

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

1. **Data Access Layer** (`data_access.py`, `csv_data_source.py`): SQLite/CSV queries via `SqliteDataSource` or `CsvDataSource`. Both implement `DataSourceProtocol`. Returns raw row models (`NetRow`, `DesignatorRow`, `ConnectorRow`, `CableRow`).
2. **Transformation Layer** (`transformations.py`): Pure functions that transform raw rows into domain models (`Connector`, `Cable`, `Connection`, `BomItem`). No I/O.
3. **Output Layer** (`BuildYaml.py`, `excel_writer.py`, `rendering/typst/`): Converts domain models into WireViz YAML dicts, Excel manufacturing documents, and Typst PDF documents.

### Orchestration

- `Project` (`project.py`): **High-level API**. Orchestrates the entire pipeline — data source creation, cable filtering, YAML generation, WireViz CLI invocation, BOM/labels, and PDF compilation. This is the primary entry point for library users.
- `WorkflowManager` (`workflow_manager.py`): Mid-level orchestrator — queries data, transforms, and writes output. Receives `DataSource` via constructor (dependency injection). Used internally by `Project`.
- `main.py`: CLI entry point. Loads config, initializes dependencies, runs workflows, invokes WireViz CLI for diagram generation.
- `ReadConfig.py`: Singleton `ConfigLoader` that reads `config.toml` for paths and settings (CLI only).

### Key Modules

- **`project.py`** — `Project` class: high-level API orchestrating data source → YAML → SVG → BOM/Labels → PDF.
- **`models.py`** — Frozen dataclasses: `Connector`, `Cable`, `Connection`, `BomItem`, `Wire`, and raw DB row models (`NetRow`, `DesignatorRow`, `ConnectorRow`, `CableRow`). All immutable.
- **`transformations.py`** — Pure transformation functions. No I/O operations.
- **`BuildYaml.py`** — YAML dict generation: `connector_to_dict`, `cable_to_dict`, `connection_to_list`, `_clean_dict`.
- **`data_access.py`** — `SqliteDataSource` for database queries.
- **`csv_data_source.py`** — `CsvDataSource` for CSV file input. Supports `auto_generate_cable_des`.
- **`protocols.py`** — `DataSourceProtocol` structural interface.
- **`excel_writer.py`** — Excel/BOM output generation.
- **`workflow_manager.py`** — Pipeline orchestration with dependency injection.
- **`exceptions.py`** — Exception hierarchy: `WireVizError` (base), `ConfigurationError`, `DatabaseError`, `DataSourceError`.
- **`rendering/typst/compiler.py`** — `HarnessDocCompiler` and `HarnessDocConfig` for PDF generation via Typst.
- **`rendering/typst/markdown_converter.py`** — Markdown → Typst conversion (`markdown_to_typst_title`, `markdown_to_typst_content`).
- **`rendering/typst/templates/harness_doc.typ`** — Typst page template (header with logo, title, version/date, page numbering).

### Design Principles

- **Immutability**: All domain models are frozen dataclasses. Never mutate; always return new instances.
- **Pure core / imperative shell**: Business logic in `transformations.py` is pure. I/O is pushed to boundaries (`main.py`, `data_access.py`, `excel_writer.py`, `rendering/`).
- **Dependency injection**: `WorkflowManager` receives its data source via constructor, making it testable.

### Source Layout

Source code lives under `wireviz_yaml_generator/` (flat layout, `packages = ["wireviz_yaml_generator"]` in pyproject.toml). Tests are in `tests/`.

### Testing

- Tests use **pytest** with **pytest-cov**.
- 120 tests across 7 test files.
- When changing transformation, YAML generation, or rendering logic, always run `pytest` and verify tests pass.

### Agent Git Workflow

- After completing each self-contained task, commit using the `commit-commands:commit` skill.