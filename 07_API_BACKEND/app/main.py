from __future__ import annotations

import logging
import os
import time
from importlib import import_module

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.cloud_migrations import ensure_powerbi_schema
from app.database import Base, SessionLocal, engine
from app.routes import capex, decision, dqe, logistics, monitoring, procurement, simulation, upload
from app.services.monitoring import MonitoringService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sp2i-capex-api")

import_routes = import_module("app.routes.import")


def _get_cors_origins() -> list[str]:
    """
    Charge les origines autorisees depuis l'environnement.

    En local, React et Streamlit peuvent tourner sur des ports differents.
    En cloud, Render doit accepter l'URL publique Streamlit configuree dans
    `CORS_ORIGINS`.
    """
    default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501"
    raw_origins = os.getenv("CORS_ORIGINS", default_origins)
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


app = FastAPI(
    title="SP2I CAPEX API",
    description="API SaaS pour analyse DQE, optimisation import/local et exposition BI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dqe.router, prefix="/dqe", tags=["DQE"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload intelligent"])
app.include_router(import_routes.router, prefix="/import", tags=["Import"])
app.include_router(simulation.router, prefix="/simulation", tags=["Simulation CAPEX"])
app.include_router(decision.router, prefix="/decision", tags=["Decision Engine"])
app.include_router(procurement.router, prefix="/procurement", tags=["Procurement Analytics"])
app.include_router(logistics.router, prefix="/logistics", tags=["Logistics Analytics"])
app.include_router(capex.router, tags=["BI"])
app.include_router(monitoring.router, tags=["Monitoring"])


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
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables PostgreSQL verifiees ou creees.")
        ensure_powerbi_schema(engine)
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
            "compare_scenarios": "/simulation/compare",
            "decision_rules": "/decision/rules",
            "decision_explain": "/decision/explain/{simulation_id}",
            "decision_risk_analysis": "/decision/risk-analysis/{scenario_id}",
            "procurement_risk_analysis": "/procurement/risk-analysis/{simulation_id}",
            "procurement_lead_time": "/procurement/lead-time/{simulation_id}",
            "procurement_cashflow": "/procurement/cashflow/{simulation_id}",
            "procurement_import_complexity": "/procurement/import-complexity/{simulation_id}",
            "logistics_container_plan": "/logistics/container-plan/{simulation_id}",
            "logistics_shipment_analysis": "/logistics/shipment-analysis/{simulation_id}",
            "logistics_freight_cost": "/logistics/freight-cost/{simulation_id}",
            "logistics_site_delivery": "/logistics/site-delivery/{simulation_id}",
            "capex_summary": "/capex/summary",
            "fact_metre": "/fact_metre",
            "monitoring": "/monitoring/status",
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
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "cors_origins": _get_cors_origins(),
        "frontend_url": os.getenv("FRONTEND_URL", ""),
        "max_upload_mb": os.getenv("MAX_UPLOAD_MB", "25"),
        "powerbi_dashboards_configured": {
            key: bool(os.getenv(key))
            for key in powerbi_keys
        },
    }
