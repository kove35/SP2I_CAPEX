from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth.models import User, WorkspaceMembership
from app.auth.routes import get_current_user
from app.database import get_db
from app.projects.models import Project
from app.projects.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectSetupUpdate,
    ProjectWorkflowResponse,
    ScenarioStatus,
    WorkflowAction,
    WorkflowStep,
)
from app.services.service_pipeline import ServicePipeline


router = APIRouter()


REQUIRED_SETUP_FIELDS = ("name", "client_name", "city", "country", "currency", "project_manager")


def _is_project_configured(project: Project) -> bool:
    return all(str(getattr(project, field, "") or "").strip() for field in REQUIRED_SETUP_FIELDS)


def _compute_setup_status(project: Project) -> str:
    return "CONFIGURED" if _is_project_configured(project) else "CONFIG_REQUIRED"


def serialize_project(project: Project) -> ProjectResponse:
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
        budget=project.target_budget or 0,
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
            latest_audit = db.execute(
                text(
                    """
                    SELECT fichier,
                           score_qualite,
                           lignes_parsees,
                           lignes_fact_metre,
                           lignes_review_required,
                           lignes_warning,
                           lignes_ignorees,
                           lignes_rejetees,
                           governance_quality,
                           created_at
                    FROM dqe_import_audit
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )
            ).mappings().first()
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

    if latest_audit:
        file_name = latest_audit.get("fichier") or ""
        trust_score = int(latest_audit.get("score_qualite") or 0)
        normalized_lines_count = int(latest_audit.get("lignes_parsees") or 0)
        ignored_lines_count = int(latest_audit.get("lignes_ignorees") or 0)
        review_required_count = int(latest_audit.get("lignes_review_required") or 0)
        data_loss_count = int(latest_audit.get("lignes_rejetees") or 0)
        governance_quality = latest_audit.get("governance_quality") or {}
        governance_status = "DATA_QUALITY_GOVERNANCE" if governance_quality else "UNKNOWN"
        if review_required_count > 0:
            certification_status = "REVIEW_REQUIRED"
        elif int(latest_audit.get("lignes_warning") or 0) > 0:
            certification_status = "CERTIFIED_WITH_WARNINGS"
        else:
            certification_status = "CERTIFIED"
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
    }


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


def compute_project_workflow_status(project: Project, db: Session | None = None) -> ProjectWorkflowResponse:
    setup_configured = _is_project_configured(project) and project.setup_status == "CONFIGURED"
    dqe_status = _resolve_project_dqe_status(project.id, db)
    budget_status = _resolve_project_budget_status(dqe_status, db)
    scenario_status = _resolve_project_scenario_status(project.id, db)
    budget_synced = bool(budget_status["is_synced"])
    scenario_ready = bool(scenario_status["status"] in {"READY", "SIMULATED", "VALIDATED"} and scenario_status["is_ready"])
    procurement_ready = scenario_ready
    execution_ready = False

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
            status="Pret" if procurement_ready else "Bloque",
            state="todo" if procurement_ready else "blocked",
            action="Preparer",
            route="/app/procurement",
        ),
        WorkflowStep(
            id="execution",
            label="Execution",
            status="Pret" if execution_ready else "Bloque",
            state="done" if execution_ready else "blocked",
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
    elif scenario_ready and not execution_ready:
        status = "SCENARIO_READY"
        label = "Scenario disponible"
        primary_action = WorkflowAction(
            label="Preparer l'approvisionnement",
            route="/app/procurement",
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
    return ProjectListResponse(projects=[serialize_project(project) for project in projects])


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
    return serialize_project(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    return serialize_project(_get_owned_project(db, current_user, project_id))


@router.patch("/{project_id}/setup", response_model=ProjectResponse)
def update_project_setup(
    project_id: int,
    payload: ProjectSetupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = _get_owned_project(db, current_user, project_id)
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
    return serialize_project(project)


@router.get("/{project_id}/workflow", response_model=ProjectWorkflowResponse)
def get_project_workflow(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectWorkflowResponse:
    return compute_project_workflow_status(_get_owned_project(db, current_user, project_id), db)
