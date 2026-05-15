from __future__ import annotations

from typing import Any


class SP2ICapexError(Exception):
    """Erreur metier racine du moteur SP2I CAPEX."""

    code = "SP2I_CAPEX_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class SimulationError(SP2ICapexError):
    """Erreur generale pendant une simulation CAPEX."""

    code = "SIMULATION_ERROR"


class DataQualityError(SP2ICapexError):
    """Erreur de qualite de donnees en mode strict."""

    code = "DATA_QUALITY_ERROR"


class InvalidScenarioError(SP2ICapexError):
    """Erreur de parametrage scenario."""

    code = "INVALID_SCENARIO_ERROR"


class ImportDecisionError(SP2ICapexError):
    """Erreur liee a la decision import/local."""

    code = "IMPORT_DECISION_ERROR"
