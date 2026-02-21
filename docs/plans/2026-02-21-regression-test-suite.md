# Regression Test Suite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a comprehensive regression test suite that locks down all core business logic so no transformation, YAML generation, or orchestration behavior can change without tests failing.

**Architecture:** Three test files covering the pure transformation layer, the YAML output layer, and the WorkflowManager orchestration layer. Shared test factories live in `tests/conftest.py`. No source code changes — tests only.

**Tech Stack:** pytest, pytest-cov, unittest.mock (for WorkflowManager), PyYAML (for YAML round-trip), tmp_path (for file I/O tests)

---

### Task 1: Create shared test factories in conftest.py

**Files:**
- Create: `tests/conftest.py`
- Modify: `tests/test_transformations.py` (remove duplicated factories)
- Modify: `tests/test_buildyaml.py` (add sys.path via conftest)

**Step 1: Create `tests/conftest.py` with shared factories and path setup**

```python
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import pytest
from models import NetRow, DesignatorRow, ConnectorRow, CableRow


# --- Test Factories ---

def make_net_row(
    cable_des="W001",
    comp_des_1="J1",
    conn_des_1="X1",
    pin_1="1",
    comp_des_2="J2",
    conn_des_2="",
    pin_2="1",
    net_name="Signal",
) -> NetRow:
    return NetRow(
        cable_des=cable_des,
        comp_des_1=comp_des_1,
        conn_des_1=conn_des_1,
        pin_1=pin_1,
        comp_des_2=comp_des_2,
        conn_des_2=conn_des_2,
        pin_2=pin_2,
        net_name=net_name,
    )


def make_designator_row(
    comp_des="J1", conn_des="X1", conn_mpn="MPN-123"
) -> DesignatorRow:
    return DesignatorRow(comp_des=comp_des, conn_des=conn_des, conn_mpn=conn_mpn)


def make_connector_row(
    mpn="MPN-123",
    pincount=10,
    mate_mpn="MATE-123",
    pin_mpn="PIN-001",
    description="Desc",
    manufacturer="Mfg",
) -> ConnectorRow:
    return ConnectorRow(
        mpn=mpn,
        pincount=pincount,
        mate_mpn=mate_mpn,
        pin_mpn=pin_mpn,
        description=description,
        manufacturer=manufacturer,
    )


def make_cable_row(
    cable_des="W001", wire_gauge=0.5, length=1000.0, note="Note"
) -> CableRow:
    return CableRow(
        cable_des=cable_des, wire_gauge=wire_gauge, length=length, note=note
    )
```

**Step 2: Update `tests/test_transformations.py` — remove local factories and sys.path, import from conftest**

Remove lines 1-61 (the docstring, imports, sys.path, and factory functions). Replace with:

```python
"""Unit Tests for Transformations Module."""

import pytest
from conftest import make_net_row, make_designator_row, make_connector_row, make_cable_row
from models import NetRow, DesignatorRow, ConnectorRow, CableRow
from transformations import (
    process_connectors,
    process_cables,
    process_connections,
    generate_bom_data,
    generate_cable_labels,
    generate_wire_labels,
)
```

Also update the `sample_data` fixture to use `cable_des="W001"` (matching conftest defaults) and keep existing tests working.

**Step 3: Update `tests/test_buildyaml.py` — remove sys.path block, rely on conftest**

Remove lines 19-24 (the sys.path and os imports). The conftest.py handles path setup. Keep:

```python
"""Unit Tests for BuildYaml Module."""

import pytest
from models import Connector, Cable, Connection
from BuildYaml import connector_to_dict, cable_to_dict, connection_to_list, _clean_dict
```

**Step 4: Run tests to verify nothing broke**

Run: `pytest tests/ -v`
Expected: All 8 existing tests PASS

**Step 5: Commit**

Message: `"refactor: extract test factories to conftest.py"`

---

### Task 2: Expand `_clean_dict` tests in `test_buildyaml.py`

**Files:**
- Modify: `tests/test_buildyaml.py`

**Step 1: Add tests for edge cases**

Append to `tests/test_buildyaml.py`:

