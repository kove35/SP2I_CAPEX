"""
Lanceur global des tests SP2I CAPEX.

Objectif :
- verifier PostgreSQL ;
- verifier la qualite des donnees ;
- verifier les calculs CAPEX ;
- verifier la coherence entre FastAPI et la base.

Commande :
    python run_tests.py
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

from tests import test_api, test_database


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("sp2i.tests.runner")
DEBUG_TESTS = os.getenv("SP2I_TEST_DEBUG", "0") == "1"


TestFunction = Callable[[], dict[str, Any]]


def print_result(label: str, result: dict[str, Any] | None, error: Exception | None = None) -> None:
    """
    Affiche un resultat lisible dans le terminal.

    On garde un format simple pour qu'un debutant comprenne rapidement ce qui
    marche, ce qui est suspect et ce qui bloque.
    """
    if error is not None:
        print(f"[ERROR] {label} - {error}")
        return

    status = (result or {}).get("status", "OK")

    if status == "OK":
        print(f"[OK] {label}")
    elif status == "WARNING":
        print(f"[WARN] {label} - anomalies detectees")
    else:
        print(f"[INFO] {label} - {status}")

    if result:
        details = {key: value for key, value in result.items() if key != "status"}
        if details:
            print(f"       {details}")


def run_test(label: str, function: TestFunction) -> bool:
    """Execute un test et retourne True si le test n'est pas en erreur."""
    try:
        result = function()
        print_result(label, result)
        return True
    except Exception as error:
        if DEBUG_TESTS:
            logger.exception("Test en erreur : %s", label)
        else:
            logger.error("Test en erreur : %s - %s", label, error)
        print_result(label, None, error)
        return False


def main() -> int:
    """Point d'entree principal du script de tests."""
    print("\nSP2I CAPEX - Tests PostgreSQL + API")
    print("=" * 42)

    database_tests: list[tuple[str, TestFunction]] = [
        ("Connexion PostgreSQL", test_database.test_connexion),
        ("Tables fact_metre / dim_famille", test_database.test_tables),
        ("Volume de donnees", test_database.test_volume),
        ("Qualite DQE", test_database.test_qualite),
        ("Coherence CAPEX", test_database.test_capex),
        ("Performance requete famille", test_database.test_performance),
        ("Repartition import/local", test_database.test_import),
    ]

    api_tests: list[tuple[str, TestFunction]] = [
        ("API /health", test_api.test_health),
        ("API /capex/summary", test_api.test_capex_summary),
        ("Coherence API vs SQL", test_api.test_api_sql_coherence),
    ]

    print("\nBase PostgreSQL")
    print("-" * 42)
    database_ok = [run_test(label, function) for label, function in database_tests]

    print("\nAPI FastAPI")
    print("-" * 42)
    api_ok = [run_test(label, function) for label, function in api_tests]

    print("\nSynthese")
    print("-" * 42)

    all_ok = all(database_ok + api_ok)
    quality_score = 0.0

    try:
        quality_score = test_database.score_qualite()
        print(f"[INFO] Score qualite global : {quality_score}%")
    except Exception as error:
        print(f"[WARN] Score qualite non disponible : {error}")

    if all_ok:
        print("[OK] Connexion OK")
        print("[OK] Tables OK")
        print("[OK] Donnees controlees")
        print("[OK] CAPEX coherent")
        print("[OK] API coherente avec PostgreSQL")
        return 0

    print("[ERROR] Certains tests sont en erreur. Voir les logs ci-dessus.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
