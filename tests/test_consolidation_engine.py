from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.consolidation_engine import ConsolidationEngine


class ConsolidationEngineTest(unittest.TestCase):
    def test_groupage_si_meme_port_et_disponible(self) -> None:
        result = ConsolidationEngine().evaluate(
            [
                {"supplier_city": "Shanghai", "supplier_availability_days": 5},
                {"supplier_city": "Shanghai", "supplier_availability_days": 7},
            ]
        )

        self.assertEqual(result["strategy"], "GROUPED_SHIPMENT")

    def test_separe_si_chantier_critique(self) -> None:
        result = ConsolidationEngine().evaluate(
            [
                {"supplier_city": "Shanghai", "project_criticality": "CRITICAL"},
                {"supplier_city": "Ningbo", "supplier_availability_days": 30},
            ]
        )

        self.assertEqual(result["strategy"], "SEPARATE_SHIPMENT")


if __name__ == "__main__":
    unittest.main()
