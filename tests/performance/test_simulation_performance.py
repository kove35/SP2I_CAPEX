"""
Benchmarks simples du moteur de simulation.

Par defaut, le test mesure 100, 1 000 et 10 000 lignes pour rester rapide en CI
locale. Le benchmark 100 000 lignes est disponible avec :

    $env:SP2I_RUN_100K_BENCH="1"
    python -m unittest tests.performance.test_simulation_performance
"""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "07_API_BACKEND"))

from app.schemas import SimulationItem, SimulationRequest
from app.services.service_simulation import ServiceSimulation


def build_items(count: int) -> list[SimulationItem]:
    return [
        SimulationItem(
            id_ligne=f"PERF-{index:06d}",
            designation="Cable electrique",
            quantite=10,
            prix_total_ht=1000,
            famille="electricite",
            lot="Lot 4",
        )
        for index in range(count)
    ]


class SimulationPerformanceTest(unittest.TestCase):
    def assert_simulation_under(self, count: int, max_seconds: float) -> None:
        request = SimulationRequest(
            items=build_items(count),
            mode="strict",
            summary_only=True,
            return_lines=False,
        )

        start = time.perf_counter()
        response = ServiceSimulation().simuler(request)
        duration = time.perf_counter() - start

        self.assertEqual(response["status"], "SUCCESS")
        self.assertEqual(response["kpi"]["lignes"], count)
        self.assertLess(
            duration,
            max_seconds,
            f"Simulation {count} lignes trop lente: {duration:.2f}s",
        )

    def test_100_lignes(self) -> None:
        self.assert_simulation_under(100, 1.0)

    def test_1000_lignes(self) -> None:
        self.assert_simulation_under(1000, 3.0)

    def test_10000_lignes(self) -> None:
        self.assert_simulation_under(10000, 15.0)

    @unittest.skipUnless(os.getenv("SP2I_RUN_100K_BENCH") == "1", "Benchmark lourd active sur demande.")
    def test_100000_lignes(self) -> None:
        self.assert_simulation_under(100000, 120.0)


if __name__ == "__main__":
    unittest.main()
