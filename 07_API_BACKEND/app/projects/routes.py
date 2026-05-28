from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth.models import User, WorkspaceMembership
from app.auth.routes import get_current_user
from app.services.project_report_export import build_project_report_pdf, generate_project_report_filename
from app.database import get_db
from app.projects.models import Project
from app.projects.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectSetupUpdate,
    ProjectWorkflowResponse,
    ProjectWorkflowStateResponse,
    ExecutionStatus,
    ProcurementDecisionBootstrapResponse,
    ProcurementDecisionListResponse,
    ProcurementDecisionOut,
    ProcurementDecisionStatus,
    ProcurementDecisionUpdate,
    ProcurementStatus,
    ScenarioStatus,
    SiteExecutionActionGenerateResponse,
    SiteExecutionActionListResponse,
    SiteExecutionActionOut,
    SiteExecutionActionStatus,
    SiteExecutionActionUpdate,
    SpatialSummaryResponse,
    WorkflowEventListResponse,
    WorkflowEventOut,
    WorkflowAction,
    WorkflowStep,
)
from app.services.procurement_decisions import (
    bootstrap_procurement_decisions_from_simulation,
    list_procurement_decisions,
    procurement_decision_status,
    update_procurement_decision,
)
from app.services.procurement_export import build_procurement_export_workbook, generate_procurement_export_filename
from app.services.site_execution_actions import (
    execution_action_status,
    generate_site_execution_actions,
    list_site_execution_actions,
    update_site_execution_action,
)
from app.spatial.services.spatial_intelligence import get_project_spatial_summary
from app.services.workflow_events import list_workflow_events, log_workflow_event
from app.services.service_pipeline import ServicePipeline
from app.governance.dqe_issue_builder import build_dqe_issue, summarize_dqe_issues
from app.workflow.project_workflow_state import build_project_workflow_state


router = APIRouter()


REQUIRED_SETUP_FIELDS = ("name", "client_name", "city", "country", "currency", "project_manager")


def _is_project_configured(project: Project) -> bool:
    return all(str(getattr(project, field, "") or "").strip() for field in REQUIRED_SETUP_FIELDS)


def _compute_setup_status(project: Project) -> str:
    return "CONFIGURED" if _is_project_configured(project) else "CONFIG_REQUIRED"


def _fetch_latest_dqe_audit(db: Session) -> Any | None:
    """
    Lit le dernier audit DQE en restant compatible avec les bases Render
    creees avant l'ajout de `lignes_rejetees`.
    """
    base_select = """
        SELECT fichier,
               score_qualite,
               lignes_parsees,
               lignes_fact_metre,
               lignes_review_required,
               lignes_warning,
               lignes_ignorees,
               {loss_column} AS lignes_rejetees,
               anomalies_json,
               governance_quality,
               metadata_json,
               created_at
        FROM dqe_import_audit
        ORDER BY created_at DESC
        LIMIT 1
    """
    try:
        return db.execute(text(base_select.format(loss_column="lignes_rejetees"))).mappings().first()
    except Exception:
        return db.execute(text(base_select.format(loss_column="0"))).mappings().first()


def serialize_project(project: Project, db: Session | None = None, include_workflow: bool = True) -> ProjectResponse:
    workflow_state: dict[str, Any] | None = None
    backend_workflow: dict[str, Any] | None = None
    trust_score = 87
    last_dqe = "DQE_PROJECT_SP2I.xlsx"
    budget = project.target_budget or 0
    workflow_status = project.setup_status or "CONFIG_REQUIRED"
    if db is not None and include_workflow:
        try:
            workflow_state = build_project_workflow_state(db, project.id, setup_status=project.setup_status)
            backend_workflow = compute_project_workflow_status(project, db).model_dump()
            trust_score = int(workflow_state.get("trust_score") or backend_workflow.get("dqe", {}).get("trust_score") or trust_score)
            last_dqe = workflow_state.get("file_name") or backend_workflow.get("dqe", {}).get("file_name") or last_dqe
            budget = float(workflow_state.get("capex_local_total") or project.target_budget or 0)
            workflow_status = backend_workflow.get("status") or workflow_status
        except Exception:
            workflow_state = None
            backend_workflow = None
    return ProjectResponse(
        id=project.id,
        name=project.name,
        client_name=project.client_name,
        city=project.city,
        country=project.country,
        currency=project.currency,
        project_type=project.project_type,
        project_manager=project.project_manager,
        target_budget=project.target_budget,
        vat_mode=project.vat_mode,
        reference_exchange_rate=project.reference_exchange_rate,
        default_transport_rate=project.default_transport_rate,
        default_customs_rate=project.default_customs_rate,
        default_insurance_rate=project.default_insurance_rate,
        default_import_margin=project.default_import_margin,
        minimum_saving_threshold=project.minimum_saving_threshold,
        planned_start_date=project.planned_start_date,
        target_delivery_date=project.target_delivery_date,
        site_storage_capacity=project.site_storage_capacity,
        setup_status=project.setup_status,
        setup_completed_at=project.setup_completed_at,
        owner_id=project.owner_id,
        status=project.status,
        created_at=project.created_at,
        trust_score=trust_score,
        last_dqe=last_dqe,
        budget=budget,
        workflow_status=workflow_status,
        backend_workflow=backend_workflow,
        workflow_state=workflow_state,
    )


