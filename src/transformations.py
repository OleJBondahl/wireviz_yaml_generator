"""
Transformation Logic Layer.

This module contains **Pure Functions** that transform Domain Models.
It includes no I/O operations (no database access, no file writing).
"""

from typing import List, Dict, Any, Set, Optional
import re
from models import (
    NetRow,
    DesignatorRow,
    ConnectorRow,
    CableRow,
    Connector,
    Cable,
    Connection,
)


def _natural_sort_key(s: str | None) -> List[Any]:
    """Helper for 'human' sorting."""
    if s is None:
        return []
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split("([0-9]+)", str(s))
    ]


def process_connectors(
    net_rows: List[NetRow],
    designator_rows: List[DesignatorRow],
    connector_rows: List[ConnectorRow],
    available_images: Set[str],
    filter_active: bool,
) -> List[Connector]:
    """
    Transforms raw DB rows into Connector domain objects.

    Args:
        net_rows: Active connections.
        designator_rows: Map of Component+Pin -> MPN.
        connector_rows: Catalog of MPN metadata.
        available_images: Set of filenames (e.g. {'connector_a.png'}) present in resources.
        filter_active: If True, only returns connectors present in `net_rows`.
    """

    # 1. Filter Designators if needed
    required_connectors: Set[str] = set()
    filtered_designators = designator_rows

    if filter_active:
        for row in net_rows:
            required_connectors.add(f"{row.comp_des_1}-{row.conn_des_1}")
            required_connectors.add(f"{row.comp_des_2}-{row.conn_des_2}")

        filtered_designators = [
            row
            for row in designator_rows
            if f"{row.comp_des}-{row.conn_des}" in required_connectors
        ]

    # 2. Sort naturally
    filtered_designators.sort(
        key=lambda x: (_natural_sort_key(x.comp_des), _natural_sort_key(x.conn_des))
    )

    # 3. Enrich with ConnectorTable data
    connector_map = {c.mpn: c for c in connector_rows}
    result_data: List[Connector] = []

    for row in filtered_designators:
        name = (
            f"{row.comp_des}" if not row.conn_des else f"{row.comp_des}-{row.conn_des}"
        )

        # Defaults
        mpn = None
        pincount = 99
        hide_disconnected = False
        show_pincount = True
        notes = None
        image_src = None
        image_caption = None

        conn_mpn = row.conn_mpn

        if conn_mpn and conn_mpn in connector_map:
            mate_info = connector_map[conn_mpn]
            pincount = mate_info.pincount
            mpn = mate_info.mate_mpn

            # Special Logic: Wire Ferrules
            if "Wire Ferrule" in mate_info.pin_mpn:
                notes = "Terminate Wires in Wire Ferrule"
                hide_disconnected = True
                show_pincount = False
                mpn = None

            # Image logic: Checked against passed-in set (Pure)
            image_filename = f"{mate_info.mate_mpn}.png"
            if image_filename in available_images:
                image_src = f"../resources/{image_filename}"
                image_caption = "ISO view"
        else:
            print(
                f"⚠️  Warning: MPN '{conn_mpn}' for connector '{name}' not found in ConnectorTable. Using default values."
            )
            mpn = "NotFound"
            hide_disconnected = True

        result_data.append(
            Connector(
                designator=name,
                mpn=mpn,
                pincount=pincount,
                hide_disconnected_pins=hide_disconnected,
                show_pincount=show_pincount,
                notes=notes,
                image_src=image_src,
                image_caption=image_caption,
            )
        )

    return result_data


def process_cables(net_rows: List[NetRow], cable_rows: List[CableRow]) -> List[Cable]:
    """Aggregates wires into Cables."""
    # CRITICAL: Sort rows in the SAME order as process_connections()
    # This ensures wire_labels[i] corresponds to via_pin = i+1 in connections.
    sorted_rows = sorted(
        net_rows, key=lambda x: (x.cable_des, x.comp_des_1, x.conn_des_1, x.pin_1)
    )

    # 1. Aggregate wires by cable_des (in sorted order)
    aggregated_wires: Dict[str, List[str]] = {}
    for row in sorted_rows:
        if row.cable_des not in aggregated_wires:
            aggregated_wires[row.cable_des] = []
        aggregated_wires[row.cable_des].append(row.net_name)

    # 2. Pre-process Cable Metadata for O(1) lookup
    cable_meta_map = {c.cable_des: c for c in cable_rows}

    cable_data: List[Cable] = []

    for cable_des, wires in aggregated_wires.items():
        gauge = None
        notes = None

        matched_row = cable_meta_map.get(cable_des)
        if matched_row:
            gauge = matched_row.wire_gauge
            notes = matched_row.note

        cable_data.append(
            Cable(
                designator=cable_des,
                wire_count=len(wires),
                wire_labels=wires,
                category="bundle",
                gauge=gauge,
                notes=notes,
                gauge_unit="mm2",
            )
        )

    return cable_data


def process_connections(net_rows: List[NetRow]) -> List[Connection]:
    """Maps net table rows to Connection objects with Via Pin assignment."""
    # 1. Sort to ensure consistent pinout order (Critical for determinism)
    sorted_rows = sorted(
        net_rows, key=lambda x: (x.cable_des, x.comp_des_1, x.conn_des_1, x.pin_1)
    )

    connection_data: List[Connection] = []
    cable_pin_counters: Dict[str, int] = {}

    for row in sorted_rows:
        via_name = row.cable_des
        if via_name not in cable_pin_counters:
            cable_pin_counters[via_name] = 0
        cable_pin_counters[via_name] += 1
        via_pin = cable_pin_counters[via_name]

        connection_data.append(
            Connection(
                from_designator=f"{row.comp_des_1}-{row.conn_des_1}"
                if row.conn_des_1
                else f"{row.comp_des_1}",
                from_pin=row.pin_1,
                to_designator=f"{row.comp_des_2}-{row.conn_des_2}"
                if row.conn_des_2
                else f"{row.comp_des_2}",
                to_pin=row.pin_2,
                via_cable=via_name,
                via_pin=via_pin,
                net_name=row.net_name,
            )
        )

    return connection_data


