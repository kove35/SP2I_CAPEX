from __future__ import annotations

from importlib import import_module

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import dqe

import_routes = import_module("app.routes.import")


app = FastAPI(
    title="SP2I CAPEX API",
    description="API SaaS pour analyse DQE, optimisation import et datasets BI.",
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"statut": "OK", "service": "SP2I CAPEX API"}
