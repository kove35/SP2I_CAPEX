from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.capex_taxonomy_engine import CAPEXTaxonomyEngine


class CAPEXTaxonomyEngineTest(unittest.TestCase):
    def test_classifies_generator_60_kva(self) -> None:
        result = CAPEXTaxonomyEngine().classify("Groupe electrogene insonorise 60 KVA")

        self.assertEqual(result["family"], "ELECTRICITE")
        self.assertEqual(result["subcategory"], "GENERATEUR")
        self.assertEqual(result["equipment_type"], "GENERATOR_60_KVA")
        self.assertEqual(result["equipment_class"], "INDUSTRIEL_LOURD")
        self.assertEqual(result["power_kva"], 60)

    def test_covers_enterprise_families(self) -> None:
        families = CAPEXTaxonomyEngine().list_families()

        self.assertGreaterEqual(len(families), 20)
        self.assertIn("EQUIPEMENTS_MEDICAUX", families)
        self.assertIn("HVAC", families)


if __name__ == "__main__":
    unittest.main()