```python
def test_clean_dict_preserves_zero():
    """Zero is a valid value and must not be stripped."""
    assert _clean_dict({"a": 0}) == {"a": 0}


def test_clean_dict_preserves_false():
    """False is a valid value and must not be stripped."""
    assert _clean_dict({"a": False}) == {"a": False}


def test_clean_dict_preserves_empty_string():
    """Empty strings are valid values and must not be stripped."""
    assert _clean_dict({"a": ""}) == {"a": ""}


def test_clean_dict_removes_nested_empty():
    """A dict whose only child is None should be fully removed."""
    assert _clean_dict({"a": {"b": None}}) == {}


def test_clean_dict_removes_nested_empty_list():
    """A dict whose only child is an empty list should be fully removed."""
    assert _clean_dict({"outer": {"inner": []}}) == {}
```

**Step 2: Run tests**

Run: `pytest tests/test_buildyaml.py -v`
Expected: All tests PASS (these test existing behavior, not new code)

**Step 3: Commit**

Message: `"test: add _clean_dict edge case tests for falsy value preservation"`

---

### Task 3: Expand `connector_to_dict` tests

**Files:**
- Modify: `tests/test_buildyaml.py`

**Step 1: Add tests**

```python
def test_connector_to_dict_show_pincount_false():
    """show_pincount=False must appear in output (inverted inclusion logic)."""
    c = Connector(designator="J1", pincount=4, show_pincount=False)
    d = connector_to_dict(c)
    assert d["show_pincount"] == False


def test_connector_to_dict_hide_disconnected_true():
    """hide_disconnected_pins=True must appear in output."""
    c = Connector(designator="J1", pincount=4, hide_disconnected_pins=True)
    d = connector_to_dict(c)
    assert d["hide_disconnected_pins"] == True


def test_connector_to_dict_no_image():
    """Connector without image_src must not have 'image' key."""
    c = Connector(designator="J1", mpn="ABC", pincount=10)
    d = connector_to_dict(c)
    assert "image" not in d


def test_connector_to_dict_minimal():
    """Connector with only designator produces minimal output."""
    c = Connector(designator="J1")
    d = connector_to_dict(c)
    # Only non-None, non-empty, non-default values remain
    assert "mpn" not in d
    assert "notes" not in d
    assert "image" not in d
```

**Step 2: Run tests**

Run: `pytest tests/test_buildyaml.py -v`
Expected: All PASS

**Step 3: Commit**

Message: `"test: add connector_to_dict tests for flag inclusion and minimal output"`

---

### Task 4: Expand `cable_to_dict` tests

**Files:**
- Modify: `tests/test_buildyaml.py`

**Step 1: Add tests**

```python
def test_cable_to_dict_wireviz_key_names():
    """Verify WireViz uses 'wirecount' and 'wirelabels', not Python field names."""
    c = Cable(designator="W1", wire_count=2, wire_labels=["A", "B"])
    d = cable_to_dict(c)
    assert "wirecount" in d
    assert "wirelabels" in d
    assert "wire_count" not in d
    assert "wire_labels" not in d


def test_cable_to_dict_no_optional_fields():
    """Cable without gauge/notes should not have those keys."""
    c = Cable(designator="W1", wire_count=1, wire_labels=["Sig"])
    d = cable_to_dict(c)
    assert "gauge" not in d
    assert "notes" not in d
    assert d["wirecount"] == 1
```

**Step 2: Run tests**

Run: `pytest tests/test_buildyaml.py -v`
Expected: All PASS

**Step 3: Commit**

Message: `"test: add cable_to_dict tests for WireViz key names and optional fields"`

---

### Task 5: Add `connection_to_list` type verification test

**Files:**
- Modify: `tests/test_buildyaml.py`

**Step 1: Add test**

```python
def test_connection_to_list_pin_types():
    """Connector pins must be str, cable via_pin must be int."""
    c = Connection(
        from_designator="J1", from_pin="3",
        to_designator="J2", to_pin="4",
        via_cable="W1", via_pin=2, net_name="Net"
    )
    result = connection_to_list(c)
    # Connector pins are strings
    assert isinstance(result[0]["J1"], str)
    assert isinstance(result[2]["J2"], str)
    # Cable pin is int
    assert isinstance(result[1]["W1"], int)
```

**Step 2: Run tests**

Run: `pytest tests/test_buildyaml.py -v`
Expected: All PASS

**Step 3: Commit**

Message: `"test: add connection_to_list pin type verification"`

---

### Task 6: Add `build_yaml_file` round-trip test

**Files:**
- Modify: `tests/test_buildyaml.py`

**Step 1: Add import for yaml and build_yaml_file at top of file**

Add to imports:

```python
import yaml
from BuildYaml import connector_to_dict, cable_to_dict, connection_to_list, _clean_dict, build_yaml_file
```

