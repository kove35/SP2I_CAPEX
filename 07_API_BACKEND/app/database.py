from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Charge le fichier .env local si present. En production SaaS, ces variables
# viennent plutot du cloud, de Docker ou du secret manager.
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/sp2i_capex",
)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
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
