from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.moq_engine import MOQEngine


class MOQEngineTest(unittest.TestCase):
    def test_moq_irrealiste_detecte_surstock(self) -> None:
        result = MOQEngine().evaluate({"QTE": 25, "supplier_moq": 200})

        self.assertFalse(result["moq_respected"])
        self.assertEqual(result["surplus_quantity"], 175)
        self.assertGreater(result["moq_risk_score"], 80)


if __name__ == "__main__":
    unittest.main()
