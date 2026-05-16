from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import CalculateurCAPEX, DataCleaner, MapperFamilles
from app.core.logging_config import configure_simulation_logging
from app.services.service_ai_mapping import ServiceAIMapping
from app.services.service_db import ServiceDB
from app.utils.data_lineage import DataLineageTracker


RACINE = Path(__file__).resolve().parents[3]
configure_simulation_logging()
pipeline_logger = logging.getLogger("sp2i.pipeline")


def _lire_csv(chemin: Path) -> list[dict[str, Any]]:
    if not chemin.exists():
        return []

    with chemin.open("r", encoding="utf-8-sig", newline="") as fichier:
        return list(csv.DictReader(fichier, delimiter=";"))


def _ecrire_csv(chemin: Path, lignes: list[dict[str, Any]]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if not lignes:
        chemin.write_text("", encoding="utf-8")
        return

    champs = list(lignes[0].keys())
    with chemin.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=champs, delimiter=";")
        writer.writeheader()
        writer.writerows(lignes)


def _ecrire_json(chemin: Path, donnees: dict[str, Any]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")


class ServicePipeline:
    """Orchestre le pipeline existant puis synchronise PostgreSQL."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.chemin_source = RACINE / "03_DONNEES_ENTREE/dqe/dqe_source_brut.json"
        self.chemin_normalise = RACINE / "03_DONNEES_ENTREE/dqe/dqe_normalise.json"
        self.chemin_enrichi = RACINE / "03_DONNEES_ENTREE/dqe/dqe_enrichi.json"
        self.chemin_parametres = RACINE / "01_PARAMETRES/parametres_import_pointe_noire.json"
        self.chemin_dqe_powerbi = RACINE / "05_RESULTATS/dqe_pret_powerbi.csv"
        self.chemin_optimisation = RACINE / "05_RESULTATS/optimisation_capex_import.csv"
        self.chemin_audit = RACINE / "05_RESULTATS/audit_qualite_dqe.xlsx"
        self.chemin_fact = RACINE / "06_ANALYSE_BI/dataset/FACT_METRE.csv"
        self.chemin_dim_famille = RACINE / "06_ANALYSE_BI/dataset/DIM_FAMILLE.csv"

    def executer_depuis_json(self, contenu: bytes) -> dict[str, Any]:
        try:
            donnees = json.loads(contenu.decode("utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise ValueError("JSON DQE invalide") from exc

        self.chemin_source.parent.mkdir(parents=True, exist_ok=True)
        with self.chemin_source.open("w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier, ensure_ascii=False, indent=2)

        return self.executer_source_courante()

    def executer_depuis_excel(self, contenu: bytes, nom_fichier: str) -> dict[str, Any]:
        """
        Importe un Excel DQE complet sans passer par une extraction partielle.

        Cette methode est additive : elle ne remplace pas `/dqe/upload` JSON.
        Elle sert a fiabiliser le nouveau flux Excel -> PostgreSQL -> Power BI.
        """
        lignes, audit_excel = ServiceAIMapping().extraire_lignes_normalisees(contenu, nom_fichier)
        self.chemin_source.parent.mkdir(parents=True, exist_ok=True)
        with self.chemin_source.open("w", encoding="utf-8") as fichier:
            json.dump(
                {
                    "source": nom_fichier,
                    "lignes": lignes,
                    "audit_excel": audit_excel,
                },
                fichier,
                ensure_ascii=False,
                indent=2,
            )

        resultat = self.executer_source_courante()
        resultat["audit_excel"] = audit_excel
        return resultat

    def executer_source_courante(self) -> dict[str, Any]:
        resultat = self._executer_moteur_backend()

        if resultat.get("status") != "SUCCESS":
            return resultat

        db_sync = self.synchroniser_exports_bi()
        resultat["db_sync"] = db_sync
        resultat.setdefault("logs", []).extend(db_sync.get("logs", []))
        return resultat

    def synchroniser_exports_bi(self) -> dict[str, Any]:
        logs: list[str] = []

        if self.db is None:
            return {
                "status": "SKIPPED",
                "fact_metre": 0,
                "dim_famille": 0,
                "logs": ["DB sync ignored: aucune session DB fournie."],
            }

        try:
            fact_metre = _lire_csv(self.chemin_fact)
            dim_famille = _lire_csv(self.chemin_dim_famille)
            service_db = ServiceDB(self.db)

            # Un run pipeline represente le dataset analytique courant. On
            # remplace donc les anciennes lignes pour eviter de melanger deux
            # sources DQE differentes dans Power BI.
            self.db.execute(text("DELETE FROM fact_metre"))
            self.db.commit()
            logs.append("DB sync OK: ancien FACT_METRE remplace.")

            familles = service_db.insert_dim_famille(dim_famille)
            faits = service_db.insert_fact_metre(fact_metre)
            self._nettoyer_dimensions_orphelines()
            logs.append(f"DB sync OK: {faits} lignes FACT_METRE.")
            logs.append(f"DB sync OK: {familles} lignes DIM_FAMILLE.")

            return {
                "status": "SUCCESS",
                "fact_metre": faits,
                "dim_famille": familles,
                "logs": logs,
            }
        except Exception as erreur:
            self.db.rollback()
            return {
                "status": "ERROR",
                "fact_metre": 0,
                "dim_famille": 0,
                "error": str(erreur),
                "logs": [f"DB sync ERROR: {erreur}"],
            }

    def _nettoyer_dimensions_orphelines(self) -> None:
        """
        Retire les valeurs de dimensions qui ne filtrent plus aucune ligne.

        Cela garde les slicers Power BI propres apres un remplacement complet du
        dataset. Les suppressions ne touchent pas les tables de faits.
        """
        statements = [
            """
            DELETE FROM dim_lot d
            WHERE NOT EXISTS (
                SELECT 1 FROM fact_metre f WHERE f.lot_id = d.lot_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM fact_simulation s WHERE s.lot_id = d.lot_id
            )
            """,
            """
            DELETE FROM dim_niveau d
            WHERE NOT EXISTS (
                SELECT 1 FROM fact_metre f WHERE f.niveau_id = d.niveau_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM fact_simulation s WHERE s.niveau_id = d.niveau_id
            )
            """,
            """
            DELETE FROM dim_batiment d
            WHERE NOT EXISTS (
                SELECT 1 FROM fact_metre f WHERE f.batiment_id = d.batiment_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM fact_simulation s WHERE s.batiment_id = d.batiment_id
            )
            """,
            """
            DELETE FROM dim_famille d
            WHERE NOT EXISTS (
                SELECT 1 FROM fact_metre f WHERE f.famille_id = d.famille_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM fact_simulation s WHERE s.famille_id = d.famille_id
            )
            """,
        ]
        for statement in statements:
            self.db.execute(text(statement))
        self.db.commit()

    def _executer_moteur_backend(self) -> dict[str, Any]:
        """
        Execute le pipeline metier avec les nouvelles couches `app/core`.

        Les scripts historiques dans `04_TRAITEMENT` restent disponibles, mais
        le backend SaaS ne depend plus d'eux pour les calculs critiques.
        """
        logs: list[str] = []
        lineage = DataLineageTracker("service_pipeline")

        try:
            logs.append("STEP 0 - Verification des fichiers et dossiers")
            if not self.chemin_source.exists():
                raise FileNotFoundError(f"Fichier source introuvable: {self.chemin_source}")

            donnees = json.loads(self.chemin_source.read_text(encoding="utf-8-sig"))
            lignes_brutes = donnees.get("lignes", donnees) if isinstance(donnees, dict) else donnees
            if not isinstance(lignes_brutes, list):
                raise ValueError("Le DQE source doit contenir une liste de lignes.")
            lineage.track("source.loaded", rows_out=len(lignes_brutes), fichier=str(self.chemin_source))
            pipeline_logger.info("source.loaded rows=%s file=%s", len(lignes_brutes), self.chemin_source)
            lineage.audit_lots("source.lots", lignes_brutes)

            logs.append("STEP 1 - Nettoyage et normalisation DQE")
            lignes_dqe = DataCleaner().normaliser_lignes(lignes_brutes)
            lineage.track("cleaning.normalized", rows_in=len(lignes_brutes), rows_out=len(lignes_dqe))
            pipeline_logger.info("cleaning.normalized rows_in=%s rows_out=%s", len(lignes_brutes), len(lignes_dqe))
            lineage.audit_lots("cleaning.lots", lignes_dqe)
            _ecrire_json(self.chemin_normalise, {"lignes": lignes_dqe})

            logs.append("STEP 2 - Enrichissement referentiel")
            lignes_enrichies = MapperFamilles().enrichir_familles(lignes_dqe)
            lineage.track("mapping.enriched", rows_in=len(lignes_dqe), rows_out=len(lignes_enrichies))
            pipeline_logger.info("mapping.enriched rows_in=%s rows_out=%s", len(lignes_dqe), len(lignes_enrichies))
            lineage.audit_lots("mapping.lots", lignes_enrichies)
            _ecrire_json(self.chemin_enrichi, {"lignes": lignes_enrichies})
            _ecrire_csv(self.chemin_dqe_powerbi, lignes_enrichies)

            logs.append("STEP 3 - Calcul CAPEX et arbitrage import/local")
            parametres = {}
            if self.chemin_parametres.exists():
                parametres = json.loads(self.chemin_parametres.read_text(encoding="utf-8-sig"))
            lignes_capex = CalculateurCAPEX(parametres).optimiser_lignes(lignes_enrichies)
            lineage.track("simulation.capex", rows_in=len(lignes_enrichies), rows_out=len(lignes_capex))
            pipeline_logger.info("simulation.capex rows_in=%s rows_out=%s", len(lignes_enrichies), len(lignes_capex))
            lineage.audit_lots("simulation.lots", lignes_capex)
            _ecrire_csv(self.chemin_optimisation, lignes_capex)

            logs.append("STEP 4 - Generation datasets Power BI sans logique critique")
            self._generer_dataset_bi(lignes_enrichies, lignes_capex)

            logs.append("STEP 5 - Audit qualite DQE")
            self._generer_audit_qualite(lignes_enrichies)

            return {
                "status": "SUCCESS",
                "resume": self._resume(lignes_dqe, lignes_capex),
                "logs": logs,
                "lineage": lineage.as_dict(),
            }
        except Exception as erreur:
            logs.append(f"ERROR - {erreur}")
            return {"status": "ERROR", "error": str(erreur), "logs": logs}

    def _generer_dataset_bi(self, lignes_dqe: list[dict[str, Any]], lignes_capex: list[dict[str, Any]]) -> None:
        capex_par_id = {
            ligne.get("id_ligne"): ligne
            for ligne in lignes_capex
            if ligne.get("id_ligne")
        }
        mapper = MapperFamilles()
        fact_metre: list[dict[str, Any]] = []
        familles: dict[str, dict[str, Any]] = {}
        signatures_deja_vues: set[tuple[str, str, float, float]] = set()

        for ligne in lignes_dqe:
            quantite = self._valeur_numerique(ligne.get("quantite"))
            prix_total_ht = self._valeur_numerique(ligne.get("prix_total_ht"))
            if quantite <= 0 or prix_total_ht <= 0:
                continue

            signature = (
                self._lot_racine(ligne.get("lot")),
                str(ligne.get("designation", "")).strip().upper(),
                round(quantite, 4),
                round(prix_total_ht, 2),
            )
            if signature in signatures_deja_vues:
                continue
            signatures_deja_vues.add(signature)

            capex = capex_par_id.get(ligne.get("id_ligne"), {})
            famille = str(ligne.get("famille") or "default").lower().strip()
            familles.setdefault(
                famille,
                {
                    "famille": famille,
                    "libelle_famille": famille.replace("_", " ").title(),
                    "categorie_achat": mapper.categorie_achat(famille),
                },
            )
            id_ligne_source = str(ligne.get("id_ligne", "")).strip()
            cle_metier = ligne.get("cle_metier") or "|".join(
                [
                    str(ligne.get("lot", "")),
                    str(ligne.get("batiment", "")),
                    str(ligne.get("niveau", "")),
                    str(id_ligne_source or ligne.get("designation", "")),
                ]
            )
            id_ligne_powerbi = self._id_ligne_powerbi(ligne, id_ligne_source, cle_metier)
            fact_metre.append(
                {
                    # Les DQE multi-feuilles reutilisent souvent 1.1, 1.2...
                    # dans chaque lot. Power BI/PostgreSQL ont besoin d'une
                    # cle technique unique : on utilise donc la cle metier
                    # stabilisee plutot que le numero court de la feuille.
                    "id_ligne": id_ligne_powerbi,
                    "id_ligne_source": id_ligne_source,
                    "cle_metier": cle_metier,
                    "lot": ligne.get("lot", ""),
                    "famille": famille,
                    "batiment": ligne.get("batiment", ""),
                    "niveau": ligne.get("niveau", ""),
                    "designation": ligne.get("designation", ""),
                    "quantite": quantite,
                    "unite": ligne.get("unite", ""),
                    "prix_total_ht": prix_total_ht,
                    "montant_local": prix_total_ht,
                    "PU_IMPORT_HT": self._valeur_numerique(capex.get("PU_IMPORT_HT")),
                    "CAPEX_IMPORT": self._valeur_numerique(capex.get("CAPEX_IMPORT")),
                    "CAPEX_LOCAL": self._valeur_numerique(capex.get("CAPEX_LOCAL")),
                    "ECONOMIE_NETTE": self._valeur_numerique(capex.get("ECONOMIE_NETTE")),
                    "DECISION_IMPORT": capex.get("DECISION_IMPORT", "LOCAL"),
                    "capex_optimise": self._valeur_numerique(capex.get("CAPEX_OPTIMISE", prix_total_ht)),
                    "economie_nette": self._valeur_numerique(capex.get("ECONOMIE_NETTE")),
                    "decision_import": capex.get("DECISION_IMPORT", "LOCAL"),
                    "statut_ligne": ligne.get("statut_ligne", ""),
                }
            )

        _ecrire_csv(self.chemin_fact, fact_metre)
        _ecrire_csv(self.chemin_dim_famille, list(familles.values()))

    def _generer_audit_qualite(self, lignes_dqe: list[dict[str, Any]]) -> None:
        try:
            from openpyxl import Workbook
        except ImportError:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Audit qualite DQE"
        champs = [
            "id_ligne",
            "designation",
            "lot",
            "famille",
            "niveau",
            "type_zone",
            "quantite",
            "prix_total_ht",
            "statut_ligne",
        ]
        ws.append(champs)
        for ligne in lignes_dqe:
            if ligne.get("statut_ligne") != "OK":
                ws.append([ligne.get(champ, "") for champ in champs])
        if ws.max_row == 1:
            ws.append(["-", "Aucune anomalie critique", "-", "-", "-", "-", 0, 0, "OK"])
        self.chemin_audit.parent.mkdir(parents=True, exist_ok=True)
        wb.save(self.chemin_audit)

    def _resume(self, lignes_dqe: list[dict[str, Any]], lignes_capex: list[dict[str, Any]]) -> dict[str, Any]:
        calculateur = CalculateurCAPEX()
        kpi = calculateur.calculer_kpi(lignes_capex)
        return {
            "lignes_dqe": len(lignes_dqe),
            "montant_local": kpi["capex_local"],
            "capex_optimise": kpi["capex_optimise"],
            "economie_nette": kpi["economie_nette"],
            "sorties": {
                "normalise": str(self.chemin_normalise),
                "enrichi": str(self.chemin_enrichi),
                "dqe_powerbi": str(self.chemin_dqe_powerbi),
                "optimisation": str(self.chemin_optimisation),
                "audit": str(self.chemin_audit),
                "fact_metre": str(self.chemin_fact),
                "dim_famille": str(self.chemin_dim_famille),
            },
        }

    def _valeur_numerique(self, valeur: Any) -> float:
        try:
            return float(valeur or 0)
        except (TypeError, ValueError):
            return 0.0

    def _id_ligne_powerbi(self, ligne: dict[str, Any], id_ligne_source: str, cle_metier: str) -> str:
        """
        Produit une cle courte compatible PostgreSQL varchar(100).

        Les numeros 1.1, 1.2 se repetent entre lots. On les prefixe donc par le
        lot. Si le fichier ne donne pas de numero stable, on utilise un hash de
        la cle metier complete.
        """
        lot = str(ligne.get("lot") or "LOT").strip()
        if id_ligne_source:
            candidat = f"{lot}|{id_ligne_source}"
            if len(candidat) <= 100:
                return candidat

        digest = hashlib.sha1(cle_metier.encode("utf-8")).hexdigest()[:16]
        candidat = f"{lot}|{digest}"
        return candidat[:100]

    def _lot_racine(self, valeur: Any) -> str:
        """
        Normalise les variantes de feuilles phase pour detecter les doublons.

        Exemple : `LOT 1`, `LOT 1_PHASE1`, `LOT 1 : PHASE 1` deviennent `LOT 1`.
        """
        texte = str(valeur or "").upper().strip()
        texte = re.sub(r"[_: ]*PHASE\s*1", "", texte)
        texte = re.sub(r"\s+", " ", texte)
        return texte.strip()
