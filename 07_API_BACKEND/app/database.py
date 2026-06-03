from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Charge le fichier .env local si present. En production SaaS, ces variables
# viennent plutot du cloud, de Docker ou du secret manager.
load_dotenv()

RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/sp2i_capex",
)


def _normalize_database_url(raw_url: str) -> URL:
    if raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif raw_url.startswith("postgres://"):
        # Certains fournisseurs cloud exposent encore le prefixe historique
        # `postgres://`. SQLAlchemy 2 prefere un dialecte explicite.
        raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)

    url = make_url(raw_url)
    query: dict[str, Any] = dict(url.query)
    host = str(url.host or "")
    if "neon.tech" in host.lower() and "sslmode" not in query:
        query["sslmode"] = "require"
    return url.set(query=query)


DATABASE_URL_OBJ = _normalize_database_url(RAW_DATABASE_URL)
DATABASE_URL = DATABASE_URL_OBJ.render_as_string(hide_password=False)

connect_args: dict[str, Any] = {}
if DATABASE_URL_OBJ.drivername.startswith("postgresql+psycopg"):
    connect_args["connect_timeout"] = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "2"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "3"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

engine = create_engine(
    DATABASE_URL_OBJ,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_recycle=DB_POOL_RECYCLE,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Base commune a tous les modeles SQLAlchemy."""


def get_db() -> Generator[Session, None, None]:
    """Ouvre une session DB par requete FastAPI, puis la ferme proprement."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def database_url_host() -> str:
    return str(DATABASE_URL_OBJ.host or "")


def database_url_database() -> str:
    return str(DATABASE_URL_OBJ.database or "")


def database_url_is_neon() -> bool:
    return "neon.tech" in database_url_host().lower()


def masked_database_url() -> str:
    return DATABASE_URL_OBJ.render_as_string(hide_password=True)
