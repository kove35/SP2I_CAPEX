from __future__ import annotations

import hashlib
import json
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.analytics.cache import analytics_cache
from app.analytics.repositories import AnalyticsRepository
from app.analytics.schemas import AnalyticsQuery


class AnalyticsService:
    """Service applicatif du moteur BI proprietaire SP2I."""

    def __init__(self, db: Session) -> None:
        self.repository = AnalyticsRepository(db)

    def dashboard(self, query: AnalyticsQuery, dashboard_type: str = "direction") -> dict[str, Any]:
        return self._cached(f"dashboard:{dashboard_type}", query, lambda: self._build_dashboard(query, dashboard_type))

    def capex(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("capex", query, lambda: self._build_dashboard(query, "capex"))

    def kpis(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("kpis", query, lambda: self._response(query, kpis=self.repository.kpis(query)))

    def risk(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("risk", query, lambda: self._response(query, charts={"risk_matrix": self.repository.heatmap(query)}))

    def procurement(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("procurement", query, lambda: self._build_dashboard(query, "procurement"))

    def logistics(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("logistics", query, lambda: self._build_dashboard(query, "logistics"))

    def scenarios(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._response(query, table=self.repository.scenarios())

    def heatmap(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._response(query, charts={"heatmap": self.repository.heatmap(query)})

    def drilldown(self, query: AnalyticsQuery) -> dict[str, Any]:
        path = self.repository.drilldown_path(query.drilldown_level)
        grouped = self.repository.grouped(query, default_group=path["next"] or path["current"])
        return self._response(query, charts={"drilldown": grouped}, metadata={"drilldown": path})

    def timeline(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._response(query, charts={"timeline": self.repository.timeline(query)})

    def system_health(self) -> dict[str, Any]:
        return {
            "status": "SUCCESS",
            "filters": {},
            "pagination": {},
            "kpis": {},
            "charts": {},
            "table": [],
            "metadata": {
                "engine": "SP2I Analytics Engine V1",
                "database": "configured",
                "cache": analytics_cache.status(),
            },
        }

    def cache_status(self) -> dict[str, Any]:
        return {
            "status": "SUCCESS",
            "filters": {},
            "pagination": {},
            "kpis": {},
            "charts": {},
            "table": [],
            "metadata": analytics_cache.status(),
        }

    def query_performance(self) -> dict[str, Any]:
        start = perf_counter()
        query = AnalyticsQuery()
        self.repository.kpis(query)
        elapsed_ms = round((perf_counter() - start) * 1000, 2)
        return {
            "status": "SUCCESS",
            "filters": {},
            "pagination": {},
            "kpis": {},
            "charts": {},
            "table": [],
            "metadata": {"last_probe_ms": elapsed_ms, "target_ms": 500},
        }

    def _build_dashboard(self, query: AnalyticsQuery, dashboard_type: str) -> dict[str, Any]:
        table, total = self.repository.table(query)
        group_default = {
            "direction": "lot",
            "capex": "lot",
            "procurement": "famille",
            "logistics": "decision_import",
            "chantier": "batiment",
        }.get(dashboard_type, "lot")
        return self._response(
            query,
            kpis=self.repository.kpis(query),
            charts={
                "bar": self.repository.grouped(query, default_group=group_default),
                "heatmap": self.repository.heatmap(query),
                "timeline": self.repository.timeline(query),
            },
            table=table,
            total=total,
            metadata={"dashboard": dashboard_type, "engine": "SP2I Analytics Engine V1"},
        )

    def _response(
        self,
        query: AnalyticsQuery,
        kpis: dict[str, Any] | None = None,
        charts: dict[str, Any] | None = None,
        table: list[dict[str, Any]] | None = None,
        total: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "status": "SUCCESS",
            "filters": query.filters.model_dump(exclude_none=True),
            "pagination": {
                "page": query.page,
                "page_size": query.page_size,
                "total": total if total is not None else len(table or []),
            },
            "kpis": kpis or {},
            "charts": charts or {},
            "table": table or [],
            "metadata": metadata or {"engine": "SP2I Analytics Engine V1"},
        }

    def _cached(self, prefix: str, query: AnalyticsQuery, builder) -> dict[str, Any]:
        key = f"{prefix}:{hashlib.sha1(query.model_dump_json().encode()).hexdigest()}"
        cached = analytics_cache.get(key)
        if cached:
            cached["metadata"] = {**cached.get("metadata", {}), "cache_hit": True}
            return cached
        value = builder()
        value["metadata"] = {**value.get("metadata", {}), "cache_hit": False}
        analytics_cache.set(key, json.loads(json.dumps(value, default=str)))
        return value
