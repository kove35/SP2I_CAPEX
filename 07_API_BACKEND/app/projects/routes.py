from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User, WorkspaceMembership
from app.auth.routes import get_current_user
from app.database import get_db
from app.projects.models import Project
from app.projects.schemas import ProjectCreate, ProjectListResponse, ProjectResponse


router = APIRouter()


def serialize_project(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        client_name=project.client_name,
        city=project.city,
        country=project.country,
        currency=project.currency,
        owner_id=project.owner_id,
        status=project.status,
        created_at=project.created_at,
    )


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
        status=payload.status.upper(),
        owner_id=current_user.id,
    )
    db.add(project)
    db.flush()
    db.add(WorkspaceMembership(user_id=current_user.id, project_id=project.id, role=current_user.role))
    db.commit()
    db.refresh(project)
    return serialize_project(project)
