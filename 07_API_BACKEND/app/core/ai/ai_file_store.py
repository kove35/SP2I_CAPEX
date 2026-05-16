from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from uuid import uuid4


class AIFileStore:
    """
    Stockage temporaire des analyses IA Excel.

    En production SaaS, ce composant sera remplace par PostgreSQL ou stockage
    objet. Pour la phase actuelle, il permet aux endpoints `/dqe/ai-*` de rester
    compatibles sans laisser l'IA ecrire directement en base.
    """

    _store: dict[str, dict] = {}

    @classmethod
    def save(cls, payload: dict) -> str:
        file_id = str(uuid4())
        cls._store[file_id] = {
            "file_id": file_id,
            "created_at": datetime.utcnow().isoformat(),
            "payload": deepcopy(payload),
            "validated_mapping": None,
        }
        return file_id

    @classmethod
    def get(cls, file_id: str) -> dict | None:
        item = cls._store.get(file_id)
        return deepcopy(item) if item else None

    @classmethod
    def validate_mapping(cls, file_id: str, mapping: list[dict]) -> dict | None:
        item = cls._store.get(file_id)
        if not item:
            return None
        item["validated_mapping"] = deepcopy(mapping)
        item["validated_at"] = datetime.utcnow().isoformat()
        return deepcopy(item)
