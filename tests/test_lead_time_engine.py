from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.lead_time_engine import LeadTimeEngine


class LeadTimeEngineTest(unittest.TestCase):
    def test_delai_chine_pointe_noire_par_defaut(self) -> None:
        result = LeadTimeEngine().evaluate({})

        self.assertEqual(result["total_import_lead_time"], 80)
        self.assertEqual(result["lead_time_level"], "HIGH")


if __name__ == "__main__":
    unittest.main()
