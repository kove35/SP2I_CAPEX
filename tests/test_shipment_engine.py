from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.shipment_engine import ShipmentEngine


class ShipmentEngineTest(unittest.TestCase):
    def test_eta_at_sea(self) -> None:
        result = ShipmentEngine().evaluate({"shipment_status": "AT_SEA"}, 80)

        self.assertEqual(result["shipment_status"], "AT_SEA")
        self.assertEqual(result["eta_days"], 18)
        self.assertIn(result["delay_risk"], {"LOW", "MEDIUM", "HIGH", "CRITICAL"})


if __name__ == "__main__":
    unittest.main()
