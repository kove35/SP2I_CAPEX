from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.ai.ai_column_mapper import AIColumnMapper


class AIColumnMapperTest(unittest.TestCase):
    def test_mappe_variantes_quantite(self) -> None:
        mapper = AIColumnMapper()

        suggestions = mapper.map_columns(["Designation", "Qté", "Montant"])
        champs = {item["champ_standard"] for item in suggestions}

        self.assertIn("designation", champs)
        self.assertIn("quantite", champs)
        self.assertIn("prix_total_ht", champs)

    def test_explique_le_mapping(self) -> None:
        mapper = AIColumnMapper()
        suggestion = mapper.map_single_column("P.U")

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion["mapped_to"], "prix_unitaire_ht")
        self.assertGreaterEqual(suggestion["confidence"], 0.58)
        self.assertTrue(suggestion["reason"])


if __name__ == "__main__":
    unittest.main()
