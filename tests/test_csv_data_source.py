"""Tests for CsvDataSource."""

import pytest
import yaml

from wireviz_yaml_generator.csv_data_source import CsvDataSource
from wireviz_yaml_generator.exceptions import DataSourceError
from wireviz_yaml_generator.workflow_manager import WorkflowManager

# --- Helper ---

FULL_HEADER = (
    "cable_des,comp_des_1,conn_des_1,pin_1,comp_des_2,conn_des_2,pin_2,net_name,"
    "conn_mpn_1,conn_mpn_2,pincount,mate_mpn,pin_mpn,conn_description,conn_manufacturer,"
    "wire_gauge,length,cable_note"
)

REQUIRED_HEADER = "cable_des,comp_des_1,conn_des_1,pin_1,comp_des_2,conn_des_2,pin_2,net_name"


def _write_csv(tmp_path, content: str, filename: str = "test.csv") -> str:
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return str(p)


def _full_row(
    cable="W001",
    cd1="J1",
    cn1="X1",
    p1="1",
    cd2="J2",
    cn2="",
    p2="1",
    net="Sig",
    mpn1="MPN-A",
    mpn2="MPN-B",
    pincount="10",
    mate="MATE-A",
    pin="PIN-001",
    desc="Desc",
    mfg="Mfg",
    gauge="0.5",
    length="1000",
    note="Note",
):
    return (
        f"{cable},{cd1},{cn1},{p1},{cd2},{cn2},{p2},{net},"
        f"{mpn1},{mpn2},{pincount},{mate},{pin},{desc},{mfg},"
        f"{gauge},{length},{note}"
    )


# --- Net table ---


def test_load_net_table_all(tmp_path):
    """All rows returned as NetRow."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\nW001,J1,X1,1,J2,,1,SigA\nW001,J1,X1,2,J2,,2,SigB\n")
    ds = CsvDataSource(csv)
    rows = ds.load_net_table()
    assert len(rows) == 2
    assert rows[0].net_name == "SigA"
    assert rows[1].pin_1 == "2"


def test_load_net_table_filtered(tmp_path):
    """Filter by cable_des."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\nW001,J1,X1,1,J2,,1,Sig\nW002,J3,,1,J4,,1,Other\n")
    ds = CsvDataSource(csv)
    rows = ds.load_net_table("W001")
    assert len(rows) == 1
    assert rows[0].cable_des == "W001"


# --- Cable existence ---


def test_check_cable_existence(tmp_path):
    """True for existing cable, False for missing."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\nW001,J1,X1,1,J2,,1,Sig\n")
    ds = CsvDataSource(csv)
    assert ds.check_cable_existence("W001") is True
    assert ds.check_cable_existence("W999") is False


# --- Designator table ---


def test_load_designator_table_dedup(tmp_path):
    """Duplicate rows produce single designator entry."""
    content = f"{FULL_HEADER}\n" + _full_row() + "\n" + _full_row(p1="2", p2="2", net="Sig2") + "\n"
    csv = _write_csv(tmp_path, content)
    ds = CsvDataSource(csv)
    result = ds.load_designator_table()
    # J1/X1/MPN-A and J2//MPN-B — each unique once
    keys = {(r.comp_des, r.conn_des, r.conn_mpn) for r in result}
    assert ("J1", "X1", "MPN-A") in keys
    assert ("J2", "", "MPN-B") in keys
    assert len(keys) == 2


def test_load_designator_table_both_sides(tmp_path):
    """Extracts from both conn_mpn_1 and conn_mpn_2."""
    content = f"{FULL_HEADER}\n" + _full_row(mpn1="AAA", mpn2="BBB") + "\n"
    csv = _write_csv(tmp_path, content)
    ds = CsvDataSource(csv)
    result = ds.load_designator_table()
    mpns = {r.conn_mpn for r in result}
    assert "AAA" in mpns
    assert "BBB" in mpns


# --- Connector table ---


def test_load_connector_table_dedup(tmp_path):
    """Single entry per MPN despite multiple rows."""
    content = f"{FULL_HEADER}\n" + _full_row() + "\n" + _full_row(p1="2", p2="2") + "\n"
    csv = _write_csv(tmp_path, content)
    ds = CsvDataSource(csv)
    result = ds.load_connector_table()
    mpns = [r.mpn for r in result]
    assert mpns.count("MPN-A") == 1


def test_load_connector_table_missing_catalog(tmp_path):
    """Missing pincount/mate_mpn/pin_mpn → graceful empty result."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER},conn_mpn_1\nW001,J1,X1,1,J2,,1,Sig,MPN-A\n")
    ds = CsvDataSource(csv)
    result = ds.load_connector_table()
    assert result == []


# --- Cable table ---


def test_load_cable_table_dedup(tmp_path):
    """Single entry per cable_des."""
    content = f"{FULL_HEADER}\n" + _full_row() + "\n" + _full_row(p1="2", p2="2") + "\n"
    csv = _write_csv(tmp_path, content)
    ds = CsvDataSource(csv)
    result = ds.load_cable_table()
    assert len(result) == 1
    assert result[0].cable_des == "W001"
    assert result[0].wire_gauge == 0.5
    assert result[0].length == 1000.0


def test_load_cable_table_missing_columns(tmp_path):
    """Missing wire_gauge/length → graceful empty result."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\nW001,J1,X1,1,J2,,1,Sig\n")
    ds = CsvDataSource(csv)
    result = ds.load_cable_table()
    assert result == []


# --- Error handling ---


def test_missing_required_columns(tmp_path):
    """DataSourceError when required columns are absent."""
    csv = _write_csv(tmp_path, "cable_des,comp_des_1,pin_1\nW001,J1,1\n")
    with pytest.raises(DataSourceError, match="missing required columns"):
        CsvDataSource(csv)


def test_empty_csv(tmp_path):
    """DataSourceError when CSV has header but no data rows."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\n")
    with pytest.raises(DataSourceError, match="no data rows"):
        CsvDataSource(csv)


