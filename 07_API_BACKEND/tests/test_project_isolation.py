from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.analytics.repositories.analytics_repository import AnalyticsRepository
from app.analytics.routes.analytics import _enforce_project_scope
from app.analytics.schemas import AnalyticsFilters, AnalyticsQuery
from app.auth.models import User
from app.database import Base
from app.projects.models import Project


def _database() -> tuple[Session, User, User]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.execute(
        text("CREATE TABLE dim_projet (projet_id INTEGER PRIMARY KEY, projet_code TEXT UNIQUE)")
    )
    owner = User(email="owner@example.com", password_hash="x", full_name="Owner", role="ANALYST")
    outsider = User(email="outsider@example.com", password_hash="x", full_name="Outsider", role="ANALYST")
    session.add_all([owner, outsider])
    session.flush()
    session.add(
        Project(
            id=1,
            name="Projet Mpemba",
            owner_id=owner.id,
            status="ACTIVE",
        )
    )
    session.execute(
        text("INSERT INTO dim_projet (projet_id, projet_code) VALUES (1, 'PROJET_MPEMBA')")
    )
    session.commit()
    return session, owner, outsider


def test_analytics_project_scope_accepts_owner_and_rejects_outsider() -> None:
    session, owner, outsider = _database()
    _enforce_project_scope("PROJET_MPEMBA", owner, session)

    with pytest.raises(HTTPException) as error:
        _enforce_project_scope("PROJET_MPEMBA", outsider, session)

    assert error.value.status_code == 404


def test_analytics_project_scope_requires_explicit_project_for_non_admin() -> None:
    session, owner, _ = _database()
    with pytest.raises(HTTPException) as error:
        _enforce_project_scope(None, owner, session)
    assert error.value.status_code == 403


def test_analytics_sql_applies_exact_project_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = AnalyticsRepository(db=object())
    monkeypatch.setattr(repository, "_fact_columns", lambda: {"project_code", "projet_id", "lot"})
    monkeypatch.setattr(
        "app.analytics.repositories.analytics_repository.load_table_columns",
        lambda _db, _source: {"project_code", "projet_id", "lot"},
    )
    query = AnalyticsQuery(filters=AnalyticsFilters(projet="PROJET_MPEMBA", lot="ELEC"))

    fact_sql, fact_params = repository.build_where_clause(query)
    financial_sql, financial_params = repository.build_financial_where_clause(query)

    assert "= LOWER(:projet)" in fact_sql
    assert "= LOWER(:projet)" in financial_sql
    assert "SELECT projet_id FROM dim_projet" in fact_sql
    assert "SELECT projet_id FROM dim_projet" in financial_sql
    assert fact_params["projet"] == "PROJET_MPEMBA"
    assert financial_params["projet"] == "PROJET_MPEMBA"
    assert financial_params["lot"] == "%ELEC%"


def test_analytics_sql_maps_project_code_when_only_numeric_id_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = AnalyticsRepository(db=object())
    monkeypatch.setattr(repository, "_fact_columns", lambda: {"projet_id", "lot"})
    monkeypatch.setattr(
        "app.analytics.repositories.analytics_repository.load_table_columns",
        lambda _db, _source: {"projet_id", "lot"},
    )
    query = AnalyticsQuery(filters=AnalyticsFilters(projet="PROJET_MPEMBA"))

    fact_sql, fact_params = repository.build_where_clause(query)
    financial_sql, financial_params = repository.build_financial_where_clause(query)

    assert "project_code" not in fact_sql
    assert "project_code" not in financial_sql
    assert "projet_id IN (SELECT projet_id FROM dim_projet" in fact_sql
    assert "projet_id IN (SELECT projet_id FROM dim_projet" in financial_sql
    assert fact_params == {"projet": "PROJET_MPEMBA"}
    assert financial_params == {"projet": "PROJET_MPEMBA"}


def test_filter_options_scope_applies_project_predicate_when_columns_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Les options de filtres sont scopees au projet quand la table de faits
    expose project_code/projet_id (anomalie B)."""
    repository = AnalyticsRepository(db=object())
    monkeypatch.setattr(repository, "_fact_columns", lambda: {"project_code", "projet_id", "lot"})
    monkeypatch.setattr(
        "app.analytics.repositories.analytics_repository.load_table_columns",
        lambda _db, _source: {"project_code", "projet_id", "lot"},
    )

    predicate, params = repository._filter_options_scope("PROJET_MPEMBA")

    assert "= LOWER(:projet)" in predicate
    assert "SELECT projet_id FROM dim_projet" in predicate
    assert params == {"projet": "PROJET_MPEMBA"}


def test_filter_options_scope_returns_no_rows_when_project_columns_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Garde-fou : si la table de faits n'a ni project_code ni projet_id, on
    renvoie ``1 = 0`` (aucune option) au lieu d'une erreur SQL
    'column does not exist'."""
    repository = AnalyticsRepository(db=object())
    monkeypatch.setattr(repository, "_fact_columns", lambda: {"lot", "batiment"})
    monkeypatch.setattr(
        "app.analytics.repositories.analytics_repository.load_table_columns",
        lambda _db, _source: {"lot", "batiment"},
    )

    predicate, params = repository._filter_options_scope("PROJET_MPEMBA")

    assert predicate == "1 = 0"
    assert params == {}


def test_filter_options_scope_empty_when_no_project() -> None:
    repository = AnalyticsRepository(db=object())
    predicate, params = repository._filter_options_scope(None)
    assert predicate == ""
    assert params == {}


def test_piece_filter_options_places_scope_inside_subquery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le predicat de portee projet doit s'appliquer DANS la sous-requete (sur
    la table de faits) car project_code/projet_id ne sont pas exposes dans la
    projection exterieure (seul ``value`` l'est)."""
    repository = AnalyticsRepository(db=object())
    monkeypatch.setattr(repository, "_fact_columns", lambda: {"project_code", "projet_id", "piece"})
    monkeypatch.setattr(
        "app.analytics.repositories.analytics_repository.load_table_columns",
        lambda _db, _source: {"project_code", "projet_id", "piece"},
    )
    monkeypatch.setattr(repository, "_piece_sql", lambda: "NULLIF(TRIM(CAST(piece AS text)), '')")
    monkeypatch.setattr(repository, "_normalise_piece_sql", lambda expr: expr)

    # Capture le SQL genere en interceptant db.execute.
    captured: dict[str, str] = {}

    class _FakeResult:
        def scalars(self):
            return self

        def all(self):
            return []

    class _FakeDB:
        def execute(self, statement, params=None):
            captured["sql"] = str(statement)
            captured["params"] = params
            return _FakeResult()

    repository.db = _FakeDB()
    repository._piece_filter_options(projet="PROJET_MPEMBA")

    sql = captured["sql"]
    # Le WHERE projet doit etre a l'interieur de la sous-requete fact_pieces,
    # c'est-a-dire entre ``FROM {fact_source}`` et la fermeture de la sous-requete.
    inner = sql.split(") fact_pieces", 1)[0]
    assert "FROM " in inner
    # Le predicat projet est applique DANS la sous-requete (sur la table de faits).
    assert "LOWER(CAST(project_code AS text)) = LOWER(:projet)" in inner
    # La sous-requete exterieure ne doit PAS referencer project_code hors scope.
    outer_where = sql.split(") fact_pieces", 1)[1]
    assert "project_code" not in outer_where