def generate_bom_data(
    net_rows: List[NetRow],
    designator_rows: List[DesignatorRow],
    connector_rows: List[ConnectorRow],
    cable_rows: List[CableRow],
) -> List[Dict[str, Any]]:
    """Calculates the Bill of Materials (BOM)."""
    bom_data: List[Dict[str, Any]] = []

    # --- Connectors Section ---
    conn_set = set()
    for row in net_rows:
        conn_set.add(f"{row.comp_des_1}-{row.conn_des_1}")
        conn_set.add(f"{row.comp_des_2}-{row.conn_des_2}")

    part_counter: Dict[str, int] = {}
    for row in designator_rows:
        full_des = f"{row.comp_des}-{row.conn_des}"
        if full_des in conn_set:
            part_counter[row.conn_mpn] = part_counter.get(row.conn_mpn, 0) + 1

    for row in connector_rows:
        if row.mpn in part_counter:
            bom_data.append(
                {
                    "mpn": row.mate_mpn,
                    "description": row.description,
                    "manufacturer": row.manufacturer,
                    "quantity": part_counter[row.mpn],
                    "unit": "pcs",
                }
            )

    # --- Wires Section ---
    wire_counter: Dict[str, int] = {}
    for row in net_rows:
        key_suffix = "White"
        if "24V" in row.net_name:
            key_suffix = "Red"
        elif "gnd" in row.net_name:
            key_suffix = "Black"

        key = f"{row.cable_des}{key_suffix}"
        wire_counter[key] = wire_counter.get(key, 0) + 1

    wire_rows: List[Dict[str, Any]] = []
    DESCRIPTION = "Radox 125"
    MANUFACTURER = ""
    UNIT = "Meter"

    for row in cable_rows:
        for color in ["Red", "Black", "White"]:
            cnt = wire_counter.get(f"{row.cable_des}{color}", 0)
            if cnt > 0:
                wire_rows.append(
                    {
                        "mpn": f"{row.wire_gauge}mm2-{color}",
                        "description": DESCRIPTION,
                        "manufacturer": MANUFACTURER,
                        "quantity": (row.length * cnt) / 1000,
                        "unit": UNIT,
                    }
                )

    # Aggregate by MPN
    mpn_quantity: Dict[str, float] = {}
    first_rows: Dict[str, Dict] = {}

    for w in wire_rows:
        mpn_quantity[w["mpn"]] = mpn_quantity.get(w["mpn"], 0) + w["quantity"]
        if w["mpn"] not in first_rows:
            first_rows[w["mpn"]] = w

    for mpn, qty in mpn_quantity.items():
        ref = first_rows[mpn]
        bom_data.append(
            {
                "mpn": mpn,
                "description": ref["description"],
                "manufacturer": ref["manufacturer"],
                "quantity": qty,
                "unit": ref["unit"],
            }
        )

    return bom_data


def generate_cable_labels(net_rows: List[NetRow]) -> List[Dict[str, str]]:
    """Generates cable tags/labels formatted for printing."""
    cable_set = set(r.cable_des for r in net_rows)
    cable_dict: Dict[str, List[str]] = {c: [] for c in cable_set}

    for row in net_rows:
        # Side 1
        c1 = row.conn_des_1
        label_1 = (
            f"{row.comp_des_1}-{c1} : {row.cable_des}"
            if c1
            else f"{row.comp_des_1} : {row.cable_des}"
        )

        # Side 2
        c2 = row.conn_des_2
        label_2 = (
            f"{row.comp_des_2}-{c2} : {row.cable_des}"
            if c2
            else f"{row.comp_des_2} : {row.cable_des}"
        )

        if label_1 not in cable_dict[row.cable_des]:
            cable_dict[row.cable_des].append(label_1)
        if label_2 not in cable_dict[row.cable_des]:
            cable_dict[row.cable_des].append(label_2)

    label_data = ["Cable Labels:"]
    for cable, label_list in cable_dict.items():
        label_data.extend(label_list)

    return [{"Label": l} for l in label_data]


def generate_wire_labels(net_rows: List[NetRow]) -> List[Dict[str, str]]:
    """Generates wire end-point labels formatted for printing."""
    # Sort for grouping by cable
    sorted_rows = sorted(
        net_rows, key=lambda x: (x.cable_des, x.comp_des_1, x.conn_des_1, x.pin_1)
    )

    wire_data = ["Wire Labels:"]
    previous_cable = None

    for row in sorted_rows:
        current_cable = row.cable_des
        if current_cable != previous_cable:
            wire_data.append(f"Labels: {current_cable}")
            previous_cable = current_cable

        # Side 1
        d1 = row.conn_des_1 if row.conn_des_1 else row.comp_des_1
        wire_data.append(f"{d1} : {row.pin_1}")

        # Side 2
        d2 = row.conn_des_2 if row.conn_des_2 else row.comp_des_2
        wire_data.append(f"{d2} : {row.pin_2}")

    return [{"Label": l} for l in wire_data]
