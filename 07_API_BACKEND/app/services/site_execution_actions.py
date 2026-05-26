from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


READY_PROCUREMENT_STATUSES = {"READY", "EXPORTABLE"}
READY_EXECUTION_STATUSES = {"READY", "ACTIVE", "AT_RISK"}
ACTION_STATUSES = {"TO_DO", "IN_PROGRESS", "DONE", "AT_RISK", "BLOCKED", "CANCELLED"}
ACTION_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def normalize_action_status(value: Any) -> str:
    status = str(value or "").strip().upper()
    return status if status in ACTION_STATUSES else "TO_DO"


def normalize_priority(value: Any) -> str:
    priority = str(value or "").strip().upper()
    return priority if priority in ACTION_PRIORITIES else "MEDIUM"


def summarize_execution_action_counts(counts: dict[str, int], procurement_ready: bool = True) -> dict[str, Any]:
    if not procurement_ready:
        return {
            "status": "BLOCKED",
            "is_ready": False,
            "message": "Preparez l'approvisionnement avant de suivre l'execution chantier.",
        }

    total = int(counts.get("actions_count") or 0)
    if total <= 0:
        return {
            "status": "REQUIRED",
            "is_ready": False,
            "message": "L'approvisionnement est pret. Preparez les actions chantier.",
        }

    blocked = int(counts.get("blocked_count") or 0)
    at_risk = int(counts.get("at_risk_count") or 0)
    open_count = int(counts.get("open_count") or 0)

    if blocked > 0 or at_risk > 0:
        return {
            "status": "AT_RISK",
            "is_ready": True,
            "message": "Execution prete avec alertes chantier a surveiller.",
        }

    if open_count > 0:
        return {
            "status": "READY",
            "is_ready": True,
            "message": "Execution prete pour suivi chantier.",
        }

    return {
        "status": "ACTIVE",
        "is_ready": True,
        "message": "Actions chantier traitees. Execution active.",
    }


def _scenario_filters(project_id: int, scenario_id: str | None = None, prefix: str = "") -> tuple[str, dict[str, Any]]:
    params: dict[str, Any] = {"project_id": project_id}
    filters = [f"{prefix}project_id = :project_id" if prefix else "project_id = :project_id"]
    if scenario_id:
        filters.append(f"{prefix}scenario_id = :scenario_id" if prefix else "scenario_id = :scenario_id")
        params["scenario_id"] = scenario_id
    return " AND ".join(filters), params


def execution_action_status(
    db: Session,
    project_id: int,
    scenario_id: str | None = None,
    procurement_ready: bool = True,
) -> dict[str, Any] | None:
    where_sql, params = _scenario_filters(project_id, scenario_id, prefix="sea.")
    try:
        row = db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) AS actions_count,
                    COUNT(*) FILTER (WHERE status NOT IN ('DONE', 'CANCELLED')) AS open_count,
                    COUNT(*) FILTER (WHERE status = 'DONE') AS done_count,
                    COUNT(*) FILTER (WHERE status = 'BLOCKED') AS blocked_count,
                    COUNT(*) FILTER (WHERE status = 'AT_RISK') AS at_risk_count,
                    COUNT(DISTINCT NULLIF(lot, '')) FILTER (
                        WHERE priority IN ('HIGH', 'CRITICAL') OR risk_level IN ('HIGH', 'CRITICAL')
                    ) AS critical_lots_count,
                    COUNT(*) FILTER (
                        WHERE action_type = 'DELIVERY' OR COALESCE(delivery_eta_days, 0) > 0
                    ) AS deliveries_to_watch_count,
                    COUNT(*) FILTER (WHERE COALESCE(delivery_eta_days, 0) > 0) AS eta_to_watch_count
                FROM site_execution_actions sea
                WHERE {where_sql}
                """
            ),
            params,
        ).mappings().first()
    except SQLAlchemyError:
        return None

    counts = {key: int(row.get(key) or 0) for key in row.keys()} if row else {}
    summary = summarize_execution_action_counts(counts, procurement_ready=procurement_ready)
    return {
        **summary,
        **counts,
        "source": "site_execution_actions",
    }


def list_site_execution_actions(
    db: Session,
    project_id: int,
    scenario_id: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[dict[str, Any]]:
    where_sql, params = _scenario_filters(project_id, scenario_id, prefix="sea.")
    params.update({"limit": limit, "offset": offset})
    rows = db.execute(
        text(
            f"""
            SELECT
                id,
                project_id,
                scenario_id,
                procurement_decision_id,
                simulation_line_id,
                batiment,
                niveau,
                appart,
                piece,
                type_zone,
                bim_object_id,
                ifc_guid,
                lot,
                family,
                designation,
                action_type,
                title,
                problem,
                impact,
                recommended_action,
                priority,
                risk_level,
                status,
                responsible_role,
                responsible_name,
                due_date,
                started_at,
                completed_at,
                delivery_eta_days,
                date_needed,
                delay_days,
                storage_impact,
                criticality_score,
                source,
                created_at,
                updated_at
            FROM site_execution_actions sea
            WHERE {where_sql}
            ORDER BY
                CASE priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
                id
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


