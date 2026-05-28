from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


READY_SCENARIO_STATUSES = {"READY", "SIMULATED", "VALIDATED"}
READY_PROCUREMENT_STATUSES = {"READY", "EXPORTABLE"}
VALIDATION_STATUSES = {
    "PENDING",
    "VALIDATED",
    "REJECTED",
    "TO_ARBITRATE",
    "REVIEW_REQUIRED",
    "BLOCKED",
    "A_ARBITRER",
    "VALIDATION_DIRECTION",
    "VALIDE",
    "REFUSE",
    "COMMANDE",
    "EN_TRANSIT",
    "EN_DOUANE",
    "LIVRE",
    "RECEPTIONNE",
}
DECISION_VALUES = {
    "IMPORT",
    "LOCAL",
    "HYBRID",
    "HYBRIDE",
    "MIXTE",
    "A_ARBITRER",
    "VALIDATION_DIRECTION",
    "VALIDE",
    "REFUSE",
    "COMMANDE",
    "EN_TRANSIT",
    "EN_DOUANE",
    "LIVRE",
    "RECEPTIONNE",
    "REVIEW_REQUIRED",
    "BLOCKED",
}


def normalize_decision(value: Any) -> str:
    decision = str(value or "").strip().upper()
    if decision in {"MIXTE"}:
        return "HYBRIDE"
    if decision in {"HYBRID"}:
        return "HYBRID"
    if decision in DECISION_VALUES:
        return decision
    return "REVIEW_REQUIRED"


def normalize_validation_status(value: Any) -> str:
    status = str(value or "").strip().upper()
    return status if status in VALIDATION_STATUSES else "PENDING"


def risk_level_from_score(value: Any) -> str:
    try:
        score = float(value or 0)
    except (TypeError, ValueError):
        score = 0
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def summarize_procurement_decision_counts(counts: dict[str, int], scenario_ready: bool = True) -> dict[str, Any]:
    if not scenario_ready:
        return {
            "status": "BLOCKED",
            "is_ready": False,
            "message": "Lancez un scenario avant de preparer l'approvisionnement.",
        }

    total = int(counts.get("decisions_count") or 0)
    if total <= 0:
        return {
            "status": "REQUIRED",
            "is_ready": False,
            "message": "Le scenario est disponible. Preparez les arbitrages achat.",
        }

    validated = int(counts.get("validated_decisions_count") or 0)
    blocked = int(counts.get("blocked_decisions_count") or 0)
    critical_pending = int(counts.get("critical_pending_count") or 0)
    pending = int(counts.get("pending_decisions_count") or 0)
    review = int(counts.get("review_required_count") or 0)
    to_arbitrate = int(counts.get("to_arbitrate_count") or 0)

    completed = validated >= total and pending == 0 and review == 0 and to_arbitrate == 0 and critical_pending == 0

    if blocked > 0:
        status = "REVIEW_REQUIRED"
        message = "Des decisions achat sont bloquees ou doivent etre arbitrees."
    elif completed:
        status = "READY"
        message = "Approvisionnement pret pour preparation chantier."
    elif review > 0 or to_arbitrate > 0 or pending > 0:
        status = "REVIEW_REQUIRED"
        message = "Arbitrages achat generes. Validation humaine requise avant preparation chantier."
    else:
        status = "REVIEW_REQUIRED"
        message = "Decisions achat a valider."

    return {
        "status": status,
        "is_ready": status in READY_PROCUREMENT_STATUSES,
        "message": message,
    }


def _scenario_filters(project_id: int, scenario_id: str | None = None, run_id: str | None = None, prefix: str = "") -> tuple[str, dict[str, Any]]:
    params: dict[str, Any] = {"project_id": project_id}
    filters = [f"{prefix}project_id = :project_id" if prefix else "project_id = :project_id"]
    if scenario_id:
        filters.append(f"{prefix}scenario_id = :scenario_id" if prefix else "scenario_id = :scenario_id")
        params["scenario_id"] = scenario_id
    if run_id:
        filters.append("fs.run_id = CAST(:run_id AS uuid)")
        params["run_id"] = run_id
    return " AND ".join(filters), params


