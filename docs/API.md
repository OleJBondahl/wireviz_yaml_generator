# WireViz YAML Generator — API Reference

## Project API (Recommended)

The `Project` class is the primary way to use this library. It orchestrates the entire pipeline from data source to finished PDF document in a single call.

### Installation

```bash
# Core library (YAML + SVG + BOM/Labels)
pip install wireviz-yaml-generator

# With PDF generation support
pip install wireviz-yaml-generator[pdf]
```

PDF generation requires the `typst` Python package, installed automatically with the `[pdf]` extra.

### Quick Start

```python
from wireviz_yaml_generator import Project

project = Project(
    title="Juicebox Cabinet Harness Documentation",
    version="02",
    date="19/01/2026",
    logo="src/ZENLogo.png",
    db="data/master.db",
    cable_start=1,
    cable_end=44,
    skip_cables=[10, 21, 32, 43],
    yaml_dir="drawings/src",
    drawings_dir="drawings/harness",
    attachments_dir="attachments",
    resources_dir="drawings/resources",
)

# Add document pages (optional — only needed for PDF output)
project.front_page("docs/front.md")
project.content_page("docs/description.md")

# Build everything
project.build(
    pdf_path="output/harness_doc.pdf",
    create_bom=True,
    create_labels=True,
)
```

This single script will:

1. Read your electrical design data from the SQLite database
2. Generate WireViz YAML files for each cable
3. Invoke WireViz CLI to produce SVG diagrams
4. Generate BOM and label Excel files
5. Compile everything into a PDF document with title page, table of contents, content sections, and wiring diagrams

### Constructor Parameters

```python
Project(
    *,
    # Project metadata
    title: str,                        # Document title (appears in header and title page)
    version: str = "01",               # Version string (appears in header)
    date: str = "",                    # Date string (appears in header)
    logo: str | None = None,           # Path to logo image (appears in header, 3cm wide)
    font: str = "Times New Roman",     # Document font family
    proprietary_notice: str | None = None,  # Notice text for bottom of title page

    # Data source — exactly one of db= or csv= is required
    db: str | None = None,             # Path to SQLite database
    csv: str | None = None,            # Path to CSV file (alternative to SQLite)
    auto_generate_cable_des: bool = False,  # CSV only: auto-assign cable designators

    # Cable selection
    cable_start: int = 0,              # First cable number to process
    cable_end: int = 50,               # Last cable number to process (inclusive)
    skip_cables: list[int] | None = None,  # Cable numbers to skip

    # Output directories (created automatically if they don't exist)
    yaml_dir: str = "drawings/src",           # Where YAML files are written
    drawings_dir: str = "drawings/harness",   # Where SVG diagrams are written
    attachments_dir: str = "attachments",     # Where BOM/Labels Excel files are written
    resources_dir: str = "drawings/resources", # Where connector images are found
)
```

Raises `ConfigurationError` if both `db` and `csv` are specified, or if neither is specified.

### Methods

#### `project.front_page(md_path: str) -> None`

Set the Markdown file used for the title page. The content is rendered centered on the page below the document title. Typically contains a revision table. A proprietary notice (if set via the constructor) is placed at the bottom of the page.

```python
project.front_page("docs/front.md")
```

Example `front.md`:

```markdown
## Revision Table
|Version|Date|Description|Created By|Approved By|
|-------|----|-----------|----------|-----------|
|01|02/12/2025|Initial version|Author|Reviewer|
|02|19/01/2026|Fixed net names|Author|Reviewer|
```

#### `project.content_page(md_path: str) -> None`

Add a content section from a Markdown file. Can be called multiple times — pages appear in the PDF in the order they are added.

```python
project.content_page("docs/description.md")
project.content_page("docs/production_notes.md")
```

Supported Markdown syntax in content pages:

| Syntax | Typst Output |
|---|---|
| `# Heading` | `= Heading` |
| `## Heading` | `== Heading` |
| `### Heading` | `=== Heading` |
| `**bold**` | `*bold*` |
| `* item` or `- item` | `- item` (bullet list) |
| `![alt](path)` | `#image("path", width: 100%)` |
| `![alt](path){width=50%}` | `#image("path", width: 50%)` |
| `\|col1\|col2\|` | Typst `#table(...)` |
| Plain paragraph | Text + `#parbreak()` |

