from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.core.parameter_registry_engine import ParameterRegistryEngine


class AuditScoreBreakdown(BaseModel):
    savings_score: float = 0.0
    risk_score: float = 0.0
    lead_time_score: float = 0.0
    criticality_score: float = 0.0
    importability_score: float = 0.0
    procurement_maturity_score: float = 0.0
    final_score: float = 0.0


class AuditParameters(BaseModel):
    registry_version: str
    decision_thresholds: dict[str, Any]
    score_weights: dict[str, Any]
    fill_rate_threshold: float


class AuditTrailEntry(BaseModel):
    timestamp: str
    engine_version: str
    scenario_type: str
    decision: str
    decision_type: str
    final_score: float
    confidence: str
    reason: dict[str, Any]
    line_context: dict[str, Any]
    scores: AuditScoreBreakdown
    parameters: AuditParameters
    parameter_snapshot: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class AuditTrailEngine:
    ENGINE_VERSION = "1.0"

    def __init__(self, registry: ParameterRegistryEngine | None = None) -> None:
        self.registry = registry or ParameterRegistryEngine()

    def build_line_audit(self, line: dict[str, Any]) -> dict[str, Any]:
        decision = line.get("DECISION_FINALE", line.get("DECISION_IMPORT", "LOCAL"))
        decision_type = line.get("DECISION_TYPE", "UNKNOWN")
        final_score = float(line.get("FINAL_DECISION_SCORE", 0.0) or 0.0)
        confidence = str(line.get("DECISION_CONFIDENCE", "UNKNOWN"))
        reason = line.get("DECISION_REASON", {}) if isinstance(line.get("DECISION_REASON"), dict) else {}

        scores = AuditScoreBreakdown(
            savings_score=float(line.get("DECISION_REASON", {}).get("savings_score", 0.0) or 0.0),
            risk_score=float(line.get("DECISION_REASON", {}).get("risk_score", 0.0) or 0.0),
            lead_time_score=float(line.get("DECISION_REASON", {}).get("lead_time_score", 0.0) or 0.0),
            criticality_score=float(line.get("DECISION_REASON", {}).get("criticality_score", 0.0) or 0.0),
            importability_score=float(line.get("DECISION_REASON", {}).get("importability_score", 0.0) or 0.0),
            procurement_maturity_score=float(line.get("DECISION_REASON", {}).get("procurement_maturity_score", 0.0) or 0.0),
            final_score=final_score,
        )

        parameters = AuditParameters(
            registry_version=self.registry.version,
            decision_thresholds=self.registry.get_decision_thresholds().model_dump(),
            score_weights=self.registry.get_score_weights().model_dump(),
            fill_rate_threshold=self.registry.get_fill_rate_threshold(),
        )

        tags = self._extract_tags(line, decision)

        entry = AuditTrailEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            engine_version=self.ENGINE_VERSION,
            scenario_type=str(line.get("DECISION_SCENARIO", "BASELINE")),
            decision=decision,
            decision_type=decision_type,
            final_score=final_score,
            confidence=confidence,
            reason=reason,
            line_context={
                "id_ligne": line.get("id_ligne"),
                "designation": line.get("designation"),
                "famille": line.get("famille"),
                "lot": line.get("lot"),
            },
            scores=scores,
            parameters=parameters,
            parameter_snapshot=self.registry.as_dict(),
            tags=tags,
        )
        return entry.model_dump()

    def build_simulation_audit(self, lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.build_line_audit(line) for line in lines]

    def _extract_tags(self, line: dict[str, Any], decision: str) -> list[str]:
        tags: list[str] = []
        if line.get("IMPORTABILITY_SCORE", 0) < self.registry.get_importability_rules().target_score:
            tags.append("importability_sous_seuil")
        if line.get("HIDDEN_SAVINGS_POTENTIAL", 0) > 0:
            tags.append("hidden_savings_detected")
        if decision == "LOCAL":
            tags.append("local_preference")
        if line.get("GLOBAL_RISK_SCORE", 0) >= 80:
            tags.append("risk_eleve")
        return tags
