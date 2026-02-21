"""Unit Tests for BuildYaml Module."""

import pytest
import yaml
from wireviz_yaml_generator.models import Connector, Cable, Connection
from wireviz_yaml_generator.BuildYaml import connector_to_dict, cable_to_dict, connection_to_list, _clean_dict, build_yaml_file

def test_clean_dict():
    """Test that None values and empty containers are removed from dictionaries."""
    dirty = {"a": 1, "b": None, "c": [], "d": {}, "e": {"f": None, "g": 2}}
    cleaned = _clean_dict(dirty)
    expected = {"a": 1, "e": {"g": 2}}
    assert cleaned == expected

def test_connector_to_dict():
    """Test conversion of Connector domain object to WireViz dictionary format."""
    c = Connector(
        designator="J1",
        mpn="ABC",
        pincount=10,
        show_pincount=True,
        hide_disconnected_pins=False,
        notes="Test Note",
        image_src="../img.png",
        image_caption="Image"
    )
    d = connector_to_dict(c)
    
    assert d['mpn'] == "ABC"
    assert d['pincount'] == 10
    assert 'show_pincount' not in d
    
    assert d['notes'] == "Test Note"
    assert d['image']['src'] == "../img.png"

def test_cable_to_dict():
    """Test conversion of Cable domain object to WireViz dictionary format."""
    c = Cable(
        designator="W1",
        wire_count=3,
        wire_labels=["A", "B", "C"],
        category="bundle",
        gauge=0.5,
        notes="Cable Note"
    )
    d = cable_to_dict(c)
    
    assert d['wirecount'] == 3
    assert d['gauge'] == 0.5
    assert d['wirelabels'] == ["A", "B", "C"]

def test_connection_to_list():
    """Test conversion of Connection domain object to WireViz connection list format."""
    c = Connection(
        from_designator="J1",
        from_pin="1",
        to_designator="J2",
        to_pin="2",
        via_cable="W1",
        via_pin=1,
        net_name="Net1"
    )
    l = connection_to_list(c)
    
    assert len(l) == 3
    assert l[0] == {"J1": "1"}
    assert l[1] == {"W1": 1}
    assert l[2] == {"J2": "2"}


# --- _clean_dict edge cases ---

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


# --- connector_to_dict edge cases ---

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
    assert "mpn" not in d
    assert "notes" not in d
    assert "image" not in d


# --- cable_to_dict edge cases ---

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


# --- connection_to_list type verification ---

def test_connection_to_list_pin_types():
    """Connector pins must be str, cable via_pin must be int."""
    c = Connection(
        from_designator="J1", from_pin="3",
        to_designator="J2", to_pin="4",
        via_cable="W1", via_pin=2, net_name="Net"
    )
    result = connection_to_list(c)
    assert isinstance(result[0]["J1"], str)
    assert isinstance(result[2]["J2"], str)
    assert isinstance(result[1]["W1"], int)


# --- build_yaml_file round-trip ---

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
        Connection(from_designator="J1-X1", from_pin="1", to_designator="J2", to_pin="1",
                   via_cable="W001", via_pin=1, net_name="Sig1"),
        Connection(from_designator="J1-X1", from_pin="2", to_designator="J2", to_pin="2",
                   via_cable="W001", via_pin=2, net_name="Sig2"),
    ]

    yaml_path = str(tmp_path / "test.yaml")
    build_yaml_file(connectors, cables, connections, yaml_path)

    with open(yaml_path, encoding="utf-8") as f:
        content = f.read()

    assert content.startswith("# WireViz YAML file")

    data = yaml.safe_load(content)

    assert "connectors" in data
    assert "cables" in data
    assert "connections" in data

    assert "J1-X1" in data["connectors"]
    assert "J2" in data["connectors"]
    assert data["connectors"]["J1-X1"]["mpn"] == "MATE-A"

    assert "W001" in data["cables"]
    assert data["cables"]["W001"]["wirecount"] == 2

    assert len(data["connections"]) == 2
    assert len(data["connections"][0]) == 3
