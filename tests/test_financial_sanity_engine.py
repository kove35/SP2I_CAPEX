from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.financial_sanity_engine import FinancialSanityEngine
from app.core.kpi_engine import KPIEngine
from app.core.procurement_enrichment_engine import ProcurementEnrichmentEngine
from app.core.scenario_engine import ScenarioEngine


class FinancialSanityEngineTest(unittest.TestCase):
    def test_validates_generator_and_explains_anomaly(self) -> None:
        result = FinancialSanityEngine().validate_line({
            "designation": "Groupe electrogene insonorise 60 KVA",
            "prix_total_ht": 150000,
            "quantite": 1,
        })

        self.assertEqual(result["classification"]["equipment_type"], "GENERATOR_60_KVA")
        self.assertGreater(result["anomaly_score"], 0)
        self.assertIn("15,000,000", result["explainability"])
        self.assertEqual(result["powerbi"]["heatmap_bucket"], "HIGH_RISK")

    def test_compatible_with_procurement_kpi_and_scenario_engines(self) -> None:
        line = {
            "designation": "Groupe electrogene insonorise 60 KVA",
            "QTE": 1,
            "prix_total_ht": 20000000,
            "prix_fob": 14000000,
            "CAPEX_LOCAL": 20000000,
            "CAPEX_IMPORT": 16000000,
            "CAPEX_OPTIMISE": 16000000,
            "famille": "equipement_technique",
        }

        sanity = FinancialSanityEngine().validate_line(line)
        enriched = ProcurementEnrichmentEngine().enrich_line({**line, **sanity["classification"]})
        kpi = KPIEngine().compute_procurement_kpi([enriched])
        scenarios = ScenarioEngine().definition()

        self.assertIn("SCORE_PROCUREMENT", kpi)
        self.assertGreaterEqual(kpi["SCORE_PROCUREMENT"], 0)
        self.assertGreaterEqual(len(scenarios), 3)


if __name__ == "__main__":
    unittest.main()
