from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.auth.models import User
from app.auth.security import hash_password
from app.database import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Cree ou promeut un administrateur SP2I.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Administrateur SP2I")
    args = parser.parse_args()

    password = getpass.getpass("Mot de passe administrateur: ")
    confirmation = getpass.getpass("Confirmer le mot de passe: ")
    if password != confirmation:
        raise SystemExit("Les mots de passe ne correspondent pas.")
    if len(password) < 12:
        raise SystemExit("Le mot de passe doit contenir au moins 12 caracteres.")

    email = args.email.strip().lower()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(password),
                full_name=args.name.strip() or "Administrateur SP2I",
                role="ADMIN",
                is_active=True,
            )
            db.add(user)
        else:
            user.password_hash = hash_password(password)
            user.role = "ADMIN"
            user.is_active = True
        db.commit()
        print(f"Administrateur configure: {email}")


if __name__ == "__main__":
    main()