**Step 2: Add test**

```python
def test_build_yaml_file_round_trip(tmp_path):
    """YAML file written by build_yaml_file must be parseable and have correct structure."""
    connectors = [
        Connector(designator="J1-X1", mpn="MATE-A", pincount=4),
        Connector(designator="J2", mpn="MATE-B", pincount=2),
    ]
    cables = [
        Cable(designator="W001", wire_count=2, wire_labels=["Sig1", "Sig2"], gauge=0.5),
    ]
    connections = [
        Connection(from_designator="J1-X1", from_pin="1", to_designator="J2", to_pin="1", via_cable="W001", via_pin=1, net_name="Sig1"),
        Connection(from_designator="J1-X1", from_pin="2", to_designator="J2", to_pin="2", via_cable="W001", via_pin=2, net_name="Sig2"),
    ]

    yaml_path = str(tmp_path / "test.yaml")
    build_yaml_file(connectors, cables, connections, yaml_path)

    with open(yaml_path, encoding="utf-8") as f:
        content = f.read()

    # Header comment present
    assert content.startswith("# WireViz YAML file")

    # Parse YAML
    data = yaml.safe_load(content)

    # Top-level keys
    assert "connectors" in data
    assert "cables" in data
    assert "connections" in data

    # Connectors keyed by designator
    assert "J1-X1" in data["connectors"]
    assert "J2" in data["connectors"]
    assert data["connectors"]["J1-X1"]["mpn"] == "MATE-A"

    # Cable keyed by designator
    assert "W001" in data["cables"]
    assert data["cables"]["W001"]["wirecount"] == 2

    # Connections is a list of 3-element lists
    assert len(data["connections"]) == 2
    assert len(data["connections"][0]) == 3
```

**Step 3: Run tests**

Run: `pytest tests/test_buildyaml.py::test_build_yaml_file_round_trip -v`
Expected: PASS

**Step 4: Commit**

Message: `"test: add build_yaml_file round-trip test with YAML parse verification"`

---

### Task 7: Add critical ordering invariant test

This is the most important test in the entire suite.

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
def test_cable_connection_ordering_invariant():
    """CRITICAL: wire_labels[i] in Cable must correspond to via_pin=i+1 in Connection.

    process_cables and process_connections must use the same sort key.
    If this test fails, wiring diagrams will have labels on wrong wires.
    """
    # Deliberately unsorted input to stress the sort
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J2", conn_des_1="X2", pin_1="3", net_name="GND"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1", net_name="+24V"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="2", net_name="Signal"),
    ]
    cable_rows = [make_cable_row(cable_des="W001")]

    cables = process_cables(net_rows, cable_rows)
    connections = process_connections(net_rows)

    cable = cables[0]
    # For each connection, the wire label at position (via_pin - 1) must match the net_name
    for conn in connections:
        assert cable.wire_labels[conn.via_pin - 1] == conn.net_name, (
            f"Wire label mismatch: wire_labels[{conn.via_pin - 1}]={cable.wire_labels[conn.via_pin - 1]!r} "
            f"but connection net_name={conn.net_name!r}"
        )
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_cable_connection_ordering_invariant -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add critical cable/connection ordering invariant test"`

---

### Task 8: Add multi-cable ordering invariant test

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
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
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_cable_connection_ordering_multi_cable -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add multi-cable ordering invariant test"`

---

### Task 9: Add wire ferrule special case test

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
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
    assert c.mpn is None  # MPN cleared for ferrules
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_process_connectors_wire_ferrule -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add wire ferrule special case test"`

---

### Task 10: Add MPN-not-found test

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
def test_process_connectors_mpn_not_found():
    """Missing MPN in ConnectorTable sets mpn='NotFound' and hide_disconnected=True."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="X1")]
    designator_rows = [make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MISSING")]
    connector_rows = []  # Empty catalog

    result = process_connectors(net_rows, designator_rows, connector_rows, set(), filter_active=True)

    c = result[0]
    assert c.mpn == "NotFound"
    assert c.hide_disconnected_pins is True
    assert c.pincount == 99  # default pincount
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_process_connectors_mpn_not_found -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add MPN-not-found fallback test"`

---

### Task 11: Add filter_active=False test

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
def test_process_connectors_filter_active_false():
    """filter_active=False returns ALL designators, not just those in net_rows."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="X1")]
    designator_rows = [
        make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-123"),
        make_designator_row(comp_des="J99", conn_des="X99", conn_mpn="MPN-123"),  # not in net_rows
    ]
    connector_rows = [make_connector_row(mpn="MPN-123")]

    result = process_connectors(net_rows, designator_rows, connector_rows, set(), filter_active=False)

    designators = [c.designator for c in result]
    assert "J1-X1" in designators
    assert "J99-X99" in designators
    assert len(result) == 2
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_process_connectors_filter_active_false -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add filter_active=False connector test"`

