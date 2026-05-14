from __future__ import annotations

import logging
import time
from importlib import import_module

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.routes import capex, dqe, monitoring
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
app.include_router(import_routes.router, prefix="/import", tags=["Import"])
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
            "extract_dqe": "/dqe/extract",
            "sync_current_dqe": "/dqe/sync-current",
            "optimize_import": "/import/optimize",
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
