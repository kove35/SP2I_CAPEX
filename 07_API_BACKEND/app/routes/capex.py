from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CapexSummary, FactMetreRead
from app.services.service_db import ServiceDB


router = APIRouter()


@router.get("/capex/summary", response_model=CapexSummary)
def capex_summary(db: Session = Depends(get_db)) -> dict:
    """Retourne les KPI CAPEX directement depuis PostgreSQL."""
    return ServiceDB(db).get_summary()


@router.get("/fact_metre", response_model=list[FactMetreRead])
def fact_metre(
    famille: str | None = None,
    lot: str | None = None,
    batiment: str | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> list:
    """Retourne FACT_METRE avec filtres simples pour le frontend et Power BI."""
    return ServiceDB(db).list_fact_metre(
        famille=famille,
        lot=lot,
        batiment=batiment,
        limit=limit,
        offset=offset,
    )
