from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_service_simulation
from app.repositories import RepositoryScenario, RepositorySimulation
from app.schemas import ScenarioRequest, SimulationRequest, SimulationResponse
from app.services.service_simulation import ServiceSimulation


router = APIRouter()
logger = logging.getLogger("sp2i-capex-api")


@router.post("/simulate", response_model=SimulationResponse)
def simulate_capex(
    demande: SimulationRequest,
    service: ServiceSimulation = Depends(get_service_simulation),
) -> dict:
    """
    Lance une simulation CAPEX temps reel.

    La route ne contient pas de formule metier : elle valide le JSON via
    Pydantic, appelle le service, puis renvoie une reponse stable au frontend.
    """
    return service.simuler(demande)


@router.post("/scenarios")
def simulate_scenarios(
    demande: ScenarioRequest,
    service: ServiceSimulation = Depends(get_service_simulation),
) -> dict:
    """Calcule plusieurs hypotheses de landed cost pour le frontend."""
    return service.analyser_scenarios(demande)


@router.get("/scenarios")
def list_scenarios(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    """Liste les scenarios historises disponibles pour Power BI et React."""
    try:
        scenarios = RepositoryScenario(db).list_scenarios(limit=limit, offset=offset)
    except Exception as erreur:
        logger.error("Historique scenarios indisponible: %s", erreur)
        return {
            "status": "SUCCESS",
            "scenarios": [],
            "warnings": [
                "Historique scenarios indisponible temporairement. Le cockpit reste utilisable sans historique."
            ],
        }
    return {"status": "SUCCESS", "scenarios": scenarios}


@router.get("/scenario/{scenario_id}")
def get_scenario(
    scenario_id: str,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    """Retourne un scenario et ses lignes simulees."""
    scenario_repo = RepositoryScenario(db)
    simulation_repo = RepositorySimulation(db)
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario introuvable.")

    return {
        "status": "SUCCESS",
        "scenario": scenario,
        "lignes": simulation_repo.get_simulation(scenario_id, limit=limit, offset=offset),
    }


@router.get("/compare")
def compare_scenarios(
    scenario_a: str,
    scenario_b: str,
    db: Session = Depends(get_db),
) -> dict:
    """Compare deux scenarios historises via les KPI PostgreSQL."""
    rows = RepositorySimulation(db).compare_simulations(scenario_a, scenario_b)
    return {
        "status": "SUCCESS",
        "scenario_a": scenario_a,
        "scenario_b": scenario_b,
        "comparison": rows,
    }
