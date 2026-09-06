"""Regression PostgreSQL : perimetre filtre du dashboard V6 (base recette).

Cible : /analytics/v6/dashboard (service.dashboard_v6) sur la base isolee
sp2i_capex_recipe. Verifie que le tableau et les compteurs respectent les
filtres existants (niveau, lot) et qu'une combinaison valide sans resultat
renvoie SUCCESS / nb_lignes=0 / tableau vide / montants 0 / ratios null.

Usage :
    python tests/integration/test_v6_dashboard_filtered_scope.py
"""
from __future__ import annotations

import os

os.environ["SP2I_FINANCIAL_SOURCE"] = "vw_fact_metre_financial_v6"

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.analytics.schemas import AnalyticsFilters, AnalyticsQuery  # noqa: E402
from app.analytics.services import AnalyticsService  # noqa: E402

DATABASE_URL = os.getenv("SP2I_TEST_DATABASE_URL", "postgresql://user:password@localhost:5433/sp2i_capex_recipe")

CHECKS: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    CHECKS.append(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")
    print(("  OK  " if ok else "  FAIL") + f" {name}: {detail}")
    if not ok:
        raise SystemExit(f"regression failed: {name}")


def dashboard(db, projet: str, niveau: str | None = None, lot: str | None = None) -> dict:
    query = AnalyticsQuery(filters=AnalyticsFilters(projet=projet, niveau=niveau, lot=lot))
    return AnalyticsService(db).dashboard_v6(query)


def main() -> int:
    engine = create_engine(DATABASE_URL)
    with Session(engine) as db:
        # 1. Projet A entier (reference conservee).
        a = dashboard(db, "PROJET_A")
        check("A statut SUCCESS", a.get("status") == "SUCCESS", str(a.get("status")))
        check("A capex_direct 3000", float(a["kpis"]["capex_direct"]) == 3000.0, str(a["kpis"]["capex_direct"]))
        check("A nb_lignes 4", int(a["kpis"]["nb_lignes"]) == 4, str(a["kpis"]["nb_lignes"]))
        check("A table 3 lots", len(a["table"]) == 3, str(len(a["table"])))
        check("A somme lots = capex", round(sum(float(r["capex_direct"]) for r in a["table"]), 2) == 3000.0, "3000")

        # 2. Niveau RDC seul (reference conservee).
        rdc = dashboard(db, "PROJET_A", niveau="RDC")
        check("RDC capex_direct 1000", float(rdc["kpis"]["capex_direct"]) == 1000.0, str(rdc["kpis"]["capex_direct"]))
        check("RDC nb_lignes 2", int(rdc["kpis"]["nb_lignes"]) == 2, str(rdc["kpis"]["nb_lignes"]))
        check("RDC table 2 lots", len(rdc["table"]) == 2, str([r["lot"] for r in rdc["table"]]))

        # 3. Combinaison valide sans resultat : RDC + LOT_CVC (CVC uniquement ETAGE1).
        empty = dashboard(db, "PROJET_A", niveau="RDC", lot="LOT_CVC")
        check("filtre-vide statut SUCCESS", empty.get("status") == "SUCCESS", str(empty.get("status")))
        check("filtre-vide nb_lignes 0", int(empty["kpis"]["nb_lignes"]) == 0, str(empty["kpis"]["nb_lignes"]))
        check("filtre-vide nb_lots 0", int(empty["kpis"]["nb_lots"]) == 0, str(empty["kpis"]["nb_lots"]))
        check("filtre-vide table vide", len(empty["table"]) == 0, str(len(empty["table"])))
        check("filtre-vide capex_direct 0", float(empty["kpis"]["capex_direct"]) == 0.0, str(empty["kpis"]["capex_direct"]))
        check("filtre-vide TPC 0", float(empty["kpis"]["total_project_cost"]) == 0.0, str(empty["kpis"]["total_project_cost"]))
        check("filtre-vide capex_m2 null", empty["kpis"].get("capex_m2") is None, str(empty["kpis"].get("capex_m2")))
        check("filtre-vide per_m2 null", empty["kpis"].get("total_project_cost_per_m2") is None,
              str(empty["kpis"].get("total_project_cost_per_m2")))
        check("filtre-vide confiance None", empty["kpis"].get("analytics_confidence") is None,
              str(empty["kpis"].get("analytics_confidence")))

        # 4. Projet B entier (reference conservee, isole).
        b = dashboard(db, "PROJET_B")
        check("B capex_direct 500", float(b["kpis"]["capex_direct"]) == 500.0, str(b["kpis"]["capex_direct"]))
        check("B nb_lignes 1", int(b["kpis"]["nb_lignes"]) == 1, str(b["kpis"]["nb_lignes"]))
        check("B table 1 lot", len(b["table"]) == 1, str([r["lot"] for r in b["table"]]))

        # 5. Projet E : vraies lignes a montant nul (pas un projet vide).
        e = dashboard(db, "PROJET_E")
        check("E nb_lignes 2", int(e["kpis"]["nb_lignes"]) == 2, str(e["kpis"]["nb_lignes"]))
        check("E capex_direct 0 (vrai zero)", float(e["kpis"]["capex_direct"]) == 0.0, str(e["kpis"]["capex_direct"]))
        check("E confiance evaluee (lignes presentes)", e["kpis"].get("analytics_confidence") == "HIGH",
              str(e["kpis"].get("analytics_confidence")))

    print("\nALL_V6_DASHBOARD_FILTERED_SCOPE_CHECKS_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
