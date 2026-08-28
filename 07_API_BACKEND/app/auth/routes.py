from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.auth.models import User
from app.auth.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse, UserRoleUpdate
from app.auth.security import create_access_token, hash_password, verify_password
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


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Un compte existe deja avec cet email.")
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name or payload.email.split("@")[0],
        role="VIEWER",
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


@router.get("/users", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    del current_user
    users = db.scalars(select(User).order_by(User.created_at.desc()).limit(500)).all()
    return [serialize_user(user) for user in users]


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if user.id == current_user.id and payload.role != "ADMIN":
        raise HTTPException(status_code=409, detail="Un administrateur ne peut pas retirer son propre role.")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return serialize_user(user)
