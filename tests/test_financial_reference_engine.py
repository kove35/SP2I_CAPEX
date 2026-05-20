from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.financial_reference_engine import FinancialReferenceEngine


class FinancialReferenceEngineTest(unittest.TestCase):
    def test_generator_range_is_realistic_for_central_africa(self) -> None:
        reference = FinancialReferenceEngine().get_reference("GENERATOR_60_KVA")

        self.assertEqual(reference["currency"], "FCFA")
        self.assertEqual(reference["region"], "CENTRAL_AFRICA")
        self.assertEqual(reference["price_min"], 15000000)
        self.assertEqual(reference["price_max"], 40000000)

    def test_region_and_quality_adjust_reference(self) -> None:
        reference = FinancialReferenceEngine().get_reference(
            "GENERATOR_60_KVA",
            region="CONGO_BRAZZAVILLE",
            quality="PREMIUM",
        )

        self.assertGreater(reference["price_min"], 15000000)
        self.assertEqual(reference["quality"], "PREMIUM")


if __name__ == "__main__":
    unittest.main()
