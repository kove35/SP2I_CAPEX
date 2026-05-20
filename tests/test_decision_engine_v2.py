from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.decision_engine_v2 import DecisionEngineV2


class DecisionEngineV2Test(unittest.TestCase):
    def test_decision_scenario_is_reported(self) -> None:
        ligne = {
            "CAPEX_LOCAL": 1000,
            "ECONOMIE_NETTE": 200,
            "supplier_risk_score": 20,
            "logistics_risk_score": 20,
            "lead_time_days": 20,
            "project_criticality": "LOW",
            "IMPORTABILITY_SCORE": 80,
            "PROCUREMENT_MATURITY_SCORE": 80,
        }
        decision = DecisionEngineV2({"scenario_type": "AGRESSIF"}).make_decision(ligne)

        self.assertEqual(decision["scenario_type"], "AGRESSIF")
        self.assertIn(decision["decision"], {"IMPORT", "MIXTE", "LOCAL"})
        self.assertGreaterEqual(decision["final_score"], 0)
        self.assertIn("reasoning", decision)

    def test_enrich_line_adds_decision_scenario(self) -> None:
        ligne = {"CAPEX_LOCAL": 1000, "ECONOMIE_NETTE": 150}
        ligne_enrichie = DecisionEngineV2({"scenario_type": "CONSERVATEUR"}).enrich_line(ligne)

        self.assertEqual(ligne_enrichie["DECISION_SCENARIO"], "CONSERVATEUR")
        self.assertIn("FINAL_DECISION_SCORE", ligne_enrichie)


if __name__ == "__main__":
    unittest.main()
