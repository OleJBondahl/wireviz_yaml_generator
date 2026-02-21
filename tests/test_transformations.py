"""Unit Tests for Transformations Module."""

import pytest
from conftest import make_net_row, make_designator_row, make_connector_row, make_cable_row
from wireviz_yaml_generator.models import NetRow, DesignatorRow, ConnectorRow, CableRow
from wireviz_yaml_generator.transformations import (
    process_connectors,
    process_cables,
    process_connections,
    generate_bom_data,
    generate_cable_labels,
    generate_wire_labels,
)


@pytest.fixture
def sample_data():
    """Pytest fixture providing consistent test data for transformation tests."""
    net_rows = [
        make_net_row(net_name="SignalA", pin_1="1", pin_2="1"),
        make_net_row(net_name="+24V", pin_1="2", pin_2="2")
    ]

    designator_rows = [
        make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-123"),
        make_designator_row(comp_des="J2", conn_des="", conn_mpn="MPN-456")
    ]

    connector_rows = [
        make_connector_row(mpn="MPN-123", mate_mpn="MATE-123", pincount=10),
        make_connector_row(mpn="MPN-456", mate_mpn="MATE-456", pincount=4)
    ]

    cable_rows = [
        make_cable_row()
    ]
    return {
        "net_rows": net_rows,
        "designator_rows": designator_rows,
        "connector_rows": connector_rows,
        "cable_rows": cable_rows
    }

def test_process_connectors(sample_data):
    """Test connector enrichment with metadata and image resolution."""
    # Passing empty image set for testing pure logic
    available_images = {"MATE-123.png"}

    result = process_connectors(
        sample_data["net_rows"],
        sample_data["designator_rows"],
        sample_data["connector_rows"],
        available_images=available_images,
        filter_active=True
    )

    assert len(result) == 2
    # Result is now a list of Connector objects
    c1 = next(r for r in result if r.designator == 'J1-X1')
    assert c1.mpn == "MATE-123"
    # Verify Image logic
    assert c1.image_src == "../resources/MATE-123.png"

    c2 = next(r for r in result if r.designator == 'J2')
    assert c2.mpn == "MATE-456"
    # Verify Image logic (not in set)
    assert c2.image_src is None

def test_process_cables(sample_data):
    """Test cable aggregation and wire label assignment."""
    result = process_cables(sample_data["net_rows"], sample_data["cable_rows"])

    assert len(result) == 1
    cable = result[0]
    assert cable.designator == "W001"
    assert cable.wire_count == 2
    # Verify set contains expected labels
    assert "SignalA" in cable.wire_labels
    assert "+24V" in cable.wire_labels

def test_process_connections(sample_data):
    """Test connection transformation and via-pin assignment."""
    result = process_connections(sample_data["net_rows"])
    assert len(result) == 2
    conn1 = result[0]
    assert conn1.from_pin == "1"

def test_generate_bom_data(sample_data):
    """Test BOM generation with correct quantity aggregation."""
    # BOM Data still returns List[Dict] as per current design (pandas ready)
    bom = generate_bom_data(
        sample_data["net_rows"],
        sample_data["designator_rows"],
        sample_data["connector_rows"],
        sample_data["cable_rows"]
    )

    # Check quantities
    c1 = next(b for b in bom if b['mpn'] == 'MATE-123')
    assert c1['quantity'] == 1

    # Check wire mapping logic
    red_wire = next(b for b in bom if 'Red' in b['mpn'])
    assert red_wire['quantity'] == 1.0


# --- Critical Ordering Invariant ---

def test_cable_connection_ordering_invariant():
    """CRITICAL: wire_labels[i] in Cable must correspond to via_pin=i+1 in Connection.

    process_cables and process_connections must use the same sort key.
    If this test fails, wiring diagrams will have labels on wrong wires.
    """
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J2", conn_des_1="X2", pin_1="3", net_name="GND"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1", net_name="+24V"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="2", net_name="Signal"),
    ]
    cable_rows = [make_cable_row(cable_des="W001")]

    cables = process_cables(net_rows, cable_rows)
    connections = process_connections(net_rows)

    cable = cables[0]
    for conn in connections:
        assert cable.wire_labels[conn.via_pin - 1] == conn.net_name, (
            f"Wire label mismatch: wire_labels[{conn.via_pin - 1}]={cable.wire_labels[conn.via_pin - 1]!r} "
            f"but connection net_name={conn.net_name!r}"
        )


