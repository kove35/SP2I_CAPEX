from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analytics.schemas import AnalyticsQuery
from app.analytics.utils.display_text import normalize_display_text


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
    "decision_import",
}

DRILLDOWN = ["projet", "batiment", "niveau", "lot", "famille", "article"]


class AnalyticsRepository:
    """Repository SQL optimise pour les dashboards React/Power BI-like."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def kpis(self, query: AnalyticsQuery) -> dict[str, Any]:
        where_sql, params = self._where(query)
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
                    COUNT(*) AS nb_lignes
                FROM fact_metre
                {where_sql}
                """
            ),
            params,
        ).mappings().one()
        return dict(row)

    def table(self, query: AnalyticsQuery) -> tuple[list[dict[str, Any]], int]:
        where_sql, params = self._where(query)
        limit = query.page_size
        offset = (query.page - 1) * query.page_size
        order_column = query.order_by if query.order_by in ALLOWED_ORDER else "capex_local"
        order_dir = "ASC" if query.order_dir == "asc" else "DESC"

        total = self.db.execute(text(f"SELECT COUNT(*) FROM fact_metre {where_sql}"), params).scalar_one()
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    id_ligne,
                    designation,
                    lot,
                    famille,
                    batiment,
                    niveau,
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
                FROM fact_metre
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
        group_column = ALLOWED_GROUPS.get(group_key, ALLOWED_GROUPS[default_group])
        where_sql, params = self._where(query)
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(CAST({group_column} AS text), 'NON_RENSEIGNE') AS label,
                    COALESCE(SUM(capex_local), 0) AS capex_brut,
                    COALESCE(SUM(capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(economie), 0) AS economie_nette,
                    COUNT(*) AS nb_lignes
                FROM fact_metre
                {where_sql}
                GROUP BY COALESCE(CAST({group_column} AS text), 'NON_RENSEIGNE')
                ORDER BY capex_brut DESC
                LIMIT 50
                """
            ),
            params,
        ).mappings().all()
        return [dict(row) for row in rows]

    def heatmap(self, query: AnalyticsQuery) -> list[dict[str, Any]]:
        where_sql, params = self._where(query)
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
                    COALESCE(famille, 'default') AS famille,
                    COALESCE(SUM(capex_optimise), 0) AS value,
                    COUNT(*) AS nb_lignes
                FROM fact_metre
                {where_sql}
                GROUP BY COALESCE(lot, 'NON_RENSEIGNE'), COALESCE(famille, 'default')
                ORDER BY value DESC
                LIMIT 200
                """
            ),
            params,
        ).mappings().all()
        return [dict(row) for row in rows]

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
        where_sql, params = self._where(query)
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    date_trunc('day', COALESCE(date_import, created_at))::date AS periode,
                    COALESCE(SUM(capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(economie), 0) AS economie_nette,
                    COUNT(*) AS nb_lignes
                FROM fact_metre
                {where_sql}
                GROUP BY date_trunc('day', COALESCE(date_import, created_at))::date
                ORDER BY periode
                """
            ),
            params,
        ).mappings().all()
        return [dict(row) for row in rows]

    def filter_options(self) -> dict[str, list[str]]:
        """Valeurs distinctes exposees au cockpit React pour les dropdowns BI."""
        fields = {
            "batiments": "batiment",
            "niveaux": "niveau",
            "lots": "lot",
            "familles": "famille",
            "import_local": "decision_import",
        }
        result: dict[str, list[str]] = {}
        for key, column in fields.items():
            rows = self.db.execute(
                text(
                    f"""
                    SELECT DISTINCT {column} AS value
                    FROM fact_metre
                    WHERE {column} IS NOT NULL AND TRIM(CAST({column} AS text)) <> ''
                    ORDER BY {column}
                    LIMIT 500
                    """
                )
            ).scalars().all()
            result[key] = [normalize_display_text(str(value)) for value in rows if value]
        return result

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
        fact_count = int(self.db.execute(text("SELECT COUNT(*) FROM fact_metre")).scalar_one() or 0)
        columns = self.db.execute(
            text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'fact_metre'
                ORDER BY ordinal_position
                """
            )
        ).mappings().all()
        sums = self.db.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(quantite), 0) AS quantite_total,
                    COALESCE(SUM(prix_total_ht), 0) AS prix_total_ht_total,
                    COALESCE(SUM(pu_local), 0) AS pu_local_total,
                    COALESCE(SUM(capex_local), 0) AS capex_local_total,
                    COALESCE(SUM(capex_optimise), 0) AS capex_optimise_total,
                    COALESCE(SUM(economie), 0) AS economie_total,
                    SUM(CASE WHEN quantite IS NULL OR quantite <= 0 THEN 1 ELSE 0 END) AS lignes_quantite_invalide,
                    SUM(CASE WHEN capex_local IS NULL OR capex_local <= 0 THEN 1 ELSE 0 END) AS lignes_capex_local_invalide,
                    SUM(CASE WHEN lot IS NULL OR lot = '' THEN 1 ELSE 0 END) AS lignes_sans_lot
                FROM fact_metre
                """
            )
        ).mappings().one()
        preview = self.db.execute(
            text(
                """
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
                FROM fact_metre
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
        if int(sums["lignes_capex_local_invalide"] or 0) > 0:
            warnings.append("Certaines lignes ont capex_local vide ou nul.")
        if int(sums["lignes_sans_lot"] or 0) > 0:
            warnings.append("Certaines lignes n'ont pas de lot.")

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

    def _where(self, query: AnalyticsQuery) -> tuple[str, dict[str, Any]]:
        filters = query.filters
        clauses: list[str] = []
        params: dict[str, Any] = {}

        for field in ("batiment", "niveau", "lot", "famille"):
            value = getattr(filters, field)
            if value:
                clauses.append(f"LOWER({field}) LIKE LOWER(:{field})")
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

    @staticmethod
    def drilldown_path(level: str | None) -> dict[str, Any]:
        current = level if level in DRILLDOWN else "projet"
        index = DRILLDOWN.index(current)
        return {
            "current": current,
            "next": DRILLDOWN[index + 1] if index + 1 < len(DRILLDOWN) else None,
            "path": DRILLDOWN,
        }
