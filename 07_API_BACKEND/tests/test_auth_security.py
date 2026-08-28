from __future__ import annotations

import base64
import json

import pytest
from pydantic import ValidationError

from app.auth.schemas import RegisterRequest
from app.auth.security import create_access_token, decode_access_token, validate_security_configuration
from app.auth.security import hash_password, verify_password


def _encode_json(value: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")


def test_registration_rejects_client_selected_role() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="admin@example.com",
            password="mot-de-passe-solide",
            full_name="Admin auto-proclame",
            role="ADMIN",
        )


def test_production_requires_strong_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SP2I_JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        validate_security_configuration()


def test_access_token_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SP2I_JWT_SECRET", "test-secret-with-at-least-32-characters")
    token = create_access_token("42", {"role": "VIEWER"}, expires_minutes=5)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "VIEWER"
    assert payload["jti"]


def test_access_token_rejects_modified_algorithm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SP2I_JWT_SECRET", "test-secret-with-at-least-32-characters")
    token = create_access_token("42")
    _, payload, signature = token.split(".")
    forged = f'{_encode_json({"alg": "none", "typ": "JWT"})}.{payload}.{signature}'
    assert decode_access_token(forged) is None


def test_password_hash_supports_new_and_legacy_formats() -> None:
    password = "mot-de-passe-solide"
    current_hash = hash_password(password)
    assert verify_password(password, current_hash)
    assert not verify_password("mauvais-mot-de-passe", current_hash)

    import hashlib

    salt = "legacy-salt"
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    assert verify_password(password, f"pbkdf2_sha256${salt}${digest}")