#### `project.build(pdf_path=None, create_bom=True, create_labels=True) -> None`

Run the full pipeline. Each parameter controls what gets generated:

| Parameter | Default | Effect |
|---|---|---|
| `pdf_path` | `None` | If set, compiles a PDF to this path. Requires `wireviz-yaml-generator[pdf]`. |
| `create_bom` | `True` | Generate `BOM.xlsx` in `attachments_dir` |
| `create_labels` | `True` | Generate `Cablelabels.xlsx` and `WireLabels.xlsx` in `attachments_dir` |

YAML files and SVG diagrams are always generated. If the `wireviz` CLI is not found on PATH, YAML files are still created but SVG generation is skipped.

### Pipeline Overview

```
project.build()
│
├─ 1. Create data source (SqliteDataSource or CsvDataSource)
├─ 2. Build cable filter list: W001, W002, ... (honoring start/end/skip)
├─ 3. Scan resources_dir for connector images (*.png)
├─ 4. Run attachment workflow → BOM.xlsx, Cablelabels.xlsx, WireLabels.xlsx
├─ 5. For each cable:
│     ├─ Skip if cable doesn't exist in data source
│     ├─ Generate YAML file
│     └─ Invoke wireviz CLI → SVG file
└─ 6. If pdf_path is set:
      ├─ Add title page (with front_page markdown + proprietary notice)
      ├─ Add table of contents
      ├─ Add content pages (all registered markdown files)
      ├─ Add diagram pages (all generated SVGs)
      └─ Compile to PDF via Typst
```

### Examples

#### Minimal: YAML + SVG only (no PDF)

```python
from wireviz_yaml_generator import Project

project = Project(title="My Harness", db="data/master.db", cable_start=1, cable_end=5)
project.build()  # YAML + SVG + BOM + Labels, no PDF
```

#### CSV input with auto-generated cable designators

```python
from wireviz_yaml_generator import Project

project = Project(
    title="Simple Harness",
    csv="data/connections.csv",
    auto_generate_cable_des=True,
    cable_start=1,
    cable_end=10,
)
project.build(create_bom=False, create_labels=False)  # YAML + SVG only
```

#### Full PDF document

```python
from wireviz_yaml_generator import Project

project = Project(
    title="Production Harness Documentation",
    version="03",
    date="21/02/2026",
    logo="assets/company_logo.png",
    proprietary_notice="CONFIDENTIAL - Property of ACME Corp.",
    db="data/master.db",
    cable_start=1,
    cable_end=44,
    skip_cables=[10, 21, 32, 43],
)

project.front_page("docs/front.md")
project.content_page("docs/description.md")

project.build(pdf_path="output/harness_documentation.pdf")
```

#### YAML generation only (no wireviz, no PDF)

If the `wireviz` CLI is not installed, `build()` still generates YAML files:

```python
project = Project(title="YAML Only", db="data/master.db", cable_start=1, cable_end=5)
project.build(pdf_path=None, create_bom=False, create_labels=False)
# Result: drawings/src/W001.yaml, W002.yaml, ... (no SVG, no Excel, no PDF)
```

---

## PDF Rendering API (Advanced)

For direct control over PDF composition without the `Project` pipeline, use `HarnessDocCompiler` directly.

### HarnessDocConfig

```python
from wireviz_yaml_generator.rendering.typst import HarnessDocConfig

config = HarnessDocConfig(
    title="Document Title",      # Header title
    version="01",                # Header version
    date="",                     # Header date
    logo_path=None,              # Path to logo image (or None)
    font_family="Times New Roman",
    proprietary_notice=None,     # Notice text for title page
    root_dir=".",                # Typst root directory for path resolution
    temp_dir="temp",             # Temp directory for Typst compilation
)
```

### HarnessDocCompiler

```python
from wireviz_yaml_generator.rendering.typst import HarnessDocCompiler, HarnessDocConfig

config = HarnessDocConfig(title="My Harness", version="02", date="21/02/2026")
compiler = HarnessDocCompiler(config)

# Add pages in order
compiler.add_title_page("docs/front.md")     # Title page from markdown (optional)
compiler.add_toc(columns=2, depth=3)          # Table of contents
compiler.add_content_page("docs/desc.md")     # Content from markdown
compiler.add_diagram_page("W001", "drawings/harness/W001.svg")  # Wiring diagram
compiler.add_custom_page("#text[Raw Typst content here]")        # Raw Typst

# Compile to PDF (requires typst package)
compiler.compile("output/document.pdf")

# Or inspect the generated Typst source without compiling
typst_source = compiler.build_typst_string()
print(typst_source)
```

