from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.main import app


class ProcurementApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def _persist_simulation(self) -> str:
        response = self.client.post(
            "/simulation/simulate",
            json={
                "items": [
                    {
                        "id_ligne": "PROC-API-001",
                        "designation": "Groupe electrogene",
                        "quantite": 1,
                        "prix_total_ht": 100000,
                        "famille": "equipement_technique",
                        "lot": "Lot Technique",
                        "project_criticality": "HIGH",
                        "supplier_moq": 1,
                        "cashflow_tension": "HIGH",
                    }
                ],
                "mode": "strict",
                "persist": True,
                "summary_only": False,
                "return_lines": True,
                "scenario_name": "TEST_PROCUREMENT_API",
                "scenario_type": "CRISE_LOGISTIQUE",
                "created_by": "tests",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["metadata"]["simulation_id"]

    def test_endpoints_procurement_lisent_fact_simulation(self) -> None:
        simulation_id = self._persist_simulation()

        for path, key in [
            ("/procurement/risk-analysis", "risk_analysis"),
            ("/procurement/lead-time", "lead_time_analysis"),
            ("/procurement/cashflow", "cashflow_analysis"),
            ("/procurement/import-complexity", "import_complexity_analysis"),
        ]:
            response = self.client.get(f"{path}/{simulation_id}")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["status"], "SUCCESS")
            self.assertGreaterEqual(payload["metadata"]["nombre_lignes"], 1)
            self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()
