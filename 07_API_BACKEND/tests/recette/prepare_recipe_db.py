"""Prepare la base isolee de recette (aucune donnee reelle).

Etapes (reproductibles) :
  1. DATABASE_URL pointe vers sp2i_capex_recipe (PostgreSQL isole 5433).
  2. `Base.metadata.create_all` : tables ORM (users, projects, fact_metre,
     workspace_memberships, dims ORM...). La fonction `ensure_powerbi_schema`
     n'est PAS utilisee : elle rejoue des vues V5 qui exigent la chaine de
     migrations complete (voir doc recette) et echoue sur base vierge.
  3. Application de recipe_v6_schema.sql (vues V6 extraites de 033, faits 100%
     synthetiques, dimensions minimales recreees).
  4. Seed des utilisateurs / projets / membres via les modeles ORM.

Usage (depuis 07_API_BACKEND) :
    python tests/recette/prepare_recipe_db.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5433/sp2i_capex_recipe"
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_STARTUP_SCHEMA_MUTATIONS"] = "false"
os.environ["SP2I_JWT_SECRET"] = "recette-local-secret-change-before-production"
os.environ["SP2I_FINANCIAL_SOURCE"] = "vw_fact_metre_financial_v6"
os.environ["SP2I_FACT_SOURCE"] = "fact_metre"

from app.auth.models import User, WorkspaceMembership  # noqa: E402
from app.auth.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app as _app  # noqa: F401,E402  (enregistre tous les modeles ORM)
from app.projects.models import Project  # noqa: E402

HERE = Path(__file__).resolve().parent


def _apply_recipe_sql() -> None:
    sql_path = HERE / "recipe_v6_schema.sql"
    container = "sp2i_capex_test_pg"
    subprocess.run(
        ["docker", "cp", str(sql_path), f"{container}:/tmp/recipe_v6_schema.sql"],
        check=True,
    )
    proc = subprocess.run(
        [
            "docker", "exec", container, "psql", "-U", "user",
            "-d", "sp2i_capex_recipe", "-v", "ON_ERROR_STOP=1",
            "-f", "/tmp/recipe_v6_schema.sql",
        ],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit("recipe SQL failed")


def _seed_identity() -> None:
    with SessionLocal() as db:
        admin = User(email="admin@recette.local", password_hash=hash_password("Admin123!"),
                     full_name="Admin Recette", role="ADMIN")
        alice = User(email="alice@recette.local", password_hash=hash_password("Alice123!"),
                     full_name="Alice Analyste", role="ANALYST")
        bob = User(email="bob@recette.local", password_hash=hash_password("Bob123!"),
                   full_name="Bob Viewer", role="VIEWER")
        db.add_all([admin, alice, bob])
        db.flush()

        # Projets ORM (ids alignes sur dim_projet 1..4).
        def make_project(pid: int, name: str, owner_id: int) -> Project:
            return Project(id=pid, name=name, client_name="Client Recette",
                           city="Pointe-Noire", country="Congo-Brazzaville",
                           currency="FCFA", owner_id=owner_id, setup_status="CONFIGURED")

        db.add_all([
            make_project(1, "Projet A synthetique", admin.id),
            make_project(2, "Projet B synthetique", admin.id),
            make_project(3, "Projet C vide", admin.id),
            make_project(4, "Projet D geometrie non resolvable", admin.id),
        ])
        db.flush()

        db.add_all([
            # Admin membre de tous les projets (recette : un seul compte voit A/B/C/D).
            WorkspaceMembership(user_id=admin.id, project_id=1, role="ADMIN"),
            WorkspaceMembership(user_id=admin.id, project_id=2, role="ADMIN"),
            WorkspaceMembership(user_id=admin.id, project_id=3, role="ADMIN"),
            WorkspaceMembership(user_id=admin.id, project_id=4, role="ADMIN"),
            WorkspaceMembership(user_id=alice.id, project_id=1, role="MANAGER"),
            WorkspaceMembership(user_id=bob.id, project_id=1, role="VIEWER"),
        ])
        db.commit()
        print("identity seeded", "admin", admin.id, "alice", alice.id, "bob", bob.id)


def main() -> int:
    with engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
    print("database reachable")
    Base.metadata.create_all(bind=engine)
    print("create_all done (ORM tables)")
    _apply_recipe_sql()
    print("recipe V6 SQL applied")
    _seed_identity()
    print("identity seeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
