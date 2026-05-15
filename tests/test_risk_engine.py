from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.risk_engine import RiskEngine


class RiskEngineTest(unittest.TestCase):
    def test_risque_eleve_sur_fournisseur_et_chantier_critique(self) -> None:
        result = RiskEngine().evaluate(
            {
                "reliability_score": 30,
                "quality_score": 45,
                "customs_risk": 70,
                "port_risk": 75,
                "project_criticality": "CRITICAL",
                "lead_time_days": 90,
            }
        )

        self.assertIn(result["risk_level"], {"HIGH", "CRITICAL"})
        self.assertGreater(result["global_risk_score"], 60)


if __name__ == "__main__":
    unittest.main()
