from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.analytics.schemas import AnalyticsResponse
from app.analytics.services import AnalyticsService
from app.analytics.utils import build_query
from app.core.startup_metrics import get_startup_status
from app.database import get_db
from app.utils.json_safe import sanitize_for_json


router = APIRouter()


def analytics_query(
    projet: str | None = None,
    scenario: str | None = None,
    batiment: str | None = None,
    niveau: str | None = None,
    appartement: str | None = None,
    zone: str | None = None,
    piece: str | None = None,
    sous_lot: str | None = None,
    lot: str | None = None,
    famille: str | None = None,
    fournisseur: str | None = None,
    devise: str | None = None,
    import_local: str | None = None,
    decision_import: str | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
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
        appartement=appartement,
        zone=zone,
        piece=piece,
        sous_lot=sous_lot,
        lot=lot,
        famille=famille,
        fournisseur=fournisseur,
        devise=devise,
        decision_import=decision_import or import_local,
        periode_debut=periode_debut or date_debut,
        periode_fin=periode_fin or date_fin,
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
    return sanitize_for_json(AnalyticsService(db).capex(query))


@router.get("/kpis", response_model=AnalyticsResponse)
def kpis(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).kpis(query))


@router.get("/risk", response_model=AnalyticsResponse)
def risk(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).risk(query))


@router.get("/procurement", response_model=AnalyticsResponse)
def procurement(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).procurement(query))


@router.get("/procurement-scenarios", response_model=AnalyticsResponse)
def procurement_scenarios(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).procurement_scenarios(query))


@router.get("/suppliers", response_model=AnalyticsResponse)
def suppliers(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).suppliers(query))


@router.get("/procurement-lines", response_model=AnalyticsResponse)
def procurement_lines(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).procurement_lines(query))


@router.get("/currency", response_model=AnalyticsResponse)
def currency(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).currency(query))


@router.get("/import-risks", response_model=AnalyticsResponse)
def import_risks(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).import_risks(query))


@router.get("/procurement-export")
def procurement_export(query=Depends(analytics_query), db: Session = Depends(get_db)):
    buffer = AnalyticsService(db).export_procurement_file(query)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="SP2I_dossier_achat_chine.xlsx"'},
    )


@router.get("/gain-analysis", response_model=AnalyticsResponse)
def gain_analysis(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).gain_analysis(query))


@router.get("/gain-analysis/export")
def gain_analysis_export(query=Depends(analytics_query), db: Session = Depends(get_db)):
    buffer = AnalyticsService(db).export_gain_analysis(query)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="SP2I_detail_gain_potentiel.xlsx"'},
    )


@router.get("/logistics", response_model=AnalyticsResponse)
def logistics(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).logistics(query))


@router.get("/scenarios", response_model=AnalyticsResponse)
def scenarios(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).scenarios(query))


@router.get("/heatmap", response_model=AnalyticsResponse)
def heatmap(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).heatmap(query))


@router.get("/drilldown", response_model=AnalyticsResponse)
def drilldown(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).drilldown(query))


@router.get("/timeline", response_model=AnalyticsResponse)
def timeline(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).timeline(query))


@router.get("/spatial")
def spatial(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).spatial(query))


@router.get("/spatial/dashboard")
def spatial_dashboard(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).spatial_dashboard(query))


@router.get("/cost-intelligence")
def cost_intelligence(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).cost_intelligence(query))


@router.get("/filters")
def filters(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).filter_options())


@router.get("/dashboard", response_model=AnalyticsResponse)
def dashboard(
    dashboard_type: str = "direction",
    query=Depends(analytics_query),
    db: Session = Depends(get_db),
) -> dict:
    return sanitize_for_json(AnalyticsService(db).dashboard(query, dashboard_type=dashboard_type))


@router.get("/system-health", response_model=AnalyticsResponse)
def system_health(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).system_health())


@router.get("/query-performance", response_model=AnalyticsResponse)
def query_performance(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).query_performance())


@router.get("/cache-status", response_model=AnalyticsResponse)
def cache_status(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).cache_status())


@router.get("/debug/cache", response_model=AnalyticsResponse)
def debug_cache(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).debug_cache())


@router.get("/debug/coldstart")
def debug_coldstart() -> dict:
    return get_startup_status()


@router.get("/debug/pipeline", response_model=AnalyticsResponse)
def debug_pipeline(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).debug_pipeline())


@router.get("/debug/database")
def debug_database(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).database_debug())


@router.get("/debug/timing")
def debug_timing(
    dashboard_type: str = "direction",
    query=Depends(analytics_query),
    db: Session = Depends(get_db),
) -> dict:
    return sanitize_for_json(AnalyticsService(db).dashboard_timing(query, dashboard_type=dashboard_type))


@router.get("/debug/consistency")
def debug_consistency(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).consistency_debug(query))


@router.get("/debug/filter-consistency")
def debug_filter_consistency(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).filter_consistency_debug(query))


@router.get("/debug/reconciliation")
def debug_reconciliation(query=Depends(analytics_query), db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).financial_reconciliation_debug(query))


@router.get("/debug/bim-maturity")
def debug_bim_maturity(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).bim_maturity_debug())


@router.get("/debug/schema-capabilities")
def debug_schema_capabilities(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).schema_capabilities_debug())


@router.get("/qa-summary", response_model=AnalyticsResponse)
def qa_summary(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).qa_summary())


@router.get("/data-quality", response_model=AnalyticsResponse)
def data_quality(db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).data_quality())


@router.get("/debug/capex-reconciliation/{project_id}")
def capex_reconciliation(project_id: int, db: Session = Depends(get_db)) -> dict:
    return sanitize_for_json(AnalyticsService(db).capex_reconciliation(project_id))
