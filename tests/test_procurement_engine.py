from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.procurement_engine import ProcurementEngine


class ProcurementEngineTest(unittest.TestCase):
    def test_procurement_engine_retourne_analyses_completes(self) -> None:
        result = ProcurementEngine().evaluate(
            {
                "designation": "Ascenseur",
                "QTE": 1,
                "supplier_moq": 1,
                "CAPEX_IMPORT": 100000,
                "project_criticality": "HIGH",
            }
        )

        self.assertIn("risk_analysis", result)
        self.assertIn("lead_time_analysis", result)
        self.assertIn("cashflow_analysis", result)
        self.assertIn("moq_analysis", result)
        self.assertIn("complexity_analysis", result)
        self.assertIn(result["decision"], {"IMPORT", "MIXTE", "LOCAL"})

    def test_enrich_line_prepare_champs_historisables(self) -> None:
        line = ProcurementEngine().enrich_line({"designation": "Carrelage", "QTE": 100, "CAPEX_IMPORT": 5000})

        self.assertIn("GLOBAL_RISK_SCORE", line)
        self.assertIn("TOTAL_IMPORT_LEAD_TIME", line)
        self.assertIn("CASHFLOW_SCORE", line)
        self.assertIn("IMPORT_COMPLEXITY_SCORE", line)


if __name__ == "__main__":
    unittest.main()