def _resolve_project_dqe_status(project_id: int, db: Session | None = None) -> dict[str, Any]:
    path = Path(__file__).resolve().parents[3] / "03_DONNEES_ENTREE" / "dqe"
    source_file = path / "dqe_source_brut.json"
    normalized_file = path / "dqe_normalise.json"
    powerbi_file = Path(__file__).resolve().parents[3] / "05_RESULTATS" / "dqe_pret_powerbi.csv"

    source_present = source_file.exists()
    normalized_present = normalized_file.exists()
    powerbi_present = powerbi_file.exists()
    latest_audit = None
    synced = False
    uploaded_at = None
    analyzed_at = None
    governance_status = None

    if source_present:
        try:
            uploaded_at = datetime.fromtimestamp(source_file.stat().st_mtime, timezone.utc)
        except Exception:
            uploaded_at = None

    if normalized_present:
        try:
            analyzed_at = datetime.fromtimestamp(normalized_file.stat().st_mtime, timezone.utc)
        except Exception:
            analyzed_at = None

    if db is not None:
        try:
            latest_audit = _fetch_latest_dqe_audit(db)
            total_rows = db.execute(text("SELECT COUNT(*) FROM fact_metre")).scalar_one()
            synced = bool(total_rows and int(total_rows) > 0)
        except Exception:
            latest_audit = None
            synced = False

    file_name = ""
    trust_score = 0
    normalized_lines_count = 0
    ignored_lines_count = 0
    data_loss_count = 0
    review_required_count = 0
    certification_status = "UNKNOWN"
    synced_at = None
    issues: list[dict[str, Any]] = []
    issues_summary: dict[str, int] = {}
    bim_maturity: dict[str, Any] = {}

    if latest_audit:
        file_name = latest_audit.get("fichier") or ""
        trust_score = int(latest_audit.get("score_qualite") or 0)
        normalized_lines_count = int(latest_audit.get("lignes_parsees") or 0)
        ignored_lines_count = int(latest_audit.get("lignes_ignorees") or 0)
        review_required_count = int(latest_audit.get("lignes_review_required") or 0)
        data_loss_count = int(latest_audit.get("lignes_rejetees") or 0)
        governance_quality = latest_audit.get("governance_quality") or {}
        governance_status = "DATA_QUALITY_GOVERNANCE" if governance_quality else "UNKNOWN"
        issues = _json_field(latest_audit.get("anomalies_json"), [])
        metadata = _json_field(latest_audit.get("metadata_json"), {})
        issues_summary = metadata.get("dqe_issues_summary") or summarize_dqe_issues(issues)
        bim_maturity = metadata.get("bim_maturity") or {}
        if review_required_count > 0:
            certification_status = "REVIEW_REQUIRED"
        elif int(latest_audit.get("lignes_warning") or 0) > 0:
            certification_status = "CERTIFIED_WITH_WARNINGS"
        else:
            certification_status = "CERTIFIED"
        if certification_status in {"CERTIFIED", "CERTIFIED_WITH_WARNINGS"} and (trust_score <= 0 or normalized_lines_count <= 0):
            issues.insert(
                0,
                build_dqe_issue(
                    "AUDIT_METRICS_INCONSISTENT",
                    detected_value={
                        "certification_status": certification_status,
                        "trust_score": trust_score,
                        "normalized_lines_count": normalized_lines_count,
                    },
                    expected_value="trust_score > 0 et normalized_lines_count > 0",
                ),
            )
            issues_summary = summarize_dqe_issues(issues)
        if synced:
            synced_at = latest_audit.get("created_at")

    elif source_present:
        try:
            content = json.loads(source_file.read_text(encoding="utf-8-sig"))
            file_name = content.get("source", "") if isinstance(content, dict) else ""
        except Exception:
            file_name = ""

    if not source_present and not latest_audit:
        status = "NOT_IMPORTED"
    elif source_present and not normalized_present:
        status = "UPLOADED"
    elif normalized_present and not latest_audit:
        status = "ANALYZED"
    elif latest_audit and synced:
        status = "SYNCED"
    elif latest_audit:
        status = certification_status
    else:
        status = "ANALYZED"

    is_active = status not in {"NOT_IMPORTED"}

    return {
        "status": status,
        "version_number": 1 if is_active else 0,
        "file_name": file_name,
        "certification_status": certification_status,
        "governance_status": governance_status,
        "trust_score": trust_score,
        "normalized_lines_count": normalized_lines_count,
        "ignored_lines_count": ignored_lines_count,
        "data_loss_count": data_loss_count,
        "review_required_count": review_required_count,
        "is_active": is_active,
        "uploaded_at": uploaded_at,
        "analyzed_at": analyzed_at,
        "synced_at": synced_at,
        "issues_summary": issues_summary,
        "issues": issues[:20],
        "bim_maturity": bim_maturity,
    }


