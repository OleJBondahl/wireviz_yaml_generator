# WireViz YAML Generator — API Reference

This document describes the data models, database schema, and public functions that make up the library's API. Fields are marked **required** or **optional** (with defaults shown).

---

## Database Schema (Input)

The library reads from a SQLite database with four tables. All columns are required unless noted.

### NetTable

Each row represents one wire connection between two pins via a cable.

| Column | Type | Description |
|---|---|---|
| `cable_des` | `TEXT` | Cable designator (e.g., `"W001"`) |
| `comp_des_1` | `TEXT` | Component designator — side 1 (e.g., `"J1"`) |
| `conn_des_1` | `TEXT` | Connector designator — side 1 (e.g., `"X1"`). Empty string if component has no sub-connector. |
| `pin_1` | `TEXT` | Pin number — side 1 |
| `comp_des_2` | `TEXT` | Component designator — side 2 |
| `conn_des_2` | `TEXT` | Connector designator — side 2. Empty string if none. |
| `pin_2` | `TEXT` | Pin number — side 2 |
| `net_name` | `TEXT` | Electrical signal name (e.g., `"+24V"`, `"gnd"`, `"SignalA"`) |

### DesignatorTable

Maps each component/connector pair to a connector part number.

| Column | Type | Description |
|---|---|---|
| `comp_des` | `TEXT` | Component designator |
| `conn_des` | `TEXT` | Connector designator (empty string if none) |
| `conn_mpn` | `TEXT` | Connector manufacturer part number — used to look up metadata in ConnectorTable |

### ConnectorTable

Catalog of connector specifications. Keyed by `mpn`.

| Column | Type | Required | Default | Description |
|---|---|---|---|---|
| `mpn` | `TEXT` | **required** | — | Manufacturer part number (primary lookup key) |
| `pincount` | `INTEGER` | **required** | — | Number of pins |
| `mate_mpn` | `TEXT` | **required** | — | Mating connector MPN — used in BOM output and image filename lookup |
| `pin_mpn` | `TEXT` | **required** | — | Pin/terminal MPN. If contains `"Wire Ferrule"`, triggers special ferrule logic. |
| `description` | `TEXT` | optional | `""` | Part description |
| `manufacturer` | `TEXT` | optional | `""` | Manufacturer name |

### CableTable

Physical properties for each cable.

| Column | Type | Description |
|---|---|---|
| `cable_des` | `TEXT` | Cable designator (must match `NetTable.cable_des`) |
| `wire_gauge` | `REAL` | Wire gauge in mm² |
| `length` | `REAL` | Cable length in mm |
| `note` | `TEXT` | Construction note (appears in YAML output) |

---

## Domain Models

All models are frozen (immutable) dataclasses defined in `src/models.py`.

### Connector

Represents a physical connector in the wiring diagram.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `designator` | `str` | **required** | — | Schematic designator (e.g., `"J1-X1"` or `"J2"`) |
| `mpn` | `str \| None` | optional | `None` | Manufacturer part number (mating side) |
| `pincount` | `int \| None` | optional | `None` | Number of pins |
| `description` | `str \| None` | optional | `None` | Part description |
| `manufacturer` | `str \| None` | optional | `None` | Manufacturer name |
| `image_src` | `str \| None` | optional | `None` | Relative path to connector image |
| `image_caption` | `str \| None` | optional | `None` | Caption for the image |
| `hide_disconnected_pins` | `bool` | optional | `False` | WireViz: hide pins with no connections |
| `show_pincount` | `bool` | optional | `True` | WireViz: show pin count on diagram |
| `notes` | `str \| None` | optional | `None` | Notes shown on the diagram |

### Cable

Represents a cable bundle containing one or more wires.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `designator` | `str` | **required** | — | Cable designator (e.g., `"W001"`) |
| `wire_count` | `int` | **required** | — | Number of wires in the bundle |
| `wire_labels` | `list[str]` | **required** | — | Signal names, one per wire. Order matches `Connection.via_pin`. |
| `category` | `str` | optional | `"bundle"` | WireViz category |
| `length` | `float \| None` | optional | `None` | Cable length in mm |
| `length_unit` | `str` | optional | `"mm"` | Unit for length |
| `gauge` | `float \| None` | optional | `None` | Wire gauge in mm² |
| `gauge_unit` | `str` | optional | `"mm2"` | Unit for gauge |
| `notes` | `str \| None` | optional | `None` | Construction notes |

