from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.site_logistics_engine import SiteLogisticsEngine


class SiteLogisticsEngineTest(unittest.TestCase):
    def test_saturation_chantier_declenche_risque(self) -> None:
        result = SiteLogisticsEngine().evaluate(
            {"site_storage_capacity_m3": 20, "storage_days": 5},
            {"volume_total": 40},
            {"delay_risk": "LOW"},
        )

        self.assertEqual(result["delivery_risk"], "HIGH")
        self.assertGreater(result["storage_cost"], 0)


if __name__ == "__main__":
    unittest.main()
