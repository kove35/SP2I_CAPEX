from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class ScenarioSnapshotRepository:
    """Repository PostgreSQL pour les snapshots et l'intelligence des scenarios."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _normalize_scenario_id(self, scenario_id: str) -> str:
        return str(UUID(scenario_id.replace("scenario_", ""))) if scenario_id.startswith("scenario_") else str(UUID(scenario_id))

    def list_scenario_history(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT
                    ds.scenario_id::text AS scenario_id,
                    ds.scenario_nom,
                    ds.scenario_type,
                    ds.created_at,
                    ds.updated_at,
                    COUNT(fs.simulation_line_id) AS nb_lignes,
                    COALESCE(SUM(fs.capex_local), 0) AS capex_local,
                    COALESCE(SUM(fs.capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(fs.economie), 0) AS economie_nette,
                    ROUND(COALESCE(AVG(fs.risk_score), 0)::numeric, 2) AS risk_score_average,
                    ROUND(COALESCE(AVG(fs.lead_time_score), 0)::numeric, 2) AS lead_time_score_average,
                    ROUND(COALESCE(AVG(fs.cashflow_score), 0)::numeric, 2) AS cashflow_score_average,
                    ROUND(COALESCE(AVG(fs.moq_risk_score), 0)::numeric, 2) AS moq_risk_score_average,
                    ROUND(COALESCE(AVG(fs.complexity_score), 0)::numeric, 2) AS complexity_score_average,
                    ROUND(COALESCE(AVG(fs.fill_rate), 0)::numeric, 4) AS fill_rate_average,
                    ROUND(COALESCE(AVG(fs.lead_time_total), 0)::numeric, 2) AS lead_time_total_average,
                    ROUND(COALESCE(AVG(fs.storage_cost), 0)::numeric, 2) AS storage_cost_average
                FROM dim_scenario ds
                LEFT JOIN fact_simulation fs ON ds.scenario_id = fs.scenario_id
                GROUP BY ds.scenario_id, ds.scenario_nom, ds.scenario_type, ds.created_at, ds.updated_at
                ORDER BY ds.created_at DESC
                LIMIT :limit OFFSET :offset
                """,
            ),
            {"limit": limit, "offset": offset},
        ).mappings().all()
        return [dict(row) for row in rows]

    def get_scenario_snapshot(self, scenario_id: str, limit: int = 500, offset: int = 0) -> dict[str, Any]:
        scenario_uuid = self._normalize_scenario_id(scenario_id)
        scenario = self.db.execute(
            text(
                """
                SELECT
                    ds.scenario_id::text AS scenario_id,
                    ds.scenario_nom,
                    ds.scenario_type,
                    ds.description,
                    ds.parameters_json,
                    ds.created_by,
                    ds.created_at,
                    ds.updated_at
                FROM dim_scenario ds
                WHERE ds.scenario_id = CAST(:scenario_id AS uuid)
                """,
            ),
            {"scenario_id": scenario_uuid},
        ).mappings().first()
        if not scenario:
            return {}

        lines = self.db.execute(
            text(
                """
                SELECT
                    fs.*
                FROM fact_simulation fs
                WHERE fs.scenario_id = CAST(:scenario_id AS uuid)
                ORDER BY fs.simulation_line_id
                LIMIT :limit OFFSET :offset
                """,
            ),
            {"scenario_id": scenario_uuid, "limit": limit, "offset": offset},
        ).mappings().all()

        return {
            "scenario": dict(scenario),
            "lines": [dict(row) for row in lines],
        }

    def get_scenario_aggregates(self, scenario_id: str) -> dict[str, Any]:
        scenario_uuid = self._normalize_scenario_id(scenario_id)
        row = self.db.execute(
            text(
                """
                SELECT
                    ds.scenario_id::text AS scenario_id,
                    ds.scenario_nom,
                    ds.scenario_type,
                    COALESCE(SUM(fs.capex_local), 0) AS capex_local,
                    COALESCE(SUM(fs.capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(fs.economie), 0) AS economie_nette,
                    ROUND(COALESCE(AVG(fs.decision_score), 0)::numeric, 2) AS decision_score_average,
                    ROUND(COALESCE(AVG(fs.risk_score), 0)::numeric, 2) AS risk_score_average,
                    ROUND(COALESCE(AVG(fs.lead_time_score), 0)::numeric, 2) AS lead_time_score_average,
                    ROUND(COALESCE(AVG(fs.cashflow_score), 0)::numeric, 2) AS cashflow_score_average,
                    ROUND(COALESCE(AVG(fs.moq_risk_score), 0)::numeric, 2) AS moq_risk_score_average,
                    ROUND(COALESCE(AVG(fs.complexity_score), 0)::numeric, 2) AS complexity_score_average,
                    ROUND(COALESCE(AVG(fs.fill_rate), 0)::numeric, 4) AS fill_rate_average,
                    ROUND(COALESCE(AVG(fs.lead_time_total), 0)::numeric, 2) AS lead_time_total_average,
                    ROUND(COALESCE(AVG(fs.storage_cost), 0)::numeric, 2) AS storage_cost_average,
                    COUNT(fs.simulation_line_id) AS nb_lignes
                FROM dim_scenario ds
                LEFT JOIN fact_simulation fs ON ds.scenario_id = fs.scenario_id
                WHERE ds.scenario_id = CAST(:scenario_id AS uuid)
                GROUP BY ds.scenario_id, ds.scenario_nom, ds.scenario_type
                """,
            ),
            {"scenario_id": scenario_uuid},
        ).mappings().first()
        return dict(row) if row else {}

    def compare_scenarios(self, scenario_ids: list[str]) -> list[dict[str, Any]]:
        normalized_ids = [self._normalize_scenario_id(sid) for sid in scenario_ids]
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    ds.scenario_id::text AS scenario_id,
                    ds.scenario_nom,
                    ds.scenario_type,
                    COALESCE(SUM(fs.capex_local), 0) AS capex_local,
                    COALESCE(SUM(fs.capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(fs.economie), 0) AS economie_nette,
                    ROUND(COALESCE(AVG(fs.decision_score), 0)::numeric, 2) AS decision_score_average,
                    ROUND(COALESCE(AVG(fs.risk_score), 0)::numeric, 2) AS risk_score_average,
                    ROUND(COALESCE(AVG(fs.lead_time_score), 0)::numeric, 2) AS lead_time_score_average,
                    ROUND(COALESCE(AVG(fs.cashflow_score), 0)::numeric, 2) AS cashflow_score_average,
                    ROUND(COALESCE(AVG(fs.moq_risk_score), 0)::numeric, 2) AS moq_risk_score_average,
                    ROUND(COALESCE(AVG(fs.fill_rate), 0)::numeric, 4) AS fill_rate_average,
                    COUNT(fs.simulation_line_id) AS nb_lignes
                FROM dim_scenario ds
                LEFT JOIN fact_simulation fs ON ds.scenario_id = fs.scenario_id
                WHERE ds.scenario_id IN ({', '.join(['CAST(:id_%d AS uuid)' % i for i in range(len(normalized_ids))])})
                GROUP BY ds.scenario_id, ds.scenario_nom, ds.scenario_type
                ORDER BY ds.created_at DESC
                """,
            ),
            {f"id_{i}": scenario_id for i, scenario_id in enumerate(normalized_ids)},
        ).mappings().all()
        return [dict(row) for row in rows]

    def get_scenario_timeline(self, scenario_id: str, limit: int = 100) -> list[dict[str, Any]]:
        scenario_uuid = self._normalize_scenario_id(scenario_id)
        rows = self.db.execute(
            text(
                """
                SELECT
                    DATE_TRUNC('day', COALESCE(fs.created_at, now()))::date AS periode,
                    COUNT(*) AS nb_lignes,
                    COALESCE(SUM(fs.capex_optimise), 0) AS capex_optimise,
                    COALESCE(SUM(fs.economie), 0) AS economie_nette,
                    ROUND(COALESCE(AVG(fs.decision_score), 0)::numeric, 2) AS decision_score_average,
                    ROUND(COALESCE(AVG(fs.risk_score), 0)::numeric, 2) AS risk_score_average
                FROM fact_simulation fs
                WHERE fs.scenario_id = CAST(:scenario_id AS uuid)
                GROUP BY DATE_TRUNC('day', COALESCE(fs.created_at, now()))::date
                ORDER BY periode
                LIMIT :limit
                """,
            ),
            {"scenario_id": scenario_uuid, "limit": limit},
        ).mappings().all()
        return [dict(row) for row in rows]
