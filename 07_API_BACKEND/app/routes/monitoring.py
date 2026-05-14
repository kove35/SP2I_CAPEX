from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.monitoring import MonitoringService


router = APIRouter()


@router.get("/monitoring/status")
def monitoring_status(db: Session = Depends(get_db)) -> dict:
    """Retourne l'etat temps reel API + PostgreSQL + qualite DQE."""
    return MonitoringService(db).get_status()
