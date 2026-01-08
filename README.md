# WireViz YAML Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

> **Transform electrical design databases into professional wiring diagrams automatically.**

An automated pipeline tool that transforms electrical design data from SQLite databases into professional wiring diagrams using [WireViz](https://github.com/formatc1702/WireViz), complete with manufacturing documentation (BOMs, cable labels).

📖 **[Full Documentation](https://olejbondahl.github.io/wireviz_yaml_generator/)** | 📸 **[Examples](examples/)**

---

## ✨ Features

- **🗄️ Database Integration**: Reads directly from SQLite (`master.db`) with well-defined schema
- **🧠 Intelligent Transformation**:
  - Aggregates individual wires into cable bundles
  - Resolves point-to-point connections with via-pin assignments
  - Enriches connectors with metadata (MPNs, images, pinouts)
- **📊 Documentation Generation**:
  - **Wiring Diagrams**: Visual harness diagrams (PNG/SVG)
  - **Bill of Materials**: Excel-based BOMs with consolidated quantities
  - **Label Lists**: Cable cut-lists and wire end-labels for manufacturing
- **🏗️ Clean Architecture**: Pure functional core with imperative shell, dependency injection
- **✅ Tested**: Comprehensive unit test coverage for transformations

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**
- **[GraphViz](https://graphviz.org/download/)** (required by WireViz)
  - Windows: Download and install MSI, ensure `dot` is in PATH
  - macOS: `brew install graphviz`
  - Linux: `sudo apt-get install graphviz`

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/OleJBondahl/wireviz_yaml_generator.git
cd wireviz_yaml_generator
```

2. **Install dependencies** (using `uv`):
```bash
uv sync
```

Or install manually with `pip`:
```bash
pip install wireviz pyyaml pandas openpyxl
```

3. **Configure paths** in `config.toml`:
```toml
base_repo_path = "/path/to/your/project"
db_path = "data/master.db"
output_path = "output/"
drawings_path = "drawings/"
attachments_path = "attachments/"
```

### Run

```bash
python src/main.py
```

The tool will:
1. ✅ Connect to your database (`master.db`)
2. 📝 Generate BOM and labels in `attachments/`
3. 📄 Generate YAML files in `output/`
4. 🖼️ Generate diagrams in `drawings/` (requires WireViz)

---

## 📖 Example Usage

### Input: Database

Your SQLite database defines connections between components:

```sql
-- NetTable: Point-to-point connections
INSERT INTO NetTable (cable_des, comp_des_1, conn_des_1, pin_1, 
                       comp_des_2, conn_des_2, pin_2, net_name) VALUES
('W001', 'JB1', '', 'J1', 'BMU1', '', 'J3', 'SignalA'),
('W001', 'JB1', '', 'J2', 'BMU1', '', 'J6', '+24V');
```

See [`examples/DATABASE_SCHEMA.md`](examples/DATABASE_SCHEMA.md) for complete schema documentation.

###  Output: YAML

```yaml
connectors:
  JB1:
    pins: [J1,J2,J3]
    show_pincount: false
  BMU1:
    pins: [J3,J6,J11]
    show_pincount: false
cables:
  W001:
    wirecount: 2
    wirelabels: [SignalA, +24V]
connections:
  - [JB1: J1, W001: 1, BMU1: J3]
  - [JB1: J2, W001: 2, BMU1: J6]
```

### Output: Visual Diagram

![Example Wiring Diagram](examples/output_sample.png)

See [`examples/`](examples/) for complete output samples including SVG, HTML, and BOM files.

---

## ⚙️ Configuration

Edit `config.toml` in the project root:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `base_repo_path` | Parent directory for relative paths | `"C:/Projects/Electrical"` |
| `db_path` | Relative path to SQLite database | `"data/master.db"` |
| `output_path` | Where to save generated YAML files | `"output/"` |
| `drawings_path` | Where WireViz saves diagram images |`"drawings/"` |
| `attachments_path` | Where to save BOM/Labels | `"attachments/"` |

### Workflow Configuration

Edit constants in `src/main.py` to control what gets generated:

```python
CREATE_BOM = True           # Generate Bill of Materials
CREATE_LABELS = True        # Generate cable/wire labels
CREATE_DRAWINGS = True      # Generate diagram images
FROM_CABLE_NR = 0           # Start of cable range
TO_CABLE_NR = 50            # End of cable range
DONT_INCLUDE_FILTER = []    # Cables to skip (list of numbers)
```

---

## 🏗️ Architecture

This project follows **Clean Architecture** principles:

```
┌─────────────┐
│   main.py   │  Entry Point (Imperative Shell)
│  (I/O Boundary)
└──────┬──────┘
      │
      ├─►workflow_manager.py   (Orchestration)
      │        │
      │        ├─►data_access.py  (Repository Pattern)
      │        │        │
      │        │        └─►SQLite Database
      │        │
      │        ├─►transformations.py  (Pure Functions)
      │        │        │
      │        │        └─►models.py (Domain Objects)
      │        │
      │        └─►Output Layer
      │                 ├─►BuildYaml.py  (YAML Writer)
      │                 └─►excel_writer.py (Excel Writer)
      │
      └─►WireViz CLI  (External Tool)
```

### Key Principles

- **Pure Core**: Business logic in `transformations.py` is pure functions (no I/O)
- **Imperative Shell**: I/O, subprocess calls, error handling in `main.py`
- **Repository Pattern**: `data_access.py` isolates SQL from business logic
- **Dependency Injection**: `WorkflowManager` receives `DataSource` via constructor
- **Data-Oriented**: Immutable domain models (`@dataclass(frozen=True)`)

See [`docs/`](docs/) for detailed architecture diagrams.

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run with coverage report:

```bash
pytest tests/ --cov=src --cov-report=term
```

### Test Structure

- `tests/test_buildyaml.py`: Tests YAML conversion functions
- `tests/test_transformations.py`: Tests core business logic transformations

All tests focus on **pure function testing** without database dependencies.

---

## 📂 Project Structure

```
wireviz_yaml_generator/
├── src/                      # Source code
│   ├── main.py              # Entry point
│   ├── models.py            # Domain models (immutable dataclasses)
│   ├── transformations.py   # Pure transformation functions
│   ├── workflow_manager.py  # Orchestration
│   ├── data_access.py       # Database repository
│   ├── BuildYaml.py         # YAML output layer
│   ├── excel_writer.py      # Excel output layer
│   ├── ReadConfig.py        # Configuration loader
│   └── exceptions.py        # Custom exceptions
├── tests/                    # Unit tests
├── docs/                     # Architecture documentation
├── examples/                 # Example outputs and schema
│   ├── README.md
│   ├── DATABASE_SCHEMA.md
│   └── output_sample.*       # Sample outputs (YAML, PNG, SVG, etc.)
├── config.toml              # Configuration file
├── pyproject.toml           # Project metadata
└── README.md                # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Code Style**: Follow existing patterns (functional core, immutable data)
2. **Documentation**: Update pydoc docstrings for all functions/classes
3. **Testing**: Add unit tests for new functionality
4. **Architecture**: Respect the clean architecture boundaries

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run tests
pytest tests/ -v

# Check code complexity
complexipy src/
```

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[WireViz](https://github.com/formatc1702/WireViz)** - The excellent diagram generation tool
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package and project manager

---

## 📬 Contact

**Ole Johan Bondahl**
- GitHub: [@OleJBondahl](https://github.com/OleJBondahl)

---

## 🗺️ Roadmap

- [ ] Add support for multi-sheet Excel BOMs
- [ ] Implement database validation checks
- [ ] Add interactive CLI with progress bars
- [ ] Support for custom connector images per-project
- [ ] Web UI for database editing

---

**⭐ If you find this tool helpful, please star the repository!**