#### Methods

| Method | Description |
|---|---|
| `add_title_page(md_path=None)` | Centered title + optional markdown content + proprietary notice |
| `add_toc(columns=2, depth=3)` | Auto-generated table of contents |
| `add_content_page(md_path, image_root=None)` | Normal-flow content from markdown |
| `add_diagram_page(title, svg_path)` | Wiring diagram with cable title and SVG image |
| `add_custom_page(typst_content)` | Raw Typst markup |
| `compile(output_path)` | Compile to PDF (raises `ImportError` if `typst` not installed) |
| `build_typst_string()` | Return the full Typst source as a string (for debugging) |

---

## Data Sources

The library supports two input formats: **SQLite database** (original) and **CSV file** (simpler alternative). Both produce the same domain models and can be used interchangeably.

### SQLite Database

The library reads from a SQLite database with four tables. All columns are required unless noted.

#### NetTable

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

#### DesignatorTable

Maps each component/connector pair to a connector part number.

| Column | Type | Description |
|---|---|---|
| `comp_des` | `TEXT` | Component designator |
| `conn_des` | `TEXT` | Connector designator (empty string if none) |
| `conn_mpn` | `TEXT` | Connector manufacturer part number — used to look up metadata in ConnectorTable |

#### ConnectorTable

Catalog of connector specifications. Keyed by `mpn`.

| Column | Type | Required | Default | Description |
|---|---|---|---|---|
| `mpn` | `TEXT` | **required** | — | Manufacturer part number (primary lookup key) |
| `pincount` | `INTEGER` | **required** | — | Number of pins |
| `mate_mpn` | `TEXT` | **required** | — | Mating connector MPN — used in BOM output and image filename lookup |
| `pin_mpn` | `TEXT` | **required** | — | Pin/terminal MPN. If contains `"Wire Ferrule"`, triggers special ferrule logic. |
| `description` | `TEXT` | optional | `""` | Part description |
| `manufacturer` | `TEXT` | optional | `""` | Manufacturer name |

#### CableTable

Physical properties for each cable.

| Column | Type | Description |
|---|---|---|
| `cable_des` | `TEXT` | Cable designator (must match `NetTable.cable_des`) |
| `wire_gauge` | `REAL` | Wire gauge in mm² |
| `length` | `REAL` | Cable length in mm |
| `note` | `TEXT` | Construction note (appears in YAML output) |

### CSV File (Alternative)

A single denormalized CSV file where each row represents one wire connection with optional inline metadata. Avoids the need for a SQLite database for simpler projects.

**Required columns** (8 — enough for basic YAML generation):

| Column | Description |
|---|---|
| `cable_des` | Cable designator (e.g., `"W001"`) |
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
| `pincount` | Pin count (associated with whichever MPN is first seen) |
| `mate_mpn` | Mating connector MPN |
| `pin_mpn` | Pin/terminal MPN |
| `conn_description` | Connector description |
| `conn_manufacturer` | Connector manufacturer |
| `wire_gauge` | Wire gauge in mm² |
| `length` | Cable length in mm |
| `cable_note` | Construction note |

**Empty-value behavior:**

| Column | Can be empty? | Effect when empty |
|---|---|---|
| `cable_des` | Only if `auto_generate_cable_des=True` | Auto-assigned `W_AUTO_001`, `W_AUTO_002`, etc. |
| `comp_des_1/2` | No | Required |
| `pin_1/2` | No | Required |
| `net_name` | No | Required |
| `conn_des_1/2` | Yes | No sub-connector |
| `conn_mpn_1/2` | Yes | No designator entry for that side |
| `pincount`, `mate_mpn`, `pin_mpn` | Yes | Connector skipped in catalog |
| `wire_gauge`, `length` | Yes | Cable skipped in cable table |
| `conn_description`, `conn_manufacturer`, `cable_note` | Yes | Defaults to `""` |

