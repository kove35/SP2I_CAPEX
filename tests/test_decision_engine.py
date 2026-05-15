"""
Tests unitaires du DecisionEngine.

Le DecisionEngine doit rester explicable : chaque decision est justifiee par des
scores visibles et des commentaires lisibles.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.decision_engine import DecisionEngine


class DecisionEngineTest(unittest.TestCase):
    def test_import_si_gain_eleve_et_risque_maitrise(self) -> None:
        decision = DecisionEngine().make_decision(
            {
                "CAPEX_LOCAL": 1000,
                "ECONOMIE_NETTE": 250,
                "supplier_risk_score": 10,
                "logistics_risk_score": 15,
                "lead_time_days": 10,
                "project_criticality": "LOW",
            }
        )

        self.assertEqual(decision["decision"], "IMPORT")
        self.assertGreaterEqual(decision["final_score"], 65)
        self.assertTrue(decision["reasoning"]["comments"])

    def test_local_si_risque_et_delai_trop_eleves(self) -> None:
        decision = DecisionEngine().make_decision(
            {
                "CAPEX_LOCAL": 1000,
                "ECONOMIE_NETTE": 80,
                "supplier_risk_score": 90,
                "logistics_risk_score": 90,
                "lead_time_days": 120,
                "project_criticality": "CRITICAL",
            }
        )

        self.assertEqual(decision["decision"], "LOCAL")
        self.assertLess(decision["final_score"], 45)

    def test_mixte_si_gain_interessant_mais_risque_present(self) -> None:
        decision = DecisionEngine().make_decision(
            {
                "CAPEX_LOCAL": 1000,
                "ECONOMIE_NETTE": 180,
                "supplier_risk_score": 45,
                "logistics_risk_score": 45,
                "lead_time_days": 45,
                "project_criticality": "MEDIUM",
            }
        )

        self.assertEqual(decision["decision"], "MIXTE")
        self.assertEqual(decision["decision_type"], "MIXTE_OPTIMISE")

    def test_faible_confiance_si_score_bas(self) -> None:
        decision = DecisionEngine().make_decision(
            {
                "CAPEX_LOCAL": 1000,
                "ECONOMIE_NETTE": 0,
                "supplier_risk_score": 80,
                "lead_time_days": 90,
                "project_criticality": "HIGH",
            }
        )

        self.assertEqual(decision["confidence"], "LOW")

    def test_enrich_line_ajoute_champs_historisables(self) -> None:
        ligne = DecisionEngine().enrich_line({"CAPEX_LOCAL": 1000, "ECONOMIE_NETTE": 250})

        self.assertIn("FINAL_DECISION_SCORE", ligne)
        self.assertIn("DECISION_REASON", ligne)
        self.assertIn("DECISION_TYPE", ligne)


if __name__ == "__main__":
    unittest.main()
