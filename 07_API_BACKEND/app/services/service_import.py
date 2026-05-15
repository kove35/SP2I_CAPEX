from __future__ import annotations

from app.services.service_simulation import ServiceSimulation


class ServiceImport:
    """
    Adaptateur de compatibilite pour l'ancien endpoint import.

    Le vrai cas d'usage vit maintenant dans `ServiceSimulation`. Cette classe
    permet de conserver les imports existants pendant la migration progressive.
    """

    def __init__(self) -> None:
        self.service_simulation = ServiceSimulation()

    def optimiser_source_courante(self) -> dict:
        return self.service_simulation.simuler_source_courante()