def _json_field(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default


def _resolve_project_budget_status(dqe_status: dict[str, Any], db: Session | None = None) -> dict[str, Any]:
    lines_count = 0
    total_amount = 0.0
    is_synced = False
    synced_at = None
    source = "FACT_METRE"
    message = "Budget non synchronisé."
    status = "SYNC_REQUIRED"

    if db is not None:
        try:
            lines_count = int(db.execute(text("SELECT COUNT(*) FROM fact_metre")).scalar_one() or 0)
            total_amount = float(db.execute(text("SELECT COALESCE(SUM(capex_local), 0) FROM fact_metre")).scalar_one() or 0.0)
            is_synced = lines_count > 0 and total_amount > 0.0
            synced_at = dqe_status.get("synced_at") if is_synced else None
            if is_synced:
                status = "SYNCED"
                message = "Budget synchronisé dans PostgreSQL."
            elif lines_count > 0:
                status = "SYNC_REQUIRED"
                message = "Des lignes FACT_METRE existent, mais le budget n'est pas encore marqué comme synchronisé."
            else:
                status = "SYNC_REQUIRED"
                message = "Aucune ligne FACT_METRE synchronisée."
        except Exception:
            status = "SYNC_REQUIRED"
            message = "Impossible de déterminer le statut de synchronisation du budget."
    else:
        is_synced = dqe_status["status"] == "SYNCED"
        synced_at = dqe_status.get("synced_at") if is_synced else None
        status = "SYNCED" if is_synced else "SYNC_REQUIRED"
        message = "Budget considéré synchronisé d'après l'état DQE." if is_synced else "Budget non synchronisé d'après l'état DQE."

    return {
        "status": status,
        "is_synced": is_synced,
        "synced_at": synced_at,
        "lines_count": lines_count,
        "total_amount": round(total_amount, 2),
        "source": source,
        "message": message,
    }


def _resolve_project_scenario_status(project_id: int, db: Session | None = None) -> dict[str, Any]:
    if db is None:
        return ScenarioStatus(
            status="NOT_STARTED",
            is_ready=False,
            message="Aucun acces base pour verifier les scenarios.",
        ).model_dump()

    try:
        row = db.execute(
            text(
                """
                SELECT
                    ds.scenario_id::text AS scenario_id,
                    ds.scenario_nom,
                    ds.scenario_type,
                    sr.run_id::text AS run_id,
                    sr.status AS run_status,
                    COALESCE(sr.ended_at, sr.started_at, ds.updated_at, ds.created_at) AS simulated_at,
                    COALESCE(sr.rows_out, 0) AS rows_out,
                    COUNT(fs.simulation_line_id) AS line_count
                FROM simulation_run sr
                JOIN dim_scenario ds ON ds.scenario_id = sr.scenario_id
                LEFT JOIN fact_simulation fs ON fs.run_id = sr.run_id
                WHERE sr.projet_id = :project_id
                  AND sr.status IN ('SUCCESS', 'READY', 'SIMULATED', 'VALIDATED')
                GROUP BY
                    ds.scenario_id,
                    ds.scenario_nom,
                    ds.scenario_type,
                    ds.created_at,
                    ds.updated_at,
                    sr.run_id,
                    sr.status,
                    sr.started_at,
                    sr.ended_at,
                    sr.rows_out
                HAVING COALESCE(sr.rows_out, 0) > 0 OR COUNT(fs.simulation_line_id) > 0
                ORDER BY COALESCE(sr.ended_at, sr.started_at, ds.updated_at, ds.created_at) DESC
                LIMIT 1
                """
            ),
            {"project_id": project_id},
        ).mappings().first()
    except Exception:
        return ScenarioStatus(
            status="UNKNOWN",
            is_ready=False,
            message="Impossible de determiner le statut scenario.",
        ).model_dump()

    if not row:
        return ScenarioStatus(
            status="NOT_STARTED",
            is_ready=False,
            message="Aucun scenario simule pour ce projet.",
        ).model_dump()

    line_count = int(row.get("line_count") or row.get("rows_out") or 0)
    run_status = str(row.get("run_status") or "").upper()
    status = "VALIDATED" if run_status == "VALIDATED" else "READY" if run_status == "READY" else "SIMULATED"
    return ScenarioStatus(
        status=status,
        is_ready=status in {"READY", "SIMULATED", "VALIDATED"} and line_count > 0,
        scenario_id=row.get("scenario_id"),
        scenario_name=row.get("scenario_nom"),
        scenario_type=row.get("scenario_type"),
        run_id=row.get("run_id"),
        run_status=run_status,
        simulated_at=row.get("simulated_at"),
        line_count=line_count,
        message="Scenario actif determine depuis simulation_run.",
    ).model_dump()


def _resolve_project_procurement_status(
    project_id: int,
    scenario_status: dict[str, Any],
    db: Session | None = None,
) -> dict[str, Any]:
    scenario_ready = bool(scenario_status.get("status") in {"READY", "SIMULATED", "VALIDATED"} and scenario_status.get("is_ready"))
    if not scenario_ready:
        return ProcurementStatus(
            status="BLOCKED",
            is_ready=False,
            message="Lancez un scenario avant de preparer l'approvisionnement.",
        ).model_dump()

    if db is None:
        return ProcurementStatus(
            status="REQUIRED",
            is_ready=False,
            message="Le scenario est disponible. Preparez les arbitrages achat.",
        ).model_dump()

    decision_status = procurement_decision_status(
        db,
        project_id,
        scenario_id=scenario_status.get("scenario_id"),
        scenario_ready=True,
    )
    if decision_status is not None:
        return ProcurementStatus(**decision_status).model_dump()

    filters = ["fs.projet_id = :project_id"]
    params: dict[str, Any] = {"project_id": project_id}
    if scenario_status.get("run_id"):
        filters.append("fs.run_id = CAST(:run_id AS uuid)")
        params["run_id"] = scenario_status["run_id"]
    elif scenario_status.get("scenario_id"):
        filters.append("fs.scenario_id = CAST(:scenario_id AS uuid)")
        params["scenario_id"] = scenario_status["scenario_id"]

    try:
        row = db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) AS decisions_count,
                    COUNT(*) FILTER (WHERE UPPER(COALESCE(fs.decision_import, '')) = 'IMPORT') AS import_lines_count,
                    COUNT(*) FILTER (WHERE UPPER(COALESCE(fs.decision_import, '')) = 'LOCAL') AS local_lines_count,
                    COUNT(*) FILTER (
                        WHERE UPPER(COALESCE(fs.decision_import, '')) IN ('HYBRIDE', 'HYBRID', 'MIXTE')
                           OR UPPER(COALESCE(fs.decision_type, '')) IN ('HYBRIDE', 'HYBRID', 'MIXTE')
                    ) AS hybrid_lines_count
                FROM fact_simulation fs
                WHERE {" AND ".join(filters)}
                  AND COALESCE(fs.designation, '') <> ''
                  AND COALESCE(fs.decision_import, '') <> ''
                """
            ),
            params,
        ).mappings().first()
    except Exception:
        return ProcurementStatus(
            status="REQUIRED",
            is_ready=False,
            message="Le scenario est disponible. Preparez les arbitrages achat.",
        ).model_dump()

    decisions_count = int(row.get("decisions_count") or 0) if row else 0
    import_lines_count = int(row.get("import_lines_count") or 0) if row else 0
    local_lines_count = int(row.get("local_lines_count") or 0) if row else 0
    hybrid_lines_count = int(row.get("hybrid_lines_count") or 0) if row else 0

    if decisions_count <= 0:
        return ProcurementStatus(
            status="REQUIRED",
            is_ready=False,
            message="Le scenario est disponible. Preparez les arbitrages achat.",
        ).model_dump()

    if scenario_status.get("status") == "VALIDATED":
        return ProcurementStatus(
            status="READY",
            is_ready=True,
            decisions_count=decisions_count,
            import_lines_count=import_lines_count,
            local_lines_count=local_lines_count,
            hybrid_lines_count=hybrid_lines_count,
            validated_decisions_count=decisions_count,
            export_available=True,
            message="Approvisionnement pret pour preparation chantier.",
        ).model_dump()

    return ProcurementStatus(
        status="REVIEW_REQUIRED",
        is_ready=False,
        decisions_count=decisions_count,
        import_lines_count=import_lines_count,
        local_lines_count=local_lines_count,
        hybrid_lines_count=hybrid_lines_count,
        message="Arbitrages achat generes. Validation humaine requise avant preparation chantier.",
    ).model_dump()


def _resolve_project_execution_status(
    project_id: int,
    procurement_status: dict[str, Any],
    scenario_status: dict[str, Any],
    db: Session | None = None,
) -> dict[str, Any]:
    procurement_ready = bool(procurement_status.get("status") in {"READY", "EXPORTABLE"} and procurement_status.get("is_ready"))
    if not procurement_ready:
        return ExecutionStatus(
            status="BLOCKED",
            is_ready=False,
            message="Preparez l'approvisionnement avant de lancer la preparation chantier.",
        ).model_dump()

    if db is None:
        return ExecutionStatus(
            status="REQUIRED",
            is_ready=False,
            message="L'approvisionnement est pret. Preparez les actions chantier.",
        ).model_dump()

    action_status = execution_action_status(
        db,
        project_id,
        scenario_id=scenario_status.get("scenario_id"),
        procurement_ready=True,
    )
    if action_status is not None:
        return ExecutionStatus(**action_status).model_dump()

    filters = ["fs.projet_id = :project_id"]
    params: dict[str, Any] = {"project_id": project_id}
    if scenario_status.get("run_id"):
        filters.append("fs.run_id = CAST(:run_id AS uuid)")
        params["run_id"] = scenario_status["run_id"]
    elif scenario_status.get("scenario_id"):
        filters.append("fs.scenario_id = CAST(:scenario_id AS uuid)")
        params["scenario_id"] = scenario_status["scenario_id"]

    try:
        row = db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) FILTER (
                        WHERE COALESCE(fs.lead_time_total, 0) > 0
                           OR COALESCE(fs.storage_cost, 0) > 0
                           OR COALESCE(fs.delivery_risk, '') <> ''
                           OR COALESCE(fs.shipment_strategy, '') <> ''
                           OR COALESCE(fs.container_strategy, '') <> ''
                    ) AS actions_count,
                    COUNT(DISTINCT fs.lot_id) FILTER (
                        WHERE UPPER(COALESCE(fs.delivery_risk, '')) IN ('ELEVE', 'HIGH', 'CRITICAL', 'CRITIQUE')
                           OR COALESCE(fs.criticality_score, 0) >= 70
                    ) AS critical_lots_count,
                    COUNT(*) FILTER (
                        WHERE UPPER(COALESCE(fs.delivery_risk, '')) NOT IN ('', 'FAIBLE', 'LOW')
                           OR COALESCE(fs.lead_time_total, 0) > 0
                    ) AS deliveries_to_watch_count,
                    COUNT(*) FILTER (WHERE COALESCE(fs.lead_time_total, 0) > 0) AS eta_to_watch_count
                FROM fact_simulation fs
                WHERE {" AND ".join(filters)}
                  AND COALESCE(fs.designation, '') <> ''
                """
            ),
            params,
        ).mappings().first()
    except Exception:
        return ExecutionStatus(
            status="REQUIRED",
            is_ready=False,
            message="L'approvisionnement est pret. Preparez les actions chantier.",
        ).model_dump()

    actions_count = int(row.get("actions_count") or 0) if row else 0
    critical_lots_count = int(row.get("critical_lots_count") or 0) if row else 0
    deliveries_to_watch_count = int(row.get("deliveries_to_watch_count") or 0) if row else 0
    eta_to_watch_count = int(row.get("eta_to_watch_count") or 0) if row else 0

    if actions_count <= 0:
        return ExecutionStatus(
            status="REQUIRED",
            is_ready=False,
            message="L'approvisionnement est pret. Preparez les actions chantier.",
        ).model_dump()

    status = "AT_RISK" if critical_lots_count > 0 else "READY"
    return ExecutionStatus(
        status=status,
        is_ready=True,
        actions_count=actions_count,
        critical_lots_count=critical_lots_count,
        deliveries_to_watch_count=deliveries_to_watch_count,
        eta_to_watch_count=eta_to_watch_count,
        message="Preparation chantier prete pour coordination terrain." if status == "READY" else "Preparation chantier prete avec alertes a surveiller.",
    ).model_dump()