def test_cable_connection_ordering_multi_cable():
    """Ordering invariant holds across multiple cables with interleaved rows."""
    net_rows = [
        make_net_row(cable_des="W002", comp_des_1="J3", conn_des_1="", pin_1="1", net_name="SigC"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="2", net_name="SigB"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1", net_name="SigA"),
        make_net_row(cable_des="W002", comp_des_1="J3", conn_des_1="", pin_1="2", net_name="SigD"),
    ]
    cable_rows = [
        make_cable_row(cable_des="W001"),
        make_cable_row(cable_des="W002"),
    ]

    cables = process_cables(net_rows, cable_rows)
    connections = process_connections(net_rows)

    cable_map = {c.designator: c for c in cables}
    for conn in connections:
        cable = cable_map[conn.via_cable]
        assert cable.wire_labels[conn.via_pin - 1] == conn.net_name


# --- process_connectors edge cases ---

def test_process_connectors_wire_ferrule():
    """When pin_mpn contains 'Wire Ferrule', special flags must be set."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="X1")]
    designator_rows = [make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-F")]
    connector_rows = [
        make_connector_row(mpn="MPN-F", mate_mpn="MATE-F", pin_mpn="Wire Ferrule DIN 0.5mm2")
    ]

    result = process_connectors(net_rows, designator_rows, connector_rows, set(), filter_active=True)

    c = result[0]
    assert c.notes == "Terminate Wires in Wire Ferrule"
    assert c.hide_disconnected_pins is True
    assert c.show_pincount is False
    assert c.mpn is None


def test_process_connectors_mpn_not_found():
    """Missing MPN in ConnectorTable sets mpn='NotFound' and hide_disconnected=True."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="X1")]
    designator_rows = [make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MISSING")]
    connector_rows = []

    result = process_connectors(net_rows, designator_rows, connector_rows, set(), filter_active=True)

    c = result[0]
    assert c.mpn == "NotFound"
    assert c.hide_disconnected_pins is True
    assert c.pincount == 99


def test_process_connectors_filter_active_false():
    """filter_active=False returns ALL designators, not just those in net_rows."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="X1")]
    designator_rows = [
        make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-123"),
        make_designator_row(comp_des="J99", conn_des="X99", conn_mpn="MPN-123"),
    ]
    connector_rows = [make_connector_row(mpn="MPN-123")]

    result = process_connectors(net_rows, designator_rows, connector_rows, set(), filter_active=False)

    designators = [c.designator for c in result]
    assert "J1-X1" in designators
    assert "J99-X99" in designators
    assert len(result) == 2


def test_process_connectors_natural_sort_order():
    """Connectors must sort naturally: J1, J2, J10 (not J1, J10, J2)."""
    net_rows = [
        make_net_row(comp_des_1="J10", conn_des_1="X1", comp_des_2="J1", conn_des_2="X1"),
        make_net_row(comp_des_1="J2", conn_des_1="X1", comp_des_2="J1", conn_des_2="X1"),
    ]
    designator_rows = [
        make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-123"),
        make_designator_row(comp_des="J2", conn_des="X1", conn_mpn="MPN-123"),
        make_designator_row(comp_des="J10", conn_des="X1", conn_mpn="MPN-123"),
    ]
    connector_rows = [make_connector_row(mpn="MPN-123")]

    result = process_connectors(net_rows, designator_rows, connector_rows, set(), filter_active=True)

    designators = [c.designator for c in result]
    assert designators == ["J1-X1", "J2-X1", "J10-X1"]


def test_process_connectors_image_resolution():
    """Image is set when '{mate_mpn}.png' is in available_images."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="X1")]
    designator_rows = [make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-123")]
    connector_rows = [make_connector_row(mpn="MPN-123", mate_mpn="MATE-IMG")]

    result_with = process_connectors(
        net_rows, designator_rows, connector_rows, {"MATE-IMG.png"}, filter_active=True
    )
    assert result_with[0].image_src == "../resources/MATE-IMG.png"
    assert result_with[0].image_caption == "ISO view"

    result_without = process_connectors(
        net_rows, designator_rows, connector_rows, set(), filter_active=True
    )
    assert result_without[0].image_src is None
    assert result_without[0].image_caption is None


# --- Designator format ---

def test_connection_designator_format_with_conn_des():
    """Designator is '{comp_des}-{conn_des}' when conn_des is non-empty."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="X1", comp_des_2="J2", conn_des_2="X2")]
    result = process_connections(net_rows)
    assert result[0].from_designator == "J1-X1"
    assert result[0].to_designator == "J2-X2"


def test_connection_designator_format_without_conn_des():
    """Designator is just '{comp_des}' when conn_des is empty."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="", comp_des_2="J2", conn_des_2="")]
    result = process_connections(net_rows)
    assert result[0].from_designator == "J1"
    assert result[0].to_designator == "J2"


# --- Cable gauge/notes lookup ---

def test_process_cables_gauge_and_notes_from_cable_rows():
    """Gauge and notes are looked up from cable_rows by cable_des."""
    net_rows = [make_net_row(cable_des="W001", net_name="Sig")]
    cable_rows = [make_cable_row(cable_des="W001", wire_gauge=1.5, note="Special")]

    result = process_cables(net_rows, cable_rows)
    assert result[0].gauge == 1.5
    assert result[0].notes == "Special"


def test_process_cables_missing_cable_row():
    """Cable not in cable_rows gets gauge=None, notes=None."""
    net_rows = [make_net_row(cable_des="W999", net_name="Sig")]
    cable_rows = []

    result = process_cables(net_rows, cable_rows)
    assert result[0].gauge is None
    assert result[0].notes is None


# --- BOM wire color and quantity ---

def test_bom_wire_color_classification():
    """Wire color: '24V' -> Red, 'gnd' -> Black, anything else -> White."""
    net_rows = [
        make_net_row(cable_des="W001", net_name="+24V", pin_1="1"),
        make_net_row(cable_des="W001", net_name="gnd", pin_1="2"),
        make_net_row(cable_des="W001", net_name="SomeSignal", pin_1="3"),
    ]
    designator_rows = [make_designator_row()]
    connector_rows = [make_connector_row()]
    cable_rows = [make_cable_row(cable_des="W001", wire_gauge=0.5, length=2000.0)]

    bom = generate_bom_data(net_rows, designator_rows, connector_rows, cable_rows)

    wire_mpns = {b["mpn"] for b in bom if b["unit"] == "Meter"}
    assert "0.5mm2-Red" in wire_mpns
    assert "0.5mm2-Black" in wire_mpns
    assert "0.5mm2-White" in wire_mpns


def test_bom_wire_quantity_calculation():
    """Wire quantity = (length_mm * count) / 1000 -> meters."""
    net_rows = [
        make_net_row(cable_des="W001", net_name="+24V", pin_1="1"),
        make_net_row(cable_des="W001", net_name="+24V_backup", pin_1="2"),
    ]
    designator_rows = [make_designator_row()]
    connector_rows = [make_connector_row()]
    cable_rows = [make_cable_row(cable_des="W001", wire_gauge=0.75, length=3000.0)]

    bom = generate_bom_data(net_rows, designator_rows, connector_rows, cable_rows)

    red_wire = next(b for b in bom if b["mpn"] == "0.75mm2-Red")
    assert red_wire["quantity"] == 6.0
    assert red_wire["unit"] == "Meter"


# --- Cable labels ---

def test_generate_cable_labels_format():
    """Cable labels use '{comp_des}-{conn_des} : {cable_des}' format."""
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", comp_des_2="J2", conn_des_2=""),
    ]
    result = generate_cable_labels(net_rows)

    assert result[0] == {"Label": "Cable Labels:"}

    labels = [r["Label"] for r in result[1:]]
    assert "J1-X1 : W001" in labels
    assert "J2 : W001" in labels


def test_generate_cable_labels_deduplication():
    """Duplicate labels within same cable are not repeated."""
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="2"),
    ]
    result = generate_cable_labels(net_rows)

    labels = [r["Label"] for r in result[1:]]
    assert labels.count("J1-X1 : W001") == 1


