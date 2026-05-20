"""Tests unitaires du moteur d'explicabilite."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.explainability_engine import ExplainabilityEngine


class ExplainabilityEngineTest(unittest.TestCase):
    def test_explain_line_generates_summary_and_insights(self) -> None:
        engine = ExplainabilityEngine()

        ligne = {
            "DECISION_FINALE": "IMPORT",
            "FINAL_DECISION_SCORE": 90,
            "IMPORTABILITY_SCORE": 80,
            "PROCUREMENT_SCORE": 60,
            "HIDDEN_SAVINGS_POTENTIAL": 12,
            "SUPPLIER_MATURITY_SCORE": 65,
            "PROCUREMENT_MATURITY_SCORE": 55,
            "CONTAINER_STRATEGY": "FCL",
            "STORAGE_COST": 800,
            "CAPEX_LOCAL": 12000,
            "CAPEX_IMPORT": 9500,
            "ECONOMIE_NETTE": 2500,
        }

        explanation = engine.explain_line(ligne)

        self.assertEqual(explanation["decision"], "IMPORT")
        self.assertTrue(isinstance(explanation["procurement"], dict))
        self.assertEqual(explanation["procurement"]["hidden_savings_potential"], 12.0)
        self.assertIn("importabilite", explanation["summary"].lower())
        self.assertIn("container_strategy", explanation["technical"])


if __name__ == "__main__":
    unittest.main()