### Connection

Represents a point-to-point electrical connection through a cable.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `from_designator` | `str` | **required** | — | Source connector designator |
| `from_pin` | `str` | **required** | — | Source pin number |
| `to_designator` | `str` | **required** | — | Destination connector designator |
| `to_pin` | `str` | **required** | — | Destination pin number |
| `via_cable` | `str` | **required** | — | Cable carrying this connection |
| `via_pin` | `int` | **required** | — | Wire position within the cable (1-indexed) |
| `net_name` | `str` | **required** | — | Electrical signal name |

### BomItem

A single line in the Bill of Materials.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `mpn` | `str` | **required** | — | Part number |
| `description` | `str` | **required** | — | Part description |
| `manufacturer` | `str` | **required** | — | Manufacturer name |
| `quantity` | `float` | **required** | — | Quantity needed |
| `unit` | `str` | **required** | — | Unit of measure (`"pcs"` or `"Meter"`) |

### Wire

Physical properties of a single wire strand.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `gauge` | `float \| None` | **required** | — | Wire gauge |
| `gauge_unit` | `str` | optional | `"mm2"` | Gauge unit |
| `color` | `str \| None` | optional | `None` | Wire color |
| `description` | `str` | optional | `"Radox 125"` | Wire type description |
| `manufacturer` | `str` | optional | `""` | Manufacturer |

---

## Raw Database Row Models

These mirror the SQLite tables exactly and are the input to all transformation functions.

### NetRow

All fields **required**: `cable_des`, `comp_des_1`, `conn_des_1`, `pin_1`, `comp_des_2`, `conn_des_2`, `pin_2`, `net_name` — all `str`.

### DesignatorRow

All fields **required**: `comp_des`, `conn_des`, `conn_mpn` — all `str`.

### ConnectorRow

| Field | Type | Required | Default |
|---|---|---|---|
| `mpn` | `str` | **required** | — |
| `pincount` | `int` | **required** | — |
| `mate_mpn` | `str` | **required** | — |
| `pin_mpn` | `str` | **required** | — |
| `description` | `str` | optional | `""` |
| `manufacturer` | `str` | optional | `""` |

### CableRow

All fields **required**: `cable_des` (`str`), `wire_gauge` (`float`), `length` (`float`), `note` (`str`).

---

## Public Functions

### Transformation Layer (`src/transformations.py`)

All functions are **pure** — no I/O, no side effects.

#### `process_connectors`

```python
process_connectors(
    net_rows: list[NetRow],
    designator_rows: list[DesignatorRow],
    connector_rows: list[ConnectorRow],
    available_images: set[str],   # e.g. {"MATE-123.png"}
    filter_active: bool,
) -> list[Connector]
```

Transforms raw rows into enriched `Connector` objects. When `filter_active=True`, only connectors referenced in `net_rows` are returned.

**Business rules:**
- Designator format: `"{comp_des}-{conn_des}"` if `conn_des` is non-empty, else `"{comp_des}"`
- Wire Ferrule: if `pin_mpn` contains `"Wire Ferrule"` → `notes="Terminate Wires in Wire Ferrule"`, `hide_disconnected=True`, `show_pincount=False`, `mpn=None`
- Image: if `"{mate_mpn}.png"` is in `available_images` → `image_src="../resources/{mate_mpn}.png"`
- MPN not found: `mpn="NotFound"`, `hide_disconnected=True`

#### `process_cables`

```python
process_cables(
    net_rows: list[NetRow],
    cable_rows: list[CableRow],
) -> list[Cable]
```

Aggregates wires into `Cable` objects. Looks up gauge/notes from `cable_rows`.

**Critical invariant:** Sorts by `(cable_des, comp_des_1, conn_des_1, pin_1)` — the same key used by `process_connections()`. This ensures `wire_labels[i]` corresponds to `via_pin = i+1`.

#### `process_connections`

```python
process_connections(net_rows: list[NetRow]) -> list[Connection]
```

Maps net rows to `Connection` objects with auto-assigned `via_pin` (1-indexed per cable).

**Critical invariant:** Uses the same sort key as `process_cables()`.

#### `generate_bom_data`

```python
generate_bom_data(
    net_rows: list[NetRow],
    designator_rows: list[DesignatorRow],
    connector_rows: list[ConnectorRow],
    cable_rows: list[CableRow],
) -> list[dict[str, Any]]
```

