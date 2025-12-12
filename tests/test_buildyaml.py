import unittest
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from models import Connector, Cable, Connection
from BuildYaml import connector_to_dict, cable_to_dict, connection_to_list, _clean_dict

class TestBuildYamlHelper(unittest.TestCase):
    
    def test_clean_dict(self):
        dirty = {"a": 1, "b": None, "c": [], "d": {}, "e": {"f": None, "g": 2}}
        cleaned = _clean_dict(dirty)
        expected = {"a": 1, "e": {"g": 2}}
        self.assertEqual(cleaned, expected)

    def test_connector_to_dict(self):
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
        
        self.assertEqual(d['mpn'], "ABC")
        self.assertEqual(d['pincount'], 10)
        self.assertNotIn('show_pincount', d) # Should be removed as it matches default logic? 
        # Wait, my logic was: "show_pincount": c.show_pincount if not c.show_pincount else None
        # So if True (default), it is None, and _clean_dict removes it. Correct.
        
        self.assertEqual(d['notes'], "Test Note")
        self.assertEqual(d['image']['src'], "../img.png")

    def test_cable_to_dict(self):
        c = Cable(
            designator="W1",
            wire_count=3,
            wire_labels=["A", "B", "C"],
            category="bundle",
            gauge=0.5,
            notes="Cable Note"
        )
        d = cable_to_dict(c)
        
        self.assertEqual(d['wirecount'], 3)
        self.assertEqual(d['gauge'], 0.5)
        self.assertEqual(d['wirelabels'], ["A", "B", "C"])

    def test_connection_to_list(self):
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
        
        # Expecting [{From}, {Via}, {To}]
        self.assertEqual(len(l), 3)
        self.assertEqual(l[0], {"J1": "1"})
        self.assertEqual(l[1], {"W1": 1})
        self.assertEqual(l[2], {"J2": "2"})

if __name__ == '__main__':
    unittest.main()
