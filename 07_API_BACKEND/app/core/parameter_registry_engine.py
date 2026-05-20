from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, validator

from app.core.global_parameters import (
    DEFAULT_RATIOS_FOB,
    DEFAULT_SEUIL_DECISION_IMPORT,
    DEFAULT_TAUX_LANDED_COST,
)
from app.core.logistics_parameters import FCL_FILL_RATE_THRESHOLD


class LogisticsRates(BaseModel):
    transport_maritime: float = Field(..., ge=0)
    assurance: float = Field(..., ge=0)
    droits_douane: float = Field(..., ge=0)
    frais_portuaires: float = Field(..., ge=0)
    logistique_locale: float = Field(..., ge=0)


class ScoreWeights(BaseModel):
    weight_savings: float = Field(default=0.30, ge=0)
    weight_risk: float = Field(default=0.25, ge=0)
    weight_lead_time: float = Field(default=0.20, ge=0)
    weight_criticality: float = Field(default=0.10, ge=0)
    weight_importability: float = Field(default=0.10, ge=0)
    weight_procurement_maturity: float = Field(default=0.05, ge=0)

    @validator("weight_procurement_maturity", "weight_importability", "weight_criticality")
    def ensure_sum_below_one(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Les poids doivent etre positifs.")
        return value


class DecisionThresholds(BaseModel):
    seuil_decision_import: float = Field(default=0.97, gt=0, le=2)
    min_import_score: float = Field(default=65, ge=0, le=100)
    min_mixed_score: float = Field(default=45, ge=0, le=100)


class ImportabilityRules(BaseModel):
    minimum_score: float = Field(default=50, ge=0, le=100)
    target_score: float = Field(default=70, ge=0, le=100)
    strict_import_score: float = Field(default=85, ge=0, le=100)


class RegistrySnapshot(BaseModel):
    version: str = Field(default="1.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    logistics_rates: LogisticsRates = Field(default_factory=lambda: LogisticsRates(**DEFAULT_TAUX_LANDED_COST))
    score_weights: ScoreWeights = Field(default_factory=ScoreWeights)
    decision_thresholds: DecisionThresholds = Field(default_factory=DecisionThresholds)
    importability_rules: ImportabilityRules = Field(default_factory=ImportabilityRules)
    ratios_fob: dict[str, float] = Field(default_factory=lambda: deepcopy(DEFAULT_RATIOS_FOB))
    fcl_fill_rate_threshold: float = Field(default=FCL_FILL_RATE_THRESHOLD, ge=0, le=1)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda dt: dt.isoformat()},
    )


def _deep_update(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


class ParameterRegistryEngine:
    """Registre centralise des parametres enterprise pour procurement, logistique et simulation."""

    DEFAULT_VERSION = "1.0"

    def __init__(self, parameters: dict[str, Any] | None = None, version: str | None = None) -> None:
        self.version = version or self.DEFAULT_VERSION
        self._raw_parameters = deepcopy(parameters or {})
        self.registry = self._build_registry(self._raw_parameters)

    def _build_registry(self, overrides: dict[str, Any]) -> RegistrySnapshot:
        base = self._default_registry()
        merged = _deep_update(base, deepcopy(overrides))
        return RegistrySnapshot(**merged)

    def _default_registry(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "logistics_rates": DEFAULT_TAUX_LANDED_COST,
            "score_weights": {
                "weight_savings": 0.30,
                "weight_risk": 0.25,
                "weight_lead_time": 0.20,
                "weight_criticality": 0.10,
                "weight_importability": 0.10,
                "weight_procurement_maturity": 0.05,
            },
            "decision_thresholds": {
                "seuil_decision_import": DEFAULT_SEUIL_DECISION_IMPORT,
                "min_import_score": 65,
                "min_mixed_score": 45,
            },
            "importability_rules": {
                "minimum_score": 50,
                "target_score": 70,
                "strict_import_score": 85,
            },
            "ratios_fob": deepcopy(DEFAULT_RATIOS_FOB),
            "fcl_fill_rate_threshold": FCL_FILL_RATE_THRESHOLD,
        }

    @lru_cache(maxsize=128)
    def get_parameter(self, key_path: str, default: Any = None) -> Any:
        current: Any = self.registry
        for part in key_path.split("."):
            if current is None:
                return default
            if isinstance(current, BaseModel):
                current = getattr(current, part, None)
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return default
        return current if current is not None else default

    def get_logistics_rates(self) -> LogisticsRates:
        return self.registry.logistics_rates

    def get_score_weights(self) -> ScoreWeights:
        return self.registry.score_weights

    def get_decision_thresholds(self) -> DecisionThresholds:
        return self.registry.decision_thresholds

    def get_importability_rules(self) -> ImportabilityRules:
        return self.registry.importability_rules

    def get_fob_ratio(self, famille: str | None = None) -> float:
        if famille is None:
            return self.registry.ratios_fob.get("default", 0.5)
        return self.registry.ratios_fob.get(famille.lower(), self.registry.ratios_fob.get("default", 0.5))

    def get_fill_rate_threshold(self) -> float:
        return self.registry.fcl_fill_rate_threshold

    def update_parameters(self, overrides: dict[str, Any]) -> None:
        self._raw_parameters = _deep_update(self._raw_parameters, overrides)
        self.registry = self._build_registry(self._raw_parameters)
        self.get_parameter.cache_clear()

    def as_dict(self) -> dict[str, Any]:
        return json.loads(self.registry.model_dump_json())

    def describe(self) -> str:
        return (
            f"ParameterRegistryEngine v{self.registry.version} "
            f"created_at={self.registry.created_at.isoformat()}"
        )
