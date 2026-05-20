from __future__ import annotations

from typing import Any

from app.repositories.scenario_snapshot_repository import ScenarioSnapshotRepository


class ScenarioBenchmarkEngine:
    def __init__(self, snapshot_repository: ScenarioSnapshotRepository) -> None:
        self.snapshot_repository = snapshot_repository

    def rank_scenarios(self, scenario_ids: list[str] | None = None, limit: int = 20) -> dict[str, Any]:
        if scenario_ids:
            candidates = self.snapshot_repository.compare_scenarios(scenario_ids)
        else:
            candidates = self.snapshot_repository.list_scenario_history(limit=limit)

        enhanced = [self._enrich_snapshot(candidate) for candidate in candidates]
        ranked = sorted(enhanced, key=lambda row: row["global_score"], reverse=True)

        return {
            "total": len(ranked),
            "limit": limit,
            "rankings": ranked[:limit],
            "best": ranked[0] if ranked else {},
            "benchmarks": self._build_benchmarks(ranked),
        }

    def best_scenario(self, scenario_ids: list[str] | None = None) -> dict[str, Any]:
        ranking = self.rank_scenarios(scenario_ids=scenario_ids, limit=1)
        return ranking.get("best", {})

    def _enrich_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        snapshot = dict(snapshot)
        snapshot["global_score"] = self._build_global_score(snapshot)
        snapshot["scenario_label"] = snapshot.get("scenario_nom") or snapshot.get("scenario_id")
        return snapshot

    def _build_global_score(self, snapshot: dict[str, Any]) -> float:
        capex_local = float(snapshot.get("capex_local") or 0)
        economie = float(snapshot.get("economie_nette") or 0)
        savings_ratio = (economie / capex_local * 100) if capex_local else 0.0
        decision_score = float(snapshot.get("decision_score_average") or 0)
        risk_score = float(snapshot.get("risk_score_average") or 0)
        lead_time_score = float(snapshot.get("lead_time_score_average") or 0)
        moq_risk = float(snapshot.get("moq_risk_score_average") or 0)

        score = (
            0.3 * min(savings_ratio, 100)
            + 0.25 * decision_score
            + 0.2 * max(0.0, 100.0 - risk_score)
            + 0.15 * lead_time_score
            + 0.1 * max(0.0, 100.0 - moq_risk)
        )
        return round(max(0.0, min(score, 100.0)), 2)

    def _build_benchmarks(self, ranked: list[dict[str, Any]]) -> dict[str, Any]:
        if not ranked:
            return {}

        average = {
            "capex_local": round(sum(item.get("capex_local", 0) for item in ranked) / len(ranked), 2),
            "capex_optimise": round(sum(item.get("capex_optimise", 0) for item in ranked) / len(ranked), 2),
            "economie_nette": round(sum(item.get("economie_nette", 0) for item in ranked) / len(ranked), 2),
            "global_score": round(sum(item.get("global_score", 0) for item in ranked) / len(ranked), 2),
        }
        return {
            "average": average,
            "top_score": ranked[0].get("global_score"),
            "bottom_score": ranked[-1].get("global_score"),
        }
