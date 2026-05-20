"""Tests unitaires du registre de parametres enterprise."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.parameter_registry_engine import ParameterRegistryEngine


class ParameterRegistryEngineTest(unittest.TestCase):
    def test_registry_defaults_are_available(self) -> None:
        registry = ParameterRegistryEngine()

        self.assertAlmostEqual(registry.get_logistics_rates().transport_maritime, 0.15)
        self.assertAlmostEqual(registry.get_logistics_rates().assurance, 0.02)
        self.assertAlmostEqual(registry.get_score_weights().weight_savings, 0.30)
        self.assertEqual(registry.get_decision_thresholds().seuil_decision_import, 0.97)
        self.assertEqual(registry.get_importability_rules().target_score, 70)

    def test_get_parameter_path_works(self) -> None:
        registry = ParameterRegistryEngine()

        self.assertEqual(registry.get_parameter("score_weights.weight_risk"), 0.25)
        self.assertEqual(registry.get_parameter("decision_thresholds.min_import_score"), 65)
        self.assertEqual(registry.get_parameter("ratios_fob.alucobond"), 0.6)
        self.assertIsNone(registry.get_parameter("not.exists"))

    def test_update_parameters_overrides_defaults(self) -> None:
        registry = ParameterRegistryEngine(parameters={"logistics_rates": {"transport_maritime": 0.22}})

        self.assertAlmostEqual(registry.get_logistics_rates().transport_maritime, 0.22)
        registry.update_parameters({"score_weights": {"weight_savings": 0.40}})
        self.assertAlmostEqual(registry.get_score_weights().weight_savings, 0.40)


if __name__ == "__main__":
    unittest.main()