def procurement_decision_status(
    db: Session,
    project_id: int,
    scenario_id: str | None = None,
    scenario_ready: bool = True,
) -> dict[str, Any] | None:
    where_sql, params = _scenario_filters(project_id, scenario_id, prefix="pd.")
    try:
        row = db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) AS decisions_count,
                    COUNT(*) FILTER (WHERE validation_status IN ('VALIDATED', 'VALIDE')) AS validated_decisions_count,
                    COUNT(*) FILTER (WHERE validation_status = 'PENDING') AS pending_decisions_count,
                    COUNT(*) FILTER (WHERE validation_status IN ('TO_ARBITRATE', 'A_ARBITRER', 'VALIDATION_DIRECTION')) AS to_arbitrate_count,
                    COUNT(*) FILTER (WHERE validation_status = 'REVIEW_REQUIRED') AS review_required_count,
                    COUNT(*) FILTER (WHERE validation_status = 'BLOCKED') AS blocked_decisions_count,
                    COUNT(*) FILTER (
                        WHERE risk_level IN ('HIGH', 'CRITICAL')
                          AND validation_status NOT IN ('VALIDATED', 'VALIDE', 'REJECTED', 'REFUSE')
                    ) AS critical_pending_count,
                    COUNT(*) FILTER (
                        WHERE COALESCE(NULLIF(validated_decision, ''), NULLIF(proposed_decision, ''), ai_decision, purchase_mode) = 'IMPORT'
                    ) AS import_lines_count,
                    COUNT(*) FILTER (
                        WHERE COALESCE(NULLIF(validated_decision, ''), NULLIF(proposed_decision, ''), ai_decision, purchase_mode) = 'LOCAL'
                    ) AS local_lines_count,
                    COUNT(*) FILTER (
                        WHERE COALESCE(NULLIF(validated_decision, ''), NULLIF(proposed_decision, ''), ai_decision, purchase_mode) IN ('HYBRID', 'HYBRIDE', 'MIXTE')
                    ) AS hybrid_lines_count
                FROM procurement_decisions pd
                WHERE {where_sql}
                """
            ),
            params,
        ).mappings().first()
    except SQLAlchemyError:
        return None

    counts = {key: int(row.get(key) or 0) for key in row.keys()} if row else {}
    summary = summarize_procurement_decision_counts(counts, scenario_ready=scenario_ready)
    return {
        **summary,
        **counts,
        "export_available": summary["status"] in READY_PROCUREMENT_STATUSES,
        "source": "procurement_decisions",
    }


def list_procurement_decisions(
    db: Session,
    project_id: int,
    scenario_id: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[dict[str, Any]]:
    where_sql, params = _scenario_filters(project_id, scenario_id, prefix="pd.")
    params.update({"limit": limit, "offset": offset})
    rows = db.execute(
        text(
            f"""
            SELECT
                id,
                project_id,
                scenario_id,
                simulation_line_id,
                lot,
                family,
                designation,
                quantity,
                unit,
                ai_decision,
                ai_score,
                ai_reason,
                proposed_decision,
                validated_decision,
                validation_status,
                supplier_selected,
                supplier_country,
                purchase_mode,
                estimated_local_cost,
                estimated_import_cost,
                estimated_savings,
                risk_level,
                validator_name,
                validator_id,
                validated_at,
                comment,
                created_at,
                updated_at
            FROM procurement_decisions pd
            WHERE {where_sql}
            ORDER BY id
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