def compute_project_workflow_status(project: Project, db: Session | None = None) -> ProjectWorkflowResponse:
    setup_configured = _is_project_configured(project) and project.setup_status == "CONFIGURED"
    workflow_state = build_project_workflow_state(db, project.id, setup_status=project.setup_status) if db is not None else {}
    dqe_status = _resolve_project_dqe_status(project.id, db)
    budget_status = _resolve_project_budget_status(dqe_status, db)
    scenario_status = _resolve_project_scenario_status(project.id, db)
    procurement_status = _resolve_project_procurement_status(project.id, scenario_status, db)
    execution_status = _resolve_project_execution_status(project.id, procurement_status, scenario_status, db)

    if workflow_state.get("dqe") == "SYNCHRONISE":
        dqe_status.update(
            {
                "status": "SYNCED",
                "certification_status": dqe_status.get("certification_status") or "CERTIFIED",
                "trust_score": workflow_state.get("trust_score") or dqe_status.get("trust_score") or 99,
                "normalized_lines_count": workflow_state.get("normalized_lines_count") or dqe_status.get("normalized_lines_count") or 0,
                "file_name": workflow_state.get("file_name") or dqe_status.get("file_name") or "",
                "is_active": True,
            }
        )
    if workflow_state.get("budget") == "SYNCHRONISE":
        budget_status.update(
            {
                "status": "SYNCED",
                "is_synced": True,
                "lines_count": workflow_state.get("counts", {}).get("fact_metre_rows") or budget_status.get("lines_count") or 0,
                "total_amount": workflow_state.get("capex_local_total") or budget_status.get("total_amount") or 0,
                "message": "Budget synchronise depuis la source projet centralisee.",
            }
        )
    if workflow_state.get("scenarios") == "SIMULE" and not scenario_status.get("is_ready"):
        scenario_status.update(
            {
                "status": "SIMULATED",
                "is_ready": True,
                "line_count": workflow_state.get("counts", {}).get("simulation_rows") or 0,
                "message": "Scenario detecte depuis la source projet centralisee.",
            }
        )
    if workflow_state.get("procurement") == "PRET" and not procurement_status.get("is_ready"):
        procurement_status.update(
            {
                "status": "READY",
                "is_ready": True,
                "decisions_count": workflow_state.get("counts", {}).get("procurement_decisions_count")
                or workflow_state.get("counts", {}).get("procurement_fact_decisions_count")
                or procurement_status.get("decisions_count")
                or 0,
                "export_available": True,
                "message": "Approvisionnement pret depuis la source projet centralisee.",
            }
        )
    if workflow_state.get("execution") == "A_PREPARER":
        execution_status.update(
            {
                "status": "REQUIRED",
                "is_ready": False,
                "actions_count": workflow_state.get("counts", {}).get("execution_actions_count") or 0,
                "message": "Approvisionnement pret. Actions chantier a preparer.",
            }
        )
    elif workflow_state.get("execution") == "A_RISQUE":
        execution_status.update({"status": "AT_RISK", "is_ready": True})
    elif workflow_state.get("execution") == "PRETE":
        execution_status.update({"status": "READY", "is_ready": True})

    budget_synced = bool(budget_status["is_synced"])
    scenario_ready = bool(scenario_status["status"] in {"READY", "SIMULATED", "VALIDATED"} and scenario_status["is_ready"])
    procurement_ready = bool(procurement_status["status"] in {"READY", "EXPORTABLE"} and procurement_status["is_ready"])
    execution_ready = bool(execution_status["status"] in {"READY", "ACTIVE", "AT_RISK"} and execution_status["is_ready"])

    dqe_label = "A importer"
    dqe_state = "todo"
    dqe_action = "Importer"
    dqe_route = "/app/dqe?tab=import"

    if setup_configured:
        if dqe_status["status"] == "NOT_IMPORTED":
            dqe_label = "A importer"
            dqe_state = "todo"
            dqe_action = "Importer"
            dqe_route = "/app/dqe?tab=import"
        elif dqe_status["status"] == "UPLOADED":
            dqe_label = "Importe"
            dqe_state = "progress"
            dqe_action = "Analyser"
            dqe_route = "/app/dqe?tab=analysis"
        elif dqe_status["status"] == "ANALYZED":
            dqe_label = "Analyse"
            dqe_state = "progress"
            dqe_action = "Verifier"
            dqe_route = "/app/dqe?tab=quality"
        elif dqe_status["status"] == "REVIEW_REQUIRED":
            dqe_label = "Validation requise"
            dqe_state = "progress"
            dqe_action = "Verifier"
            dqe_route = "/app/dqe?tab=quality"
        elif dqe_status["status"] == "CERTIFIED_WITH_WARNINGS":
            dqe_label = "Certifie avec points a verifier"
            dqe_state = "progress"
            dqe_action = "Verifier"
            dqe_route = "/app/dqe?tab=quality"
        elif dqe_status["status"] == "CERTIFIED":
            dqe_label = "Certifie"
            dqe_state = "done"
            dqe_action = "Synchroniser"
            dqe_route = "/app/dqe?tab=sync"
        elif dqe_status["status"] == "REJECTED":
            dqe_label = "Rejete"
            dqe_state = "blocked"
            dqe_action = "Verifier"
            dqe_route = "/app/dqe?tab=quality"
        elif dqe_status["status"] == "SYNCED":
            dqe_label = "Synchronise"
            dqe_state = "done"
            dqe_action = "Tester"
            dqe_route = "/app/simulation"
    else:
        dqe_label = "Bloque"
        dqe_state = "blocked"
        dqe_action = "Importer"
        dqe_route = "/app/dqe?tab=import"

    steps = [
        WorkflowStep(
            id="configuration",
            label="Configuration",
            status="Termine" if setup_configured else "A completer",
            state="done" if setup_configured else "blocking",
            action="Modifier" if setup_configured else "Configurer",
            route="/app/projects",
        ),
        WorkflowStep(
            id="dqe",
            label="DQE",
            status=dqe_label,
            state=dqe_state,
            action=dqe_action,
            route=dqe_route,
        ),
        WorkflowStep(
            id="budget",
            label="Budget",
            status="Synchronise" if budget_synced else "A synchroniser",
            state="done" if budget_synced else ("todo" if dqe_status["status"] == "CERTIFIED" else "blocked"),
            action="Synchroniser",
            route="/app/dqe?tab=sync",
        ),
        WorkflowStep(
            id="scenarios",
            label="Scenarios",
            status="Simule" if scenario_ready else ("Pret" if budget_synced else "Bloque"),
            state="done" if scenario_ready else ("todo" if budget_synced else "blocked"),
            action="Tester",
            route="/app/simulation",
        ),
        WorkflowStep(
            id="procurement",
            label="Approvisionnement",
            status=(
                "Pret"
                if procurement_ready
                else "Validation requise"
                if procurement_status["status"] == "REVIEW_REQUIRED"
                else "A preparer"
                if procurement_status["status"] == "REQUIRED"
                else "Bloque"
            ),
            state=(
                "done"
                if procurement_ready
                else "progress"
                if procurement_status["status"] == "REVIEW_REQUIRED"
                else "todo"
                if procurement_status["status"] == "REQUIRED"
                else "blocked"
            ),
            action="Preparer",
            route="/app/procurement",
        ),
        WorkflowStep(
            id="execution",
            label="Preparation Chantier",
            status=(
                "Pret"
                if execution_ready
                else "A preparer"
                if execution_status["status"] in {"REQUIRED", "PLANNING_REQUIRED"}
                else "Bloque"
            ),
            state="done" if execution_ready else ("todo" if execution_status["status"] in {"REQUIRED", "PLANNING_REQUIRED"} else "blocked"),
            action="Suivre",
            route="/app/site?tab=planning",
        ),
    ]

    if not setup_configured:
        status = "CONFIG_REQUIRED"
        label = "Configuration requise"
        primary_action = WorkflowAction(
            label="Configurer le projet",
            route="/app/projects",
            mode="setup",
        )
    elif dqe_status["status"] == "NOT_IMPORTED":
        status = "DQE_REQUIRED"
        label = "DQE a importer"
        primary_action = WorkflowAction(
            label="Importer le DQE",
            route="/app/dqe?tab=import",
        )
    elif dqe_status["status"] == "UPLOADED":
        status = "DQE_UPLOADED"
        label = "DQE importe"
        primary_action = WorkflowAction(
            label="Analyser le DQE",
            route="/app/dqe?tab=analysis",
        )
    elif dqe_status["status"] in {"ANALYZED", "REVIEW_REQUIRED", "CERTIFIED_WITH_WARNINGS", "REJECTED"}:
        status = "DQE_ANALYZED"
        label = "DQE a verifier"
        primary_action = WorkflowAction(
            label="Verifier le DQE",
            route="/app/dqe?tab=quality",
        )
    elif dqe_status["status"] == "CERTIFIED":
        status = "DQE_CERTIFIED"
        label = "DQE certifie"
        primary_action = WorkflowAction(
            label="Synchroniser le budget",
            route="/app/dqe?tab=sync",
        )
    elif budget_synced and not scenario_ready:
        status = "BUDGET_SYNCED"
        label = "Budget synchronise"
        primary_action = WorkflowAction(
            label="Tester un scenario",
            route="/app/simulation",
        )
    elif procurement_status["status"] == "REQUIRED":
        status = "SCENARIO_READY"
        label = "Scenario disponible"
        primary_action = WorkflowAction(
            label="Preparer l'approvisionnement",
            route="/app/procurement",
        )
    elif procurement_status["status"] == "REVIEW_REQUIRED":
        status = "PROCUREMENT_REVIEW_REQUIRED"
        label = "Arbitrages achat a valider"
        primary_action = WorkflowAction(
            label="Valider les arbitrages achat",
            route="/app/procurement",
        )
    elif procurement_status["status"] in {"READY", "EXPORTABLE"}:
        if execution_status["status"] in {"REQUIRED", "PLANNING_REQUIRED"}:
            status = "PROCUREMENT_READY"
            label = "Approvisionnement pret"
            primary_action = WorkflowAction(
                label="Preparer le chantier",
                route="/app/site?tab=planning",
            )
        elif execution_status["status"] in {"READY", "ACTIVE", "AT_RISK"}:
            status = "EXECUTION_READY"
            label = "Preparation chantier prete"
            primary_action = WorkflowAction(
                label="Ouvrir Preparation Chantier",
                route="/app/site?tab=planning",
            )
        else:
            status = "PROCUREMENT_READY"
            label = "Approvisionnement pret"
            primary_action = WorkflowAction(
                label="Preparer le chantier",
                route="/app/site?tab=planning",
            )
    else:
        status = "ACTIVE"
        label = "Projet actif"
        primary_action = WorkflowAction(
            label="Ouvrir le workspace",
            route="/app",
        )

    return ProjectWorkflowResponse(
        status=status,
        label=label,
        completion=round((sum(1 for step in steps if step.state == "done") / len(steps)) * 100),
        steps=steps,
        primary_action=primary_action,
        dqe=dqe_status,
        budget=budget_status,
        scenario=scenario_status,
        procurement=procurement_status,
        execution=execution_status,
    )


