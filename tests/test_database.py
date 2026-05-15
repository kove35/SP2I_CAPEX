"""
Tests de controle PostgreSQL pour SP2I CAPEX.

Ce fichier peut etre utilise de deux facons :
- directement par `run_tests.py` pour un rapport lisible ;
- par `pytest` plus tard si le projet ajoute une CI.

Les commentaires sont volontairement pedagogiques pour aider un debutant a
comprendre ce qui est controle dans une base data/BI.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Generator
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv

try:
    import psycopg2
    from psycopg2.extensions import connection as PostgresConnection
except ImportError as exc:  # pragma: no cover - message utile si dependance absente.
    try:
        import psycopg as psycopg2
        from psycopg import Connection as PostgresConnection
    except ImportError:
        raise RuntimeError(
            "La dependance PostgreSQL est manquante. Installez psycopg avec : "
            "pip install psycopg[binary]"
        ) from exc


load_dotenv()

logger = logging.getLogger("sp2i.tests.database")

EXPECTED_TABLES = ("fact_metre", "dim_famille")


def get_database_url() -> str:
    """Recupere l'URL PostgreSQL depuis .env ou utilise une valeur locale."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/sp2i_capex",
    )

    # SQLAlchemy peut utiliser `postgresql+psycopg://`.
    # psycopg2 attend plutot `postgresql://`.
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def build_connection_error(error: Exception) -> RuntimeError:
    """
    Transforme une erreur psycopg2 parfois difficile a lire en message clair.

    Sous Windows, PostgreSQL peut renvoyer des messages localises avec des
    accents. Certains drivers les decodent mal, d'ou le cas UnicodeDecodeError.
    """
    if isinstance(error, UnicodeDecodeError):
        return RuntimeError(
            "Connexion PostgreSQL impossible. Verifiez que PostgreSQL est lance, "
            "que DATABASE_URL pointe vers la bonne base, et que l'utilisateur/mot "
            "de passe sont corrects."
        )

    return RuntimeError(f"Connexion PostgreSQL impossible : {error}")


def mask_database_url(database_url: str) -> str:
    """Masque le mot de passe avant d'afficher l'URL dans les logs."""
    parts = urlsplit(database_url)
    if not parts.password:
        return database_url

    username = parts.username or ""
    hostname = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    netloc = f"{username}:***@{hostname}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


@contextmanager
def get_connection() -> Generator[PostgresConnection, None, None]:
    """
    Ouvre puis ferme proprement une connexion PostgreSQL.

    Le `with get_connection()` evite de laisser des connexions ouvertes, ce qui
    est important dans une application SaaS.
    """
    connection = None
    try:
        connection = psycopg2.connect(get_database_url(), connect_timeout=5)
        yield connection
    except Exception as error:
        logger.error(
            "Connexion PostgreSQL impossible. DATABASE_URL=%s",
            mask_database_url(get_database_url()),
        )
        raise build_connection_error(error) from error
    finally:
        if connection is not None:
            connection.close()


def fetch_one(query: str, params: tuple[Any, ...] | None = None) -> tuple[Any, ...]:
    """Execute une requete SQL et retourne une seule ligne."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result or tuple()


def fetch_all(query: str, params: tuple[Any, ...] | None = None) -> list[tuple[Any, ...]]:
    """Execute une requete SQL et retourne toutes les lignes."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return list(cursor.fetchall())


def score_qualite() -> float:
    """
    Calcule le score qualite du DQE en base.

    Formule :
    score = lignes OK / total des lignes
    """
    total, ok = fetch_one(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE COALESCE(statut_ligne, '') = 'OK') AS ok
        FROM fact_metre
        """
    )

    if not total:
        logger.warning("Score qualite non calculable : aucune ligne en base.")
        return 0.0

    return round((float(ok) / float(total)) * 100, 2)


def test_connexion() -> dict[str, Any]:
    """Test 1 - Verifie que PostgreSQL repond avec un SELECT 1."""
    value = fetch_one("SELECT 1")[0]
    assert value == 1
    logger.info("Connexion PostgreSQL OK.")
    return {"status": "OK", "message": "Connexion OK"}


def test_tables() -> dict[str, Any]:
    """Test 2 - Verifie que les tables BI existent."""
    rows = fetch_all(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = ANY(%s)
        ORDER BY table_name
        """,
        (list(EXPECTED_TABLES),),
    )

    tables_found = {row[0] for row in rows}
    missing_tables = sorted(set(EXPECTED_TABLES) - tables_found)

    assert not missing_tables, f"Tables manquantes : {', '.join(missing_tables)}"
    logger.info("Tables PostgreSQL OK : %s.", ", ".join(sorted(tables_found)))
    return {"status": "OK", "tables": sorted(tables_found)}


