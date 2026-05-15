from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.main import app


class LogisticsApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def _persist_simulation(self) -> str:
        response = self.client.post(
            "/simulation/simulate",
            json={
                "items": [
                    {
                        "id_ligne": "LOG-API-001",
                        "designation": "Luminaire Shanghai",
                        "quantite": 500,
                        "prix_total_ht": 25000,
                        "famille": "luminaire",
                        "lot": "Lot Electricite",
                        "volume_unitaire_m3": 0.03,
                        "poids_unitaire_kg": 4,
                        "supplier_city": "Shanghai",
                        "shipment_status": "AT_SEA",
                    }
                ],
                "mode": "strict",
                "persist": True,
                "summary_only": False,
                "return_lines": True,
                "scenario_name": "TEST_LOGISTICS_API",
                "scenario_type": "IMPORT_AGRESSIF",
                "created_by": "tests",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["metadata"]["simulation_id"]

    def test_endpoints_logistics(self) -> None:
        simulation_id = self._persist_simulation()

        for path, key in [
            ("/logistics/container-plan", "container_plan"),
            ("/logistics/shipment-analysis", "shipment_analysis"),
            ("/logistics/freight-cost", "freight_cost"),
            ("/logistics/site-delivery", "site_delivery"),
        ]:
            response = self.client.get(f"{path}/{simulation_id}")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["status"], "SUCCESS")
            self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()
