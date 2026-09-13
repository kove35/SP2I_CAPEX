from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.analytics.schemas import AnalyticsFilters, AnalyticsQuery
from app.analytics.repositories import analytics_repository as repo_module
from app.analytics.repositories.analytics_repository import AnalyticsRepository


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def one(self):
        return self._rows[0]

    def all(self):
        return self._rows


class _FakeDb:
    """Capture le SQL emis (aucune connexion)."""

    def __init__(self, rows):
        self.sql: list[str] = []
        self._rows = rows

    def execute(self, statement, params=None):
        self.sql.append(str(statement))
        return _FakeResult(self._rows)

    @property
    def all_sql(self) -> str:
        return "\n".join(self.sql)


def _repo(columns: set[str], rows) -> AnalyticsRepository:
    repo = AnalyticsRepository.__new__(AnalyticsRepository)
    repo.db = _FakeDb(rows)
    repo._financial_source = lambda: "vw_fact_metre_financial_canonical"  # type: ignore[assignment]
    repo._json_safe = lambda value: value  # type: ignore[assignment]
    repo.get_project_cost_summary = lambda query: {  # type: ignore[assignment]
        "capex_direct": 100.0,
        "capex_import": 0.0,
        "capex_optimise": 90.0,
        "economie_nette": 10.0,
        "indirect_costs": 0.0,
        "site_installation": 0.0,
        "import_logistics": 0.0,
        "contingency": 0.0,
        "total_project_cost": 100.0,
    }
    repo_module.load_table_columns = lambda db, table, schema_name=None, force=False: set(columns)  # type: ignore[assignment]
    return repo


def _query() -> AnalyticsQuery:
    return AnalyticsQuery(filters=AnalyticsFilters(projet="PROJET_TEST"))


BY_LOT_ROW = {
    "lot": "LOT_1",
    "capex_direct": 100,
    "nb_lignes": 1,
    "nb_articles": 1,
    "fallback_legacy_lot_lines": 0,
    "fallback_legacy_lot_capex": 0,
}


class PricingScopeAbsentTest(unittest.TestCase):
    """vw_fact_metre_financial_canonical (prod) n'expose pas pricing_scope."""

    def test_dashboard_direction_sql_omits_pricing_scope_when_absent(self) -> None:
        repo = _repo(columns=set(), rows=[BY_LOT_ROW])
        out = repo.get_dashboard_direction_v6(_query())

        self.assertNotIn("pricing_scope", repo.db.all_sql)
        self.assertIn("0::numeric AS fallback_legacy_lot_lines", repo.db.all_sql)
        self.assertIn("0::numeric AS fallback_legacy_lot_capex", repo.db.all_sql)
        self.assertEqual(out[0]["fallback_legacy_lot_lines"], 0)
        self.assertEqual(out[0]["fallback_legacy_lot_capex"], 0)

    def test_dashboard_direction_sql_keeps_pricing_scope_when_present(self) -> None:
        repo = _repo(columns={"pricing_scope"}, rows=[BY_LOT_ROW])
        repo.get_dashboard_direction_v6(_query())

        self.assertIn("pricing_scope = 'LEGACY_LOT_FALLBACK'", repo.db.all_sql)

    def test_financial_lines_v6_exposes_null_pricing_scope_when_absent(self) -> None:
        repo = _repo(columns=set(), rows=[{"id_ligne": "1", "pricing_scope": None}])
        repo.get_financial_lines_v6(_query())

        self.assertIn("NULL::text AS pricing_scope", repo.db.all_sql)
        self.assertNotIn("decision_import, pricing_scope", repo.db.all_sql)

    def test_financial_lines_v6_keeps_column_when_present(self) -> None:
        repo = _repo(columns={"pricing_scope"}, rows=[{"id_ligne": "1", "pricing_scope": "STANDARD"}])
        repo.get_financial_lines_v6(_query())

        self.assertIn("decision_import, pricing_scope", repo.db.all_sql)
        self.assertNotIn("NULL::text AS pricing_scope", repo.db.all_sql)

    def test_fallback_helper_returns_zero_constants_when_absent(self) -> None:
        repo = _repo(columns=set(), rows=[])
        lines_sql, capex_sql = repo._fallback_legacy_expressions("vw_fact_metre_financial_canonical")
        self.assertEqual(lines_sql, "0::numeric")
        self.assertEqual(capex_sql, "0::numeric")


