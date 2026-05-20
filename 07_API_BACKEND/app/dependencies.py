from __future__ import annotations

from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import RepositoryBPU, RepositoryExcel, RepositoryMapping, RepositorySimulation
from app.services.service_ai_mapping import ServiceAIMapping
from app.services.service_simulation import ServiceSimulation
from app.services.service_scenario_intelligence import ServiceScenarioIntelligence


RACINE = Path(__file__).resolve().parents[2]


def get_repository_bpu() -> RepositoryBPU:
    """Point unique pour brancher fichier, parquet ou stockage objet plus tard."""
    return RepositoryBPU(RACINE)


def get_repository_mapping() -> RepositoryMapping:
    """Point unique pour brancher les referentiels metier."""
    return RepositoryMapping(RACINE)


def get_repository_simulation(db: Session = Depends(get_db)) -> RepositorySimulation:
    """Expose le repository PostgreSQL aux services qui en ont besoin."""
    return RepositorySimulation(db)


def get_repository_excel() -> RepositoryExcel:
    """Lecteur Excel injectable pour les tests et les futurs stockages."""
    return RepositoryExcel()


def get_service_simulation(
    repository_bpu: RepositoryBPU = Depends(get_repository_bpu),
    repository_mapping: RepositoryMapping = Depends(get_repository_mapping),
    db: Session = Depends(get_db),
) -> ServiceSimulation:
    """
    Fabrique un service par requete au lieu d'utiliser un singleton global.

    Cela evite les etats partages dangereux et rend les tests beaucoup plus
    simples : chaque test peut injecter ses propres repositories.
    """
    return ServiceSimulation(
        repository_bpu=repository_bpu,
        repository_mapping=repository_mapping,
        db=db,
    )


def get_service_ai_mapping(
    repository_excel: RepositoryExcel = Depends(get_repository_excel),
    service_simulation: ServiceSimulation = Depends(get_service_simulation),
) -> ServiceAIMapping:
    """Construit le service IA de mapping sans singleton global."""
    return ServiceAIMapping(
        repository_excel=repository_excel,
        service_simulation=service_simulation,
    )


def get_service_scenario_intelligence(
    db: Session = Depends(get_db),
) -> ServiceScenarioIntelligence:
    """Expose l'intelligence des scenarios pour les routes de comparaison et d'analytics."""
    return ServiceScenarioIntelligence(db)
