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
    assert fact_params["projet"] == "PROJET_MPEMBA"
    assert financial_params["projet"] == "PROJET_MPEMBA"
    assert financial_params["lot"] == "%ELEC%"
