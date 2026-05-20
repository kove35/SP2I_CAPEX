from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class PriceReferenceRepository:
    """Charge les referentiels JSON CAPEX en lecture seule."""

    BASE_DIR = Path(__file__).resolve().parent
    TAXONOMY_DIR = BASE_DIR / "capex_taxonomy"
    FINANCIAL_RANGES_DIR = BASE_DIR / "financial_ranges"

    @lru_cache(maxsize=1)
    def load_taxonomy(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for path in sorted(self.TAXONOMY_DIR.glob("*_taxonomy.json")):
            payload = self._load_json(path)
            family = str(payload.get("family", path.stem.replace("_taxonomy", "").upper()))
            data[family] = payload
        return data

    @lru_cache(maxsize=1)
    def load_financial_ranges(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for path in sorted(self.FINANCIAL_RANGES_DIR.glob("*_medium.json")):
            payload = self._load_json(path)
            family = str(payload.get("family", path.stem.replace("_medium", "").upper()))
            for equipment_type, reference in payload.get("references", {}).items():
                data[equipment_type] = {**reference, "family": family}
        return data

    def get_equipment_reference(self, equipment_type: str | None) -> dict[str, Any]:
        if not equipment_type:
            return {}
        return dict(self.load_financial_ranges().get(equipment_type, {}))

    def get_family_references(self, family: str | None) -> list[dict[str, Any]]:
        if not family:
            return []
        return [
            {"equipment_type": equipment_type, **reference}
            for equipment_type, reference in self.load_financial_ranges().items()
            if reference.get("family") == family
        ]

    def _load_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
