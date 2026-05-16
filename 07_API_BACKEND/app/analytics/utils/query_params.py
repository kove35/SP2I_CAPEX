from __future__ import annotations

from app.analytics.schemas import AnalyticsFilters, AnalyticsQuery


def build_query(
    projet: str | None = None,
    scenario: str | None = None,
    batiment: str | None = None,
    niveau: str | None = None,
    lot: str | None = None,
    famille: str | None = None,
    fournisseur: str | None = None,
    decision_import: str | None = None,
    periode_debut: str | None = None,
    periode_fin: str | None = None,
    criticite: str | None = None,
    statut_chantier: str | None = None,
    page: int = 1,
    page_size: int = 100,
    group_by: str | None = None,
    order_by: str | None = None,
    order_dir: str = "desc",
    drilldown_level: str | None = None,
) -> AnalyticsQuery:
    return AnalyticsQuery(
        filters=AnalyticsFilters(
            projet=projet,
            scenario=scenario,
            batiment=batiment,
            niveau=niveau,
            lot=lot,
            famille=famille,
            fournisseur=fournisseur,
            decision_import=decision_import,
            periode_debut=periode_debut,
            periode_fin=periode_fin,
            criticite=criticite,
            statut_chantier=statut_chantier,
        ),
        page=page,
        page_size=page_size,
        group_by=group_by,
        order_by=order_by,
        order_dir="asc" if order_dir == "asc" else "desc",
        drilldown_level=drilldown_level,
    )
