import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import pytest
from models import NetRow, DesignatorRow, ConnectorRow, CableRow


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
