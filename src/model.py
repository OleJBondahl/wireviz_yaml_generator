

#Dataclasses containing the main objects in wireviz yaml file:
#Connectors, cables, connections, options, image

from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any



# Each type alias have their legal values described in comments - validation might be implemented in the future
PlainText = str  # Text not containing HTML tags nor newlines
Hypertext = str  # Text possibly including HTML hyperlinks that are removed in all outputs except HTML output
MultilineHypertext = (
    str  # Hypertext possibly also including newlines to break lines in diagram output
)

Designator = PlainText  # Case insensitive unique name of connector or cable
Pin = Union[int, PlainText]  # Pin identifier
Wire = Union[int, PlainText]  # Wire number or Literal['s'] for shield

@dataclass
class Image:
    # Attributes of the image object <img>:
    src: str
    caption: Optional[MultilineHypertext] = None
    width: Optional[int] = None


@dataclass(frozen=True)
class Connector:
  name: Designator
  #pincount: Optional[int] = None
  pincount: int
  mpn: Optional[MultilineHypertext] = None
  pins: List[Pin] = field(default_factory=list)
  image: Optional[Image] = None
  show_pincount: Optional[bool] = None
  hide_disconnected_pins: bool = False
  notes: Optional[MultilineHypertext] = None



@dataclass
class Cable:
  name: Designator
  category: Optional[str] = "bundle"
  wirecount: Optional[int] = None
  wirelabels: List[Wire] = field(default_factory=list)
  gauge: Optional[float] = None
  gauge_unit: Optional[str] = "mm2"
  length: float = 0
  length_unit: Optional[str] = "mm"
  ignore_in_bom: bool = False
  notes: Optional[MultilineHypertext] = None


@dataclass
class Connection:
    # En liste av dictionaries som representerer hele tilkoblingsstien.
    nodes: List[Dict[Designator, Pin]]