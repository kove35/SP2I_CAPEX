from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.routes import get_current_user
from app.database import get_db
from app.projects.models import Project
from app.workflow.engine.workflow_state_engine import WorkflowStateEngine
from app.workflow.schemas.workflow import WorkflowState
from app.workflow.services.workflow_cache import workflow_cache
from app.utils.json_safe import sanitize_for_json


router = APIRouter()


def _get_owned_project(db: Session, current_user: User, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return project


@router.get("/{project_id}", response_model=WorkflowState)
def get_workflow_state(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkflowState:
    project = _get_owned_project(db, current_user, project_id)
    return WorkflowStateEngine(db).compute(project.id, setup_status=project.setup_status)


@router.get("/{project_id}/timeline")
def get_workflow_timeline(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = _get_owned_project(db, current_user, project_id)
    state = WorkflowStateEngine(db).compute(project.id, setup_status=project.setup_status)
    return sanitize_for_json({"project_id": project.id, "timeline": [item.model_dump(mode="json") for item in state.timeline]})


@router.get("/{project_id}/metrics")
def get_workflow_metrics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = _get_owned_project(db, current_user, project_id)
    state = WorkflowStateEngine(db).compute(project.id, setup_status=project.setup_status)
    return sanitize_for_json({"project_id": project.id, "metrics": state.metrics.model_dump(mode="json"), "progress_percent": state.progress_percent})


@router.get("/{project_id}/alerts")
def get_workflow_alerts(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = _get_owned_project(db, current_user, project_id)
    state = WorkflowStateEngine(db).compute(project.id, setup_status=project.setup_status)
    return sanitize_for_json({"project_id": project.id, "alerts": [alert.model_dump(mode="json") for alert in state.alerts], "blockers": [blocker.model_dump(mode="json") for blocker in state.blockers]})


@router.post("/{project_id}/refresh", response_model=WorkflowState)
def refresh_workflow_state(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkflowState:
    project = _get_owned_project(db, current_user, project_id)
    workflow_cache.invalidate(project.id)
    return WorkflowStateEngine(db).compute(project.id, setup_status=project.setup_status, use_cache=False)
