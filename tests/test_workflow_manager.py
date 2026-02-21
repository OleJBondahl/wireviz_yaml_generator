"""Unit Tests for WorkflowManager orchestration."""

import os
import yaml
from unittest.mock import MagicMock

from conftest import make_net_row, make_designator_row, make_connector_row, make_cable_row
from wireviz_yaml_generator.workflow_manager import WorkflowManager


def _build_mock_source(net_rows, designator_rows, connector_rows, cable_rows):
    """Create a mock SqliteDataSource that returns the given data."""
    source = MagicMock()
    source.load_net_table.return_value = net_rows
    source.load_designator_table.return_value = designator_rows
    source.load_connector_table.return_value = connector_rows
    source.load_cable_table.return_value = cable_rows
    return source


def test_run_yaml_workflow_creates_valid_yaml(tmp_path):
    """run_yaml_workflow produces a valid WireViz YAML file."""
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1",
                     comp_des_2="J2", conn_des_2="", pin_2="1", net_name="Sig1"),
    ]
    designator_rows = [
        make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-A"),
        make_designator_row(comp_des="J2", conn_des="", conn_mpn="MPN-B"),
    ]
    connector_rows = [
        make_connector_row(mpn="MPN-A", mate_mpn="MATE-A", pincount=4),
        make_connector_row(mpn="MPN-B", mate_mpn="MATE-B", pincount=2),
    ]
    cable_rows = [make_cable_row(cable_des="W001")]

    source = _build_mock_source(net_rows, designator_rows, connector_rows, cable_rows)
    wm = WorkflowManager(source)

    yaml_path = str(tmp_path / "W001.yaml")
    wm.run_yaml_workflow("W001", yaml_path, set())

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f.read())

    assert "connectors" in data
    assert "cables" in data
    assert "connections" in data
    assert "J1-X1" in data["connectors"]
    assert "W001" in data["cables"]


def test_run_yaml_workflow_calls_data_source(tmp_path):
    """run_yaml_workflow calls all four data source methods."""
    source = _build_mock_source(
        [make_net_row()],
        [make_designator_row()],
        [make_connector_row()],
        [make_cable_row()],
    )
    wm = WorkflowManager(source)

    yaml_path = str(tmp_path / "test.yaml")
    wm.run_yaml_workflow("W001", yaml_path, set())

    source.load_net_table.assert_called_once_with("W001")
    source.load_designator_table.assert_called_once()
    source.load_connector_table.assert_called_once()
    source.load_cable_table.assert_called_once()


def test_run_attachment_workflow_creates_bom_file(tmp_path):
    """run_attachment_workflow creates BOM.xlsx when create_bom=True."""
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1",
                     comp_des_2="J2", conn_des_2="", net_name="+24V"),
    ]
    designator_rows = [
        make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-A"),
        make_designator_row(comp_des="J2", conn_des="", conn_mpn="MPN-B"),
    ]
    connector_rows = [
        make_connector_row(mpn="MPN-A", mate_mpn="MATE-A"),
        make_connector_row(mpn="MPN-B", mate_mpn="MATE-B"),
    ]
    cable_rows = [make_cable_row(cable_des="W001")]

    source = _build_mock_source(net_rows, designator_rows, connector_rows, cable_rows)
    wm = WorkflowManager(source)

    output = str(tmp_path)
    wm.run_attachment_workflow(["W001"], output, create_bom=True, create_labels=False)

    assert os.path.exists(os.path.join(output, "BOM.xlsx"))


def test_run_attachment_workflow_creates_label_files(tmp_path):
    """run_attachment_workflow creates Cablelabels.xlsx and WireLabels.xlsx."""
    net_rows = [make_net_row(cable_des="W001")]
    source = _build_mock_source(
        net_rows,
        [make_designator_row()],
        [make_connector_row()],
        [make_cable_row(cable_des="W001")],
    )
    wm = WorkflowManager(source)

    output = str(tmp_path)
    wm.run_attachment_workflow(["W001"], output, create_bom=False, create_labels=True)

    assert os.path.exists(os.path.join(output, "Cablelabels.xlsx"))
    assert os.path.exists(os.path.join(output, "WireLabels.xlsx"))


def test_run_attachment_workflow_filters_cables(tmp_path):
    """Only cables in cable_filters appear in output."""
    net_rows = [
        make_net_row(cable_des="W001", net_name="Sig1", pin_1="1"),
        make_net_row(cable_des="W002", net_name="Sig2", pin_1="1"),
    ]
    source = _build_mock_source(
        net_rows,
        [make_designator_row()],
        [make_connector_row()],
        [make_cable_row(cable_des="W001"), make_cable_row(cable_des="W002")],
    )
    wm = WorkflowManager(source)

    output = str(tmp_path)
    wm.run_attachment_workflow(["W001"], output, create_bom=False, create_labels=True)

    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(output, "WireLabels.xlsx"))
    ws = wb.active
    all_text = " ".join(str(cell.value) for row in ws.iter_rows() for cell in row if cell.value)
    assert "W001" in all_text
    assert "W002" not in all_text
