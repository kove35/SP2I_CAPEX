from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.freight_engine import FreightEngine


class FreightEngineTest(unittest.TestCase):
    def test_cout_logistique_total(self) -> None:
        result = FreightEngine().evaluate(
            {"CAPEX_IMPORT": 100000, "storage_days": 5},
            {"container_cost": 12000, "volume_total": 40},
        )

        self.assertEqual(result["freight_cost"], 12000)
        self.assertGreater(result["total_logistics_cost"], 20000)


if __name__ == "__main__":
    unittest.main()
