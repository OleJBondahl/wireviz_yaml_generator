import sys
import os
from typing import Optional
import pytest

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from models import NetRow, DesignatorRow, ConnectorRow, CableRow
from transformations import process_connectors, process_cables, process_connections, generate_bom_data

# --- Test Factories (Robustness) ---
def make_net_row(
    cable_des="W1", comp_des_1="J1", conn_des_1="X1", pin_1="1",
    comp_des_2="J2", conn_des_2="", pin_2="1", net_name="Signal"
) -> NetRow:
    return NetRow(
        cable_des=cable_des,
        comp_des_1=comp_des_1, conn_des_1=conn_des_1, pin_1=pin_1,
        comp_des_2=comp_des_2, conn_des_2=conn_des_2, pin_2=pin_2,
        net_name=net_name
    )

def make_designator_row(comp_des="J1", conn_des="X1", conn_mpn="MPN-123") -> DesignatorRow:
    return DesignatorRow(comp_des=comp_des, conn_des=conn_des, conn_mpn=conn_mpn)

def make_connector_row(
    mpn="MPN-123", pincount=10, 
    mate_mpn="MATE-123", pin_mpn="PIN-001", 
    description="Desc", manufacturer="Mfg"
) -> ConnectorRow:
    return ConnectorRow(
        mpn=mpn, pincount=pincount, 
        mate_mpn=mate_mpn, pin_mpn=pin_mpn, 
        description=description, manufacturer=manufacturer
    )

def make_cable_row(cable_des="W1", wire_gauge=0.5, length=1000.0, note="Note") -> CableRow:
    return CableRow(cable_des=cable_des, wire_gauge=wire_gauge, length=length, note=note)


@pytest.fixture
def sample_data():
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
        make_cable_row(cable_des="W1")
    ]
    return {
        "net_rows": net_rows,
        "designator_rows": designator_rows,
        "connector_rows": connector_rows,
        "cable_rows": cable_rows
    }

def test_process_connectors(sample_data):
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
    result = process_cables(sample_data["net_rows"], sample_data["cable_rows"])
    
    assert len(result) == 1
    cable = result[0]
    assert cable.designator == "W1"
    assert cable.wire_count == 2
    # Verify set contains expected labels
    assert "SignalA" in cable.wire_labels
    assert "+24V" in cable.wire_labels

def test_process_connections(sample_data):
    result = process_connections(sample_data["net_rows"])
    assert len(result) == 2
    conn1 = result[0]
    assert conn1.from_pin == "1"

def test_generate_bom_data(sample_data):
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