def test_volume() -> dict[str, Any]:
    """Test 3 - Verifie que les tables contiennent des donnees."""
    fact_count = fetch_one("SELECT COUNT(*) FROM fact_metre")[0]
    dim_count = fetch_one("SELECT COUNT(*) FROM dim_famille")[0]

    warnings = []
    if fact_count == 0:
        warnings.append("fact_metre est vide")
    if dim_count == 0:
        warnings.append("dim_famille est vide")

    if warnings:
        logger.warning("Volume a verifier : %s.", " ; ".join(warnings))
        return {
            "status": "WARNING",
            "fact_metre": fact_count,
            "dim_famille": dim_count,
            "warnings": warnings,
        }

    logger.info("Volume OK : %s lignes FACT, %s familles.", fact_count, dim_count)
    return {"status": "OK", "fact_metre": fact_count, "dim_famille": dim_count}


def test_qualite() -> dict[str, Any]:
    """Test 4 - Detecte les anomalies de quantite, prix et statut qualite."""
    quantite_invalides = fetch_one(
        "SELECT COUNT(*) FROM fact_metre WHERE COALESCE(quantite, 0) <= 0"
    )[0]
    prix_invalides = fetch_one(
        "SELECT COUNT(*) FROM fact_metre WHERE COALESCE(prix_total_ht, 0) <= 0"
    )[0]
    statut_non_ok = fetch_one(
        "SELECT COUNT(*) FROM fact_metre WHERE COALESCE(statut_ligne, '') <> 'OK'"
    )[0]
    score = score_qualite()

    anomalies = int(quantite_invalides) + int(prix_invalides) + int(statut_non_ok)

    if anomalies:
        logger.warning(
            "Anomalies detectees : quantites=%s, prix=%s, statuts=%s, score=%s%%.",
            quantite_invalides,
            prix_invalides,
            statut_non_ok,
            score,
        )
        return {
            "status": "WARNING",
            "quantite_invalides": quantite_invalides,
            "prix_invalides": prix_invalides,
            "statut_non_ok": statut_non_ok,
            "score_qualite": score,
        }

    logger.info("Qualite OK : score=%s%%.", score)
    return {"status": "OK", "score_qualite": score}


def test_capex() -> dict[str, Any]:
    """Test 5 - Verifie les totaux CAPEX et la coherence des economies."""
    capex_local, capex_optimise, economie = fetch_one(
        """
        SELECT
            COALESCE(SUM(prix_total_ht), 0),
            COALESCE(SUM(capex_optimise), 0),
            COALESCE(SUM(economie_nette), 0)
        FROM fact_metre
        """
    )

    capex_local = float(capex_local)
    capex_optimise = float(capex_optimise)
    economie = float(economie)
    expected_economie = capex_local - capex_optimise

    assert capex_local >= 0, "CAPEX local negatif"
    assert capex_optimise >= 0, "CAPEX optimise negatif"
    assert economie >= -0.01, "Economie nette negative"

    # Petite tolerance pour eviter les faux positifs lies aux arrondis.
    if abs(expected_economie - economie) > 1.0:
        logger.warning(
            "Ecart CAPEX : local - optimise = %.2f, economie stockee = %.2f.",
            expected_economie,
            economie,
        )
        return {
            "status": "WARNING",
            "capex_local": round(capex_local, 2),
            "capex_optimise": round(capex_optimise, 2),
            "economie": round(economie, 2),
            "economie_attendue": round(expected_economie, 2),
        }

    logger.info("CAPEX coherent : economie=%.2f.", economie)
    return {
        "status": "OK",
        "capex_local": round(capex_local, 2),
        "capex_optimise": round(capex_optimise, 2),
        "economie": round(economie, 2),
    }


def test_performance() -> dict[str, Any]:
    """Test 6 - Mesure le temps d'une requete filtree par famille."""
    famille = fetch_one(
        """
        SELECT famille
        FROM fact_metre
        WHERE COALESCE(famille, '') <> ''
        GROUP BY famille
        ORDER BY COUNT(*) DESC
        LIMIT 1
        """
    )

    famille_value = famille[0] if famille else ""
    start = time.perf_counter()
    count = fetch_one(
        "SELECT COUNT(*) FROM fact_metre WHERE famille = %s",
        (famille_value,),
    )[0]
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    if duration_ms > 1000:
        logger.warning("Requete lente : %sms pour famille=%s.", duration_ms, famille_value)
        status = "WARNING"
    else:
        logger.info("Performance OK : %sms pour famille=%s.", duration_ms, famille_value)
        status = "OK"

    return {
        "status": status,
        "famille": famille_value,
        "lignes": count,
        "duration_ms": duration_ms,
    }


def test_import() -> dict[str, Any]:
    """Test 7 - Analyse la repartition des decisions LOCAL / IMPORT."""
    rows = fetch_all(
        """
        SELECT COALESCE(decision_import, 'NON_RENSEIGNE') AS decision, COUNT(*)
        FROM fact_metre
        GROUP BY COALESCE(decision_import, 'NON_RENSEIGNE')
        ORDER BY decision
        """
    )

    repartition = {decision: count for decision, count in rows}

    if not repartition:
        logger.warning("Aucune decision import/local trouvee.")
        return {"status": "WARNING", "repartition": repartition}

    logger.info("Repartition import/local OK : %s.", repartition)
    return {"status": "OK", "repartition": repartition}
