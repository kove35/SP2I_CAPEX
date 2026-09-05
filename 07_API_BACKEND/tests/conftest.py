"""Fixtures partagees de la suite backend.

Cette fixture est limitee au harnais de test : elle ne modifie en rien
l'authentification applicative (les dependances FastAPI d'origine restent
en place en dehors des tests). Elle fournit un utilisateur ADMIN de test en
surchargeant uniquement `get_current_user` via `app.dependency_overrides`,
puis restaure integralement les overrides apres chaque test.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.main import app


@pytest.fixture
def admin_auth() -> None:
    """Authentifie le TestClient en ADMIN sans toucher a l'auth applicative.

    Surpplante `get_current_user` (dependance racine de `require_analyst`,
    `require_manager` et `require_admin`) pour la duree du test uniquement.
    """
    class _Admin:
        id = 1
        email = "admin-test@sp2i.local"
        full_name = "Admin Test"
        role = "ADMIN"
        is_active = True

    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_current_user] = lambda: _Admin()
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.fixture
def client() -> TestClient:
    """TestClient FastAPI partage pour les tests qui en ont besoin."""
    return TestClient(app)
