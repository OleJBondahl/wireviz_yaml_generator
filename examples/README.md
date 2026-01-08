# WireViz YAML Generator Examples

This folder contains example outputs demonstrating the capabilities of the WireViz YAML Generator.

## Contents

- **output_sample.yaml**: Generated WireViz YAML file for a sample harness
- **output_sample.png**: Rendered wiring diagram (PNG format)
- **output_sample.svg**: Rendered wiring diagram (SVG format) 
- **output_sample.html**: Interactive HTML diagram with connection table
- **output_sample.bom.tsv**: Bill of Materials tab-separated values file
- **DATABASE_SCHEMA.md**: Expected database schema documentation

## Understanding the Output

The YAML file (`output_sample.yaml`) shows how the generator transforms database connection tables into WireViz format, including:

- **Connectors**: Component designators with pin counts
- **Cables**: Wire bundles with wire counts
- **Connections**: Point-to-point wiring via cables

The diagrams visualize these connections, making it easy to understand the electrical harness layout.

## Running Your Own Example

1. Set up your SQLite database with the required tables (see `DATABASE_SCHEMA.md`)
2. Configure `config.toml` with your database and output paths
3. Run: `python src/main.py`

The generator will:
- Read your database
- Generate YAML files
- Create visual diagrams
- Produce BOM and label lists
