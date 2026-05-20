"""
Tests API du Scenario Intelligence.

Ces tests verifient que les nouveaux endpoints d'historique, de comparaison,
de meilleur scenario et d'analytics sont exposés correctement.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.main import app


class ScenarioIntelligenceApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def _persist_scenario(self, scenario_name: str, scenario_type: str) -> dict:
        response = self.client.post(
            "/simulation/simulate",
            json={
                "items": [
                    {
                        "id_ligne": "SCENARIO-INTELLIGENCE-001",
                        "designation": "Acier importable",
                        "quantite": 10,
                        "prix_total_ht": 5000,
                        "famille": "acier",
                        "lot": "Lot 1",
                    }
                ],
                "parameters": {
                    "taux_landed_cost": {
                        "transport_maritime": 0.12,
                        "assurance": 0.02,
                        "droits_douane": 0.08,
                    }
                },
                "mode": "strict",
                "persist": True,
                "summary_only": False,
                "return_lines": False,
                "scenario_name": scenario_name,
                "scenario_type": scenario_type,
                "created_by": "tests",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        return payload["metadata"]

    def test_scenario_history_endpoint_returns_items(self) -> None:
        metadata = self._persist_scenario("HISTORY_TEST_SCENARIO", "IMPORT_STANDARD")
        response = self.client.get("/simulation/scenarios/history?limit=5")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertIn("history", payload)
        self.assertGreaterEqual(len(payload["history"]), 1)
        self.assertIn("scenario_id", payload["history"][0])

    def test_best_scenarios_endpoint_returns_ranked_results(self) -> None:
        metadata = self._persist_scenario("BEST_TEST_SCENARIO", "IMPORT_STANDARD")
        response = self.client.get("/simulation/scenarios/best?limit=3")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertIn("best", payload)
        self.assertIn("rankings", payload)
        self.assertIsInstance(payload["rankings"], list)

    def test_scenario_analytics_endpoint_returns_trend(self) -> None:
        metadata = self._persist_scenario("ANALYTICS_TEST_SCENARIO", "IMPORT_STANDARD")
        scenario_id = metadata["scenario_id"]
        response = self.client.get(f"/simulation/scenarios/analytics?scenario_id={scenario_id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertIn("analytics", payload)
        self.assertIn("trend", payload["analytics"])
        self.assertIn("score_breakdown", payload["analytics"])

    def test_scenario_compare_endpoint_compares_two_scenarios(self) -> None:
        first_metadata = self._persist_scenario("COMPARE_TEST_A", "IMPORT_STANDARD")
        second_metadata = self._persist_scenario("COMPARE_TEST_B", "IMPORT_AGRESSIF")
        scenario_a = first_metadata["scenario_id"]
        scenario_b = second_metadata["scenario_id"]

        response = self.client.get(
            "/simulation/scenarios/compare",
            params={"scenario_a": scenario_a, "scenario_b": scenario_b},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertIn("comparison", payload)
        self.assertIn("scenarios", payload["comparison"])
        self.assertEqual(len(payload["comparison"]["scenarios"]), 2)


if __name__ == "__main__":
    unittest.main()
