from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.ai.ai_excel_classifier import AIExcelClassifier


class AIExcelClassifierTest(unittest.TestCase):
    def test_classifie_feuille_dqe(self) -> None:
        classifier = AIExcelClassifier()

        result = classifier.classify_sheet(
            "DQE Gros oeuvre",
            [
                ["Lot", "Designation", "QTE", "PU", "Montant"],
                ["LOT 1", "Beton", 10, 1000, 10000],
            ],
        )

        self.assertEqual(result["document_type"], "DQE")
        self.assertGreater(result["confidence"], 0)


if __name__ == "__main__":
    unittest.main()
