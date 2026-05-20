from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.kpi_engine import KPIEngine


class KPIEngineTest(unittest.TestCase):
    def test_compute_procurement_kpi_returns_expected_keys(self) -> None:
        engine = KPIEngine()
        lignes = [
            {
                "CAPEX_LOCAL": 1000,
                "CAPEX_IMPORT": 700,
                "CAPEX_OPTIMISE": 700,
                "IMPORTABILITY_SCORE": 80,
                "PROCUREMENT_SCORE": 75,
            }
        ]
        kpi = engine.compute_procurement_kpi(lignes)

        self.assertIn("CAPEX_BRUT", kpi)
        self.assertIn("CAPEX_DECISION", kpi)
        self.assertIn("POTENTIEL_CACHE", kpi)
        self.assertIn("SCORE_PROCUREMENT", kpi)
        self.assertIsInstance(kpi["DEPENDANCE_IMPORT"], float)


if __name__ == "__main__":
    unittest.main()
