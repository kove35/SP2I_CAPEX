"""
Tests API pour SP2I CAPEX.

Ces tests verifient que FastAPI expose bien les KPI attendus et que les
reponses API restent coherentes avec PostgreSQL.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from tests.test_database import fetch_one


load_dotenv()

logger = logging.getLogger("sp2i.tests.api")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def api_get(path: str, timeout: int = 10) -> dict[str, Any]:
    """
    Appelle un endpoint GET et retourne le JSON.

    La librairie standard `urllib` evite d'ajouter une dependance inutile.
    """
    url = f"{API_BASE_URL}{path}"
    request = Request(url, method="GET")

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("Erreur HTTP %s sur %s : %s", exc.code, url, body)
        raise RuntimeError(f"Erreur API {exc.code} sur {path} : {body}") from exc
    except URLError:
        logger.exception("API indisponible sur %s.", url)
        raise RuntimeError(f"API indisponible sur {url}") from None


def test_health() -> dict[str, Any]:
    """Test API 1 - Verifie que `/health` repond."""
    data = api_get("/health")
    status = data.get("statut") or data.get("status")

    assert status in {"OK", "RUNNING"}
    logger.info("API /health OK.")
    return {"status": "OK", "response": data}


def test_capex_summary() -> dict[str, Any]:
    """Test API 2 - Verifie que `/capex/summary` retourne les KPI attendus."""
    data = api_get("/capex/summary")

    required_keys = {"capex_local", "capex_optimise", "economie", "lignes"}
    missing_keys = required_keys - set(data)

    assert not missing_keys, f"Cles manquantes dans /capex/summary : {missing_keys}"
    assert float(data["capex_local"]) >= 0
    assert float(data["capex_optimise"]) >= 0
    assert int(data["lignes"]) >= 0

    logger.info("API /capex/summary OK.")
    return {"status": "OK", "response": data}


def test_api_sql_coherence() -> dict[str, Any]:
    """Test API 3 - Compare les KPI API avec les sommes SQL."""
    api_summary = api_get("/capex/summary")
    sql_local, sql_optimise, sql_economie, sql_lignes = fetch_one(
        """
        SELECT
            COALESCE(SUM(prix_total_ht), 0),
            COALESCE(SUM(capex_optimise), 0),
            COALESCE(SUM(economie_nette), 0),
            COUNT(*)
        FROM fact_metre
        """
    )

    sql_summary = {
        "capex_local": round(float(sql_local), 2),
        "capex_optimise": round(float(sql_optimise), 2),
        "economie": round(float(sql_economie), 2),
        "lignes": int(sql_lignes),
    }

    differences = {}
    for key, sql_value in sql_summary.items():
        api_value = api_summary.get(key)
        if isinstance(sql_value, float):
            if abs(float(api_value) - sql_value) > 1.0:
                differences[key] = {"api": api_value, "sql": sql_value}
        elif api_value != sql_value:
            differences[key] = {"api": api_value, "sql": sql_value}

    assert not differences, f"Incoherence API vs SQL : {differences}"
    logger.info("Coherence API vs SQL OK.")
    return {"status": "OK", "api": api_summary, "sql": sql_summary}
