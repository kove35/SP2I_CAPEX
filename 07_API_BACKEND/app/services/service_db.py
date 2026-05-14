from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import DimFamille, FactMetre


def _nombre(valeur: Any) -> float:
    """Convertit une valeur en float sans faire tomber l'API."""
    try:
        return float(valeur or 0)
    except (TypeError, ValueError):
        return 0.0


def _texte(valeur: Any) -> str:
    """Convertit une valeur en texte propre pour PostgreSQL."""
    return str(valeur or "").strip()


class ServiceDB:
    """Service centralise pour ecrire et lire les tables BI dans PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def insert_fact_metre(self, data: list[dict[str, Any]]) -> int:
        lignes = [
            {
                "id_ligne": _texte(ligne.get("id_ligne")),
                "designation": _texte(ligne.get("designation")),
                "quantite": _nombre(ligne.get("quantite")),
                "prix_total_ht": _nombre(ligne.get("prix_total_ht") or ligne.get("montant_local")),
                "capex_optimise": _nombre(ligne.get("capex_optimise")),
                "economie_nette": _nombre(ligne.get("economie_nette")),
                "decision_import": _texte(ligne.get("decision_import") or "LOCAL"),
                "lot": _texte(ligne.get("lot")),
                "famille": _texte(ligne.get("famille") or "default"),
                "batiment": _texte(ligne.get("batiment")),
                "niveau": _texte(ligne.get("niveau")),
                "statut_ligne": _texte(ligne.get("statut_ligne") or "OK"),
            }
            for ligne in data
            if ligne.get("id_ligne")
        ]

        if not lignes:
            return 0

        statement = pg_insert(FactMetre).values(lignes)
        update_columns = {
            colonne.name: getattr(statement.excluded, colonne.name)
            for colonne in FactMetre.__table__.columns
            if colonne.name not in {"id_ligne", "created_at", "updated_at"}
        }
        update_columns["updated_at"] = func.now()

        statement = statement.on_conflict_do_update(
            index_elements=[FactMetre.id_ligne],
            set_=update_columns,
        )
        self.db.execute(statement)
        self.db.commit()
        return len(lignes)

    def insert_dim_famille(self, data: list[dict[str, Any]]) -> int:
        lignes = [
            {
                "famille": _texte(ligne.get("famille") or "default"),
                "libelle_famille": _texte(ligne.get("libelle_famille") or ligne.get("famille")),
                "categorie_achat": _texte(ligne.get("categorie_achat") or "A_ANALYSER"),
            }
            for ligne in data
            if ligne.get("famille")
        ]

        if not lignes:
            return 0

        statement = pg_insert(DimFamille).values(lignes)
        statement = statement.on_conflict_do_update(
            index_elements=[DimFamille.famille],
            set_={
                "libelle_famille": statement.excluded.libelle_famille,
                "categorie_achat": statement.excluded.categorie_achat,
                "updated_at": func.now(),
            },
        )
        self.db.execute(statement)
        self.db.commit()
        return len(lignes)

    def get_summary(self) -> dict[str, Any]:
        row = self.db.execute(
            select(
                func.coalesce(func.sum(FactMetre.prix_total_ht), 0),
                func.coalesce(func.sum(FactMetre.capex_optimise), 0),
                func.coalesce(func.sum(FactMetre.economie_nette), 0),
                func.count(FactMetre.id_ligne),
            )
        ).one()

        return {
            "capex_local": round(float(row[0]), 2),
            "capex_optimise": round(float(row[1]), 2),
            "economie": round(float(row[2]), 2),
            "lignes": int(row[3]),
        }

    def list_fact_metre(
        self,
        famille: str | None = None,
        lot: str | None = None,
        batiment: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[FactMetre]:
        statement = select(FactMetre).order_by(FactMetre.id_ligne).limit(limit).offset(offset)

        if famille:
            statement = statement.where(FactMetre.famille == famille)
        if lot:
            statement = statement.where(FactMetre.lot == lot)
        if batiment:
            statement = statement.where(FactMetre.batiment == batiment)

        return list(self.db.scalars(statement).all())
