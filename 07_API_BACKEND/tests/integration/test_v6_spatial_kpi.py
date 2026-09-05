"""Test d'integration V6 : filtres spatiaux appliques aux KPI avant aggregation.

S'execute contre le PostgreSQL de test isole (donnees 100% synthetiques) :
    docker exec sp2i_capex_test_pg psql -U user -d sp2i_capex_test ...

Verifie :
- montants attendus pour chaque niveau (RDC=1000, ETAGE1=2000) ;
- somme des montants additifs = total projet (3000) ;
- absence de melange entre projets (PROJET_B isole) ;
- denominateurs des ratios adaptes au perimetre filtre ;
- coherence des KPI derives (indirect 11%, site 4.2%, import 3.5%, contingence 12%).

Usage :
    python tests/integration/test_v6_spatial_kpi.py
"""
from __future__ import annotations

import os
import sys

os.environ["SP2I_FINANCIAL_SOURCE"] = "vw_fact_metre_financial_v6"

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.analytics.repositories.analytics_repository import AnalyticsRepository  # noqa: E402
from app.analytics.schemas import AnalyticsFilters, AnalyticsQuery  # noqa: E402

DATABASE_URL = os.getenv(
    "SP2I_TEST_DATABASE_URL",
    "postgresql://user:password@localhost:5433/sp2i_capex_test",
)

INDIRECT_RATE = 0.11
SITE_RATE = 0.042
IMPORT_LOGISTICS_RATE = 0.035
CONTINGENCY_RATE = 0.12


def _expected_derived(capex_direct: float) -> dict[str, float]:
    indirect = round(capex_direct * INDIRECT_RATE, 2)
    site = round(capex_direct * SITE_RATE, 2)
    import_logistics = round(capex_direct * IMPORT_LOGISTICS_RATE, 2)
    base = capex_direct + indirect + site + import_logistics
    contingency = round(base * CONTINGENCY_RATE, 2)
    total = round(base * (1 + CONTINGENCY_RATE), 2)
    return {
        "indirect_costs": indirect,
        "site_installation": site,
        "import_logistics": import_logistics,
        "contingency": contingency,
        "total_project_cost": total,
    }


def _summary(repo: AnalyticsRepository, projet: str, niveau: str | None = None) -> dict:
    query = AnalyticsQuery(filters=AnalyticsFilters(projet=projet, niveau=niveau))
    return repo.get_project_cost_summary(query)


def _check(name: str, actual: float, expected: float, tol: float = 0.01) -> None:
    if abs(actual - expected) > tol:
        raise AssertionError(
            f"[{name}] attendu={expected} obtenu={actual} (ecart={abs(actual - expected)})"
        )
    print(f"  OK  {name}: {actual} == {expected}")


def main() -> int:
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        # Sanity : la vue V6 de test est bien la source.
        n = session.execute(text("SELECT COUNT(*) FROM vw_fact_metre_financial_v6")).scalar_one()
        assert n == 5, f"attendu 5 lignes synthetiques, obtenu {n}"
        repo = AnalyticsRepository(db=session)

        print("== Projet A - total (aucun filtre spatial) ==")
        total_a = _summary(repo, "PROJET_A")
        _check("capex_direct total A", total_a["capex_direct"], 3000.0)
        _check("capex_import total A", total_a["capex_import"], 900.0)
        _check("capex_optimise total A", total_a["capex_optimise"], 2700.0)
        _check("economie_nette total A", total_a["economie_nette"], 300.0)
        for key, expected in _expected_derived(3000.0).items():
            _check(f"{key} total A", total_a[key], expected)

        print("== Projet A - niveau RDC (capex_direct attendu 1000) ==")
        rdc = _summary(repo, "PROJET_A", niveau="RDC")
        _check("capex_direct RDC", rdc["capex_direct"], 1000.0)
        _check("capex_import RDC", rdc["capex_import"], 300.0)
        _check("capex_optimise RDC", rdc["capex_optimise"], 900.0)
        _check("economie_nette RDC", rdc["economie_nette"], 100.0)
        for key, expected in _expected_derived(1000.0).items():
            _check(f"{key} RDC", rdc[key], expected)

        print("== Projet A - niveau ETAGE1 (capex_direct attendu 2000) ==")
        et1 = _summary(repo, "PROJET_A", niveau="ETAGE1")
        _check("capex_direct ETAGE1", et1["capex_direct"], 2000.0)
        _check("capex_import ETAGE1", et1["capex_import"], 600.0)
        _check("capex_optimise ETAGE1", et1["capex_optimise"], 1800.0)
        _check("economie_nette ETAGE1", et1["economie_nette"], 200.0)
        for key, expected in _expected_derived(2000.0).items():
            _check(f"{key} ETAGE1", et1[key], expected)

        print("== Additivite : RDC + ETAGE1 == total projet A ==")
        _check("capex_direct additif", rdc["capex_direct"] + et1["capex_direct"], total_a["capex_direct"])
        _check("total_project_cost additif", rdc["total_project_cost"] + et1["total_project_cost"], total_a["total_project_cost"])

        print("== Absence de melange inter-projets ==")
        total_b = _summary(repo, "PROJET_B")
        _check("capex_direct total B", total_b["capex_direct"], 500.0)
        rdc_b = _summary(repo, "PROJET_B", niveau="RDC")
        _check("capex_direct B RDC", rdc_b["capex_direct"], 500.0)
        # Aucune ligne de A ne doit fuir dans B.
        assert total_b["capex_direct"] != total_a["capex_direct"]

        print("== Denominateurs adaptes au perimetre ==")
        # RDC : 2 appartements distincts (A-RDC-01, A-RDC-02) -> nb_appartements = 2
        _check("nb_appartements RDC", rdc["nb_appartements"], 2.0)
        # ETAGE1 : 1 appartement distinct -> nb_appartements = 1
        _check("nb_appartements ETAGE1", et1["nb_appartements"], 1.0)
        # Chaque niveau = 1 niveau distinct
        _check("nb_niveaux RDC", rdc["nb_niveaux"], 1.0)
        _check("nb_niveaux ETAGE1", et1["nb_niveaux"], 1.0)
        # Ratio /appartement sur le perimetre RDC = total_RDC / 2
        expected_per_app_rdc = round(rdc["total_project_cost"] / 2.0, 2)
        _check("cost_per_apartment RDC", rdc["cost_per_apartment"], expected_per_app_rdc)

    print("\nALL_V6_SPATIAL_KPI_CHECKS_PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
