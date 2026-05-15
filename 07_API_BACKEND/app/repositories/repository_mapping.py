from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RepositoryMapping:
    """Charge les parametres et referentiels de mapping metier."""

    def __init__(self, racine: Path) -> None:
        self.racine = racine
        self.chemin_parametres_import = racine / "01_PARAMETRES/parametres_import_pointe_noire.json"

    def lire_parametres_import(self) -> dict[str, Any]:
        if not self.chemin_parametres_import.exists():
            return {}

        return json.loads(self.chemin_parametres_import.read_text(encoding="utf-8-sig"))
