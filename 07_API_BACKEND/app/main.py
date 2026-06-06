from __future__ import annotations

import logging
import os
import time
from time import perf_counter
from importlib import import_module

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.middleware.json_safe_middleware import JsonSafeMiddleware

from app.analytics.cache import analytics_cache
from app.analytics.routes import router as analytics_router
from app.analytics.utils.schema_utils import preload_schema_capabilities
from app.approval.routes.approvals import router as approvals_router
from app.auth.routes import router as auth_router
from app.cloud_migrations import ensure_powerbi_schema
from app.core.startup_metrics import mark_startup_begin, mark_startup_complete, record_startup_stage
from app.database import Base, SessionLocal, engine
from app.projects.routes import router as projects_router
from app.routes import capex, decision, dqe, logistics, monitoring, procurement, simulation, upload
from app.services.monitoring import MonitoringService
from app.workflow.routes.workflow import router as workflow_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sp2i-capex-api")

import_routes = import_module("app.routes.import")
import_module("app.models")
import_module("app.approval.models")
import_module("app.auth.models")
import_module("app.projects.models")


def _get_cors_origins() -> list[str]:
    """
    Charge les origines autorisées depuis l'environnement.
    """

    default_origins = (
        "http://localhost:5173,"
        "http://localhost:5174,"
        "http://localhost:5175,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:5174,"
        "http://127.0.0.1:5175,"
        "http://localhost:8501"
    )

    raw_origins = os.getenv("CORS_ORIGINS", default_origins)

    return [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]

def _get_cors_origin_regex() -> str | None:
    """
    Autorise localhost sur n'importe quel port
    ainsi que les domaines Vercel.
    """

    return os.getenv(
        "CORS_ORIGIN_REGEX",
        r"(http://localhost:\d+|http://127\.0\.0\.1:\d+|https://.*\.vercel\.app)"
    )

