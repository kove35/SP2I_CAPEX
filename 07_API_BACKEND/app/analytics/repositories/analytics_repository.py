from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analytics.schemas import AnalyticsQuery
from app.analytics.utils.display_text import normalize_display_text
from app.analytics.utils.schema_utils import first_non_empty_sql, load_table_columns, optional_column_sql
from app.config.fact_source import get_fact_source
from app.config.financial_source import get_financial_source


ALLOWED_GROUPS = {
    "projet": "projet_id",
    "batiment": "batiment",
    "niveau": "niveau",
    "lot": "lot",
    "famille": "famille",
    "decision_import": "decision_import",
}

ALLOWED_ORDER = {
    "capex_local",
    "capex_optimise",
    "economie",
    "lot",
    "famille",
    "batiment",
    "niveau",
    "appartement_id",
    "appart",
    "piece",
    "decision_import",
}

DRILLDOWN = ["projet", "batiment", "niveau", "appartement", "piece", "lot", "famille", "article"]


class AnalyticsRepository:
    """Repository SQL optimise pour les dashboards React/Power BI-like."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _fact_source() -> str:
        return get_fact_source()

    @staticmethod
    def _financial_source() -> str:
        return get_financial_source()

    def schema_capabilities(self) -> dict[str, dict[str, bool]]:
        columns = self._fact_columns()
        return {
            "fact_metre": {
                column: column in columns
                for column in (
                    "appartement_id",
                    "appartement_code",
                    "appart",
                    "piece",
                    "piece_id",
                    "piece_code",
                    "piece_type",
                    "type_zone",
                    "ifc_guid",
                    "ifc_type",
                    "bim_object",
                    "bim_object_id",
                    "omniclass",
                    "uniclass",
                    "classification",
                )
            }
        }

    def kpis(self, query: AnalyticsQuery) -> dict[str, Any]:
        financial_source = self._financial_source()
        where_sql, params = self.build_financial_where_clause(query)
        row = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(SUM(capex_local), 0) AS capex_brut,
                    COALESCE(SUM(capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(economie), 0) AS economie_nette,
                    CASE WHEN COALESCE(SUM(capex_local), 0) = 0 THEN 0
                         ELSE SUM(economie) / NULLIF(SUM(capex_local), 0)
                    END AS taux_economie,
                    CASE WHEN COALESCE(SUM(capex_import), 0) = 0 THEN 0
                         ELSE SUM(economie) / NULLIF(SUM(capex_import), 0)
                    END AS roi_import,
                    CASE WHEN COUNT(*) = 0 THEN 0
                         ELSE SUM(CASE WHEN decision_import = 'IMPORT' THEN 1 ELSE 0 END)::float / COUNT(*)
                    END AS taux_importable,
                    COUNT(DISTINCT lot) FILTER (WHERE lot IS NOT NULL AND TRIM(CAST(lot AS text)) <> '') AS nb_lots,
                    COUNT(*) AS nb_lignes
                FROM {financial_source}
                {where_sql}
                """
            ),
            params,
        ).mappings().one()
        return dict(row)

    def get_project_cost_summary(self, query: AnalyticsQuery) -> dict[str, Any]:
        where_sql, params = self._v6_project_where(query, table_alias="s")
        row = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(SUM(s.capex_direct), 0) AS capex_direct,
                    COALESCE(SUM(s.capex_import), 0) AS capex_import,
                    COALESCE(SUM(s.capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(s.economie_nette), 0) AS economie_nette,
                    COALESCE(SUM(s.indirect_costs), 0) AS indirect_costs,
                    COALESCE(SUM(s.site_installation), 0) AS site_installation,
                    COALESCE(SUM(s.import_logistics), 0) AS import_logistics,
                    COALESCE(SUM(s.contingency), 0) AS contingency,
                    COALESCE(SUM(s.total_project_cost), 0) AS total_project_cost,
                    CASE WHEN COALESCE(SUM(s.surface_m2), 0) = 0 THEN 0
                         ELSE SUM(s.capex_direct) / NULLIF(SUM(s.surface_m2), 0) END AS capex_direct_per_m2,
                    CASE WHEN COALESCE(SUM(s.surface_m2), 0) = 0 THEN 0
                         ELSE SUM(s.total_project_cost) / NULLIF(SUM(s.surface_m2), 0) END AS total_project_cost_per_m2,
                    CASE WHEN COALESCE(SUM(s.nb_appartements), 0) = 0 THEN 0
                         ELSE SUM(s.total_project_cost) / NULLIF(SUM(s.nb_appartements), 0) END AS total_project_cost_per_appartement,
                    CASE WHEN COALESCE(SUM(s.nb_niveaux), 0) = 0 THEN 0
                         ELSE SUM(s.total_project_cost) / NULLIF(SUM(s.nb_niveaux), 0) END AS total_project_cost_per_niveau,
                    COALESCE(SUM(s.fallback_legacy_lot_capex), 0) AS fallback_legacy_lot_capex,
                    CASE WHEN COALESCE(SUM(s.capex_direct), 0) = 0 THEN 0
                         ELSE 100.0 * SUM(s.fallback_legacy_lot_capex) / NULLIF(SUM(s.capex_direct), 0) END AS fallback_legacy_lot_pct
                FROM vw_project_cost_summary_v6 s
                {where_sql}
                """
            ),
            params,
        ).mappings().one()
        summary = dict(row)
        summary["capex_m2"] = summary.get("total_project_cost_per_m2")
        summary["cost_per_apartment"] = summary.get("total_project_cost_per_appartement")
        summary["cost_per_level"] = summary.get("total_project_cost_per_niveau")
        return self._json_safe(summary)

    def get_dashboard_direction_v6(self, query: AnalyticsQuery) -> list[dict[str, Any]]:
        where_sql, params = self._v6_project_where(query, table_alias="d")
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    lot,
                    capex_direct,
                    pct_capex_direct,
                    nb_lignes,
                    nb_articles,
                    fallback_legacy_lot_lines,
                    fallback_legacy_lot_capex,
                    project_capex_direct,
                    indirect_costs,
                    site_installation,
                    import_logistics,
                    contingency,
                    total_project_cost,
                    total_project_cost_per_m2,
                    total_project_cost_per_appartement,
                    total_project_cost_per_niveau
                FROM vw_dashboard_direction_v6_scoped d
                {where_sql}
                ORDER BY capex_direct DESC
                """
            ),
            params,
        ).mappings().all()
        return [self._json_safe(dict(row)) for row in rows]

    def get_cost_intelligence_v6(self, query: AnalyticsQuery) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        filters = query.filters
        if filters.projet:
            clauses.append(self._project_predicate("project_code", "projet_id"))
            params["projet"] = filters.projet
        if filters.lot:
            clauses.append("lot = :lot")
            params["lot"] = filters.lot
        if filters.sous_lot:
            clauses.append("sous_lot = :sous_lot")
            params["sous_lot"] = filters.sous_lot
        if filters.decision_import:
            clauses.append("decision_import = :decision_import")
            params["decision_import"] = filters.decision_import
        where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    lot,
                    sous_lot,
                    article_code,
                    designation,
                    unite,
                    quantite,
                    prix_local_fcfa,
                    prix_import_fcfa,
                    prix_optimise_fcfa,
                    capex_local,
                    capex_import,
                    capex_optimise,
                    economie,
                    decision_import,
                    pricing_scope,
                    pricing_confidence,
                    price_reference_code
                FROM vw_cost_intelligence_v6_scoped
                {where_sql}
                ORDER BY capex_local DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                **params,
                "limit": query.page_size,
                "offset": (query.page - 1) * query.page_size,
            },
        ).mappings().all()
        return [self._json_safe(dict(row)) for row in rows]

    def table(self, query: AnalyticsQuery) -> tuple[list[dict[str, Any]], int]:
        where_sql, params = self.build_where_clause(query)
        fact_source = self._fact_source()
        limit = query.page_size
        offset = (query.page - 1) * query.page_size
        order_column = query.order_by if query.order_by in ALLOWED_ORDER and self._fact_column_exists(query.order_by) else "capex_local"
        order_dir = "ASC" if query.order_dir == "asc" else "DESC"
        appartement_sql = self._appartement_sql()
        piece_sql = self._piece_sql()
        piece_type_sql = self._piece_type_sql()
        family_sql = self._family_sql()
        ifc_guid_sql = self._optional_text_column("ifc_guid")
        ifc_type_sql = self._optional_text_column("ifc_type")
        bim_object_sql = self._bim_object_sql()

        total = self.db.execute(text(f"SELECT COUNT(*) FROM {fact_source} {where_sql}"), params).scalar_one()
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    id_ligne,
                    designation,
                    lot,
                    {family_sql} AS famille,
                    batiment,
                    niveau,
                    {appartement_sql} AS appartement,
                    {piece_sql} AS piece,
                    {piece_type_sql} AS piece_type,
                    {ifc_guid_sql} AS ifc_guid,
                    {ifc_type_sql} AS ifc_type,
                    {bim_object_sql} AS bim_object,
                    quantite,
                    pu_local,
                    pu_import,
                    capex_local,
                    capex_import,
                    capex_optimise,
                    economie,
                    taux_economie,
                    decision_import,
                    date_import
                FROM {fact_source}
                {where_sql}
                ORDER BY {order_column} {order_dir}
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": limit, "offset": offset},
        ).mappings().all()
        return [dict(row) for row in rows], int(total)

    def grouped(self, query: AnalyticsQuery, default_group: str = "lot") -> list[dict[str, Any]]:
        group_key = query.group_by or default_group
        group_column = self._group_column(group_key, default_group)
        where_sql, params = self.build_where_clause(query)
        fact_source = self._fact_source()
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(CAST({group_column} AS text), 'NON_RENSEIGNE') AS label,
                    COALESCE(SUM(capex_local), 0) AS capex_brut,
                    COALESCE(SUM(capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(economie), 0) AS economie_nette,
                    COUNT(*) AS nb_lignes
                FROM {fact_source}
                {where_sql}
                GROUP BY COALESCE(CAST({group_column} AS text), 'NON_RENSEIGNE')
                ORDER BY capex_brut DESC
                LIMIT 50
                """
            ),
            params,
        ).mappings().all()
        return [dict(row) for row in rows]

    def heatmap_rows(self, query: AnalyticsQuery) -> list[dict[str, Any]]:
        where_sql, params = self.build_where_clause(query)
        fact_source = self._fact_source()
        family_sql = self._family_sql()
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
                    COALESCE({family_sql}, 'Famille non renseignee') AS famille,
                    COALESCE(SUM(capex_local), 0) AS budget,
                    COALESCE(SUM(capex_optimise), 0) AS value,
                    COALESCE(SUM(economie), 0) AS economie,
                    COUNT(*) AS nb_lignes
                FROM {fact_source}
                {where_sql}
                GROUP BY COALESCE(lot, 'NON_RENSEIGNE'), COALESCE({family_sql}, 'Famille non renseignee')
                ORDER BY value DESC
                LIMIT 200
                """
            ),
            params,
        ).mappings().all()
        return [dict(row) for row in rows]

    def heatmap(self, query: AnalyticsQuery) -> dict[str, Any]:
        rows = self.heatmap_rows(query)
        distinct_lots = len({str(row.get("lot") or "").strip() for row in rows if str(row.get("lot") or "").strip()})
        x_labels = list(dict.fromkeys(str(row.get("lot") or "NON_RENSEIGNE") for row in rows))
        y_labels = list(dict.fromkeys(str(row.get("famille") or "default") for row in rows))
        x_index = {label: index for index, label in enumerate(x_labels)}
        y_index = {label: index for index, label in enumerate(y_labels)}
        data = [
            [
                x_index[str(row.get("lot") or "NON_RENSEIGNE")],
                y_index[str(row.get("famille") or "default")],
                float(row.get("value") or 0),
            ]
            for row in rows
        ]
        return {
            "xLabels": x_labels,
            "yLabels": y_labels,
            "data": data,
            "rows": rows,
            "max": max((item[2] for item in data), default=0),
            "min": min((item[2] for item in data), default=0),
            "sample_size": {
                "nb_lots": distinct_lots,
                "nb_lignes": sum(int(row.get("nb_lignes") or 0) for row in rows),
                "state": "INSUFFICIENT_DATA" if distinct_lots < 5 else "OK",
                "message": "Donnees insuffisantes pour calculer un risque fiable" if distinct_lots < 5 else "",
            },
        }

    def sankey(self, query: AnalyticsQuery) -> list[dict[str, Any]]:
        where_sql, params = self.build_where_clause(query)
        fact_source = self._fact_source()
        family_sql = self._family_sql()
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(decision_import, 'LOCAL') AS decision,
                    COALESCE({family_sql}, 'SP2I Supply') AS fournisseur,
                    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
                    COALESCE(SUM(capex_optimise), 0) AS value,
                    COALESCE(SUM(economie), 0) AS economie,
                    CASE WHEN COALESCE(SUM(capex_import), 0) = 0 THEN 0
                         ELSE COALESCE(SUM(economie), 0) / NULLIF(SUM(capex_import), 0)
                    END AS roi,
                    COUNT(*) AS nb_lignes
                FROM {fact_source}
                {where_sql}
                GROUP BY COALESCE(decision_import, 'LOCAL'), COALESCE({family_sql}, 'SP2I Supply'), COALESCE(lot, 'NON_RENSEIGNE')
                ORDER BY value DESC
                LIMIT 80
                """
            ),
            params,
        ).mappings().all()
        links: list[dict[str, Any]] = []
        for row in rows:
            decision = normalize_display_text(str(row["decision"] or "LOCAL")).upper()
            fournisseur = normalize_display_text(str(row["fournisseur"] or "SP2I Supply"))
            lot = normalize_display_text(str(row["lot"] or "NON_RENSEIGNE"))
            value = float(row["value"] or 0)
            economie = float(row["economie"] or 0)
            roi = float(row["roi"] or 0)
            delai = 75 if decision == "IMPORT" else 14
            links.extend([
                {
                    "source": "CAPEX",
                    "target": decision,
                    "value": value,
                    "roi": roi,
                    "gain": economie,
                    "economie": economie,
                    "fournisseur": fournisseur,
                    "delai": delai,
                    "decision": decision,
                    "lot": lot,
                    "nb_lignes": int(row["nb_lignes"] or 0),
                },
                {
                    "source": decision,
                    "target": fournisseur,
                    "value": value,
                    "roi": roi,
                    "gain": economie,
                    "economie": economie,
                    "fournisseur": fournisseur,
                    "delai": delai,
                    "decision": decision,
                    "lot": lot,
                    "nb_lignes": int(row["nb_lignes"] or 0),
                },
                {
                    "source": fournisseur,
                    "target": lot,
                    "value": value,
                    "roi": roi,
                    "gain": economie,
                    "economie": economie,
                    "fournisseur": fournisseur,
                    "delai": delai,
                    "decision": decision,
                    "lot": lot,
                    "nb_lignes": int(row["nb_lignes"] or 0),
                },
            ])
        return links

    def risk_matrix(self, query: AnalyticsQuery) -> list[dict[str, Any]]:
        """Dataset risques agrege pour le cockpit enterprise.

        Le risque est volontairement explicable: il combine l'impact financier,
        le choix import/local, l'economie attendue et la densite de lignes.
        """
        where_sql, params = self.build_where_clause(query)
        fact_source = self._fact_source()
        family_sql = self._family_sql()
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
                    COALESCE({family_sql}, 'SP2I Supply') AS fournisseur,
                    COALESCE(decision_import, 'LOCAL') AS decision_import,
                    COALESCE(SUM(capex_local), 0) AS impact,
                    COALESCE(SUM(capex_optimise), 0) AS capex_expose,
                    COALESCE(SUM(economie), 0) AS economie,
                    CASE WHEN COALESCE(SUM(capex_local), 0) = 0 THEN 0
                         ELSE COALESCE(SUM(economie), 0) / NULLIF(SUM(capex_local), 0)
                    END AS economie_rate,
                    COUNT(*) AS nb_lignes
                FROM {fact_source}
                {where_sql}
                GROUP BY COALESCE(lot, 'NON_RENSEIGNE'), COALESCE({family_sql}, 'SP2I Supply'), COALESCE(decision_import, 'LOCAL')
                ORDER BY impact DESC
                LIMIT 96
                """
            ),
            params,
        ).mappings().all()
        distinct_lots = {str(row["lot"] or "").strip() for row in rows if str(row["lot"] or "").strip()}
        max_impact = max((float(row["impact"] or 0) for row in rows), default=1) or 1
        risks: list[dict[str, Any]] = []
        insufficient_sample = len(distinct_lots) < 5

        for row in rows:
            lot = normalize_display_text(str(row["lot"] or "NON_RENSEIGNE"))
            fournisseur = normalize_display_text(str(row["fournisseur"] or "SP2I Supply"))
            decision = normalize_display_text(str(row["decision_import"] or "LOCAL")).upper()
            impact = float(row["impact"] or 0)
            capex_expose = float(row["capex_expose"] or impact)
            economie = float(row["economie"] or 0)
            economie_rate = float(row["economie_rate"] or 0)
            nb_lignes = int(row["nb_lignes"] or 0)

            impact_score = min((impact / max_impact) * 100, 100)
            import_penalty = 20 if decision == "IMPORT" else 7
            density_penalty = min(nb_lignes / 4, 18)
            savings_volatility = min(max(economie_rate, 0) * 100, 24)
            probabilite = self._clamp(24 + import_penalty + density_penalty + savings_volatility, 5, 95)
            criticite = self._clamp((impact_score * 0.48) + (probabilite * 0.52), 5, 100)
            delai = 75 if decision == "IMPORT" else 14

            if insufficient_sample:
                criticite = min(criticite, 54)
                risque_type = "Donnees insuffisantes"
            elif criticite >= 72:
                risque_type = "Critique"
            elif probabilite >= 55:
                risque_type = "Surveillance"
            elif impact_score >= 50:
                risque_type = "Quick wins"
            else:
                risque_type = "Faible priorite"

            risks.append({
                "lot": lot,
                "impact": round(impact, 2),
                "probabilite": round(probabilite, 2),
                "criticite": round(criticite, 2),
                "capex_expose": round(capex_expose, 2),
                "delai": delai,
                "fournisseur": fournisseur,
                "risque_type": risque_type,
                "decision_import": decision,
                "economie": round(economie, 2),
                "nb_lignes": nb_lignes,
                "sample_size_state": "INSUFFICIENT_DATA" if insufficient_sample else "OK",
                "sample_size_message": "Donnees insuffisantes pour calculer un risque fiable" if insufficient_sample else "",
                "nb_lots": len(distinct_lots),
            })

        return risks

    def scenarios(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT scenario_id::text, scenario_nom, scenario_type, created_at
                FROM dim_scenario
                ORDER BY created_at DESC
                LIMIT 100
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def timeline(self, query: AnalyticsQuery) -> list[dict[str, Any]]:
        where_sql, params = self.build_where_clause(query)
        fact_source = self._fact_source()
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    date_trunc('day', COALESCE(date_import, created_at))::date AS periode,
                    COALESCE(SUM(capex_local), 0) AS capex_brut,
                    COALESCE(SUM(capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(economie), 0) AS economie_nette,
                    COUNT(*) AS nb_lignes
                FROM {fact_source}
                {where_sql}
                GROUP BY date_trunc('day', COALESCE(date_import, created_at))::date
                ORDER BY periode
                """
            ),
            params,
        ).mappings().all()
        if len(rows) >= 4:
            return [
                {
                    "date": str(row["periode"]),
                    "budget_initial": float(row["capex_brut"] or 0),
                    "capex": float(row["capex_optimise"] or 0),
                    "economie": float(row["economie_nette"] or 0),
                    "roi": 0,
                    "scenario": "Historique",
                    "risque": 42,
                    "jalon": "Import DQE",
                    "nb_lignes": int(row["nb_lignes"] or 0),
                }
                for row in rows
            ]

        kpis = self.kpis(query)
        capex_brut = float(kpis.get("capex_brut") or 0)
        capex_final = float(kpis.get("capex_optimise") or 0)
        economie = float(kpis.get("economie_nette") or 0)
        roi = float(kpis.get("roi_import") or 0)
        risque_base = min(95, max(22, 68 - roi * 100))
        today = date.today()
        points = [
            (-90, "Baseline local", capex_brut, 0, 0, risque_base + 14, "DQE initial"),
            (-60, "Nettoyage DQE", capex_brut - economie * 0.18, economie * 0.18, roi * 0.25, risque_base + 8, "Normalisation"),
            (-30, "Mixte optimise", capex_brut - economie * 0.52, economie * 0.52, roi * 0.55, risque_base + 2, "Arbitrage CAPEX"),
            (0, "Scenario actif", capex_final, economie, roi, risque_base, "Validation cockpit"),
            (30, "Projection achats", max(capex_final - economie * 0.06, 0), economie * 1.06, roi * 1.05, max(risque_base - 6, 12), "Procurement"),
            (60, "Import agressif", max(capex_final - economie * 0.11, 0), economie * 1.11, roi * 1.12, max(risque_base - 10, 10), "Logistique"),
        ]
        return [
            {
                "date": str(today.fromordinal(today.toordinal() + offset)),
                "budget_initial": round(capex_brut, 2),
                "capex": round(capex, 2),
                "economie": round(gain, 2),
                "roi": round(item_roi, 4),
                "scenario": scenario,
                "risque": round(risque, 2),
                "jalon": jalon,
                "nb_lignes": int(kpis.get("nb_lignes") or 0),
            }
            for offset, scenario, capex, gain, item_roi, risque, jalon in points
        ]

    def filter_options(self) -> dict[str, list[str]]:
        """Valeurs distinctes exposees au cockpit React pour les dropdowns BI."""
        fact_source = self._fact_source()
        fields = {
            "batiments": "batiment",
            "niveaux": "niveau",
            "appartements": self._appartement_sql(),
            "pieces": self._piece_sql(),
            "lots": "lot",
            "familles": "famille",
            "import_local": "decision_import",
        }
        result: dict[str, list[str]] = {}
        for key, column in fields.items():
            if key == "pieces":
                result[key] = self._piece_filter_options()
                continue
            if column == "NULL":
                result[key] = []
                continue
            rows = self.db.execute(
                text(
                    f"""
                    SELECT DISTINCT {column} AS value
                    FROM {fact_source}
                    WHERE {column} IS NOT NULL AND TRIM(CAST({column} AS text)) <> ''
                    ORDER BY value
                    LIMIT 500
                    """
                )
            ).scalars().all()
            result[key] = [normalize_display_text(str(value)) for value in rows if value]
        return result

    def _piece_filter_options(self) -> list[str]:
        """Options Piece robustes PLAN_READY: FACT_METRE puis DIM_PIECE si disponible."""
        fact_source = self._fact_source()
        piece_sql = self._piece_sql()
        unions = [
            f"""
            SELECT DISTINCT value
            FROM (
                SELECT {piece_sql} AS value
                FROM {fact_source}
            ) fact_pieces
            WHERE value IS NOT NULL AND TRIM(CAST(value AS text)) <> ''
            """
        ]
        dim_piece_columns = load_table_columns(self.db, "dim_piece")
        dim_piece_candidates = [
            f"NULLIF(TRIM(CAST({column} AS text)), '')"
            for column in ("piece_nom", "piece_code", "piece")
            if column in dim_piece_columns
        ]
        if dim_piece_candidates:
            dim_piece_sql = f"COALESCE({', '.join(dim_piece_candidates)})"
            unions.append(
                f"""
                SELECT DISTINCT {self._normalise_piece_sql(dim_piece_sql)} AS value
                FROM dim_piece
                WHERE {dim_piece_sql} IS NOT NULL
                """
            )
        rows = self.db.execute(
            text(
                f"""
                WITH piece_values AS (
                    {" UNION ".join(unions)}
                )
                SELECT value
                FROM piece_values
                ORDER BY
                    CASE value
                        WHEN 'ENTREE' THEN 1
                        WHEN 'SEJOUR' THEN 2
                        WHEN 'CUISINE' THEN 3
                        WHEN 'CHAMBRE_1' THEN 4
                        WHEN 'CHAMBRE_2' THEN 5
                        WHEN 'CHAMBRE_3' THEN 6
                        WHEN 'SDB_1' THEN 7
                        WHEN 'SDB_2' THEN 8
                        WHEN 'SDB_3' THEN 9
                        WHEN 'DRESSING' THEN 10
                        WHEN 'WC_VISITEUR' THEN 11
                        WHEN 'DEGAGEMENT' THEN 12
                        WHEN 'BALCON' THEN 13
                        ELSE 99
                    END,
                    value
                LIMIT 500
                """
            )
        ).scalars().all()
        return [normalize_display_text(str(value)) for value in rows if value]

    def get_generation_diagnostic(self) -> dict[str, Any]:
        """Diagnostic read-only des couches generatives V5.2 a V5.3."""
        counts = {
            "fact_generation_bim": self._safe_relation_count("fact_generation_bim"),
            "fact_generation_network": self._safe_relation_count("fact_generation_network"),
            "fact_generation_dqe": self._safe_relation_count("fact_generation_dqe"),
            "fact_generation_expansion": self._safe_relation_count("fact_generation_expansion"),
        }
        view_counts = {
            "building_rows": self._safe_relation_count("vw_sp2i_generated_building"),
            "envelope_rows": self._safe_relation_count("vw_sp2i_generated_envelope"),
            "special_rows": self._safe_relation_count("vw_sp2i_generated_special_systems"),
        }
        statuses = {
            "v52_status": "DEPLOYED" if counts["fact_generation_dqe"] > 0 else "MISSING",
            "v521_status": "DEPLOYED" if counts["fact_generation_expansion"] > 0 else "MISSING",
            "v522_status": "DEPLOYED" if self._relation_exists("vw_energy_resilience_dashboard") else "MISSING",
            "v53_status": "DEPLOYED" if all(value > 0 for value in view_counts.values()) else "MISSING",
        }
        return self._json_safe({
            **statuses,
            **counts,
            **view_counts,
            "coverage_pct": self._generation_coverage_pct(counts, view_counts),
        })

    def get_generation_engine(self) -> dict[str, Any]:
        """Synthese CAPEX generatif V5.2/V5.2.1 sans addition avec FACT_METRE."""
        capex = {
            "generated_capex_local": 0,
            "generated_capex_import": 0,
            "generated_savings": 0,
            "generated_lines": 0,
        }
        if self._relation_exists("vw_sp2i_generated_capex"):
            row = self.db.execute(
                text(
                    """
                    SELECT
                        COALESCE(SUM(capex_local), 0) AS generated_capex_local,
                        COALESCE(SUM(capex_import), 0) AS generated_capex_import,
                        COALESCE(SUM(economie_potentielle), 0) AS generated_savings,
                        COALESCE(SUM(nb_lignes_dqe), 0) AS generated_lines
                    FROM vw_sp2i_generated_capex
                    """
                )
            ).mappings().one()
            capex = dict(row)

        by_lot: list[dict[str, Any]] = []
        generated_lot_views = [
            "vw_sp2i_generated_quantities",
            "vw_sp2i_generated_building",
            "vw_sp2i_generated_envelope",
            "vw_sp2i_generated_special_systems",
        ]
        existing_generated_lot_views = [
            view_name for view_name in generated_lot_views if self._relation_exists(view_name)
        ]
        if existing_generated_lot_views:
            union_sql = "\nUNION ALL\n".join(
                f"""
                SELECT
                    COALESCE(NULLIF(lot_code, ''), 'NON_RENSEIGNE') AS lot_code,
                    generated_article_code,
                    quantity
                FROM {view_name}
                """
                for view_name in existing_generated_lot_views
            )
            rows = self.db.execute(
                text(
                    f"""
                    WITH all_generated_lots AS (
                        {union_sql}
                    )
                    SELECT
                        COALESCE(NULLIF(lot_code, ''), 'NON_RENSEIGNE') AS lot_code,
                        COUNT(*) AS nb_lignes,
                        COUNT(DISTINCT generated_article_code) AS nb_articles,
                        ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 4) AS quantity_total
                    FROM all_generated_lots
                    GROUP BY COALESCE(NULLIF(lot_code, ''), 'NON_RENSEIGNE')
                    ORDER BY lot_code
                    """
                )
            ).mappings().all()
            by_lot = [dict(row) for row in rows]

        diagnostic = self.get_generation_diagnostic()
        return self._json_safe({
            **capex,
            "coverage_pct": diagnostic.get("coverage_pct", 0),
            "by_lot": by_lot,
        })

    def get_energy_resilience(self) -> dict[str, Any]:
        """Synthese resilience energetique issue des vues V5.2.2."""
        resilience = {
            "solar_kwc": 0,
            "battery_capacity_kwh": 0,
            "generator": "",
            "autonomy_hours": 0,
        }
        if self._relation_exists("vw_energy_resilience_dashboard"):
            row = self.db.execute(
                text(
                    """
                    SELECT
                        COALESCE(solar_kwc, 0) AS solar_kwc,
                        COALESCE(battery_capacity_kwh, 0) AS battery_capacity_kwh,
                        COALESCE(generator_code, '') AS generator,
                        COALESCE(autonomie_totale_h, 0) AS autonomy_hours
                    FROM vw_energy_resilience_dashboard
                    ORDER BY created_at DESC NULLS LAST
                    LIMIT 1
                    """
                )
            ).mappings().first()
            if row:
                resilience = dict(row)

        generator_rows: list[dict[str, Any]] = []
        if self._relation_exists("vw_generator_dashboard"):
            rows = self.db.execute(
                text(
                    """
                    SELECT
                        generator_code,
                        generator_name,
                        puissance_kva,
                        consommation_l_h,
                        consommation_jour_l,
                        fuel_type,
                        is_recommended,
                        heures_historique,
                        litres_historique,
                        cout_historique
                    FROM vw_generator_dashboard
                    ORDER BY is_recommended DESC, puissance_kva DESC
                    """
                )
            ).mappings().all()
            generator_rows = [dict(row) for row in rows]

        energy_sources: list[dict[str, Any]] = []
        if self._relation_exists("vw_energy_sources_dashboard"):
            rows = self.db.execute(
                text(
                    """
                    SELECT
                        system_code,
                        system_name,
                        lot_code,
                        COUNT(*) AS nb_lignes,
                        COUNT(DISTINCT equipment_code) AS nb_equipements,
                        ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 4) AS quantity_total
                    FROM vw_energy_sources_dashboard
                    GROUP BY system_code, system_name, lot_code
                    ORDER BY nb_lignes DESC, system_code
                    """
                )
            ).mappings().all()
            energy_sources = [dict(row) for row in rows]

        return self._json_safe({
            **resilience,
            "generators": generator_rows,
            "energy_sources": energy_sources,
        })

    def get_building_completion(self) -> dict[str, Any]:
        """Compteurs V5.3 par univers batiment, enveloppe et systemes speciaux."""
        building = self._lot_counts_from_view("vw_sp2i_generated_building")
        envelope = self._lot_counts_from_view("vw_sp2i_generated_envelope")
        special = self._lot_counts_from_view("vw_sp2i_generated_special_systems")
        building_total = sum(building.values())
        envelope_increment = sum(count for lot, count in envelope.items() if lot != "LOT_TOIT")
        special_increment = sum(count for lot, count in special.items() if lot != "LOT_VRD")
        payload = {
            "go_rows": building.get("LOT_GO", 0),
            "masonry_rows": building.get("LOT_MAC", 0),
            "roof_rows": building.get("LOT_TOIT", 0),
            "facade_rows": envelope.get("LOT_FACADE", 0),
            "vrd_rows": building.get("LOT_VRD", 0),
            "security_rows": special.get("LOT_SECURITE", 0),
            "fire_rows": special.get("LOT_INCENDIE", 0),
            "elevator_rows": special.get("LOT_ASC", 0),
            "total_rows": building_total + envelope_increment + special_increment,
            "by_lot": {
                "building": building,
                "envelope": envelope,
                "special_systems": special,
            },
        }
        return self._json_safe(payload)

    def quality_metrics(self) -> dict[str, Any]:
        fact_source = self._fact_source()
        row = self.db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) AS nb_lignes,
                    COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0) AS capex_local_total,
                    SUM(CASE WHEN quantite IS NULL OR quantite <= 0 THEN 1 ELSE 0 END) AS lignes_quantite_invalide,
                    SUM(CASE WHEN COALESCE(capex_local, prix_total_ht, 0) <= 0 THEN 1 ELSE 0 END) AS lignes_capex_invalide,
                    SUM(CASE WHEN capex_local IS NULL AND COALESCE(prix_total_ht, 0) > 0 THEN 1 ELSE 0 END) AS lignes_capex_fallback,
                    SUM(CASE WHEN lot IS NULL OR TRIM(lot) = '' THEN 1 ELSE 0 END) AS lignes_sans_lot,
                    SUM(CASE WHEN designation IS NULL OR TRIM(designation) = '' THEN 1 ELSE 0 END) AS lignes_sans_designation,
                    SUM(CASE WHEN famille IS NULL OR TRIM(famille) = '' OR LOWER(famille) IN ('default', 'unknown') THEN 1 ELSE 0 END) AS lignes_famille_a_classer,
                    SUM(CASE WHEN NULLIF(TRIM(COALESCE(appart, '')), '') IS NULL THEN 1 ELSE 0 END) AS lignes_appart_legacy_vides,
                    SUM(CASE WHEN NULLIF(TRIM(COALESCE(piece, '')), '') IS NULL THEN 1 ELSE 0 END) AS lignes_piece_legacy_vides,
                    COUNT(DISTINCT lot) AS lots_distincts,
                    COUNT(DISTINCT batiment) AS batiments_distincts,
                    COUNT(DISTINCT niveau) AS niveaux_distincts
                FROM {fact_source}
                """
            )
        ).mappings().one()
        return self._json_safe(dict(row))

    def import_audit_history(self, limit: int = 10) -> list[dict[str, Any]]:
        try:
            rows = self.db.execute(
                text(
                    """
                    SELECT
                        import_id,
                        fichier,
                        statut,
                        score_qualite,
                        lignes_excel,
                        lignes_parsees,
                        lignes_fact_metre,
                        capex_source,
                        capex_fact_metre,
                        ecart_capex,
                        ecart_capex_pct,
                        lots_detectes,
                        colonnes_reconnues,
                        created_at
                    FROM dqe_import_audit
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            ).mappings().all()
            return [self._json_safe(dict(row)) for row in rows]
        except Exception:
            return []

    def pipeline_debug(self) -> dict[str, Any]:
        """
        Retourne un diagnostic SQL lisible du pipeline DQE -> PostgreSQL.

        Cet endpoint aide a distinguer :
        - base vide ;
        - colonnes manquantes ;
        - montants non calcules ;
        - vues analytics vides ;
        - cache qui masque un refresh recent.
        """
        fact_source = self._fact_source()
        fact_count = int(self.db.execute(text(f"SELECT COUNT(*) FROM {fact_source}")).scalar_one() or 0)
        columns = self.db.execute(
            text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = :fact_source
                ORDER BY ordinal_position
                """
            ),
            {"fact_source": fact_source},
        ).mappings().all()
        sums = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(SUM(quantite), 0) AS quantite_total,
                    COALESCE(SUM(prix_total_ht), 0) AS prix_total_ht_total,
                    COALESCE(SUM(pu_local), 0) AS pu_local_total,
                    COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0) AS capex_local_total,
                    COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0) AS capex_optimise_total,
                    COALESCE(SUM(economie), 0) AS economie_total,
                    SUM(CASE WHEN quantite IS NULL OR quantite <= 0 THEN 1 ELSE 0 END) AS lignes_quantite_invalide,
                    SUM(CASE WHEN COALESCE(capex_local, prix_total_ht, 0) IS NULL OR COALESCE(capex_local, prix_total_ht, 0) <= 0 THEN 1 ELSE 0 END) AS lignes_capex_local_invalide,
                    SUM(CASE WHEN capex_local IS NULL AND COALESCE(prix_total_ht, 0) > 0 THEN 1 ELSE 0 END) AS lignes_capex_fallback,
                    SUM(CASE WHEN lot IS NULL OR lot = '' THEN 1 ELSE 0 END) AS lignes_sans_lot,
                    SUM(CASE WHEN NULLIF(TRIM(COALESCE(appart, '')), '') IS NULL THEN 1 ELSE 0 END) AS lignes_appart_legacy_vides,
                    SUM(CASE WHEN NULLIF(TRIM(COALESCE(piece, '')), '') IS NULL THEN 1 ELSE 0 END) AS lignes_piece_legacy_vides
                FROM {fact_source}
                """
            )
        ).mappings().one()
        preview = self.db.execute(
            text(
                f"""
                SELECT
                    id_ligne,
                    designation,
                    lot,
                    famille,
                    quantite,
                    pu_local,
                    prix_total_ht,
                    capex_local,
                    capex_optimise,
                    economie,
                    decision_import
                FROM {fact_source}
                ORDER BY created_at DESC NULLS LAST, id_ligne
                LIMIT 20
                """
            )
        ).mappings().all()
        view_checks = {
            "vw_capex_summary": self._safe_view_one("SELECT * FROM vw_capex_summary LIMIT 1"),
            "vw_project_kpis": self._safe_view_one("SELECT * FROM vw_project_kpis LIMIT 1"),
            "vw_dashboard_direction": self._safe_view_one("SELECT * FROM vw_dashboard_direction LIMIT 1"),
        }
        warnings: list[str] = []
        if fact_count == 0:
            warnings.append("fact_metre est vide : synchroniser un DQE avec /api/upload/excel/sync.")
        if float(sums["capex_local_total"] or 0) == 0 and fact_count > 0:
            warnings.append("fact_metre contient des lignes mais capex_local total vaut 0 : verifier mapping montant/PU.")
        if int(sums["lignes_capex_fallback"] or 0) > 0:
            warnings.append("Certaines lignes utilisent le montant de secours prix_total_ht pour le cockpit.")
        if int(sums["lignes_capex_local_invalide"] or 0) > 0:
            warnings.append("Certaines lignes ont capex_local vide ou nul.")
        if int(sums["lignes_sans_lot"] or 0) > 0:
            warnings.append("Certaines lignes n'ont pas de lot.")
        spatial_legacy_empty = max(
            int(sums["lignes_appart_legacy_vides"] or 0),
            int(sums["lignes_piece_legacy_vides"] or 0),
        )
        if fact_count and spatial_legacy_empty / fact_count > 0.10:
            warnings.append("DATA_QUALITY: BIM spatial dimensions incomplete")

        return {
            "fact_metre_count": fact_count,
            "columns": [dict(row) for row in columns],
            "sums": self._json_safe(dict(sums)),
            "preview": [self._json_safe(dict(row)) for row in preview],
            "views": view_checks,
            "warnings": warnings,
        }

    def _safe_view_one(self, sql: str) -> dict[str, Any]:
        try:
            row = self.db.execute(text(sql)).mappings().first()
            return {"status": "OK", "row": self._json_safe(dict(row)) if row else None}
        except Exception as exc:
            return {"status": "ERROR", "error": str(exc)}

    def _relation_exists(self, relation_name: str) -> bool:
        row = self.db.execute(
            text("SELECT to_regclass(:relation_name) IS NOT NULL AS exists_now"),
            {"relation_name": relation_name},
        ).mappings().one()
        return bool(row["exists_now"])

    def _safe_relation_count(self, relation_name: str) -> int:
        if not self._relation_exists(relation_name):
            return 0
        return int(self.db.execute(text(f"SELECT COUNT(*) FROM {relation_name}")).scalar_one() or 0)

    def _lot_counts_from_view(self, view_name: str) -> dict[str, int]:
        if not self._relation_exists(view_name):
            return {}
        rows = self.db.execute(
            text(
                f"""
                SELECT COALESCE(NULLIF(lot_code, ''), 'NON_RENSEIGNE') AS lot_code, COUNT(*) AS nb
                FROM {view_name}
                GROUP BY COALESCE(NULLIF(lot_code, ''), 'NON_RENSEIGNE')
                """
            )
        ).mappings().all()
        return {str(row["lot_code"]): int(row["nb"] or 0) for row in rows}

    @staticmethod
    def _generation_coverage_pct(counts: dict[str, int], view_counts: dict[str, int]) -> float:
        required = {
            "fact_generation_bim": 216,
            "fact_generation_network": 126,
            "fact_generation_dqe": 216,
            "fact_generation_expansion": 1854,
            "building_rows": 1200,
            "envelope_rows": 875,
            "special_rows": 805,
        }
        observed = {**counts, **view_counts}
        if not required:
            return 0
        ratios = [
            min(float(observed.get(key) or 0) / target, 1)
            for key, target in required.items()
            if target
        ]
        return round(sum(ratios) / len(ratios) * 100, 2) if ratios else 0

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_safe(item) for item in value]
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, str):
            return normalize_display_text(value)
        return value

    def build_where_clause(self, query: AnalyticsQuery) -> tuple[str, dict[str, Any]]:
        filters = query.filters
        clauses: list[str] = []
        params: dict[str, Any] = {}

        if filters.projet:
            columns = self._fact_columns()
            project_code = "project_code" if "project_code" in columns else "NULL"
            project_id = "projet_id" if "projet_id" in columns else "NULL"
            if project_code == "NULL" and project_id == "NULL":
                clauses.append("1 = 0")
            else:
                clauses.append(self._project_predicate(project_code, project_id))
                params["projet"] = filters.projet

        filter_columns = {
            "batiment": "batiment",
            "niveau": "niveau",
            "appartement": self._appartement_sql(),
            "piece": self._piece_sql(),
            "lot": "lot",
            "famille": "famille",
        }

        for field, column in filter_columns.items():
            value = getattr(filters, field)
            if value:
                if column == "NULL":
                    clauses.append("1 = 0")
                    continue
                clauses.append(f"LOWER(CAST({column} AS text)) LIKE LOWER(:{field})")
                params[field] = f"%{value}%"

        if filters.decision_import:
            clauses.append("LOWER(decision_import) = LOWER(:decision_import)")
            params["decision_import"] = filters.decision_import

        if filters.periode_debut:
            clauses.append("COALESCE(date_import, created_at) >= CAST(:periode_debut AS timestamptz)")
            params["periode_debut"] = filters.periode_debut
        if filters.periode_fin:
            clauses.append("COALESCE(date_import, created_at) <= CAST(:periode_fin AS timestamptz)")
            params["periode_fin"] = filters.periode_fin

        if not clauses:
            return "", params
        return "WHERE " + " AND ".join(clauses), params

    def build_financial_where_clause(self, query: AnalyticsQuery) -> tuple[str, dict[str, Any]]:
        filters = query.filters
        financial_source = self._financial_source()
        columns = load_table_columns(self.db, financial_source)

        def first_available(candidates: tuple[str, ...], default_sql: str = "NULL") -> str:
            available = [
                f"NULLIF(TRIM(CAST({column} AS text)), '')"
                for column in candidates
                if column in columns
            ]
            if not available:
                return default_sql
            return f"COALESCE({', '.join(available)})"

        filter_columns = {
            "batiment": first_available(("batiment", "batiment_code")),
            "niveau": first_available(("niveau", "niveau_code")),
            "appartement": first_available(("appartement", "appartement_code", "appartement_id", "appart")),
            "piece": first_available(("piece", "piece_code", "piece_id")),
            "lot": first_available(("lot", "lot_code")),
            "famille": first_available(("famille",)),
        }

        clauses: list[str] = []
        params: dict[str, Any] = {}
        if filters.projet:
            project_code = "project_code" if "project_code" in columns else "NULL"
            project_id = "projet_id" if "projet_id" in columns else "NULL"
            if project_code == "NULL" and project_id == "NULL":
                clauses.append("1 = 0")
            else:
                clauses.append(self._project_predicate(project_code, project_id))
                params["projet"] = filters.projet

        for field, column in filter_columns.items():
            value = getattr(filters, field)
            if value:
                if column == "NULL":
                    clauses.append("1 = 0")
                    continue
                clauses.append(f"LOWER(CAST({column} AS text)) LIKE LOWER(:{field})")
                params[field] = f"%{value}%"

        if filters.decision_import and "decision_import" in columns:
            clauses.append("LOWER(decision_import) = LOWER(:decision_import)")
            params["decision_import"] = filters.decision_import

        date_column = None
        if "date_import" in columns and "created_at" in columns:
            date_column = "COALESCE(date_import, created_at)"
        elif "date_import" in columns:
            date_column = "date_import"
        elif "created_at" in columns:
            date_column = "created_at"

        if date_column and filters.periode_debut:
            clauses.append(f"{date_column} >= CAST(:periode_debut AS timestamptz)")
            params["periode_debut"] = filters.periode_debut
        if date_column and filters.periode_fin:
            clauses.append(f"{date_column} <= CAST(:periode_fin AS timestamptz)")
            params["periode_fin"] = filters.periode_fin

        if not clauses:
            return "", params
        return "WHERE " + " AND ".join(clauses), params

    @staticmethod
    def _project_predicate(project_code_sql: str, project_id_sql: str) -> str:
        predicates: list[str] = []
        if project_code_sql != "NULL":
            predicates.append(f"LOWER(CAST({project_code_sql} AS text)) = LOWER(:projet)")
        if project_id_sql != "NULL":
            predicates.extend(
                [
                    f"CAST({project_id_sql} AS text) = CAST(:projet AS text)",
                    f"{project_id_sql} IN ("
                    "SELECT projet_id FROM dim_projet "
                    "WHERE LOWER(projet_code) = LOWER(:projet)"
                    ")",
                ]
            )
        return "(" + " OR ".join(predicates) + ")" if predicates else "1 = 0"

    def _v6_project_where(
        self,
        query: AnalyticsQuery,
        *,
        table_alias: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        if not query.filters.projet:
            return "", {}
        prefix = f"{table_alias}." if table_alias else ""
        return (
            "WHERE " + self._project_predicate(f"{prefix}project_code", f"{prefix}projet_id"),
            {"projet": query.filters.projet},
        )

    def _where(self, query: AnalyticsQuery) -> tuple[str, dict[str, Any]]:
        return self.build_where_clause(query)

    def _fact_columns(self) -> set[str]:
        return load_table_columns(self.db, self._fact_source())

    def _fact_column_exists(self, column_name: str | None) -> bool:
        return bool(column_name) and column_name in self._fact_columns()

    def _optional_text_column(self, column_name: str, default_sql: str = "NULL") -> str:
        return optional_column_sql(self._fact_columns(), column_name, default_sql=default_sql)

    def _appartement_sql(self) -> str:
        return first_non_empty_sql(
            self._fact_columns(),
            ("appartement_code", "appartement_id", "appart"),
        )

    def _piece_sql(self) -> str:
        columns = self._fact_columns()
        available: list[str] = []
        for column in ("piece_code", "piece"):
            if column in columns:
                available.append(f"NULLIF(TRIM(CAST({column} AS text)), '')")
        if "piece_id" in columns:
            available.append("NULLIF(TRIM(CAST(piece_id AS text)), '')")
        if not available:
            return "NULL"
        return self._normalise_piece_sql(f"COALESCE({', '.join(available)})")

    @staticmethod
    def _normalise_piece_sql(expression: str) -> str:
        return f"""
        CASE
            WHEN {expression} IN ('SDB_PARENTALE', 'SDB_PARENT') THEN 'SDB_1'
            ELSE {expression}
        END
        """

    def _piece_type_sql(self) -> str:
        return first_non_empty_sql(self._fact_columns(), ("piece_type", "type_zone"))

    @staticmethod
    def _family_sql() -> str:
        return """
        CASE
            WHEN famille IS NOT NULL
                 AND TRIM(CAST(famille AS text)) <> ''
                 AND LOWER(TRIM(CAST(famille AS text))) NOT IN ('default', 'non classe', 'non classé', 'classification en attente')
                THEN famille
            WHEN lot = 'LOT_ELEC' AND (
                UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%ECL%'
                OR UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%LUM%'
                OR UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%SPOT%'
            ) THEN 'Eclairage'
            WHEN lot = 'LOT_ELEC' AND (
                UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%PRISE%'
                OR UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%PC%'
            ) THEN 'Prises'
            WHEN lot = 'LOT_ELEC' AND (
                UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%CF%'
                OR UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%COURANT%'
                OR UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%DATA%'
                OR UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%TV%'
            ) THEN 'Courants faibles'
            WHEN lot = 'LOT_ELEC' AND (
                UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%TABLEAU%'
                OR UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%TD%'
                OR UPPER(COALESCE(sous_lot_id, sous_lot, designation, '')) LIKE '%DISJ%'
            ) THEN 'Tableau electrique'
            WHEN lot = 'LOT_ELEC' THEN 'Electricite'
            WHEN lot = 'LOT_CVC' THEN 'Climatisation'
            WHEN lot = 'LOT_CAR' THEN 'Carrelage et revetements'
            WHEN lot = 'LOT_FP' THEN 'Faux plafonds'
            WHEN lot = 'LOT_PNT' THEN 'Peinture'
            WHEN lot = 'LOT_SOL' THEN 'Plomberie'
            WHEN lot = 'LOT_TOIT' THEN 'Toiture'
            ELSE 'Famille non renseignee'
        END
        """

    def _bim_object_sql(self) -> str:
        return first_non_empty_sql(self._fact_columns(), ("bim_object", "bim_object_id"))

    def _group_column(self, group_key: str, default_group: str) -> str:
        if group_key == "appartement":
            return self._appartement_sql()
        if group_key == "piece":
            return self._piece_sql()
        if group_key == "famille":
            return self._family_sql()
        if group_key in ALLOWED_GROUPS:
            return ALLOWED_GROUPS[group_key]
        if default_group == "appartement":
            return self._appartement_sql()
        if default_group == "piece":
            return self._piece_sql()
        return ALLOWED_GROUPS.get(default_group, ALLOWED_GROUPS["lot"])

    @staticmethod
    def drilldown_path(level: str | None) -> dict[str, Any]:
        current = level if level in DRILLDOWN else "projet"
        index = DRILLDOWN.index(current)
        return {
            "current": current,
            "next": DRILLDOWN[index + 1] if index + 1 < len(DRILLDOWN) else None,
            "path": DRILLDOWN,
        }

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))
