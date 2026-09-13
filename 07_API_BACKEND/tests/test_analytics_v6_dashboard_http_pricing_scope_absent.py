from __future__ import annotations

import os
import unittest
from types import SimpleNamespace


# La config backend lit DATABASE_URL a l'import : valeur factice (jamais connectee,
# la dependance FastAPI get_db est surchargee par un faux session recorder).
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/sp2i_test")

OPTIONAL_PRICE_COLUMNS = ("pricing_scope", "pricing_confidence", "price_reference_code")


def _reads_optional_price_column(sql: str) -> bool:
    """Vrai si le SQL lit reellement une colonne de pricing optionnelle.

    Les alias neutres (``NULL::text AS <colonne>``) conservent le contrat de
    reponse sans lire aucune colonne : ils sont exclus du controle.
    """
    cleaned = sql
    for column in OPTIONAL_PRICE_COLUMNS:
        cleaned = cleaned.replace(f"NULL::text AS {column}", "")
    return any(column in cleaned for column in OPTIONAL_PRICE_COLUMNS)


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def one(self):
        return self._rows[0]

    def all(self):
        return self._rows


class _DashboardFakeDb:
    """Faux session SQLAlchemy : capture le SQL, ne se connecte jamais.

    Reproduit le mode production ou la source financiere
    (vw_fact_metre_financial_canonical) n'expose pas pricing_scope.
    """

    def __init__(self) -> None:
        self.sql: list[str] = []

    def execute(self, statement, params=None):
        sql = str(statement)
        self.sql.append(sql)
        if "AS nb_articles" in sql:
            return _FakeResult(
                [
                    {
                        "lot": "MENUISERIE",
                        "capex_direct": 1000,
                        "nb_lignes": 3,
                        "nb_articles": 2,
                        "fallback_legacy_lot_lines": 0,
                        "fallback_legacy_lot_capex": 0,
                    }
                ]
            )
        if "id_ligne, projet_id" in sql:
            return _FakeResult(
                [
                    {
                        "id_ligne": "L1",
                        "projet_id": "PROJET_TEST",
                        "project_code": "PROJET_TEST",
                        "designation": "Porte",
                        "quantite": 4,
                        "unite": "U",
                        "lot": "MENUISERIE",
                        "article_code": "ART1",
                        "sous_lot": None,
                        "batiment": "B1",
                        "niveau": "RDC",
                        "appartement": None,
                        "piece": None,
                        "famille": "MENUISERIE",
                        "prix_local_fcfa": 250,
                        "prix_import_fcfa": 200,
                        "prix_optimise_fcfa": 220,
                        "capex_local": 1000,
                        "capex_import": 800,
                        "capex_optimise": 880,
                        "economie": 120,
                        "decision_import": "LOCAL",
                        "pricing_scope": None,
                    }
                ]
            )
        if "FROM vw_cost_intelligence_v6_scoped" in sql:
            return _FakeResult(
                [
                    {
                        "lot": "MENUISERIE",
                        "sous_lot": "S1",
                        "article_code": "ART1",
                        "designation": "Porte",
                        "unite": "U",
                        "quantite": 4,
                        "prix_local_fcfa": 250,
                        "prix_import_fcfa": 200,
                        "prix_optimise_fcfa": 220,
                        "capex_local": 1000,
                        "capex_import": 800,
                        "capex_optimise": 880,
                        "economie": 120,
                        "decision_import": "LOCAL",
                        "pricing_scope": None,
                        "pricing_confidence": None,
                        "price_reference_code": None,
                    }
                ]
            )
        return _FakeResult(
            [
                {
                    "nb_lignes": 1,
                    "capex_local_total": 1000,
                    "max_created_at": None,
                    "capex_direct": 1000,
                    "capex_import": 800,
                    "capex_optimise": 880,
                    "economie_nette": 120,
                    "indirect_costs": 110,
                    "site_installation": 42,
                    "import_logistics": 28,
                    "contingency": 120,
                    "total_project_cost": 1300,
                    "capex_direct_per_m2": 10,
                    "total_project_cost_per_m2": 13,
                    "total_project_cost_per_appartement": 130,
                    "total_project_cost_per_niveau": 130,
                    "fallback_legacy_lot_capex": 0,
                    "fallback_legacy_lot_pct": 0,
                }
            ]
        )