Returns BOM as list-of-dicts with keys: `mpn`, `description`, `manufacturer`, `quantity`, `unit`.

**Business rules:**
- Connector quantity: count of active designators per `conn_mpn`, outputs `mate_mpn`
- Wire color: `"Red"` if `"24V"` in net_name, `"Black"` if `"gnd"` in net_name, `"White"` otherwise (case-sensitive)
- Wire quantity: `(length_mm × wire_count) / 1000` → meters
- Wire MPN format: `"{wire_gauge}mm2-{color}"`

#### `generate_cable_labels`

```python
generate_cable_labels(net_rows: list[NetRow]) -> list[dict[str, str]]
```

Returns `[{"Label": ...}, ...]`. First entry is `"Cable Labels:"` header. Labels are deduplicated per cable. Format: `"{comp_des}-{conn_des} : {cable_des}"`.

#### `generate_wire_labels`

```python
generate_wire_labels(net_rows: list[NetRow]) -> list[dict[str, str]]
```

Returns `[{"Label": ...}, ...]`. First entry is `"Wire Labels:"` header. Grouped by cable with `"Labels: {cable_des}"` sub-headers. Each wire produces two lines (one per side).

### YAML Output Layer (`src/BuildYaml.py`)

#### `connector_to_dict`

```python
connector_to_dict(c: Connector) -> dict[str, Any]
```

Converts to WireViz dict. `show_pincount` only appears when `False`. `hide_disconnected_pins` only appears when `True`. Image included as nested dict with `height=50`.

#### `cable_to_dict`

```python
cable_to_dict(c: Cable) -> dict[str, Any]
```

Converts to WireViz dict. Key mapping: `wire_count` → `"wirecount"`, `wire_labels` → `"wirelabels"`.

#### `connection_to_list`

```python
connection_to_list(c: Connection) -> list[dict[str, Any]]
```

Returns 3-element list: `[{from_designator: from_pin}, {via_cable: via_pin}, {to_designator: to_pin}]`. Pin values for connectors are `str`, for cables `int`.

#### `build_yaml_file`

```python
build_yaml_file(
    connectors: list[Connector],
    cables: list[Cable],
    connections: list[Connection],
    yaml_filepath: str,
) -> None
```

Writes a complete WireViz YAML file. Root structure:

```yaml
connectors:
  <designator>: {mpn, pincount, ...}
cables:
  <designator>: {wirecount, category, ...}
connections:
  - [{from: pin}, {cable: pin}, {to: pin}]
```

### Data Access Layer (`src/data_access.py`)

#### `SqliteDataSource`

```python
class SqliteDataSource:
    def __init__(self, db_filepath: str): ...
    def check_cable_existence(self, cable_des: str) -> bool: ...
    def load_net_table(self, cable_des_filter: str = "") -> list[NetRow]: ...
    def load_designator_table(self) -> list[DesignatorRow]: ...
    def load_connector_table(self) -> list[ConnectorRow]: ...
    def load_cable_table(self) -> list[CableRow]: ...
```

Raises `DatabaseError` (subclass of `WireVizError`) on SQLite failures.

### Orchestration (`src/workflow_manager.py`)

#### `WorkflowManager`

```python
class WorkflowManager:
    def __init__(self, data_source: SqliteDataSource): ...

    def run_yaml_workflow(
        self,
        cable_filter: str,             # single cable designator
        yaml_filepath: str,            # output path
        available_images: set[str],    # image filenames in resources/
    ) -> None: ...

    def run_attachment_workflow(
        self,
        cable_filters: list[str],     # cable designators to include
        output_path: str,             # directory for Excel files
        create_bom: bool = True,
        create_labels: bool = True,
    ) -> None: ...
```

### Excel Output (`src/excel_writer.py`)

```python
def write_xlsx(data: list[dict[str, Any]], filename: str, output_path: str) -> None
def add_misc_bom_items(bom_data: list[dict[str, Any]], filename: str, output_path: str) -> list[dict[str, Any]]
```

`write_xlsx` creates `{output_path}/{filename}.xlsx`. Skips creation if `data` is empty.

`add_misc_bom_items` reads `{output_path}/{filename}.csv` and appends rows to `bom_data`. Returns original data unchanged if CSV not found.