def _get_owned_project(db: Session, current_user: User, project_id: int) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return project


def _ensure_demo_project(db: Session, user: User) -> None:
    count = db.scalar(select(Project).where(Project.owner_id == user.id).limit(1))
    if count:
        return
    project = Project(
        name="Centre medical Pointe-Noire",
        client_name="SP2I",
        city="Pointe-Noire",
        country="Congo-Brazzaville",
        currency="FCFA",
        project_type="Etablissement de sante",
        project_manager="Direction SP2I",
        setup_status="CONFIGURED",
        setup_completed_at=datetime.now(timezone.utc),
        owner_id=user.id,
        status="ACTIVE",
    )
    db.add(project)
    db.flush()
    db.add(WorkspaceMembership(user_id=user.id, project_id=project.id, role=user.role))
    db.commit()


@router.get("", response_model=ProjectListResponse)
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    _ensure_demo_project(db, current_user)
    projects = db.scalars(select(Project).where(Project.owner_id == current_user.id).order_by(Project.created_at.desc())).all()
    return ProjectListResponse(projects=[serialize_project(project, db) for project in projects])


@router.post("", response_model=ProjectResponse)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = Project(
        name=payload.name,
        client_name=payload.client_name,
        city=payload.city,
        country=payload.country,
        currency=payload.currency,
        project_type=payload.project_type,
        project_manager=payload.project_manager,
        setup_status="CONFIG_REQUIRED",
        status=payload.status.upper(),
        owner_id=current_user.id,
    )
    project.setup_status = _compute_setup_status(project)
    if project.setup_status == "CONFIGURED":
        project.setup_completed_at = datetime.now(timezone.utc)
    db.add(project)
    db.flush()
    db.add(WorkspaceMembership(user_id=current_user.id, project_id=project.id, role=current_user.role))
    db.commit()
    db.refresh(project)
    return serialize_project(project, db)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    return serialize_project(_get_owned_project(db, current_user, project_id), db)


