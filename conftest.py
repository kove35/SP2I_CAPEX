from __future__ import annotations

import pytest

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.main import app


@pytest.fixture
def admin_auth() -> None:
    """Authenticate API integration tests without weakening production routes."""
    test_admin = User(
        id=1,
        email="ci-admin@sp2i.test",
        password_hash="not-used-in-tests",
        full_name="SP2I CI Admin",
        role="ADMIN",
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: test_admin
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)
