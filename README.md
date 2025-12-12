# WireViz YAML Generator

More docs at: https://olejbondahl.github.io/wireviz_yaml_generator/

An automated pipeline tool that transforms electrical design data from an SQLite database into professional wiring diagrams (using [WireViz](https://github.com/formatc1702/WireViz)) and manufacturing attachments (BOM, Labels).

## 🚀 Features

*   **Database Integration**: Reads directly from an SQLite database (`master.db`).
*   **Intelligent Transformation**:
    *   Aggregates wires into bundles/cables.
    *   Resolves point-to-point connections with via-points.
    *   Enriches connectors with metadata (MPNs, Images).
*   **Documentation Generation**:
    *   **Wiring Diagrams**: Generates visual harness diagrams (PNG/SVG).
    *   **Bill of Materials (BOM)**: Creates Excel-based BOMs with consolidated quantities.
    *   **Label Lists**: Generates cut-lists and labels for cables/wires.

## 🛠️ Requirements

*   Python 3.13+
*   [GraphViz](https://graphviz.org/download/) (Needed by WireViz)

### Python Dependencies
*   `wireviz`
*   `pyyaml`
*   `pandas`
*   `openpyxl`

## 📦 Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/YourUser/wireviz-yaml-generator.git
    cd wireviz-yaml-generator
    ```

2.  **Install Dependencies** (Using PIP):
    ```bash
    pip install wireviz pyyaml pandas openpyxl
    ```
    *Alternatively, if using Poetry:*
    ```bash
    poetry install
    ```

3.  **Install GraphViz**:
    *   Ensure `dot` is in your system PATH.

## ⚙️ Configuration

The application is configured via `config.toml` in the project root:

```toml
[paths]
base_repo_path = "C:/Users/..."     # Absolute path to repo root
db_path = "data/master.db"          # Relative path to DB
output_path = "output/"             # Where to save YAML/XLSX
drawings_path = "drawings/"         # Where to save Images
attachments_path = "attachments/"   # Where to save BOM
```

## ▶️ Usage

Run the main script from the project root:

```bash
py src/main.py
```

The script will:
1.  Connect to the database.
2.  Generate BOM and Labels in `attachments/`.
3.  Generate YAML files in `output/`.
4.  Run `wireviz` to generate diagrams in `drawings/`.

## 🧪 Testing

The project includes a comprehensive unit test suite ensuring the correctness of the transformation logic.

Run tests with:
```bash
py -m unittest discover tests
```

## 🏗️ Architecture

This project follows a **Clean Architecture** approach:

1.  **Workflow Manager**: Orchestrates the pipeline.
2.  **Data Access**: Repository pattern for SQLite (`src/data_access.py`).
3.  **Transformations**: Pure functions for business logic (`src/transformations.py`).
4.  **View Layer**: Output formatting (`src/BuildYaml.py`, `src/excel_writer.py`).

See `docs/` for detailed architectural diagrams.