---

### Task 12: Add natural sort order test

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
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
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_process_connectors_natural_sort_order -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add natural sort order test for connectors"`

---

### Task 13: Add designator format tests

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
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
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py -k "designator_format" -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add designator format tests for with/without conn_des"`

---

### Task 14: Add cable gauge/notes lookup test

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
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
    cable_rows = []  # No matching cable

    result = process_cables(net_rows, cable_rows)
    assert result[0].gauge is None
    assert result[0].notes is None
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py -k "cables_gauge" -v`
Expected: PASS (both tests)

**Step 3: Commit**

Message: `"test: add cable gauge/notes lookup tests"`

---

### Task 15: Add wire color classification tests

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
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
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_bom_wire_color_classification -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add wire color classification test (24V/gnd/other)"`

---

### Task 16: Add BOM wire quantity calculation test

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
def test_bom_wire_quantity_calculation():
    """Wire quantity = (length_mm * count) / 1000 -> meters."""
    net_rows = [
        make_net_row(cable_des="W001", net_name="+24V", pin_1="1"),
        make_net_row(cable_des="W001", net_name="+24V_backup", pin_1="2"),  # also has 24V -> Red
    ]
    designator_rows = [make_designator_row()]
    connector_rows = [make_connector_row()]
    cable_rows = [make_cable_row(cable_des="W001", wire_gauge=0.75, length=3000.0)]

    bom = generate_bom_data(net_rows, designator_rows, connector_rows, cable_rows)

    red_wire = next(b for b in bom if b["mpn"] == "0.75mm2-Red")
    # 2 red wires * 3000mm / 1000 = 6.0 meters
    assert red_wire["quantity"] == 6.0
    assert red_wire["unit"] == "Meter"
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_bom_wire_quantity_calculation -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add BOM wire quantity calculation test"`

---

### Task 17: Add cable label tests

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
def test_generate_cable_labels_format():
    """Cable labels use '{comp_des}-{conn_des} : {cable_des}' format."""
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", comp_des_2="J2", conn_des_2=""),
    ]
    result = generate_cable_labels(net_rows)

    # First entry is always the header
    assert result[0] == {"Label": "Cable Labels:"}

    labels = [r["Label"] for r in result[1:]]
    assert "J1-X1 : W001" in labels
    assert "J2 : W001" in labels  # no conn_des -> just comp_des


def test_generate_cable_labels_deduplication():
    """Duplicate labels within same cable are not repeated."""
    net_rows = [
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="2"),  # same connector, different pin
    ]
    result = generate_cable_labels(net_rows)

    labels = [r["Label"] for r in result[1:]]
    # J1-X1 : W001 should appear only once despite two net rows
    assert labels.count("J1-X1 : W001") == 1
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py -k "cable_labels" -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add cable label format and deduplication tests"`

---

### Task 18: Add wire label tests

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
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
    # Side 1: conn_des_1 is used when non-empty
    assert labels[2] == "X1 : 1"
    # Side 2: comp_des_2 is used when conn_des_2 is empty
    assert labels[3] == "J2 : 5"


def test_generate_wire_labels_grouped_by_cable():
    """Wire labels are grouped by cable with sub-headers."""
    net_rows = [
        make_net_row(cable_des="W002", comp_des_1="J3", conn_des_1="", pin_1="1"),
        make_net_row(cable_des="W001", comp_des_1="J1", conn_des_1="X1", pin_1="1"),
    ]
    result = generate_wire_labels(net_rows)

    labels = [r["Label"] for r in result]
    # Should be sorted: W001 before W002
    w1_idx = labels.index("Labels: W001")
    w2_idx = labels.index("Labels: W002")
    assert w1_idx < w2_idx
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py -k "wire_labels" -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add wire label format and grouping tests"`

---

### Task 19: Add empty input tests

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add tests**

```python
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
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py -k "empty_input" -v`
Expected: All 6 PASS

**Step 3: Commit**

Message: `"test: add empty input tests for all transformation functions"`

---

### Task 20: Add image resolution test

