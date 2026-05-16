from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.ai.ai_dqe_parser import AIDQEParser


class AIDQEParserTest(unittest.TestCase):
    def test_preserve_contexte_lot_pour_articles_suivants(self) -> None:
        parser = AIDQEParser()
        rows = [
            ["Lot", "Designation", "QTE", "PU", "Montant"],
            ["LOT 4 : ELECTRICITE", "", "", "", ""],
            ["", "Cable principal", 20, 5000, 100000],
        ]
        analysis = {
            "ligne_entete": 1,
            "mapping": [
                {"champ_standard": "lot", "colonne_index": 0},
                {"champ_standard": "designation", "colonne_index": 1},
                {"champ_standard": "quantite", "colonne_index": 2},
                {"champ_standard": "prix_unitaire_ht", "colonne_index": 3},
                {"champ_standard": "prix_total_ht", "colonne_index": 4},
            ],
        }

        normalized, classified = parser.parse_rows(rows, analysis)

        self.assertEqual(classified[0]["row_type"], "lot")
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["lot"], "LOT 4 : ELECTRICITE")


if __name__ == "__main__":
    unittest.main()
