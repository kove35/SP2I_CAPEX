"""
Tests d'integration de l'historisation des scenarios.

Ces tests utilisent l'API FastAPI en memoire et PostgreSQL local. Ils verifient
que `persist=true` sauvegarde bien scenario, run et lignes simulees.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.main import app


class ScenarioHistoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def persist_scenario(self, name: str, transport: float) -> str:
        response = self.client.post(
            "/simulation/simulate",
            json={
                "items": [
                    {
                        "id_ligne": f"{name}-001",
                        "designation": "Cable electrique",
                        "quantite": 10,
                        "prix_total_ht": 1000,
                        "famille": "electricite",
                        "lot": "Lot 4",
                    }
                ],
                "parameters": {
                    "taux_landed_cost": {
                        "transport_maritime": transport,
                        "assurance": 0.02,
                        "droits_douane": 0.10,
                    },
                    "seuil_decision_import": 0.97,
                },
                "mode": "strict",
                "persist": True,
                "summary_only": True,
                "return_lines": False,
                "scenario_name": name,
                "scenario_type": "BASELINE",
                "created_by": "tests",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        return payload["metadata"]["scenario_id"].replace("scenario_", "")

    def test_persist_true_cree_un_scenario_lisible(self) -> None:
        scenario_id = self.persist_scenario("TEST_SCENARIO_HISTORY_A", 0.10)

        response = self.client.get(f"/simulation/scenario/{scenario_id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertEqual(payload["scenario"]["scenario_nom"], "TEST_SCENARIO_HISTORY_A")
        self.assertEqual(len(payload["lignes"]), 1)

    def test_compare_scenarios_retourne_deux_kpi(self) -> None:
        scenario_a = self.persist_scenario("TEST_SCENARIO_COMPARE_A", 0.10)
        scenario_b = self.persist_scenario("TEST_SCENARIO_COMPARE_B", 0.30)

        response = self.client.get(
            "/simulation/compare",
            params={"scenario_a": scenario_a, "scenario_b": scenario_b},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertEqual(len(payload["comparison"]), 2)

    def test_list_scenarios(self) -> None:
        self.persist_scenario("TEST_SCENARIO_LIST", 0.10)

        response = self.client.get("/simulation/scenarios")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "SUCCESS")
        self.assertGreaterEqual(len(response.json()["scenarios"]), 1)


if __name__ == "__main__":
    unittest.main()
