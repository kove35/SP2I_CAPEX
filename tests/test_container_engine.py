from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.container_engine import ContainerEngine


class ContainerEngineTest(unittest.TestCase):
    def test_choisit_40ft_pour_volume_moyen(self) -> None:
        result = ContainerEngine().evaluate({"QTE": 1000, "volume_unitaire_m3": 0.04})

        self.assertEqual(result["container_type"], "40FT")
        self.assertEqual(result["containers_required"], 1)
        self.assertGreater(result["fill_rate"], 0.55)


if __name__ == "__main__":
    unittest.main()
