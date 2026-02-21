"""
Domain Models for the WireViz YAML Generator.

This module defines the immutable data structures (Functional Models) used throughout
the application. These models act as the contract between the Data Access Layer,
the Transformation Layer, and the Output Layer.

Design Philosophy:
- Data-Oriented: These classes are pure data carriers.
- Immutability: All classes are frozen dataclasses to prevent accidental mutation.
- Type Safety: All fields are typed, ensuring robustness.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class Connector:
    """
    Represents a physical connector in the design.
    
    Attributes:
        designator: The schematic designator (e.g., "X1" or "J1-X1").
        mpn: Manufacturer Part Number.
        pincount: Number of pins.
        description: Description of the part.
        manufacturer: Manufacturer name.
        image_src: Relative path to an image file (for WireViz).
        image_caption: Caption for the image.
        hide_disconnected_pins: WireViz flag to hide unused pins.
        show_pincount: WireViz flag to show/hide pin count.
        notes: Additional notes or warnings.
    """
    designator: str
    mpn: Optional[str] = None
    pincount: Optional[int] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    image_src: Optional[str] = None
    image_caption: Optional[str] = None
    hide_disconnected_pins: bool = False
    show_pincount: bool = True
    notes: Optional[str] = None

@dataclass(frozen=True)
class Wire:
    """
    Represents the physical properties of a single wire strand.
    """
    gauge: Optional[float]
    gauge_unit: str = "mm2"
    color: Optional[str] = None
    description: str = "Radox 125"
    manufacturer: str = ""

@dataclass(frozen=True)
class Cable:
    """
    Represents a cable bundle containing multiple wires.
    
    Attributes:
        designator: Cable designator (e.g., "W1").
        wire_count: Total number of wires in the cable.
        wire_labels: List of signal names carried by the cable.
        category: WireViz category (e.g., "bundle").
        length: Physical length of the cable.
        length_unit: Unit of measurement for length (default: "mm").
        gauge: Aggregate gauge or gauge of wires.
        gauge_unit: Unit for gauge (default: "mm2").
        notes: Physical notes or construction instructions.
    """
    designator: str
    wire_count: int
    wire_labels: List[str]
    category: str = "bundle"
    length: Optional[float] = None
    length_unit: str = "mm"
    gauge: Optional[float] = None
    gauge_unit: str = "mm2"
    notes: Optional[str] = None

@dataclass(frozen=True)
class Connection:
    """
    Represents a point-to-point electrical connection.
    
    Attributes:
        from_designator: Starting component/connector designator.
        from_pin: Pin number at start.
        to_designator: Ending component/connector designator.
        to_pin: Pin number at end.
        via_cable: The cable carrier used for this connection.
        via_pin: The wire number/color/position within the cable.
        net_name: The electrical signal name.
    """
    from_designator: str
    from_pin: str
    to_designator: str
    to_pin: str
    via_cable: str
    via_pin: int
    net_name: str

@dataclass(frozen=True)
class BomItem:
    """
    Represents a Bill of Materials line item.
    """
    mpn: str
    description: str
    manufacturer: str
    quantity: float
    unit: str

# --- Raw Database Row Models (Intermediate) ---
# These mirror the exact schema of the SQLite tables.

@dataclass(frozen=True)
class NetRow:
    """Raw row from NetTable."""
    cable_des: str
    comp_des_1: str
    conn_des_1: str
    pin_1: str
    comp_des_2: str
    conn_des_2: str
    pin_2: str
    net_name: str

@dataclass(frozen=True)
class DesignatorRow:
    """Raw row from DesignatorTable."""
    comp_des: str
    conn_des: str
    conn_mpn: str

@dataclass(frozen=True)
class ConnectorRow:
    """Raw row from ConnectorTable."""
    mpn: str
    pincount: int
    mate_mpn: str
    pin_mpn: str
    description: str = ""
    manufacturer: str = ""

@dataclass(frozen=True)
class CableRow:
    """Raw row from CableTable."""
    cable_des: str
    wire_gauge: float
    length: float
    note: str
