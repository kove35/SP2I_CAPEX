from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.security import decode_access_token
from app.database import get_db


ROLE_RANK = {
    "VIEWER": 10,
    "ANALYST": 20,
    "MANAGER": 30,
    "ADMIN": 40,
}


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authentification requise.")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session invalide ou expiree.")

    try:
        user_id = int(payload.get("sub") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Session invalide ou expiree.") from None

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur inactif ou introuvable.")
    return user


def require_min_role(minimum_role: str) -> Callable[..., User]:
    minimum = minimum_role.upper()
    if minimum not in ROLE_RANK:
        raise ValueError(f"Role minimum inconnu: {minimum_role}")

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        current_rank = ROLE_RANK.get(str(current_user.role or "").upper(), 0)
        if current_rank < ROLE_RANK[minimum]:
            raise HTTPException(status_code=403, detail="Droits insuffisants pour cette operation.")
        return current_user

    return dependency


require_analyst = require_min_role("ANALYST")
require_manager = require_min_role("MANAGER")
require_admin = require_min_role("ADMIN")