def bootstrap_procurement_decisions_from_simulation(
    db: Session,
    project_id: int,
    scenario_id: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    where_parts = ["fs.projet_id = :project_id"]
    params: dict[str, Any] = {"project_id": project_id}
    if scenario_id:
        where_parts.append("fs.scenario_id = CAST(:scenario_id AS uuid)")
        params["scenario_id"] = scenario_id
    if run_id:
        where_parts.append("fs.run_id = CAST(:run_id AS uuid)")
        params["run_id"] = run_id

    result = db.execute(
        text(
            f"""
            INSERT INTO procurement_decisions (
                project_id,
                scenario_id,
                simulation_line_id,
                lot,
                family,
                designation,
                quantity,
                unit,
                ai_decision,
                ai_score,
                ai_reason,
                proposed_decision,
                validation_status,
                purchase_mode,
                estimated_local_cost,
                estimated_import_cost,
                estimated_savings,
                risk_level,
                created_at,
                updated_at
            )
            SELECT
                fs.projet_id,
                fs.scenario_id::text,
                fs.simulation_line_id,
                COALESCE(dl.lot, ''),
                COALESCE(df.famille, ''),
                COALESCE(fs.designation, ''),
                COALESCE(fs.quantite, 0),
                '',
                CASE
                    WHEN UPPER(COALESCE(fs.decision_import, '')) IN ('HYBRIDE', 'MIXTE') THEN 'HYBRID'
                    WHEN UPPER(COALESCE(fs.decision_import, '')) IN ('IMPORT', 'LOCAL', 'HYBRID', 'REVIEW_REQUIRED', 'BLOCKED') THEN UPPER(fs.decision_import)
                    ELSE 'REVIEW_REQUIRED'
                END,
                COALESCE(fs.decision_score, 0),
                COALESCE(fs.procurement_reason::text, '{{}}'),
                CASE
                    WHEN UPPER(COALESCE(fs.decision_type, '')) IN ('HYBRIDE', 'MIXTE') THEN 'HYBRID'
                    WHEN UPPER(COALESCE(fs.decision_type, '')) IN ('IMPORT', 'LOCAL', 'HYBRID', 'REVIEW_REQUIRED', 'BLOCKED') THEN UPPER(fs.decision_type)
                    WHEN UPPER(COALESCE(fs.decision_import, '')) IN ('HYBRIDE', 'MIXTE') THEN 'HYBRID'
                    WHEN UPPER(COALESCE(fs.decision_import, '')) IN ('IMPORT', 'LOCAL', 'HYBRID', 'REVIEW_REQUIRED', 'BLOCKED') THEN UPPER(fs.decision_import)
                    ELSE 'REVIEW_REQUIRED'
                END,
                CASE
                    WHEN COALESCE(fs.global_risk_score, 0) >= 80 THEN 'REVIEW_REQUIRED'
                    WHEN UPPER(COALESCE(fs.decision_import, '')) IN ('HYBRIDE', 'HYBRID', 'MIXTE')
                      OR UPPER(COALESCE(fs.decision_type, '')) IN ('HYBRIDE', 'HYBRID', 'MIXTE')
                    THEN 'TO_ARBITRATE'
                    ELSE 'PENDING'
                END,
                CASE
                    WHEN UPPER(COALESCE(fs.decision_import, '')) IN ('HYBRIDE', 'MIXTE') THEN 'HYBRID'
                    WHEN UPPER(COALESCE(fs.decision_import, '')) IN ('IMPORT', 'LOCAL', 'HYBRID') THEN UPPER(fs.decision_import)
                    ELSE ''
                END,
                COALESCE(fs.capex_local, 0),
                COALESCE(fs.capex_import, 0),
                COALESCE(fs.economie, 0),
                CASE
                    WHEN COALESCE(fs.global_risk_score, 0) >= 80 THEN 'CRITICAL'
                    WHEN COALESCE(fs.global_risk_score, 0) >= 60 THEN 'HIGH'
                    WHEN COALESCE(fs.global_risk_score, 0) >= 35 THEN 'MEDIUM'
                    ELSE 'LOW'
                END,
                now(),
                now()
            FROM fact_simulation fs
            LEFT JOIN dim_lot dl ON dl.lot_id = fs.lot_id
            LEFT JOIN dim_famille df ON df.famille_id = fs.famille_id
            WHERE {" AND ".join(where_parts)}
              AND COALESCE(fs.designation, '') <> ''
            ON CONFLICT (project_id, scenario_id, simulation_line_id) DO NOTHING
            """
        ),
        params,
    )
    inserted = int(result.rowcount or 0)
    db.commit()
    status = procurement_decision_status(db, project_id, scenario_id=scenario_id, scenario_ready=True) or {}
    return {"inserted_count": inserted, "status": status}


def update_procurement_decision(
    db: Session,
    project_id: int,
    decision_id: int,
    values: dict[str, Any],
) -> dict[str, Any] | None:
    allowed = {
        "validated_decision",
        "validation_status",
        "supplier_selected",
        "supplier_country",
        "purchase_mode",
        "validator_name",
        "validator_id",
        "comment",
    }
    updates = {key: value for key, value in values.items() if key in allowed}
    if "validation_status" in updates:
        updates["validation_status"] = normalize_validation_status(updates["validation_status"])
    if "validated_decision" in updates:
        updates["validated_decision"] = normalize_decision(updates["validated_decision"])
    if "purchase_mode" in updates:
        updates["purchase_mode"] = normalize_decision(updates["purchase_mode"])

    if updates.get("validation_status") in {"VALIDATED", "VALIDE", "REJECTED", "REFUSE", "TO_ARBITRATE", "A_ARBITRER", "VALIDATION_DIRECTION"}:
        updates["validated_at"] = datetime.now(timezone.utc)

    if not updates:
        row = db.execute(
            text("SELECT * FROM procurement_decisions WHERE id = :id AND project_id = :project_id"),
            {"id": decision_id, "project_id": project_id},
        ).mappings().first()
        return dict(row) if row else None

    set_sql = ", ".join([f"{key} = :{key}" for key in updates.keys()])
    row = db.execute(
        text(
            f"""
            UPDATE procurement_decisions
            SET {set_sql}, updated_at = now()
            WHERE id = :id AND project_id = :project_id
            RETURNING
                id,
                project_id,
                scenario_id,
                simulation_line_id,
                lot,
                family,
                designation,
                quantity,
                unit,
                ai_decision,
                ai_score,
                ai_reason,
                proposed_decision,
                validated_decision,
                validation_status,
                supplier_selected,
                supplier_country,
                purchase_mode,
                estimated_local_cost,
                estimated_import_cost,
                estimated_savings,
                risk_level,
                validator_name,
                validator_id,
                validated_at,
                comment,
                created_at,
                updated_at
            """
        ),
        {**updates, "id": decision_id, "project_id": project_id},
    ).mappings().first()
    db.commit()
    return dict(row) if row else None