# --- Wire labels ---

def test_generate_wire_labels_format():
    """Wire labels have header, cable group headers, and two lines per wire."""
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1",
                     comp_des_2="J2", conn_des_2="", pin_2="5"),
    ]
    result = generate_wire_labels(net_rows)

    labels = [r["Label"] for r in result]
    assert labels[0] == "Wire Labels:"
    assert labels[1] == "Labels: W001"
    assert labels[2] == "X1 : 1"
    assert labels[3] == "J2 : 5"


def test_generate_wire_labels_grouped_by_cable():
    """Wire labels are grouped by cable with sub-headers."""
    net_rows = [
        make_net_row(cable_des="W002", comp_des_1="J3", conn_des_1="", pin_1="1"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1"),
    ]
    result = generate_wire_labels(net_rows)

    labels = [r["Label"] for r in result]
    w1_idx = labels.index("Labels: W001")
    w2_idx = labels.index("Labels: W002")
    assert w1_idx < w2_idx


# --- Empty input ---

def test_process_connectors_empty_input():
    """Empty net_rows with filter_active=True produces no connectors."""
    result = process_connectors([], [], [], set(), filter_active=True)
    assert result == []


def test_process_cables_empty_input():
    """Empty net_rows produces no cables."""
    result = process_cables([], [])
    assert result == []


def test_process_connections_empty_input():
    """Empty net_rows produces no connections."""
    result = process_connections([])
    assert result == []


def test_generate_bom_data_empty_input():
    """Empty net_rows produces empty BOM."""
    result = generate_bom_data([], [], [], [])
    assert result == []


def test_generate_cable_labels_empty_input():
    """Empty net_rows produces only header."""
    result = generate_cable_labels([])
    assert result == [{"Label": "Cable Labels:"}]


def test_generate_wire_labels_empty_input():
    """Empty net_rows produces only header."""
    result = generate_wire_labels([])
    assert result == [{"Label": "Wire Labels:"}]
