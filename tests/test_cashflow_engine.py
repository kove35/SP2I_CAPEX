from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.cashflow_engine import CashflowEngine


class CashflowEngineTest(unittest.TestCase):
    def test_acompte_et_solde_30_70(self) -> None:
        result = CashflowEngine().evaluate({"CAPEX_IMPORT": 100000})

        self.assertEqual(result["advance_payment"], 30000)
        self.assertEqual(result["remaining_payment"], 70000)
        self.assertEqual(result["cashflow_risk"], "MEDIUM")


if __name__ == "__main__":
    unittest.main()