PRICE_COLUMNS = ("pricing_scope", "pricing_confidence", "price_reference_code")


def _bare_price_references(sql: str) -> list[str]:
    """Colonnes de pricing encore LITes (les alias neutres NULL AS x sont exclus)."""
    cleaned = sql
    for column in PRICE_COLUMNS:
        cleaned = cleaned.replace(f"NULL::text AS {column}", "")
    return [column for column in PRICE_COLUMNS if column in cleaned]


class CostIntelligenceV6PricingScopeTest(unittest.TestCase):
    """vw_cost_intelligence_v6_scoped peut ne pas exposer les colonnes de pricing."""

    def test_sql_returns_neutral_values_when_columns_absent(self) -> None:
        repo = _repo(columns=set(), rows=[{"lot": "LOT_1"}])
        repo.get_cost_intelligence_v6(_query())

        sql = repo.db.all_sql
        for column in PRICE_COLUMNS:
            self.assertIn(f"NULL::text AS {column}", sql)
        self.assertEqual(_bare_price_references(sql), [])
        self.assertIn(f"FROM {repo_module.COST_INTELLIGENCE_V6_SOURCE}", sql)

    def test_sql_keeps_columns_when_present(self) -> None:
        repo = _repo(columns=set(PRICE_COLUMNS), rows=[{"lot": "LOT_1"}])
        repo.get_cost_intelligence_v6(_query())

        sql = repo.db.all_sql
        for column in PRICE_COLUMNS:
            self.assertNotIn(f"NULL::text AS {column}", sql)
            self.assertIn(column, sql)
        self.assertEqual(_bare_price_references(sql), list(PRICE_COLUMNS))


# Colonnes de la couche canonique (phase 026) : aucune lignee projet, aucun
# pricing_scope (le lignage et le pricing BPU sont ajoutes en phase 033).
CANONICAL_COLUMNS = {
    "id_ligne", "lot", "sous_lot", "sous_lot_id", "component_code",
    "designation", "designation_originale", "designation_normalisee",
    "article_code", "code_article", "quantite", "unite",
    "pu_local", "pu_import", "prix_local_fcfa", "prix_import_fcfa", "prix_optimise_fcfa",
    "capex_local", "capex_import", "capex_optimise", "economie", "taux_economie",
    "batiment", "niveau", "appartement", "piece", "decision_import", "fournisseur",
    "famille", "created_at", "date_import",
}


class FinancialLinesV6ProjectLineageTest(unittest.TestCase):
    """canonical n'expose ni projet_id ni project_code (lignage construit en 033)."""

    def test_lines_sql_neutralizes_project_lineage_when_absent(self) -> None:
        repo = _repo(columns=CANONICAL_COLUMNS, rows=[{"id_ligne": "L1"}])
        repo.get_financial_lines_v6(_query())

        sql = repo.db.all_sql
        self.assertIn("NULL::text AS projet_id", sql)
        self.assertIn("NULL::text AS project_code", sql)
        cleaned = sql.replace("NULL::text AS projet_id", "").replace("NULL::text AS project_code", "")
        self.assertNotIn("projet_id", cleaned)
        self.assertNotIn("project_code", cleaned)

    def test_lines_sql_keeps_project_lineage_when_present(self) -> None:
        columns = CANONICAL_COLUMNS | {"projet_id", "project_code", "pricing_scope"}
        repo = _repo(columns=columns, rows=[{"id_ligne": "L1"}])
        repo.get_financial_lines_v6(_query())

        sql = repo.db.all_sql
        self.assertNotIn("NULL::text AS projet_id", sql)
        self.assertNotIn("NULL::text AS project_code", sql)
        self.assertIn("projet_id", sql)
        self.assertIn("project_code", sql)


if __name__ == "__main__":
    unittest.main()
