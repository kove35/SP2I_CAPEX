from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.procurement_enrichment_engine import ProcurementEnrichmentEngine


class ProcurementEnrichmentEngineTest(unittest.TestCase):
    def test_enrich_line_adds_procurement_signals(self) -> None:
        line = {
            "designation": "Groupe electrogene",
            "QTE": 1,
            "prix_total_ht": 100000,
            "prix_fob": 70000,
            "famille": "equipement_technique",
            "supplier_moq": 1,
            "quality_score": 88,
            "reliability_score": 82,
        }
        result = ProcurementEnrichmentEngine().enrich_line(line)

        self.assertIn("SOURCING_COVERAGE", result)
        self.assertIn("IMPORTABILITY_SCORE", result)
        self.assertIn("PROCUREMENT_SCORE", result)
        self.assertIn("HIDDEN_SAVINGS_POTENTIAL", result)
        self.assertIn("PROCUREMENT_ANALYSIS", result)
        self.assertGreaterEqual(result["SOURCING_COVERAGE"], 0)
        self.assertLessEqual(result["SOURCING_COVERAGE"], 100)


if __name__ == "__main__":
    unittest.main()
