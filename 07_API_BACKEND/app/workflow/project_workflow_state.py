from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


PROJECT_DONE_STATUSES = {"CONFIGURED", "ACTIVE", "DONE"}
PROCUREMENT_READY_STATUSES = {"PRET", "READY", "EXPORTABLE"}
EXECUTION_READY_STATUSES = {"PRETE", "READY", "ACTIVE", "A_RISQUE", "AT_RISK"}


@dataclass(frozen=True)
class WorkflowMetrics:
    setup_configured: bool = False
    fact_metre_rows: int = 0
    fact_metre_project_rows: int = 0
    capex_local_total: float = 0
    latest_trust_score: int = 0
    latest_file_name: str = ""
    latest_audit_rows: int = 0
    latest_fact_rows: int = 0
    simulation_rows: int = 0
    simulation_project_rows: int = 0
    procurement_decisions_count: int = 0
    procurement_fact_decisions_count: int = 0
    execution_actions_count: int = 0
    execution_blocked_count: int = 0
    execution_at_risk_count: int = 0
    last_dqe_certification: datetime | None = None
    last_fact_metre_sync: datetime | None = None
    sync_status: str = "OUT_OF_SYNC"
    sync_delta_rows: int = 0
    sync_delta_capex: float = 0


def _safe_scalar(db: Session, sql: str, params: dict[str, Any] | None = None, default: Any = 0) -> Any:
    try:
        value = db.execute(text(sql), params or {}).scalar_one_or_none()
    except Exception:
        return default
    return default if value is None else value


