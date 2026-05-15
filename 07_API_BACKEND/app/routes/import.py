from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_service_simulation
from app.services.service_simulation import ServiceSimulation


router = APIRouter()


@router.post("/optimize")
def optimize_import(service: ServiceSimulation = Depends(get_service_simulation)) -> dict:
    """
    Endpoint historique conserve pour compatibilite.

    Il utilise maintenant le service injecte par FastAPI. `ServiceImport` reste
    disponible pour les anciens imports Python, mais la route n'instancie plus
    de service directement.
    """
    return service.simuler_source_courante()
