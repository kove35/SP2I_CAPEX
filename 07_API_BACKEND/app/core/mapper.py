from __future__ import annotations

from typing import Any


class MapperFamilles:
    """
    Regroupe les petites regles de mapping metier.

    Le repository fournit les donnees de reference, ce mapper applique ensuite
    les regles sans connaitre le format de stockage.
    """

    FAMILLES_TECHNIQUES_IMPORTABLES = {
        "alucobond",
        "ascenseur",
        "climatisation",
        "electricite",
        "menuiserie",
        "plomberie",
    }

    def categorie_achat(self, famille: str) -> str:
        famille = str(famille or "default").lower().strip()
        if famille == "gros_oeuvre":
            return "LOCAL_DOMINANT"
        if famille in self.FAMILLES_TECHNIQUES_IMPORTABLES:
            return "IMPORTABLE"
        return "A_ANALYSER"

    def enrichir_familles(self, lignes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                **ligne,
                "famille": str(ligne.get("famille") or "default").lower().strip(),
                "categorie_achat": self.categorie_achat(str(ligne.get("famille") or "default")),
            }
            for ligne in lignes
        ]
