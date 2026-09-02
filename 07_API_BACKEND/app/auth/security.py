from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


JWT_ALGORITHM = "HS256"
DEVELOPMENT_JWT_SECRET = "sp2i-dev-secret-change-me"
PASSWORD_ITERATIONS = 600_000


def _is_production() -> bool:
    return os.getenv("ENVIRONMENT", "development").strip().lower() in {"prod", "production"}


def get_jwt_secret() -> str:
    secret = os.getenv("SP2I_JWT_SECRET", "").strip()
    if _is_production():
        if not secret or secret == DEVELOPMENT_JWT_SECRET or len(secret) < 32:
            raise RuntimeError(
                "SP2I_JWT_SECRET doit etre configure avec au moins 32 caracteres en production."
            )
        return secret
    return secret or DEVELOPMENT_JWT_SECRET


def validate_security_configuration() -> None:
    get_jwt_secret()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        parts = password_hash.split("$")
        if len(parts) == 4:
            algorithm, iterations_text, salt, digest = parts
            iterations = int(iterations_text)
        elif len(parts) == 3:
            algorithm, salt, digest = parts
            iterations = 120_000
        else:
            return False
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    if iterations < 100_000 or iterations > 2_000_000:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return hmac.compare_digest(candidate, digest)


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _b64url_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(f"{payload}{padding}")


def create_access_token(subject: str, extra: dict[str, Any] | None = None, expires_minutes: int = 720) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "jti": secrets.token_urlsafe(16),
        **(extra or {}),
    }
    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(get_jwt_secret().encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
        header = json.loads(_b64url_decode(header_part).decode("utf-8"))
        if header.get("alg") != JWT_ALGORITHM or header.get("typ") != "JWT":
            return None
        signing_input = f"{header_part}.{payload_part}"
        expected = hmac.new(get_jwt_secret().encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected), signature_part):
            return None
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
        if int(payload.get("exp") or 0) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return payload
    except Exception:
        return None
