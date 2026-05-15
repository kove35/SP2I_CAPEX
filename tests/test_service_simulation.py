"""
Tests unitaires de `ServiceSimulation`.

Ces tests verifient le contrat applicatif sans demarrer de serveur FastAPI.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.schemas import SimulationItem, SimulationRequest
from app.services.service_simulation import ServiceSimulation


class ServiceSimulationTest(unittest.TestCase):
    def test_simulation_stricte_retourne_metadata(self) -> None:
        request = SimulationRequest(
            items=[
                SimulationItem(
                    designation="Cable electrique",
                    quantite=10,
                    prix_total_ht=1000,
                    lot="Lot 4",
                )
            ],
            mode="strict",
        )

        response = ServiceSimulation().simuler(request)

        self.assertEqual(response["status"], "SUCCESS")
        self.assertEqual(response["kpi"]["lignes"], 1)
        self.assertTrue(response["metadata"]["simulation_id"].startswith("sim_"))
        self.assertTrue(response["metadata"]["run_id"].startswith("run_"))
        self.assertTrue(response["metadata"]["scenario_id"].startswith("scenario_"))
        self.assertEqual(len(response["lignes"]), 1)

    def test_summary_only_ne_retourne_pas_les_lignes(self) -> None:
        request = SimulationRequest(
            items=[SimulationItem(designation="Ascenseur", quantite=1, prix_total_ht=10000)],
            summary_only=True,
            return_lines=False,
            mode="strict",
        )

        response = ServiceSimulation().simuler(request)

        self.assertEqual(response["status"], "SUCCESS")
        self.assertEqual(response["lignes"], [])
        self.assertEqual(response["kpi"]["lignes"], 1)

    def test_mode_strict_retourne_erreur_structuree(self) -> None:
        request = SimulationRequest(
            items=[SimulationItem(designation="Prix manquant", quantite=1, prix_total_ht=0)],
            mode="strict",
        )

        response = ServiceSimulation().simuler(request)

        self.assertEqual(response["status"], "ERROR")
        self.assertEqual(response["errors"][0]["code"], "DATA_QUALITY_ERROR")
        self.assertEqual(response["kpi"]["lignes"], 0)

    def test_mode_tolerant_retourne_warning(self) -> None:
        request = SimulationRequest(
            items=[SimulationItem(designation="Prix manquant", quantite=1, prix_total_ht=0)],
            mode="tolerant",
        )

        response = ServiceSimulation().simuler(request)

        self.assertEqual(response["status"], "SUCCESS")
        self.assertTrue(response["warnings"])


if __name__ == "__main__":
    unittest.main()