def generate_site_execution_actions(
    db: Session,
    project_id: int,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    filters = ["pd.project_id = :project_id"]
    params: dict[str, Any] = {"project_id": project_id}
    if scenario_id:
        filters.append("pd.scenario_id = :scenario_id")
        params["scenario_id"] = scenario_id

    result = db.execute(
        text(
            f"""
            INSERT INTO site_execution_actions (
                project_id,
                scenario_id,
                procurement_decision_id,
                simulation_line_id,
                batiment,
                niveau,
                appart,
                piece,
                type_zone,
                bim_object_id,
                ifc_guid,
                lot,
                family,
                designation,
                action_type,
                title,
                problem,
                impact,
                recommended_action,
                priority,
                risk_level,
                status,
                responsible_role,
                delivery_eta_days,
                delay_days,
                storage_impact,
                criticality_score,
                source,
                created_at,
                updated_at
            )
            SELECT
                pd.project_id,
                pd.scenario_id,
                pd.id,
                pd.simulation_line_id,
                COALESCE(NULLIF(fm.batiment, ''), dbat.batiment, ''),
                COALESCE(NULLIF(fm.niveau, ''), dniv.niveau, ''),
                COALESCE(NULLIF(fm.appart, ''), ''),
                COALESCE(NULLIF(fm.piece, ''), ''),
                COALESCE(NULLIF(fm.type_zone, ''), ''),
                COALESCE(NULLIF(fm.bim_object_id, ''), ''),
                COALESCE(NULLIF(fm.ifc_guid, ''), ''),
                COALESCE(NULLIF(pd.lot, ''), ''),
                COALESCE(NULLIF(pd.family, ''), ''),
                COALESCE(NULLIF(pd.designation, ''), ''),
                CASE
                    WHEN UPPER(COALESCE(fs.delivery_risk, '')) NOT IN ('', 'FAIBLE', 'LOW')
                      OR COALESCE(fs.lead_time_total, 0) > 0 THEN 'DELIVERY'
                    WHEN COALESCE(fs.storage_cost, 0) > 0 THEN 'STORAGE'
                    WHEN COALESCE(fs.criticality_score, 0) >= 70 THEN 'RISK'
                    WHEN pd.validation_status <> 'VALIDATED' THEN 'PROCUREMENT'
                    ELSE 'PLANNING'
                END,
                CASE
                    WHEN UPPER(COALESCE(fs.delivery_risk, '')) NOT IN ('', 'FAIBLE', 'LOW')
                      OR COALESCE(fs.lead_time_total, 0) > 0 THEN 'Surveiller livraison chantier'
                    WHEN COALESCE(fs.storage_cost, 0) > 0 THEN 'Consolider stockage site'
                    WHEN COALESCE(fs.criticality_score, 0) >= 70 THEN 'Arbitrer risque chantier'
                    WHEN pd.validation_status <> 'VALIDATED' THEN 'Finaliser arbitrage achat'
                    ELSE 'Preparer planning chantier'
                END,
                CASE
                    WHEN pd.validation_status <> 'VALIDATED' THEN 'Validation achat incomplete.'
                    WHEN UPPER(COALESCE(fs.delivery_risk, '')) NOT IN ('', 'FAIBLE', 'LOW')
                      OR COALESCE(fs.lead_time_total, 0) > 0 THEN 'ETA ou risque livraison a surveiller.'
                    WHEN COALESCE(fs.storage_cost, 0) > 0 THEN 'Impact stockage a consolider.'
                    ELSE 'Action chantier a planifier.'
                END,
                CASE
                    WHEN COALESCE(fs.criticality_score, 0) >= 70 THEN 'Chemin critique ou lot sensible.'
                    WHEN COALESCE(fs.lead_time_total, 0) > 0 THEN 'Risque planning lie au delai fournisseur.'
                    WHEN COALESCE(fs.storage_cost, 0) > 0 THEN 'Risque de capacite stockage.'
                    ELSE 'Coordination achat / chantier requise.'
                END,
                CASE
                    WHEN pd.validation_status <> 'VALIDATED' THEN 'Valider la decision achat avant engagement chantier.'
                    WHEN UPPER(COALESCE(fs.delivery_risk, '')) NOT IN ('', 'FAIBLE', 'LOW')
                      OR COALESCE(fs.lead_time_total, 0) > 0 THEN 'Confirmer ETA, fournisseur et alternative locale si necessaire.'
                    WHEN COALESCE(fs.storage_cost, 0) > 0 THEN 'Planifier reception et zone de stockage.'
                    ELSE 'Affecter un responsable chantier et une echeance.'
                END,
                CASE
                    WHEN COALESCE(fs.criticality_score, 0) >= 80
                      OR UPPER(COALESCE(fs.delivery_risk, '')) IN ('CRITICAL', 'CRITIQUE') THEN 'CRITICAL'
                    WHEN COALESCE(fs.criticality_score, 0) >= 60
                      OR UPPER(COALESCE(fs.delivery_risk, '')) IN ('HIGH', 'ELEVE') THEN 'HIGH'
                    WHEN COALESCE(fs.criticality_score, 0) >= 35
                      OR COALESCE(fs.lead_time_total, 0) > 0
                      OR COALESCE(fs.storage_cost, 0) > 0 THEN 'MEDIUM'
                    ELSE 'LOW'
                END,
                CASE
                    WHEN COALESCE(fs.criticality_score, 0) >= 80
                      OR UPPER(COALESCE(fs.delivery_risk, '')) IN ('CRITICAL', 'CRITIQUE') THEN 'CRITICAL'
                    WHEN COALESCE(fs.criticality_score, 0) >= 60
                      OR UPPER(COALESCE(fs.delivery_risk, '')) IN ('HIGH', 'ELEVE') THEN 'HIGH'
                    WHEN COALESCE(fs.criticality_score, 0) >= 35
                      OR COALESCE(fs.lead_time_total, 0) > 0
                      OR COALESCE(fs.storage_cost, 0) > 0 THEN 'MEDIUM'
                    ELSE 'LOW'
                END,
                CASE
                    WHEN pd.validation_status <> 'VALIDATED' THEN 'BLOCKED'
                    WHEN COALESCE(fs.criticality_score, 0) >= 70
                      OR UPPER(COALESCE(fs.delivery_risk, '')) IN ('HIGH', 'ELEVE', 'CRITICAL', 'CRITIQUE') THEN 'AT_RISK'
                    ELSE 'TO_DO'
                END,
                CASE
                    WHEN pd.validation_status <> 'VALIDATED' THEN 'Responsable achat'
                    WHEN COALESCE(fs.lead_time_total, 0) > 0 THEN 'Responsable chantier'
                    ELSE 'Conducteur travaux'
                END,
                COALESCE(fs.lead_time_total, 0),
                COALESCE(fs.lead_time_total, 0),
                COALESCE(fs.storage_cost, 0),
                COALESCE(fs.criticality_score, 0),
                'procurement_decisions',
                now(),
                now()
            FROM procurement_decisions pd
            LEFT JOIN fact_simulation fs
              ON fs.projet_id = pd.project_id
             AND fs.simulation_line_id = pd.simulation_line_id
             AND (pd.scenario_id IS NULL OR fs.scenario_id::text = pd.scenario_id)
            LEFT JOIN dim_batiment dbat ON dbat.batiment_id = fs.batiment_id
            LEFT JOIN dim_niveau dniv ON dniv.niveau_id = fs.niveau_id
            LEFT JOIN fact_metre fm ON fm.id_ligne = fs.id_ligne
            WHERE {" AND ".join(filters)}
              AND COALESCE(pd.designation, '') <> ''
              AND (
                pd.validation_status = 'VALIDATED'
                OR pd.validation_status IN ('REVIEW_REQUIRED', 'TO_ARBITRATE', 'BLOCKED')
              )
            ON CONFLICT (project_id, scenario_id, procurement_decision_id, action_type) DO NOTHING
            """
        ),
        params,
    )
    inserted = int(result.rowcount or 0)
    db.commit()
    status = execution_action_status(db, project_id, scenario_id=scenario_id, procurement_ready=True) or {}
    return {"inserted_count": inserted, "status": status}


def update_site_execution_action(
    db: Session,
    project_id: int,
    action_id: int,
    values: dict[str, Any],
) -> dict[str, Any] | None:
    allowed = {
        "status",
        "responsible_name",
        "responsible_role",
        "due_date",
        "recommended_action",
    }
    updates = {key: value for key, value in values.items() if key in allowed}
    if "status" in updates:
        updates["status"] = normalize_action_status(updates["status"])
        if updates["status"] == "IN_PROGRESS":
            updates["started_at"] = datetime.now(timezone.utc)
        if updates["status"] == "DONE":
            updates["completed_at"] = datetime.now(timezone.utc)

    if not updates:
        row = db.execute(
            text("SELECT * FROM site_execution_actions WHERE id = :id AND project_id = :project_id"),
            {"id": action_id, "project_id": project_id},
        ).mappings().first()
        return dict(row) if row else None

    set_sql = ", ".join([f"{key} = :{key}" for key in updates.keys()])
    row = db.execute(
        text(
            f"""
            UPDATE site_execution_actions
            SET {set_sql}, updated_at = now()
            WHERE id = :id AND project_id = :project_id
            RETURNING *
            """
        ),
        {**updates, "id": action_id, "project_id": project_id},
    ).mappings().first()
    db.commit()
    return dict(row) if row else None