**Deduplication rules:**
- Connector catalog columns (`pincount` through `conn_manufacturer`) only need to be specified on the first row where a given MPN appears.
- `load_designator_table()` extracts unique `(comp_des, conn_des, conn_mpn)` triples from both sides.
- `load_connector_table()` creates one `ConnectorRow` per unique MPN (requires `pincount`, `mate_mpn`, and `pin_mpn` all present).
- `load_cable_table()` creates one `CableRow` per unique `cable_des` (requires both `wire_gauge` and `length`).

---

## Domain Models

All models are frozen (immutable) dataclasses defined in `models.py`.

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

## Low-Level API Reference

These are the building blocks used internally by `Project`. Use them directly when you need fine-grained control over individual pipeline steps.

### Data Access

#### `SqliteDataSource`

```python
from wireviz_yaml_generator import SqliteDataSource

source = SqliteDataSource("data/master.db")
nets = source.load_net_table("W001")      # Filtered by cable
connectors = source.load_connector_table() # Full catalog
exists = source.check_cable_existence("W001")
```

#### `CsvDataSource`

```python
from wireviz_yaml_generator import CsvDataSource

source = CsvDataSource("data/input.csv")
source = CsvDataSource("data/input.csv", auto_generate_cable_des=True)
```

Both implement `DataSourceProtocol`:

```python
class DataSourceProtocol(Protocol):
    def check_cable_existence(self, cable_des: str) -> bool: ...
    def load_net_table(self, cable_des_filter: str = "") -> list[NetRow]: ...
    def load_designator_table(self) -> list[DesignatorRow]: ...
    def load_connector_table(self) -> list[ConnectorRow]: ...
    def load_cable_table(self) -> list[CableRow]: ...
```

### WorkflowManager

Orchestrates data loading, transformation, and output for a given data source.

```python
from wireviz_yaml_generator import WorkflowManager, SqliteDataSource

source = SqliteDataSource("data/master.db")
workflow = WorkflowManager(source)

# Generate YAML for a single cable
workflow.run_yaml_workflow("W001", "output/W001.yaml", available_images={"connector.png"})

# Generate BOM + Labels for multiple cables
workflow.run_attachment_workflow(
    cable_filters=["W001", "W002", "W003"],
    output_path="attachments/",
    create_bom=True,
    create_labels=True,
)
```

### Transformation Functions

All functions in `transformations.py` are **pure** — no I/O, no side effects.

```python
from wireviz_yaml_generator.transformations import (
    process_connectors,
    process_cables,
    process_connections,
    generate_bom_data,
    generate_cable_labels,
    generate_wire_labels,
)
```

| Function | Input | Output |
|---|---|---|
| `process_connectors(net_rows, designator_rows, connector_rows, available_images, filter_active)` | Raw DB rows + image set | `list[Connector]` |
| `process_cables(net_rows, cable_rows)` | Raw DB rows | `list[Cable]` |
| `process_connections(net_rows)` | Raw DB rows | `list[Connection]` |
| `generate_bom_data(net_rows, designator_rows, connector_rows, cable_rows)` | Raw DB rows | `list[dict]` |
| `generate_cable_labels(net_rows)` | Net rows | `list[dict]` |
| `generate_wire_labels(net_rows)` | Net rows | `list[dict]` |

### YAML Output

```python
from wireviz_yaml_generator.BuildYaml import build_yaml_file, connector_to_dict, cable_to_dict, connection_to_list

# Write a complete YAML file
build_yaml_file(connectors, cables, connections, "output/W001.yaml")

# Or convert individual models to dicts
d = connector_to_dict(connector)
d = cable_to_dict(cable)
l = connection_to_list(connection)  # Returns 3-element list
```

### Exceptions

```python
from wireviz_yaml_generator import WireVizError, ConfigurationError, DatabaseError, DataSourceError
```

| Exception | Raised by | When |
|---|---|---|
| `WireVizError` | Base class | — |
| `ConfigurationError` | `Project`, `ConfigLoader` | Invalid configuration (e.g., both db and csv specified) |
| `DatabaseError` | `SqliteDataSource` | SQLite connection or query failure |
| `DataSourceError` | `CsvDataSource` | Missing file, empty CSV, missing columns, empty cable_des |
