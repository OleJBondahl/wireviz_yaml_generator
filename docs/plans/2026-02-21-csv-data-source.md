# Plan: Add CSV Data Source

## Context

The library currently only reads from SQLite databases (4 tables: NetTable, DesignatorTable, ConnectorTable, CableTable). The user wants a simpler alternative: a **single CSV file** containing all data in a denormalized flat format (one row per wire/connection). This avoids needing to set up a SQLite database for smaller projects. The library is unreleased and personally used — no backward compatibility needed.

The existing architecture already supports this cleanly: `WorkflowManager` uses dependency injection, and all transformation functions accept domain model objects — they don't care where the data comes from.

## CSV Column Schema

Each row = one wire connection, with connector/cable metadata inline.

**Required columns** (8 — enough for basic YAML generation):

| Column | Description |
|---|---|
| `cable_des` | Cable designator, e.g. `W001` |
| `comp_des_1` | Component designator — side 1 |
| `conn_des_1` | Connector designator — side 1 (empty string if none) |
| `pin_1` | Pin number — side 1 |
| `comp_des_2` | Component designator — side 2 |
| `conn_des_2` | Connector designator — side 2 (empty string if none) |
| `pin_2` | Pin number — side 2 |
| `net_name` | Signal name |

**Optional columns** (10 — enable BOM, connector enrichment, cable specs):

| Column | Description |
|---|---|
| `conn_mpn_1` | Connector MPN for side 1 endpoint |
| `conn_mpn_2` | Connector MPN for side 2 endpoint |
| `pincount` | Pin count (associated with whichever MPN is first seen on this row) |
| `mate_mpn` | Mating connector MPN |
| `pin_mpn` | Pin/terminal MPN |
| `conn_description` | Connector description |
| `conn_manufacturer` | Connector manufacturer |
| `wire_gauge` | Wire gauge in mm² |
| `length` | Cable length in mm |
| `cable_note` | Construction note |

Connector catalog columns (`pincount` through `conn_manufacturer`) are deduplicated by MPN — only need to be specified once per unique connector, on the first row where that MPN appears.

## Implementation Steps

### Step 1: Add `DataSourceError` to `src/exceptions.py`

Add a new exception class under the existing hierarchy:
```python
class DataSourceError(WireVizError):
    """Raised when a data source cannot be read."""
```

### Step 2: Create `src/protocols.py`

Define a `DataSourceProtocol` using `typing.Protocol` with the 5 methods that both `SqliteDataSource` and `CsvDataSource` share:
- `check_cable_existence(cable_des: str) -> bool`
- `load_net_table(cable_des_filter: str = "") -> list[NetRow]`
- `load_designator_table() -> list[DesignatorRow]`
- `load_connector_table() -> list[ConnectorRow]`
- `load_cable_table() -> list[CableRow]`

`SqliteDataSource` already satisfies this structurally — no changes needed to `src/data_access.py`.

### Step 3: Create `src/csv_data_source.py`

New `CsvDataSource` class:
- `__init__(csv_filepath: str)` — parse CSV once via `csv.DictReader`, store rows in memory, validate required columns exist
- `check_cable_existence()` — scan stored rows
- `load_net_table()` — map required columns to `NetRow`, optional filter by `cable_des`
- `load_designator_table()` — extract unique `(comp_des, conn_des, conn_mpn)` triples from both `conn_mpn_1` and `conn_mpn_2` columns. Skip rows where the MPN column is missing/empty
- `load_connector_table()` — extract unique connector catalog entries keyed by MPN. Only create `ConnectorRow` when `pincount`+`mate_mpn`+`pin_mpn` are all present
- `load_cable_table()` — extract unique cable entries keyed by `cable_des`. Only create `CableRow` when `wire_gauge`+`length` are present

Raises `DataSourceError` on missing file, empty CSV, or missing required columns.

### Step 4: Update `src/workflow_manager.py`

Change constructor type hint from `SqliteDataSource` to `DataSourceProtocol`:
```python
from protocols import DataSourceProtocol

class WorkflowManager:
    def __init__(self, data_source: DataSourceProtocol):
```

### Step 5: Update `src/__init__.py`

Add exports: `CsvDataSource`, `DataSourceProtocol`, `DataSourceError`.

### Step 6: Create `tests/test_csv_data_source.py`

Tests using `tmp_path` fixture with CSV strings:
1. `test_load_net_table_all` — all rows returned as NetRow
2. `test_load_net_table_filtered` — filter by cable_des
3. `test_check_cable_existence` — True/False cases
4. `test_load_designator_table_dedup` — no duplicates from repeated rows
5. `test_load_designator_table_both_sides` — extracts from both conn_mpn_1 and conn_mpn_2
6. `test_load_connector_table_dedup` — single entry per MPN
7. `test_load_connector_table_missing_catalog` — graceful empty result
8. `test_load_cable_table_dedup` — single entry per cable_des
9. `test_load_cable_table_missing_columns` — graceful empty result
10. `test_missing_required_columns` — DataSourceError raised
11. `test_empty_csv` — DataSourceError raised
12. `test_file_not_found` — DataSourceError raised
13. `test_minimal_csv_only_required` — net table works, other tables return empty
14. `test_csv_with_workflow_manager` — end-to-end: CsvDataSource → WorkflowManager → YAML output

### Step 7: Create example CSV and update docs

- Create `examples/example_input.csv` — sample CSV with both required and optional columns
- Update `docs/API.md` — add a "CSV Input (Alternative)" section documenting the column schema, usage example, and deduplication rules. Add `CsvDataSource` to the Data Access Layer section alongside `SqliteDataSource`. Add `DataSourceProtocol` reference.

## Files Changed

| File | Action |
|---|---|
| `src/exceptions.py` | Add `DataSourceError` |
| `src/protocols.py` | **New** — `DataSourceProtocol` |
| `src/csv_data_source.py` | **New** — `CsvDataSource` |
| `src/workflow_manager.py` | Change type hint to `DataSourceProtocol` |
| `src/__init__.py` | Add new exports |
| `tests/test_csv_data_source.py` | **New** — all CSV tests |
| `examples/example_input.csv` | **New** — sample CSV |
| `docs/API.md` | Add CSV format docs |

Files **not** changed: `src/data_access.py`, `src/models.py`, `src/transformations.py`, `src/BuildYaml.py`, `src/main.py`, existing tests.

## Verification

1. `pytest` — all existing tests still pass + new CSV tests pass
2. `uv run ruff check && uv run ruff format --check` — no lint issues
3. `uv run ty check` — no new type errors
4. Manual: create a CSV from `examples/example_input.csv`, instantiate `CsvDataSource`, pass to `WorkflowManager`, verify YAML output matches expected structure