class DashboardV6HttpPricingScopeAbsentTest(unittest.TestCase):
    """GET /analytics/v6/dashboard avec une source financiere sans pricing_scope."""

    def setUp(self) -> None:
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except Exception as erreur:  # pragma: no cover - depend de l'environnement
            self.skipTest(f"fastapi/httpx indisponible: {erreur}")
        try:
            from app.analytics.routes.analytics import router as analytics_router
            from app.database import get_db
        except Exception as erreur:  # pragma: no cover - depend de l'environnement
            self.skipTest(f"backend non importable hors DB: {erreur}")

        from app.analytics.cache import analytics_cache
        from app.analytics.repositories import analytics_repository as repo_module
        from app.auth.dependencies import require_analyst

        analytics_cache.clear()
        original = repo_module.load_table_columns

        def _no_pricing_scope(db, table, schema_name=None, force=False):
            return set()

        repo_module.load_table_columns = _no_pricing_scope  # type: ignore[assignment]
        self.addCleanup(lambda: setattr(repo_module, "load_table_columns", original))

        self.fake_db = _DashboardFakeDb()
        app = FastAPI()
        app.include_router(analytics_router, prefix="/analytics")
        app.dependency_overrides[get_db] = lambda: self.fake_db
        # La route est protegee par require_analyst (comme en production) : on
        # surcharge uniquement l'authentification, pas la logique analytics.
        app.dependency_overrides[require_analyst] = lambda: SimpleNamespace(
            id=1, email="audit@sp2i.local", role="ADMIN"
        )
        self.client = TestClient(app)

    def test_dashboard_v6_returns_200_when_pricing_scope_absent(self) -> None:
        response = self.client.get(
            "/analytics/v6/dashboard",
            params={"projet": "PROJET_TEST", "page_size": 100},
        )

        self.assertEqual(response.status_code, 200, response.text[:800])
        body = response.json()
        self.assertEqual(body.get("status"), "SUCCESS")
        # Chemin non spatial : le summary expose capex/pct ; les lignes par lot
        # portent fallback_legacy_lot_lines.
        self.assertEqual(body["kpis"]["fallback_legacy_lot_capex"], 0)
        self.assertEqual(body["kpis"]["fallback_legacy_lot_pct"], 0)
        self.assertEqual(body["table"][0]["fallback_legacy_lot_lines"], 0)
        self.assertEqual(body["table"][0]["fallback_legacy_lot_capex"], 0)
        self.assertEqual(body["lines"][0]["pricing_scope"], None)

        offending = [sql for sql in self.fake_db.sql if _reads_optional_price_column(sql)]
        self.assertEqual(
            offending,
            [],
            "aucun SQL ne doit lire pricing_scope quand la colonne est absente",
        )

    def test_cost_intelligence_v6_returns_200_when_pricing_columns_absent(self) -> None:
        response = self.client.get(
            "/analytics/v6/cost-intelligence",
            params={"projet": "PROJET_TEST", "page_size": 100},
        )

        self.assertEqual(response.status_code, 200, response.text[:800])
        body = response.json()
        self.assertEqual(body.get("status"), "SUCCESS")
        self.assertEqual(body["kpis"]["nb_lignes"], 1)

        offending = [sql for sql in self.fake_db.sql if _reads_optional_price_column(sql)]
        self.assertEqual(
            offending,
            [],
            "aucun SQL ne doit lire les colonnes de pricing quand elles sont absentes",
        )

    def test_dashboard_queries_use_zero_constants(self) -> None:
        self.client.get("/analytics/v6/dashboard", params={"projet": "PROJET_AUTRE", "page_size": 100})

        joins = "\n".join(self.fake_db.sql)
        self.assertIn("0::numeric AS fallback_legacy_lot_lines", joins)
        self.assertIn("0::numeric AS fallback_legacy_lot_capex", joins)
        self.assertIn("NULL::text AS pricing_scope", joins)


if __name__ == "__main__":
    unittest.main()
