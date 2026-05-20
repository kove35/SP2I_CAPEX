from __future__ import annotations

from typing import Any


class KPIEngine:
    """Calcule les KPI enterprise procurement a partir des lignes enrichies."""

    def compute_procurement_kpi(self, lignes: list[dict[str, Any]]) -> dict[str, Any]:
        capex_brut = 0.0
        capex_import_simple = 0.0
        capex_import_optimise = 0.0
        capex_decision = 0.0
        economie_capturee = 0.0
        potentiel_theorique_max = 0.0
        capex_importable = 0.0
        lignes_importables = 0
        lignes_totales = len(lignes)
        weighted_procurement_score = 0.0
        weighted_risk_score = 0.0
        total_weight = 0.0

        for ligne in lignes:
            capex_local = self._number(ligne.get("CAPEX_LOCAL") or ligne.get("capex_local"), 0)
            capex_import = self._number(ligne.get("CAPEX_IMPORT") or ligne.get("capex_import"), 0)
            capex_optimise = self._number(ligne.get("CAPEX_OPTIMISE") or ligne.get("capex_optimise"), 0)
            importability = self._number(ligne.get("IMPORTABILITY_SCORE"), 0)
            procurement_score = self._number(ligne.get("PROCUREMENT_SCORE") or ligne.get("procurement_score"), 0)
            risk_score = self._number(ligne.get("RISK_SCORE") or ligne.get("risk_score"), 50)
            capex_brut += capex_local
            capex_import_simple += capex_import
            capex_import_optimise += min(capex_import, capex_local)
            capex_decision += capex_optimise
            economie_capturee += max(0.0, capex_local - capex_optimise)

            if importability >= 50:
                capex_importable += capex_local
                lignes_importables += 1
                potentiel_theorique_max += max(0.0, capex_local - capex_import) * (importability / 100)

            weight = capex_local if capex_local > 0 else 1.0
            weighted_procurement_score += procurement_score * weight
            weighted_risk_score += risk_score * weight
            total_weight += weight

        potential_cache = max(0.0, potentiel_theorique_max - economie_capturee)
        dependence_import = capex_import_simple / capex_brut if capex_brut else 0.0
        taux_couverture_sourcing = capex_importable / capex_brut if capex_brut else 0.0
        taux_importabilite = lignes_importables / lignes_totales if lignes_totales else 0.0
        average_procurement_score = weighted_procurement_score / total_weight if total_weight else 0.0
        average_risk_score = weighted_risk_score / total_weight if total_weight else 0.0

        return {
            "CAPEX_BRUT": round(capex_brut, 2),
            "CAPEX_IMPORT_SIMPLE": round(capex_import_simple, 2),
            "CAPEX_IMPORT_OPTIMISE": round(capex_import_optimise, 2),
            "CAPEX_DECISION": round(capex_decision, 2),
            "POTENTIEL_THEORIQUE_MAX": round(potentiel_theorique_max, 2),
            "ECONOMIE_CAPTUREE": round(economie_capturee, 2),
            "POTENTIEL_CACHE": round(potential_cache, 2),
            "TAUX_COUVERTURE_SOURCING": round(taux_couverture_sourcing, 4),
            "TAUX_IMPORTABILITE": round(taux_importabilite, 4),
            "SCORE_PROCUREMENT": round(average_procurement_score, 2),
            "RISQUE_LOGISTIQUE": round(average_risk_score, 2),
            "DEPENDANCE_IMPORT": round(dependence_import, 4),
            "LIGNES_TOTAL": lignes_totales,
            "LIGNES_IMPORTABLES": lignes_importables,
        }

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
