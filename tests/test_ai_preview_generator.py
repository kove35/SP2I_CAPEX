from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.ai.ai_preview_generator import AIPreviewGenerator


class AIPreviewGeneratorTest(unittest.TestCase):
    def test_genere_resume_intelligent(self) -> None:
        generator = AIPreviewGenerator()

        preview = generator.generate(
            rows=[
                {"lot": "LOT 1", "prix_total_ht": 1000},
                {"lot": "LOT 2", "prix_total_ht": 2000},
            ],
            sheet_analysis={"mapping": [{"confiance": 0.9}, {"confiance": 0.6}]},
            anomalies=[{"line_id": 1}],
            confidence={"global_confidence": 0.82, "needs_human_validation": True},
        )

        self.assertEqual(preview["lots_detected"], 2)
        self.assertEqual(preview["recognized_columns"], 2)
        self.assertEqual(preview["invalid_rows"], 1)
        self.assertEqual(preview["estimated_capex_detected"], 3000)


if __name__ == "__main__":
    unittest.main()