**Files:**
- Modify: `tests/test_transformations.py`

**Step 1: Add test**

```python
def test_process_connectors_image_resolution():
    """Image is set when '{mate_mpn}.png' is in available_images."""
    net_rows = [make_net_row(comp_des_1="J1", conn_des_1="X1")]
    designator_rows = [make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-123")]
    connector_rows = [make_connector_row(mpn="MPN-123", mate_mpn="MATE-IMG")]

    # With image available
    result_with = process_connectors(
        net_rows, designator_rows, connector_rows, {"MATE-IMG.png"}, filter_active=True
    )
    assert result_with[0].image_src == "../resources/MATE-IMG.png"
    assert result_with[0].image_caption == "ISO view"

    # Without image available
    result_without = process_connectors(
        net_rows, designator_rows, connector_rows, set(), filter_active=True
    )
    assert result_without[0].image_src is None
    assert result_without[0].image_caption is None
```

**Step 2: Run test**

Run: `pytest tests/test_transformations.py::test_process_connectors_image_resolution -v`
Expected: PASS

**Step 3: Commit**

Message: `"test: add image resolution test for process_connectors"`

---

### Task 21: Create WorkflowManager test file

**Files:**
- Create: `tests/test_workflow_manager.py`

**Step 1: Create test file with mocked DataSource and YAML workflow test**

```python
"""Unit Tests for WorkflowManager orchestration."""

import yaml
from unittest.mock import MagicMock
from conftest import make_net_row, make_designator_row, make_connector_row, make_cable_row
from workflow_manager import WorkflowManager


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

    # Verify file was written and is valid YAML
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f.read())

    assert "connectors" in data
    assert "cables" in data
    assert "connections" in data
    assert "J1-X1" in data["connectors"]
    assert "W001" in data["cables"]


def test_run_yaml_workflow_calls_data_source():
    """run_yaml_workflow calls all four data source methods."""
    source = _build_mock_source(
        [make_net_row()],
        [make_designator_row()],
        [make_connector_row()],
        [make_cable_row()],
    )
    wm = WorkflowManager(source)

    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        yaml_path = os.path.join(td, "test.yaml")
        wm.run_yaml_workflow("W001", yaml_path, set())

    source.load_net_table.assert_called_once_with("W001")
    source.load_designator_table.assert_called_once()
    source.load_connector_table.assert_called_once()
    source.load_cable_table.assert_called_once()
```

**Step 2: Run tests**

Run: `pytest tests/test_workflow_manager.py -v`
Expected: All PASS

**Step 3: Commit**

Message: `"test: add WorkflowManager yaml workflow tests with mocked DataSource"`

---

### Task 22: Add WorkflowManager attachment workflow tests

**Files:**
- Modify: `tests/test_workflow_manager.py`

**Step 1: Add tests**

```python
import os


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
    # Only request W001
    wm.run_attachment_workflow(["W001"], output, create_bom=False, create_labels=True)

    # Labels should only contain W001 references
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(output, "WireLabels.xlsx"))
    ws = wb.active
    all_text = " ".join(str(cell.value) for row in ws.iter_rows() for cell in row if cell.value)
    assert "W001" in all_text
    assert "W002" not in all_text
```

**Step 2: Run tests**

Run: `pytest tests/test_workflow_manager.py -v`
Expected: All PASS

**Step 3: Commit**

Message: `"test: add WorkflowManager attachment workflow tests"`

---

### Task 23: Run full test suite and verify coverage

**Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS (~35+ tests)

**Step 2: Run with coverage**

Run: `pytest tests/ --cov=src --cov-report=term-missing -v`
Review output to confirm high coverage on transformations.py and BuildYaml.py.

**Step 3: Final commit**

Message: `"test: complete regression test suite for core functionality"`

---

## Summary

| File | Tests Added | What It Locks Down |
|---|---|---|
| `tests/conftest.py` | Shared factories | DRY test data creation |
| `tests/test_buildyaml.py` | ~10 new tests | _clean_dict edge cases, connector/cable/connection dict conversion, YAML round-trip |
| `tests/test_transformations.py` | ~18 new tests | Ordering invariant, wire ferrule, MPN-not-found, filter_active, natural sort, designator format, gauge lookup, wire colors, BOM quantity math, labels, empty inputs |
| `tests/test_workflow_manager.py` | ~5 new tests | YAML workflow integration, attachment workflow files, cable filtering |

Total: ~33 new tests + 8 existing = ~41 tests covering all core behavior.
