"""Tests unitaires du canal d'audit enterprise."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.audit_trail_engine import AuditTrailEngine
from app.core.parameter_registry_engine import ParameterRegistryEngine


class AuditTrailEngineTest(unittest.TestCase):
    def test_build_line_audit_includes_expected_fields(self) -> None:
        registry = ParameterRegistryEngine()
        engine = AuditTrailEngine(registry)

        ligne = {
            "id_ligne": "L-001",
            "designation": "Test produit",
            "famille": "electricite",
            "lot": "Lot 1",
            "DECISION_FINALE": "IMPORT",
            "DECISION_TYPE": "IMPORT_CONTROLE",
            "FINAL_DECISION_SCORE": 77,
            "DECISION_CONFIDENCE": "MEDIUM",
            "DECISION_REASON": {
                "savings_score": 80,
                "risk_score": 20,
                "lead_time_score": 40,
                "criticality_score": 10,
                "importability_score": 90,
                "procurement_maturity_score": 55,
            },
        }

        audit = engine.build_line_audit(ligne)

        self.assertEqual(audit["decision"], "IMPORT")
        self.assertEqual(audit["decision_type"], "IMPORT_CONTROLE")
        self.assertEqual(audit["scores"]["final_score"], 77)
        self.assertEqual(audit["parameters"]["registry_version"], "1.0")
        self.assertEqual(audit["line_context"]["lot"], "Lot 1")
        self.assertIn("engine_version", audit)


if __name__ == "__main__":
    unittest.main()
