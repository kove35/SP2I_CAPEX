from __future__ import annotations

import re
import unicodedata
from typing import Any


class SemanticNormalizationEngine:
    """Normalise les designations CAPEX fournisseurs, OCR et DQE."""

    REPLACEMENTS = {
        "grp": "groupe",
        "ge": "groupe electrogene",
        "g.e": "groupe electrogene",
        "g/e": "groupe electrogene",
        "clim": "climatiseur",
        "split ac": "split climatiseur",
        "vrf": "vrv",
        "v.r.v": "vrv",
        "td": "tableau divisionnaire",
        "tgbt": "tableau general basse tension",
        "baes": "bloc autonome eclairage securite",
        "cfa": "courant faible",
        "cf": "courant fort",
        "vid surveillance": "videosurveillance",
        "ctrl acces": "controle acces",
        "alu": "aluminium",
        "placo": "faux plafond",
    }

    UNIT_PATTERNS = {
        "power_kva": re.compile(r"\b(\d+(?:[.,]\d+)?)\s*k\s*v\s*a\b"),
        "power_kw": re.compile(r"\b(\d+(?:[.,]\d+)?)\s*k\s*w\b"),
        "section_mm2": re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(?:mm2|mm\s*2|mm\^2)\b"),
        "diameter_mm": re.compile(r"\b(?:dn|diam|diametre|diameter)?\s*(\d+(?:[.,]\d+)?)\s*mm\b"),
        "surface_m2": re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(?:m2|m\s*2|m\^2)\b"),
        "volume_l": re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(?:l|litres?|liter)\b"),
        "btu": re.compile(r"\b(\d+(?:[.,]\d+)?)\s*btu\b"),
    }

    def normalize(self, designation: str | None) -> dict[str, Any]:
        raw = designation or ""
        normalized = self._strip_accents(raw).lower()
        normalized = normalized.replace("\u0153", "oe").replace("\u00e6", "ae")
        normalized = re.sub(r"[/_()\-]+", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        for source, target in self.REPLACEMENTS.items():
            normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        tokens = [token for token in normalized.split(" ") if token]
        attributes = self.extract_attributes(normalized)
        return {
            "raw_designation": raw,
            "normalized_designation": normalized,
            "tokens": tokens,
            "attributes": attributes,
            "normalization_confidence_score": self._confidence(raw, normalized, attributes),
        }

    def extract_attributes(self, text: str) -> dict[str, Any]:
        attributes: dict[str, Any] = {}
        for name, pattern in self.UNIT_PATTERNS.items():
            match = pattern.search(text)
            if match:
                attributes[name] = self._number(match.group(1))
        return attributes

    def _strip_accents(self, value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value)
        return "".join(char for char in decomposed if not unicodedata.combining(char))

    def _number(self, value: str) -> float:
        return float(value.replace(",", "."))

    def _confidence(self, raw: str, normalized: str, attributes: dict[str, Any]) -> float:
        if not raw.strip():
            return 0.0
        score = 60.0
        if len(normalized.split()) >= 2:
            score += 15.0
        if attributes:
            score += 15.0
        if any(char.isdigit() for char in raw):
            score += 5.0
        if len(raw) >= 8:
            score += 5.0
        return round(min(score, 100.0), 2)