def test_file_not_found():
    """DataSourceError when file doesn't exist."""
    with pytest.raises(DataSourceError, match="not found"):
        CsvDataSource("/nonexistent/path.csv")


# --- Minimal CSV ---


def test_minimal_csv_only_required(tmp_path):
    """Net table works; other tables return empty when only required columns present."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\nW001,J1,X1,1,J2,,1,Sig\n")
    ds = CsvDataSource(csv)
    assert len(ds.load_net_table()) == 1
    assert ds.load_designator_table() == []
    assert ds.load_connector_table() == []
    assert ds.load_cable_table() == []


# --- End-to-end with WorkflowManager ---


# --- Auto-generate cable_des ---


def test_empty_cable_des_raises_by_default(tmp_path):
    """Empty cable_des with default param raises DataSourceError."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\n,J1,X1,1,J2,,1,Sig\n")
    with pytest.raises(DataSourceError, match="empty 'cable_des'"):
        CsvDataSource(csv)


def test_auto_generate_cable_des(tmp_path):
    """Empty cable_des values get W_AUTO_001, W_AUTO_002."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\n,J1,X1,1,J2,,1,Sig\n,J3,,1,J4,,1,Other\n")
    ds = CsvDataSource(csv, auto_generate_cable_des=True)
    rows = ds.load_net_table()
    assert rows[0].cable_des == "W_AUTO_001"
    assert rows[1].cable_des == "W_AUTO_002"


def test_auto_generate_preserves_existing(tmp_path):
    """Mixed empty/non-empty: existing values preserved, empties auto-assigned."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\nW001,J1,X1,1,J2,,1,Sig\n,J3,,1,J4,,1,Other\n")
    ds = CsvDataSource(csv, auto_generate_cable_des=True)
    rows = ds.load_net_table()
    assert rows[0].cable_des == "W001"
    assert rows[1].cable_des == "W_AUTO_001"


def test_auto_generate_check_existence(tmp_path):
    """Auto-generated designators visible via check_cable_existence."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\n,J1,X1,1,J2,,1,Sig\n")
    ds = CsvDataSource(csv, auto_generate_cable_des=True)
    assert ds.check_cable_existence("W_AUTO_001") is True
    assert ds.check_cable_existence("W999") is False


def test_auto_generate_cable_table(tmp_path):
    """Auto-generated cable_des flows into load_cable_table."""
    content = f"{FULL_HEADER}\n" + _full_row(cable="", gauge="0.5", length="1000") + "\n"
    csv = _write_csv(tmp_path, content)
    ds = CsvDataSource(csv, auto_generate_cable_des=True)
    result = ds.load_cable_table()
    assert len(result) == 1
    assert result[0].cable_des == "W_AUTO_001"


def test_whitespace_cable_des_treated_as_empty(tmp_path):
    """Whitespace-only cable_des treated as empty."""
    csv = _write_csv(tmp_path, f"{REQUIRED_HEADER}\n   ,J1,X1,1,J2,,1,Sig\n")
    with pytest.raises(DataSourceError, match="empty 'cable_des'"):
        CsvDataSource(csv)


def test_auto_generate_end_to_end(tmp_path):
    """Full pipeline: CsvDataSource with auto_generate → WorkflowManager → valid YAML.

    Each empty cable_des row gets its own unique cable, so W_AUTO_001 has wirecount=1.
    """
    content = (
        f"{FULL_HEADER}\n"
        + _full_row(cable="", cd1="J1", cn1="X1", p1="1", cd2="J2", cn2="", p2="1", net="+24V")
        + "\n"
        + _full_row(cable="", cd1="J3", cn1="", p1="1", cd2="J4", cn2="", p2="1", net="gnd")
        + "\n"
    )
    csv_path = _write_csv(tmp_path, content)
    yaml_path = str(tmp_path / "output.yaml")

    ds = CsvDataSource(csv_path, auto_generate_cable_des=True)
    wm = WorkflowManager(ds)
    wm.run_yaml_workflow(cable_filter="W_AUTO_001", yaml_filepath=yaml_path, available_images=set())

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f.read())

    assert "W_AUTO_001" in data["cables"]
    assert data["cables"]["W_AUTO_001"]["wirecount"] == 1
    assert "connectors" in data
    assert "connections" in data


def test_csv_with_workflow_manager(tmp_path):
    """CsvDataSource → WorkflowManager → valid YAML output."""
    content = (
        f"{FULL_HEADER}\n"
        + _full_row(cable="W001", cd1="J1", cn1="X1", p1="1", cd2="J2", cn2="", p2="1", net="+24V")
        + "\n"
        + _full_row(
            cable="W001", cd1="J1", cn1="X1", p1="2", cd2="J2", cn2="", p2="2", net="gnd", mpn1="MPN-A", mpn2="MPN-B"
        )
        + "\n"
    )
    csv_path = _write_csv(tmp_path, content)
    yaml_path = str(tmp_path / "output.yaml")

    ds = CsvDataSource(csv_path)
    wm = WorkflowManager(ds)
    wm.run_yaml_workflow(cable_filter="W001", yaml_filepath=yaml_path, available_images=set())

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f.read())

    assert "connectors" in data
    assert "cables" in data
    assert "connections" in data
    assert "J1-X1" in data["connectors"]
    assert "J2" in data["connectors"]
    assert data["cables"]["W001"]["wirecount"] == 2
    assert len(data["connections"]) == 2
