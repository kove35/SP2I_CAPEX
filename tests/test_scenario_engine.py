from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.scenario_engine import ScenarioEngine


class ScenarioEngineTest(unittest.TestCase):
    def test_definition_contains_three_profiles(self) -> None:
        engine = ScenarioEngine()
        profiles = engine.definition()

        self.assertEqual(len(profiles), 3)
        self.assertIn("CONSERVATEUR", [profile["code"] for profile in profiles])
        self.assertIn("EQUILIBRE", [profile["code"] for profile in profiles])
        self.assertIn("AGRESSIF", [profile["code"] for profile in profiles])

    def test_analyse_landed_cost_variations_returns_scenarios(self) -> None:
        engine = ScenarioEngine({"taux_landed_cost": {"transport_maritime": 0.15}})
        lignes = [{"designation": "Cable electrique", "quantite": 10, "prix_total_ht": 1000}]
        result = engine.analyse_landed_cost_variations(lignes, [-0.1, 0.0, 0.1])

        self.assertEqual(len(result), 3)
        self.assertIn("variation", result[0])
        self.assertIn("kpi", result[0])


if __name__ == "__main__":
    unittest.main()
