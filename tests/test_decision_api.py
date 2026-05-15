"""
Tests API du Decision Engine.

Ces tests verifient que les decisions historisees sont explicables via l'API
sans recalculer la logique metier cote Power BI.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.main import app


class DecisionApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def _persist_decision_scenario(self) -> dict:
        response = self.client.post(
            "/simulation/simulate",
            json={
                "items": [
                    {
                        "id_ligne": "DECISION-API-001",
                        "designation": "Menuiserie importable",
                        "quantite": 5,
                        "prix_total_ht": 1000,
                        "famille": "menuiserie",
                        "lot": "Lot 6",
                    }
                ],
                "parameters": {
                    "taux_landed_cost": {
                        "transport_maritime": 0.10,
                        "assurance": 0.02,
                        "droits_douane": 0.08,
                    }
                },
                "mode": "strict",
                "persist": True,
                "summary_only": False,
                "return_lines": True,
                "scenario_name": "TEST_DECISION_API",
                "scenario_type": "IMPORT_AGRESSIF",
                "created_by": "tests",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        return payload

    def test_rules_expose_parametres_decisionnels(self) -> None:
        response = self.client.get("/decision/rules")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertIn("weights", payload)
        self.assertIn("thresholds", payload)

    def test_explain_retourne_raisonnement_historise(self) -> None:
        simulation = self._persist_decision_scenario()
        simulation_id = simulation["metadata"]["simulation_id"]

        response = self.client.get(f"/decision/explain/{simulation_id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertEqual(payload["metadata"]["nombre_lignes"], 1)
        self.assertIn("decision_reason", payload["lignes"][0])
        self.assertGreaterEqual(payload["lignes"][0]["decision_score"], 0)

    def test_risk_analysis_filtre_par_scenario(self) -> None:
        simulation = self._persist_decision_scenario()
        scenario_id = simulation["metadata"]["scenario_id"]

        response = self.client.get(f"/decision/risk-analysis/{scenario_id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertGreaterEqual(payload["metadata"]["nombre_groupes"], 1)


if __name__ == "__main__":
    unittest.main()
