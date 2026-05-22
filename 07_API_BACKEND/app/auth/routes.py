from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.auth.security import create_access_token, decode_access_token, hash_password, verify_password
from app.database import get_db


router = APIRouter()


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authentification requise.")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session invalide ou expiree.")
    user = db.get(User, int(payload.get("sub") or 0))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur inactif ou introuvable.")
    return user


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Un compte existe deja avec cet email.")
    role = payload.role.upper()
    if role not in {"ADMIN", "MANAGER", "ANALYST", "VIEWER"}:
        role = "VIEWER"
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name or payload.email.split("@")[0],
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), {"role": user.role, "email": user.email})
    return AuthResponse(access_token=token, user=serialize_user(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte desactive.")
    token = create_access_token(str(user.id), {"role": user.role, "email": user.email})
    return AuthResponse(access_token=token, user=serialize_user(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return serialize_user(current_user)
