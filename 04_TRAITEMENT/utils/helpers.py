from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


def racine_projet() -> Path:
    return Path(__file__).resolve().parents[2]


def lire_json(chemin: str | Path) -> Any:
    with Path(chemin).open("r", encoding="utf-8") as fichier:
        return json.load(fichier)


def ecrire_json(chemin: str | Path, donnees: Any) -> None:
    cible = Path(chemin)
    cible.parent.mkdir(parents=True, exist_ok=True)
    with cible.open("w", encoding="utf-8") as fichier:
        json.dump(donnees, fichier, ensure_ascii=False, indent=2)


def extraire_lignes(donnees: Any) -> list[dict[str, Any]]:
    if isinstance(donnees, dict):
        donnees = donnees.get("lignes", [])
    if not isinstance(donnees, list):
        return []
    return [ligne for ligne in donnees if isinstance(ligne, dict)]


def ecrire_csv(chemin: str | Path, lignes: Iterable[dict[str, Any]], separateur: str = ";") -> None:
    lignes = list(lignes)
    cible = Path(chemin)
    cible.parent.mkdir(parents=True, exist_ok=True)

    if not lignes:
        cible.write_text("", encoding="utf-8")
        return

    champs = list(lignes[0].keys())
    with cible.open("w", newline="", encoding="utf-8-sig") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=champs, delimiter=separateur)
        writer.writeheader()
        writer.writerows(lignes)
