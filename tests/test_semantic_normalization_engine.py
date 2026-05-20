from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.semantic_normalization_engine import SemanticNormalizationEngine


class SemanticNormalizationEngineTest(unittest.TestCase):
    def test_normalize_generator_extracts_kva(self) -> None:
        result = SemanticNormalizationEngine().normalize("Groupe electrogene insonorise 60 KVA")

        self.assertIn("groupe", result["tokens"])
        self.assertEqual(result["attributes"]["power_kva"], 60)
        self.assertGreaterEqual(result["normalization_confidence_score"], 80)


if __name__ == "__main__":
    unittest.main()