def _safe_mapping(db: Session, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        row = db.execute(text(sql), params or {}).mappings().first()
    except Exception:
        return {}
    return dict(row) if row else {}


def _count_fact_rows(db: Session, project_id: int) -> tuple[int, int]:
    project_rows = int(
        _safe_scalar(
            db,
            "SELECT COUNT(*) FROM fact_metre WHERE projet_id = :project_id",
            {"project_id": project_id},
            0,
        )
        or 0
    )
    total_rows = int(_safe_scalar(db, "SELECT COUNT(*) FROM fact_metre", default=0) or 0)
    return project_rows, project_rows or total_rows


def _sum_fact_capex(db: Session, project_id: int) -> float:
    project_total = float(
        _safe_scalar(
            db,
            """
            SELECT COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)
            FROM fact_metre
            WHERE projet_id = :project_id
            """,
            {"project_id": project_id},
            0,
        )
        or 0
    )
    if project_total > 0:
        return project_total
    return float(
        _safe_scalar(
            db,
            "SELECT COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0) FROM fact_metre",
            default=0,
        )
        or 0
    )


def _latest_audit_metrics(db: Session) -> dict[str, Any]:
    return _safe_mapping(
        db,
        """
        SELECT fichier,
               score_qualite,
               lignes_parsees,
               lignes_fact_metre,
               capex_source,
               capex_fact_metre,
               created_at
        FROM dqe_import_audit
        ORDER BY created_at DESC
        LIMIT 1
        """,
    )


def _current_fact_totals(db: Session) -> tuple[int, float, datetime | None]:
    total_rows = int(_safe_scalar(db, "SELECT COUNT(*) FROM fact_metre", default=0) or 0)
    total_capex = float(
        _safe_scalar(
            db,
            "SELECT COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0) FROM fact_metre",
            default=0,
        )
        or 0
    )
    last_sync = _safe_scalar(db, "SELECT MAX(updated_at) FROM fact_metre", default=None)
    return total_rows, total_capex, last_sync


def _compute_sync_validation(
    audit: dict[str, Any],
    total_rows: int,
    total_capex: float,
    last_sync: datetime | None,
) -> dict[str, Any]:
    if not audit:
        return {
            "last_dqe_certification": None,
            "last_fact_metre_sync": last_sync,
            "sync_status": "OUT_OF_SYNC",
            "sync_delta_rows": total_rows,
            "sync_delta_capex": total_capex,
        }

    expected_rows = int(audit.get("lignes_fact_metre") or 0)
    expected_capex = float(audit.get("capex_fact_metre") or 0)
    created_at = audit.get("created_at")
    row_match = total_rows == expected_rows
    capex_match = abs(total_capex - expected_capex) <= 1.0
    sync_after_cert = last_sync is not None and created_at is not None and last_sync >= created_at
    synced = row_match and capex_match and sync_after_cert
    return {
        "last_dqe_certification": created_at,
        "last_fact_metre_sync": last_sync,
        "sync_status": "SYNCED" if synced else "OUT_OF_SYNC",
        "sync_delta_rows": total_rows - expected_rows,
        "sync_delta_capex": total_capex - expected_capex,
    }


def _simulation_counts(db: Session, project_id: int) -> tuple[int, int]:
    project_rows = int(
        _safe_scalar(
            db,
            "SELECT COUNT(*) FROM fact_simulation WHERE projet_id = :project_id",
            {"project_id": project_id},
            0,
        )
        or 0
    )
    total_rows = int(_safe_scalar(db, "SELECT COUNT(*) FROM fact_simulation", default=0) or 0)
    return project_rows, project_rows or total_rows


def _procurement_decision_count(db: Session, project_id: int) -> int:
    return int(
        _safe_scalar(
            db,
            "SELECT COUNT(*) FROM procurement_decisions WHERE project_id = :project_id",
            {"project_id": project_id},
            0,
        )
        or 0
    )


def _fact_procurement_decision_count(db: Session, project_id: int) -> int:
    project_rows = int(
        _safe_scalar(
            db,
            """
            SELECT COUNT(*)
            FROM fact_simulation
            WHERE projet_id = :project_id
              AND COALESCE(designation, '') <> ''
              AND COALESCE(decision_import, decision_type, '') <> ''
            """,
            {"project_id": project_id},
            0,
        )
        or 0
    )
    if project_rows > 0:
        return project_rows
    return int(
        _safe_scalar(
            db,
            """
            SELECT COUNT(*)
            FROM fact_metre
            WHERE COALESCE(designation, '') <> ''
              AND COALESCE(decision_import, decision, import_local, '') <> ''
            """,
            default=0,
        )
        or 0
    )


def _execution_counts(db: Session, project_id: int) -> dict[str, int]:
    row = _safe_mapping(
        db,
        """
        SELECT
            COUNT(*) AS actions_count,
            COUNT(*) FILTER (WHERE status = 'BLOCKED') AS blocked_count,
            COUNT(*) FILTER (WHERE status = 'AT_RISK') AS at_risk_count
        FROM site_execution_actions
        WHERE project_id = :project_id
        """,
        {"project_id": project_id},
    )
    return {key: int(row.get(key) or 0) for key in ("actions_count", "blocked_count", "at_risk_count")}


def collect_project_workflow_metrics(db: Session, project_id: int, setup_configured: bool = False) -> WorkflowMetrics:
    fact_project_rows, fact_rows = _count_fact_rows(db, project_id)
    simulation_project_rows, simulation_rows = _simulation_counts(db, project_id)
    audit = _latest_audit_metrics(db)
    total_rows, total_capex, last_sync = _current_fact_totals(db)
    sync = _compute_sync_validation(audit, total_rows, total_capex, last_sync)
    execution = _execution_counts(db, project_id)
    return WorkflowMetrics(
        setup_configured=setup_configured,
        fact_metre_rows=fact_rows,
        fact_metre_project_rows=fact_project_rows,
        capex_local_total=_sum_fact_capex(db, project_id),
        latest_trust_score=int(audit.get("score_qualite") or 0),
        latest_file_name=str(audit.get("fichier") or ""),
        latest_audit_rows=int(audit.get("lignes_parsees") or 0),
        latest_fact_rows=int(audit.get("lignes_fact_metre") or 0),
        simulation_rows=simulation_rows,
        simulation_project_rows=simulation_project_rows,
        procurement_decisions_count=_procurement_decision_count(db, project_id),
        procurement_fact_decisions_count=_fact_procurement_decision_count(db, project_id),
        execution_actions_count=execution["actions_count"],
        execution_blocked_count=execution["blocked_count"],
        execution_at_risk_count=execution["at_risk_count"],
        last_dqe_certification=sync["last_dqe_certification"],
        last_fact_metre_sync=sync["last_fact_metre_sync"],
        sync_status=sync["sync_status"],
        sync_delta_rows=sync["sync_delta_rows"],
        sync_delta_capex=sync["sync_delta_capex"],
    )


def compute_project_workflow_state_from_metrics(metrics: WorkflowMetrics) -> dict[str, Any]:
    sync_status = str(getattr(metrics, "sync_status", "OUT_OF_SYNC") or "OUT_OF_SYNC")
    dqe_synced = sync_status == "SYNCED"
    budget_synced = dqe_synced and metrics.capex_local_total > 0
    scenarios_ready = metrics.simulation_rows > 0
    procurement_ready = metrics.procurement_decisions_count > 0 or metrics.procurement_fact_decisions_count > 0

    workflow_state = "OUT_OF_SYNC" if not dqe_synced else "BUDGET_SYNCED"
    if dqe_synced and budget_synced and scenarios_ready:
        workflow_state = "SIMULATION_READY"

    if not dqe_synced:
        dqe = "A_SYNCHRONISER"
    else:
        dqe = "SYNCHRONISE"

    budget = "SYNCHRONISE" if budget_synced else "A_SYNCHRONISER"
    scenarios = "SIMULE" if scenarios_ready else "A_SIMULER"
    procurement = "PRET" if procurement_ready else ("A_PREPARER" if scenarios_ready else "BLOQUE")

    if procurement not in {"PRET"}:
        execution = "BLOQUEE"
    elif metrics.execution_actions_count <= 0:
        execution = "A_PREPARER"
    elif metrics.execution_blocked_count > 0 or metrics.execution_at_risk_count > 0:
        execution = "A_RISQUE"
    else:
        execution = "PRETE"

    trust_score = metrics.latest_trust_score
    if dqe_synced and trust_score <= 0:
        trust_score = 99

    done_steps = [
        metrics.setup_configured,
        dqe == "SYNCHRONISE",
        budget == "SYNCHRONISE",
        scenarios == "SIMULE",
        procurement == "PRET",
        execution in {"PRETE", "A_RISQUE"},
    ]

    def _serialize(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()

    return {
        "workflow_state": workflow_state,
        "dqe_synced": dqe_synced,
        "sync_status": sync_status,
        "sync_delta_rows": int(metrics.sync_delta_rows or 0),
        "sync_delta_capex": round(float(metrics.sync_delta_capex or 0), 2),
        "last_dqe_certification": _serialize(metrics.last_dqe_certification),
        "last_fact_metre_sync": _serialize(metrics.last_fact_metre_sync),
        "dqe": dqe,
        "budget": budget,
        "scenarios": scenarios,
        "procurement": procurement,
        "execution": execution,
        "trust_score": int(trust_score or 0),
        "progress_percent": round((sum(1 for value in done_steps if value) / len(done_steps)) * 100),
        "counts": {
            "fact_metre_rows": metrics.fact_metre_rows,
            "fact_metre_project_rows": metrics.fact_metre_project_rows,
            "simulation_rows": metrics.simulation_rows,
            "simulation_project_rows": metrics.simulation_project_rows,
            "procurement_decisions_count": metrics.procurement_decisions_count,
            "procurement_fact_decisions_count": metrics.procurement_fact_decisions_count,
            "execution_actions_count": metrics.execution_actions_count,
        },
        "source": {
            "dqe": "FACT_METRE" if dqe == "SYNCHRONISE" else "dqe_import_audit",
            "budget": "FACT_METRE",
            "scenarios": "fact_simulation",
            "procurement": "procurement_decisions" if metrics.procurement_decisions_count > 0 else "fact_simulation",
            "execution": "site_execution_actions",
        },
        "file_name": metrics.latest_file_name,
        "normalized_lines_count": metrics.fact_metre_rows or metrics.latest_fact_rows or metrics.latest_audit_rows,
        "capex_local_total": round(float(metrics.capex_local_total or 0), 2),
        "next_action": "Resynchroniser le DQE" if workflow_state == "OUT_OF_SYNC" else None,
    }


def build_project_workflow_state(db: Session, project_id: int, setup_status: str | None = None) -> dict[str, Any]:
    setup_configured = str(setup_status or "").upper() in PROJECT_DONE_STATUSES
    metrics = collect_project_workflow_metrics(db, project_id, setup_configured=setup_configured)
    state = compute_project_workflow_state_from_metrics(metrics)
    state["project_id"] = project_id
    state["setup"] = "CONFIGURE" if setup_configured else "A_COMPLETER"
    return state
