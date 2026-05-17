from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.schemas import AnalyticsResponse
from app.analytics.services import AnalyticsService
from app.analytics.utils import build_query
from app.database import get_db


router = APIRouter()


def analytics_query(
    projet: str | None = None,
    scenario: str | None = None,
    batiment: str | None = None,
    niveau: str | None = None,
    lot: str | None = None,
    famille: str | None = None,
    fournisseur: str | None = None,
    decision_import: str | None = None,
    periode_debut: str | None = None,
    periode_fin: str | None = None,
    criticite: str | None = None,
    statut_chantier: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=5000),
    group_by: str | None = None,
    order_by: str | None = None,
    order_dir: str = "desc",
    drilldown_level: str | None = None,
):
    return build_query(
        projet=projet,
        scenario=scenario,
        batiment=batiment,
        niveau=niveau,
        lot=lot,
        famille=famille,
        fournisseur=fournisseur,
        decision_import=decision_import,
        periode_debut=periode_debut,
        periode_fin=periode_fin,
        criticite=criticite,
        statut_chantier=statut_chantier,
        page=page,
        page_size=page_size,
        group_by=group_by,
        order_by=order_by,
        order_dir=order_dir,
        drilldown_level=drilldown_level,
    )


@router.get("/capex", response_model=AnalyticsResponse)
def capex(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).capex(query)


@router.get("/kpis", response_model=AnalyticsResponse)
def kpis(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).kpis(query)


@router.get("/risk", response_model=AnalyticsResponse)
def risk(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).risk(query)


@router.get("/procurement", response_model=AnalyticsResponse)
def procurement(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).procurement(query)


@router.get("/logistics", response_model=AnalyticsResponse)
def logistics(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).logistics(query)


@router.get("/scenarios", response_model=AnalyticsResponse)
def scenarios(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).scenarios(query)


@router.get("/heatmap", response_model=AnalyticsResponse)
def heatmap(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).heatmap(query)


@router.get("/drilldown", response_model=AnalyticsResponse)
def drilldown(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).drilldown(query)


@router.get("/timeline", response_model=AnalyticsResponse)
def timeline(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).timeline(query)


@router.get("/dashboard", response_model=AnalyticsResponse)
def dashboard(
    dashboard_type: str = "direction",
    query=Depends(analytics_query),
    db: Session = Depends(get_db),
) -> dict:
    return AnalyticsService(db).dashboard(query, dashboard_type=dashboard_type)


@router.get("/system-health", response_model=AnalyticsResponse)
def system_health(db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).system_health()


@router.get("/query-performance", response_model=AnalyticsResponse)
def query_performance(db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).query_performance()


@router.get("/cache-status", response_model=AnalyticsResponse)
def cache_status(db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).cache_status()


@router.get("/debug/pipeline", response_model=AnalyticsResponse)
def debug_pipeline(db: Session = Depends(get_db)) -> dict:
    return AnalyticsService(db).debug_pipeline()
