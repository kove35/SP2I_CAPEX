from __future__ import annotations

import logging
import time
from importlib import import_module

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.routes import capex, decision, dqe, monitoring, procurement, simulation, upload
from app.services.monitoring import MonitoringService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sp2i-capex-api")

import_routes = import_module("app.routes.import")

app = FastAPI(
    title="SP2I CAPEX API",
    description="API SaaS pour analyse DQE, optimisation import/local et exposition BI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
    except Exception as erreur:
        logger.error("PostgreSQL indisponible au demarrage: %s", erreur)


@app.get("/")
def root() -> dict:
    return {
        "service": "SP2I CAPEX API",
        "version": "1.0.0",
        "status": "RUNNING",
        "environment": "DEV",
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
            "capex_summary": "/capex/summary",
            "fact_metre": "/fact_metre",
            "monitoring": "/monitoring/status",
            "docs": "/docs",
        },
        "description": "API metier pour analyse DQE et optimisation CAPEX import/local",
        "frontend": {
            "url": "http://localhost:5173",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "statut": "OK",
        "service": "SP2I CAPEX API",
    }
