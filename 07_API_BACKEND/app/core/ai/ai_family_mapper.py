from __future__ import annotations

from app.ai.excel_mapping_rules import normaliser_libelle


class AIFamilyMapper:
    """Mappe les designations vers des familles metier explicables."""

    FAMILY_KEYWORDS = {
        "CVC": {"vrv", "cassette", "clim", "split", "ventilation", "cta"},
        "ELECTRICITE": {"cable", "tableau", "prise", "luminaire", "disjoncteur"},
        "PLOMBERIE": {"pvc", "tube", "robinet", "sanitaire", "evacuation"},
        "GROS_OEUVRE": {"beton", "coffrage", "armature", "fondation", "dalle"},
        "SECOND_OEUVRE": {"peinture", "carrelage", "plafond", "menuiserie"},
        "ASCENSEUR": {"ascenseur", "lift", "elevateur"},
    }

    def map_family(self, designation: str) -> dict[str, object]:
        normalized = normaliser_libelle(designation)
        tokens = set(normalized.split("_"))

        best_family = "INCONNUE"
        best_hits = 0
        for family, keywords in self.FAMILY_KEYWORDS.items():
            hits = len(tokens & {normaliser_libelle(keyword) for keyword in keywords})
            if hits > best_hits:
                best_family = family
                best_hits = hits

        confidence = min(0.55 + (best_hits * 0.18), 0.95) if best_hits else 0.2
        return {
            "famille": best_family,
            "confidence": round(confidence, 2),
            "reason": "Famille deduite des mots cles de designation." if best_hits else "Aucun mot cle famille robuste detecte.",
        }

    def enrich_rows(self, rows: list[dict]) -> list[dict]:
        enriched = []
        for row in rows:
            family = self.map_family(str(row.get("designation", "")))
            enriched.append(
                {
                    **row,
                    "famille_ai": family["famille"],
                    "famille_ai_confidence": family["confidence"],
                    "famille_ai_reason": family["reason"],
                }
            )
        return enriched
