# Gemini Agent Guidelines

This document summarizes the architectural principles and coding standards established for the **WireViz Generator** project. Use these guidelines for future development to ensure consistency.

## 1. Architectural Patterns
*   **Clean Architecture**: Enforce strict separation of concerns.
    *   **Data Layer**: Repositories (e.g., `SqliteDataSource`) handle I/O and return Domain Objects.
    *   **Domain Layer**: `models.py` defines immutable data structures.
    *   **Logic Layer**: `transformations.py` contains **Pure Functions** only.
    *   **View Layer**: `BuildYaml.py` converts Domain Objects to output formats.
*   **Repository Pattern**: Isolate database logic. The application core should never see SQL queries or Cursor objects.
*   **Dependency Injection**: Orchestrators (e.g., `WorkflowManager`) must receive their dependencies (DataSources) via `__init__`, not instantiate them internally.

## 2. Data-Oriented Programming
*   **Immutability**: Use `@dataclass(frozen=True)` for all domain entities. Data should flow but not change state in place.
*   **Type Safety**: Avoid `Dict` and `Any` in internal logic. Use strict types (`Connector`, `Cable`) until the final boundary (Writing to file).

## 3. Implementation Rules
*   **Pure Core, Imperative Shell**:
    *   Core logic functions must be deterministic and side-effect free.
    *   Push I/O (Database access, File existence checks) to the "Shell" (`main.py` / `workflow_manager.py`).
*   **Error Handling**:
    *   **Never** use `sys.exit()` in library code.
    *   Raise specific custom exceptions (e.g., `WireVizError`, `ConfigurationError`).
    *   Handle exceptions only at the entry point (`main.py`).

## 4. Documentation Standards
*   **In-Code**: Comprehensive `pydoc` docstrings for all modules, classes, and functions.
*   **Architecture**: Use **Mermaid** diagrams for Component and Sequence flows.
*   **Format**: Use **Quarto** (`.qmd`) for generating professional HTML documentation.

# 5. Testing Standards
*   **Unit Tests**: Write unit tests for all core logic functions.
*   **Integration Tests**: Write integration tests for all data flows.
*   **End-to-End Tests**: Write end-to-end tests for all user flows.
    **Coverage**: Use *pytest* to measure test coverage.