@router.patch("/{project_id}/setup", response_model=ProjectResponse)
def update_project_setup(
    project_id: int,
    payload: ProjectSetupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = _get_owned_project(db, current_user, project_id)
    previous_status = project.setup_status
    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(project, field):
            setattr(project, field, value)

    project.setup_status = _compute_setup_status(project)
    if project.setup_status == "CONFIGURED" and project.setup_completed_at is None:
        project.setup_completed_at = datetime.now(timezone.utc)
    elif project.setup_status != "CONFIGURED":
        project.setup_completed_at = None

    db.add(project)
    db.commit()
    db.refresh(project)
    log_workflow_event(
        db,
        project_id=project.id,
        user_id=current_user.id,
        event_type="PROJECT_SETUP_UPDATED",
        entity_type="project",
        entity_id=project.id,
        previous_status=previous_status,
        new_status=project.setup_status,
        message="Configuration projet mise a jour.",
        metadata={"setup_completion_percent": project.setup_completion_percent},
    )
    return serialize_project(project, db)


@router.get("/{project_id}/workflow", response_model=ProjectWorkflowResponse)
def get_project_workflow(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectWorkflowResponse:
    return compute_project_workflow_status(_get_owned_project(db, current_user, project_id), db)


@router.get("/{project_id}/workflow-state", response_model=ProjectWorkflowStateResponse)
def get_project_workflow_state(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectWorkflowStateResponse:
    project = _get_owned_project(db, current_user, project_id)
    return ProjectWorkflowStateResponse(**build_project_workflow_state(db, project.id, setup_status=project.setup_status))


@router.get("/{project_id}/spatial/summary", response_model=SpatialSummaryResponse)
def get_project_spatial_intelligence_summary(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SpatialSummaryResponse:
    _get_owned_project(db, current_user, project_id)
    return SpatialSummaryResponse(**get_project_spatial_summary(db, project_id))


@router.get("/{project_id}/report.pdf")
def get_project_report_pdf(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_owned_project(db, current_user, project_id)
    pdf_stream = build_project_report_pdf(project.id, db)
    filename = generate_project_report_filename(project)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(pdf_stream, media_type="application/pdf", headers=headers)


@router.get("/{project_id}/workflow/events", response_model=WorkflowEventListResponse)
def get_project_workflow_events(
    project_id: int,
    limit: int = Query(default=30, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkflowEventListResponse:
    _get_owned_project(db, current_user, project_id)
    rows = list_workflow_events(db, project_id, limit=limit, offset=offset)
    return WorkflowEventListResponse(events=[WorkflowEventOut(**row) for row in rows])


@router.get("/{project_id}/procurement/decisions", response_model=ProcurementDecisionListResponse)
def get_project_procurement_decisions(
    project_id: int,
    scenario_id: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcurementDecisionListResponse:
    _get_owned_project(db, current_user, project_id)
    rows = list_procurement_decisions(db, project_id, scenario_id=scenario_id, limit=limit, offset=offset)
    return ProcurementDecisionListResponse(decisions=[ProcurementDecisionOut(**row) for row in rows])


@router.post("/{project_id}/procurement/decisions/bootstrap", response_model=ProcurementDecisionBootstrapResponse)
def bootstrap_project_procurement_decisions(
    project_id: int,
    scenario_id: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcurementDecisionBootstrapResponse:
    _get_owned_project(db, current_user, project_id)
    payload = bootstrap_procurement_decisions_from_simulation(db, project_id, scenario_id=scenario_id, run_id=run_id)
    log_workflow_event(
        db,
        project_id=project_id,
        user_id=current_user.id,
        event_type="PROCUREMENT_DECISIONS_BOOTSTRAPPED",
        entity_type="procurement_decisions",
        previous_status="REQUIRED",
        new_status=payload.get("status", {}).get("status", ""),
        message="Decisions achat generees depuis la simulation.",
        metadata={"inserted_count": payload.get("inserted_count", 0), "scenario_id": scenario_id, "run_id": run_id},
    )
    return ProcurementDecisionBootstrapResponse(**payload)


@router.patch("/{project_id}/procurement/decisions/{decision_id}", response_model=ProcurementDecisionOut)
def patch_project_procurement_decision(
    project_id: int,
    decision_id: int,
    payload: ProcurementDecisionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcurementDecisionOut:
    _get_owned_project(db, current_user, project_id)
    previous_row = db.execute(
        text(
            """
            SELECT validation_status
            FROM procurement_decisions
            WHERE id = :decision_id AND project_id = :project_id
            """
        ),
        {"decision_id": decision_id, "project_id": project_id},
    ).mappings().first()
    row = update_procurement_decision(db, project_id, decision_id, payload.model_dump(exclude_unset=True))
    if not row:
        raise HTTPException(status_code=404, detail="Decision achat introuvable.")
    log_workflow_event(
        db,
        project_id=project_id,
        user_id=current_user.id,
        event_type="PROCUREMENT_DECISION_UPDATED",
        entity_type="procurement_decision",
        entity_id=decision_id,
        previous_status=(previous_row or {}).get("validation_status", ""),
        new_status=row.get("validation_status", ""),
        message="Decision achat mise a jour.",
        metadata={"validated_decision": row.get("validated_decision"), "supplier_selected": row.get("supplier_selected")},
    )
    return ProcurementDecisionOut(**row)


@router.get("/{project_id}/procurement/status", response_model=ProcurementDecisionStatus)
def get_project_procurement_status(
    project_id: int,
    scenario_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcurementDecisionStatus:
    _get_owned_project(db, current_user, project_id)
    scenario = _resolve_project_scenario_status(project_id, db)
    scenario_ready = bool(scenario.get("status") in {"READY", "SIMULATED", "VALIDATED"} and scenario.get("is_ready"))
    status = procurement_decision_status(db, project_id, scenario_id=scenario_id or scenario.get("scenario_id"), scenario_ready=scenario_ready)
    if status is None:
        status = _resolve_project_procurement_status(project_id, scenario, db)
    return ProcurementDecisionStatus(**status)


@router.get("/{project_id}/procurement/export.xlsx")
def export_project_procurement_workbook(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_owned_project(db, current_user, project_id)
    workflow = compute_project_workflow_status(project, db).model_dump()
    buffer = build_procurement_export_workbook(project_id, db, workflow=workflow)
    filename = generate_procurement_export_filename(project)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/execution/actions", response_model=SiteExecutionActionListResponse)
def get_project_execution_actions(
    project_id: int,
    scenario_id: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SiteExecutionActionListResponse:
    _get_owned_project(db, current_user, project_id)
    rows = list_site_execution_actions(db, project_id, scenario_id=scenario_id, limit=limit, offset=offset)
    return SiteExecutionActionListResponse(actions=[SiteExecutionActionOut(**row) for row in rows])


@router.post("/{project_id}/execution/actions/generate", response_model=SiteExecutionActionGenerateResponse)
def generate_project_execution_actions(
    project_id: int,
    scenario_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SiteExecutionActionGenerateResponse:
    _get_owned_project(db, current_user, project_id)
    scenario = _resolve_project_scenario_status(project_id, db)
    payload = generate_site_execution_actions(db, project_id, scenario_id=scenario_id or scenario.get("scenario_id"))
    log_workflow_event(
        db,
        project_id=project_id,
        user_id=current_user.id,
        event_type="SITE_EXECUTION_ACTIONS_GENERATED",
        entity_type="site_execution_actions",
        previous_status="REQUIRED",
        new_status=payload.get("status", {}).get("status", ""),
        message="Actions chantier generees depuis les arbitrages achat.",
        metadata={"inserted_count": payload.get("inserted_count", 0), "scenario_id": scenario_id or scenario.get("scenario_id")},
    )
    return SiteExecutionActionGenerateResponse(**payload)


@router.patch("/{project_id}/execution/actions/{action_id}", response_model=SiteExecutionActionOut)
def patch_project_execution_action(
    project_id: int,
    action_id: int,
    payload: SiteExecutionActionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SiteExecutionActionOut:
    _get_owned_project(db, current_user, project_id)
    previous_row = db.execute(
        text(
            """
            SELECT status
            FROM site_execution_actions
            WHERE id = :action_id AND project_id = :project_id
            """
        ),
        {"action_id": action_id, "project_id": project_id},
    ).mappings().first()
    row = update_site_execution_action(db, project_id, action_id, payload.model_dump(exclude_unset=True))
    if not row:
        raise HTTPException(status_code=404, detail="Action chantier introuvable.")
    log_workflow_event(
        db,
        project_id=project_id,
        user_id=current_user.id,
        event_type="SITE_EXECUTION_ACTION_UPDATED",
        entity_type="site_execution_action",
        entity_id=action_id,
        previous_status=(previous_row or {}).get("status", ""),
        new_status=row.get("status", ""),
        message="Statut action chantier mis a jour.",
        metadata={"responsible_name": row.get("responsible_name"), "responsible_role": row.get("responsible_role")},
    )
    return SiteExecutionActionOut(**row)


@router.get("/{project_id}/execution/status", response_model=SiteExecutionActionStatus)
def get_project_execution_status(
    project_id: int,
    scenario_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SiteExecutionActionStatus:
    _get_owned_project(db, current_user, project_id)
    scenario = _resolve_project_scenario_status(project_id, db)
    procurement = _resolve_project_procurement_status(project_id, scenario, db)
    procurement_ready = bool(procurement.get("status") in {"READY", "EXPORTABLE"} and procurement.get("is_ready"))
    status = execution_action_status(db, project_id, scenario_id=scenario_id or scenario.get("scenario_id"), procurement_ready=procurement_ready)
    if status is None:
        status = _resolve_project_execution_status(project_id, procurement, scenario, db)
    return SiteExecutionActionStatus(**status)
