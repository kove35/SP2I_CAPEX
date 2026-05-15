from __future__ import annotations

from io import BytesIO
from typing import Any

from openpyxl import load_workbook


class RepositoryExcel:
    """
    Lecture Excel isolee du reste du backend.

    Le service IA recoit des donnees tabulaires simples et ne connait pas
    `openpyxl`. Cela permettra de remplacer le lecteur plus tard si besoin.
    """

    def lire_workbook(self, contenu: bytes) -> dict[str, list[list[Any]]]:
        workbook = load_workbook(BytesIO(contenu), read_only=True, data_only=True)
        feuilles: dict[str, list[list[Any]]] = {}

        for worksheet in workbook.worksheets:
            lignes: list[list[Any]] = []
            for row in worksheet.iter_rows(values_only=True):
                lignes.append(list(row))
            feuilles[worksheet.title] = lignes

        return feuilles