app = FastAPI(
    title="SP2I CAPEX API",
    description="API SaaS pour analyse DQE, optimisation import/local et exposition BI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_origin_regex=_get_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure responses are JSON-safe (convert datetimes, decimals, UUIDs etc.)
app.add_middleware(JsonSafeMiddleware)

app.include_router(dqe.router, prefix="/dqe", tags=["DQE"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(projects_router, prefix="/projects", tags=["Projects"])
app.include_router(workflow_router, prefix="/workflow", tags=["Workflow Engine"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload intelligent"])
app.include_router(import_routes.router, prefix="/import", tags=["Import"])
app.include_router(simulation.router, prefix="/simulation", tags=["Simulation CAPEX"])
app.include_router(decision.router, prefix="/decision", tags=["Decision Engine"])
app.include_router(procurement.router, prefix="/procurement", tags=["Procurement Analytics"])
app.include_router(logistics.router, prefix="/logistics", tags=["Logistics Analytics"])
app.include_router(approvals_router, prefix="/approvals", tags=["Approval Engine"])
app.include_router(analytics_router, prefix="/analytics", tags=["SP2I Analytics Engine"])
app.include_router(capex.router, tags=["BI"])
app.include_router(monitoring.router, tags=["Monitoring"])


def _print_startup_routes() -> None:
    print("=" * 80)
    print("SP2I BACKEND LOADED")
    print(__file__)
    print("FASTAPI ROUTES")
    for route in app.routes:
        print(route.path)
    print("=" * 80)


_print_startup_routes()


@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """
    Mesure automatiquement le temps de reponse de chaque requete API.

    Le monitoring est volontairement tolerant : si PostgreSQL est indisponible,
    la requete utilisateur continue quand meme.
    """
    start = time.perf_counter()
    response = await call_next(request)
    duration = round(time.perf_counter() - start, 4)

    db = SessionLocal()
    try:
        service = MonitoringService(db)
        service.log_metric(
            "api_response_time",
            duration,
            message=f"{request.method} {request.url.path} returned {response.status_code}",
        )

        if response.status_code >= 500:
            service.log_event(
                "api_error",
                f"{request.method} {request.url.path} returned {response.status_code}",
                niveau="ERROR",
            )
    except Exception as erreur:
        logger.error("Monitoring middleware error: %s", erreur)
    finally:
        db.close()

    response.headers["X-Response-Time"] = str(duration)
    return response


@app.on_event("startup")
def startup() -> None:
    """
    Cree les tables si elles n'existent pas.

    Pour un SaaS mature, on remplacera cette creation automatique par Alembic,
    mais cette approche est simple et pratique pour demarrer le projet.
    """
    mark_startup_begin()
    startup_begin = perf_counter()
    try:
        database_start = perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database_elapsed = round((perf_counter() - database_start) * 1000, 2)
        record_startup_stage("database_connect", database_elapsed)
        logger.info("Startup database_connect_ms=%s", database_elapsed)

        schema_start = perf_counter()
        Base.metadata.create_all(bind=engine)
        ensure_powerbi_schema(engine)
        with SessionLocal() as schema_db:
            preload_schema_capabilities(schema_db)
        schema_elapsed = round((perf_counter() - schema_start) * 1000, 2)
        record_startup_stage("schema_check", schema_elapsed)
        logger.info("Startup schema_check_ms=%s", schema_elapsed)

        cache_start = perf_counter()
        analytics_cache.status()
        cache_elapsed = round((perf_counter() - cache_start) * 1000, 2)
        record_startup_stage("analytics_cache_load", cache_elapsed)
        logger.info("Startup analytics_cache_load_ms=%s", cache_elapsed)

        total_elapsed = round((perf_counter() - startup_begin) * 1000, 2)
        record_startup_stage("startup", total_elapsed)
        mark_startup_complete()
        logger.info("Startup complete startup_ms=%s", total_elapsed)
    except Exception as erreur:
        logger.error("PostgreSQL indisponible au demarrage: %s", erreur)


@app.get("/")
def root() -> dict:
    return {
        "service": "SP2I CAPEX API",
        "version": "1.0.0",
        "status": "RUNNING",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "health": "/health",
            "upload_dqe": "/dqe/upload",
            "upload_excel": "/api/upload/excel",
            "sync_excel": "/api/upload/excel/sync",
            "extract_dqe": "/dqe/extract",
            "sync_current_dqe": "/dqe/sync-current",
            "optimize_import": "/import/optimize",
            "simulate_capex": "/simulation/simulate",
            "simulate_scenarios": "/simulation/scenarios",
            "list_scenarios": "/simulation/scenarios",
            "scenario_history": "/simulation/scenarios/history",
            "scenario_compare": "/simulation/scenarios/compare",
            "scenario_best": "/simulation/scenarios/best",
            "scenario_analytics": "/simulation/scenarios/analytics",
            "compare_scenarios": "/simulation/compare",
            "decision_rules": "/decision/rules",
            "decision_explain": "/decision/explain/{simulation_id}",
            "decision_risk_analysis": "/decision/risk-analysis/{scenario_id}",
            "procurement_risk_analysis": "/procurement/risk-analysis/{simulation_id}",
            "procurement_lead_time": "/procurement/lead-time/{simulation_id}",
            "procurement_cashflow": "/procurement/cashflow/{simulation_id}",
            "procurement_import_complexity": "/procurement/import-complexity/{simulation_id}",
            "approvals": "/approvals",
            "approval_statuses": "/approvals/statuses",
            "approval_summary": "/approvals/summary/{project_id}",
            "logistics_container_plan": "/logistics/container-plan/{simulation_id}",
            "logistics_shipment_analysis": "/logistics/shipment-analysis/{simulation_id}",
            "logistics_freight_cost": "/logistics/freight-cost/{simulation_id}",
            "logistics_site_delivery": "/logistics/site-delivery/{simulation_id}",
            "capex_summary": "/capex/summary",
            "fact_metre": "/fact_metre",
            "monitoring": "/monitoring/status",
            "analytics_dashboard": "/analytics/dashboard",
            "analytics_kpis": "/analytics/kpis",
            "analytics_debug_pipeline": "/analytics/debug/pipeline",
            "analytics_debug_database": "/analytics/debug/database",
            "analytics_debug_timing": "/analytics/debug/timing",
            "analytics_debug_consistency": "/analytics/debug/consistency",
            "analytics_debug_filter_consistency": "/analytics/debug/filter-consistency",
            "analytics_debug_schema_capabilities": "/analytics/debug/schema-capabilities",
            "analytics_debug_bim_maturity": "/analytics/debug/bim-maturity",
            "analytics_capex_reconciliation": "/analytics/debug/capex-reconciliation/{project_id}",
            "analytics_data_quality": "/analytics/data-quality",
            "docs": "/docs",
        },
        "description": "API metier pour analyse DQE et optimisation CAPEX import/local",
        "frontend": {
            "url": os.getenv("FRONTEND_URL", "http://localhost:5173"),
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "statut": "OK",
        "service": "SP2I CAPEX API",
    }


@app.get("/debug/config")
def debug_config() -> dict:
    """
    Expose une configuration non sensible pour verifier le deploiement cloud.

    Cet endpoint ne renvoie jamais les secrets eux-memes. Il indique seulement
    si les briques critiques sont configurees.
    """
    powerbi_keys = [
        "POWERBI_DIRECTION_URL",
        "POWERBI_FINANCE_URL",
        "POWERBI_IMPORT_URL",
        "POWERBI_CHANTIER_URL",
        "POWERBI_DQE_URL",
    ]
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "render_git_commit": os.getenv("RENDER_GIT_COMMIT", ""),
        "render_service_id": os.getenv("RENDER_SERVICE_ID", ""),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "cors_origins": _get_cors_origins(),
        "frontend_url": os.getenv("FRONTEND_URL", ""),
        "max_upload_mb": os.getenv("MAX_UPLOAD_MB", "25"),
        "powerbi_dashboards_configured": {
            key: bool(os.getenv(key))
            for key in powerbi_keys
        },
    }

@app.get("/debug/database")
def debug_database():
    from app.database import database_url_database, database_url_host, database_url_is_neon, masked_database_url
    from app.database import engine

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT
                current_database() AS database_name,
                COUNT(*) AS fact_metre_count,
                COALESCE(SUM(capex_local), 0) AS capex_local_total
            FROM fact_metre
        """)).mappings().one()

    return {
        "database_url": masked_database_url(),
        "database_url_host": database_url_host(),
        "database_name": row["database_name"] or database_url_database(),
        "is_neon": database_url_is_neon(),
        "fact_metre_count": int(row["fact_metre_count"] or 0),
        "capex_local_total": float(row["capex_local_total"] or 0),
    }
@app.get("/debug/tables")
def debug_tables():
    from sqlalchemy import text
    from app.database import engine

    with engine.connect() as conn:
        tables = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name
        """)).fetchall()

    return {
        "tables": [t[0] for t in tables]
    }
from sqlalchemy import text

@app.get("/debug/render-capex")
def debug_render_capex():
    from app.database import engine

    with engine.connect() as conn:

        fact = conn.execute(text("""
            SELECT COUNT(*) AS nb_lignes,
                   COALESCE(SUM(capex_local),0) AS capex
            FROM fact_metre
        """)).mappings().first()

        vw = conn.execute(text("""
            SELECT *
            FROM vw_capex_summary
        """)).mappings().first()

    return {
        "fact_metre": dict(fact),
        "vw_capex_summary": dict(vw) if vw else None
    }
