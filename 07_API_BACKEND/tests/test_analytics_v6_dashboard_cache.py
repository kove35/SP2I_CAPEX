from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.analytics.cache import analytics_cache
from app.analytics.schemas import AnalyticsFilters, AnalyticsQuery
from app.analytics.services.analytics_service import AnalyticsService


def _service_with_builder(builder):
    """Service V6 isole : aucun acces DB (builder, signature et traces stubés)."""
    service = AnalyticsService.__new__(AnalyticsService)
    service.repository = SimpleNamespace(_json_safe=lambda value: value)
    service._fact_metre_cache_signature = lambda: {"signature": "test"}  # type: ignore[assignment]
    service._build_dashboard_v6 = builder  # type: ignore[assignment]
    service._endpoint_from_cache_prefix = lambda prefix: "/analytics/" + str(prefix)  # type: ignore[assignment]
    service._cache_value_summary = lambda value: "test"  # type: ignore[assignment]
    service._trace_endpoint = lambda *args, **kwargs: args[2]  # type: ignore[assignment]
    return service


def _business(payload):
    """Payload hors telemetrie (metadata.cache_* / performance.*) : comparable entre miss et hit."""
    return {key: value for key, value in payload.items() if key != "metadata"}


class DashboardV6CacheTest(unittest.TestCase):
    def setUp(self) -> None:
        analytics_cache.clear()

    def test_dashboard_v6_builder_called_once_for_same_query(self) -> None:
        calls = {"count": 0}

        def builder(query):
            calls["count"] += 1
            return {"status": "SUCCESS", "projet": query.filters.projet}

        service = _service_with_builder(builder)
        query = AnalyticsQuery(filters=AnalyticsFilters(projet="PROJET_TEST"))

        first = service.dashboard_v6(query)
        second = service.dashboard_v6(query)

        # Les donnees metier sont identiques ; seuls les champs de telemetrie
        # (metadata.cache_* / performance.*) different entre miss et hit.
        self.assertEqual(_business(first), _business(second))
        self.assertEqual(calls["count"], 1, "le builder V6 doit etre appele une seule fois (cache)")

    def test_dashboard_v6_cache_separates_projects(self) -> None:
        seen: list[str] = []

        def builder(query):
            seen.append(str(query.filters.projet))
            return {"status": "SUCCESS", "projet": query.filters.projet}

        service = _service_with_builder(builder)
        service.dashboard_v6(AnalyticsQuery(filters=AnalyticsFilters(projet="PROJET_A")))
        service.dashboard_v6(AnalyticsQuery(filters=AnalyticsFilters(projet="PROJET_B")))

        self.assertEqual(seen, ["PROJET_A", "PROJET_B"])


if __name__ == "__main__":
    unittest.main()
