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

from app.analytics.cache import analytics_cache
from app.core import CalculateurCAPEX, DataCleaner, MapperFamilles
from app.core.logging_config import configure_simulation_logging
from app.core.cleaner import nettoyer_nombre
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
            capex_fact_csv = sum(
                self._valeur_numerique(ligne.get("CAPEX_LOCAL") or ligne.get("capex_local") or ligne.get("montant_local") or ligne.get("prix_total_ht"))
                for ligne in fact_metre
            )

            # Garde-fou important : ne jamais remplacer PostgreSQL par un
            # dataset vide ou sans montant. Cela evite un dashboard Power BI a
            # zero apres un parsing Excel incomplet.
            if not fact_metre or capex_fact_csv <= 0:
                message = (
                    "DB sync blocked: FACT_METRE genere vide ou sans CAPEX_LOCAL positif. "
                    "Verifier mapping quantite/PU/montant avant synchronisation."
                )
                pipeline_logger.error(
                    "db.sync.blocked fact_rows=%s capex_fact_csv=%s",
                    len(fact_metre),
                    capex_fact_csv,
                )
                return {
                    "status": "ERROR",
                    "fact_metre": 0,
                    "dim_famille": 0,
                    "error": message,
                    "logs": [message],
                }

            # Un run pipeline represente le dataset analytique courant. On
            # remplace donc les anciennes lignes pour eviter de melanger deux
            # sources DQE differentes dans Power BI.
            self.db.execute(text("DELETE FROM fact_metre"))
            self.db.commit()
            logs.append("DB sync OK: ancien FACT_METRE remplace.")

            familles = service_db.insert_dim_famille(dim_famille)
            faits = service_db.insert_fact_metre(fact_metre)
            self._nettoyer_dimensions_orphelines()
            total_sql = self.db.execute(text("SELECT COUNT(*) FROM fact_metre")).scalar_one()
            total_capex = self.db.execute(text("SELECT COALESCE(SUM(capex_local), 0) FROM fact_metre")).scalar_one()
            source_quality = self._calculer_qualite_source(total_sql, total_capex)
            self._historiser_import_dqe(source_quality, logs)
            analytics_cache.clear()
            logs.append(f"DB sync OK: {faits} lignes FACT_METRE.")
            logs.append(f"DB sync OK: {familles} lignes DIM_FAMILLE.")
            logs.append(f"DB sync CHECK: {total_sql} lignes presentes dans PostgreSQL.")
            logs.append(f"DB sync CHECK: capex_local total={round(float(total_capex or 0), 2)}.")
            pipeline_logger.info(
                "db.sync.success inserted_fact=%s sql_count=%s capex_local=%s dim_famille=%s",
                faits,
                total_sql,
                total_capex,
                familles,
            )

            return {
                "status": "SUCCESS",
                "fact_metre": faits,
                "dim_famille": familles,
                "fact_metre_sql_count": int(total_sql or 0),
                "capex_local_sql_total": round(float(total_capex or 0), 2),
                "analytics_cache_cleared": True,
                "data_quality": source_quality,
                "logs": logs,
            }
        except Exception as erreur:
            self.db.rollback()
            pipeline_logger.exception("db.sync.error")
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

    def _calculer_qualite_source(self, lignes_fact: Any, capex_fact: Any) -> dict[str, Any]:
        """Reconcilie le dernier fichier source avec le FACT_METRE synchronise."""
        payload: dict[str, Any] = {}
        if self.chemin_source.exists():
            try:
                payload = json.loads(self.chemin_source.read_text(encoding="utf-8-sig"))
            except Exception:
                payload = {}

        lignes_source = payload.get("lignes", []) if isinstance(payload, dict) else []
        audit_excel = payload.get("audit_excel", {}) if isinstance(payload, dict) else {}
        ai_preview = audit_excel.get("ai_preview", {}) if isinstance(audit_excel, dict) else {}
        capex_source = sum(self._montant_local_source(ligne) for ligne in lignes_source if isinstance(ligne, dict))
        capex_fact_float = float(capex_fact or 0)
        ecart = capex_fact_float - capex_source
        ecart_pct = abs(ecart) / capex_source if capex_source else 0
        lignes_excel = int(ai_preview.get("lignes_detectees") or len(lignes_source) or 0)
        lignes_parsees = len(lignes_source)
        lignes_fact_int = int(lignes_fact or 0)
        pertes = max(lignes_excel - lignes_parsees, 0)

        score = 100.0
        if capex_source and ecart_pct > 0.005:
            score -= min(35, ecart_pct * 1000)
        if lignes_excel and lignes_fact_int:
            line_gap = abs(lignes_fact_int - lignes_parsees) / max(lignes_parsees, 1)
            score -= min(25, line_gap * 100)
        if pertes:
            score -= min(15, (pertes / max(lignes_excel, 1)) * 100)
        score = max(0, round(score, 1))

        return {
            "score_qualite": score,
            "fichier": payload.get("source", "") if isinstance(payload, dict) else "",
            "lignes_excel": lignes_excel,
            "lignes_parsees": lignes_parsees,
            "lignes_fact_metre": lignes_fact_int,
            "lignes_rejetees": pertes,
            "capex_source": round(capex_source, 2),
            "capex_fact_metre": round(capex_fact_float, 2),
            "ecart_capex": round(ecart, 2),
            "ecart_capex_pct": round(ecart_pct, 6),
            "lots_detectes": int(ai_preview.get("lots_detected") or 0),
            "colonnes_reconnues": int(ai_preview.get("recognized_columns") or 0),
            "anomalies": audit_excel.get("ai_anomalies", []) if isinstance(audit_excel, dict) else [],
            "sheet_selection": audit_excel.get("sheet_selection", {}) if isinstance(audit_excel, dict) else {},
        }

    def _montant_local_source(self, ligne: dict[str, Any]) -> float:
        quantite = self._valeur_numerique(ligne.get("quantite"))
        pu = self._valeur_numerique(ligne.get("prix_unitaire_ht") or ligne.get("pu_local") or ligne.get("PU_LOCAL"))
        return self._montant_local(ligne, quantite, pu)

    def _historiser_import_dqe(self, quality: dict[str, Any], logs: list[str]) -> None:
        """Stocke un audit minimal du dernier import si la table existe."""
        if self.db is None:
            return
        try:
            self.db.execute(
                text(
                    """
                    INSERT INTO dqe_import_audit (
                        fichier,
                        statut,
                        score_qualite,
                        lignes_excel,
                        lignes_parsees,
                        lignes_fact_metre,
                        capex_source,
                        capex_fact_metre,
                        ecart_capex,
                        ecart_capex_pct,
                        lots_detectes,
                        colonnes_reconnues,
                        anomalies_json,
                        metadata_json
                    )
                    VALUES (
                        :fichier,
                        'SUCCESS',
                        :score_qualite,
                        :lignes_excel,
                        :lignes_parsees,
                        :lignes_fact_metre,
                        :capex_source,
                        :capex_fact_metre,
                        :ecart_capex,
                        :ecart_capex_pct,
                        :lots_detectes,
                        :colonnes_reconnues,
                        CAST(:anomalies_json AS jsonb),
                        CAST(:metadata_json AS jsonb)
                    )
                    """
                ),
                {
                    "fichier": quality.get("fichier", ""),
                    "score_qualite": quality.get("score_qualite", 0),
                    "lignes_excel": quality.get("lignes_excel", 0),
                    "lignes_parsees": quality.get("lignes_parsees", 0),
                    "lignes_fact_metre": quality.get("lignes_fact_metre", 0),
                    "capex_source": quality.get("capex_source", 0),
                    "capex_fact_metre": quality.get("capex_fact_metre", 0),
                    "ecart_capex": quality.get("ecart_capex", 0),
                    "ecart_capex_pct": quality.get("ecart_capex_pct", 0),
                    "lots_detectes": quality.get("lots_detectes", 0),
                    "colonnes_reconnues": quality.get("colonnes_reconnues", 0),
                    "anomalies_json": json.dumps(quality.get("anomalies", []), ensure_ascii=False, default=str),
                    "metadata_json": json.dumps({"sheet_selection": quality.get("sheet_selection", {})}, ensure_ascii=False, default=str),
                },
            )
            self.db.commit()
            logs.append("DB sync OK: audit qualite DQE historise.")
        except Exception as exc:
            self.db.rollback()
            logs.append(f"DB sync WARN: audit qualite non historise ({exc}).")

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
        rejet_quantite = 0
        rejet_montant = 0
        rejet_doublon = 0

        for ligne in lignes_dqe:
            quantite = self._valeur_numerique(ligne.get("quantite"))
            prix_unitaire_ht = self._valeur_numerique(
                ligne.get("prix_unitaire_ht")
                or ligne.get("prix_unitaire")
                or ligne.get("pu")
                or ligne.get("PU")
                or ligne.get("P.U")
            )
            prix_total_ht = self._montant_local(ligne, quantite, prix_unitaire_ht)
            if quantite <= 0:
                rejet_quantite += 1
                continue
            if prix_total_ht <= 0:
                rejet_montant += 1
                continue

            signature = (
                self._lot_racine(ligne.get("lot")),
                str(ligne.get("designation", "")).strip().upper(),
                round(quantite, 4),
                round(prix_total_ht, 2),
            )
            if signature in signatures_deja_vues:
                rejet_doublon += 1
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
                    "prix_unitaire_ht": prix_unitaire_ht,
                    "prix_total_ht": prix_total_ht,
                    "montant_local": prix_total_ht,
                    "PU_IMPORT_HT": self._valeur_numerique(capex.get("PU_IMPORT_HT")),
                    "CAPEX_IMPORT": self._valeur_numerique(capex.get("CAPEX_IMPORT")),
                    "CAPEX_LOCAL": self._valeur_numerique(capex.get("CAPEX_LOCAL") or prix_total_ht),
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
        pipeline_logger.info(
            "dataset_bi.generated source_rows=%s capex_rows=%s fact_rows=%s dim_famille=%s rejected_quantite=%s rejected_montant=%s rejected_duplicates=%s",
            len(lignes_dqe),
            len(lignes_capex),
            len(fact_metre),
            len(familles),
            rejet_quantite,
            rejet_montant,
            rejet_doublon,
        )

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
        return float(nettoyer_nombre(valeur, 0) or 0)

    def _montant_local(self, ligne: dict[str, Any], quantite: float, prix_unitaire_ht: float) -> float:
        """
        Retrouve le montant local avec plusieurs fallbacks Excel.

        Beaucoup de DQE n'appellent pas le montant `prix_total_ht`. Si cette
        valeur n'est pas trouvee mais que quantite et PU existent, on recalcule
        le montant pour ne pas generer un FACT_METRE vide.
        """
        candidats = (
            ligne.get("prix_total_ht"),
            ligne.get("montant_total"),
            ligne.get("montant_ht"),
            ligne.get("total_ht"),
            ligne.get("total"),
            ligne.get("montant"),
            ligne.get("MONTANT_LOCAL"),
            ligne.get("CAPEX_LOCAL"),
        )
        for candidat in candidats:
            montant = self._valeur_numerique(candidat)
            if montant > 0:
                return montant
        if quantite > 0 and prix_unitaire_ht > 0:
            return quantite * prix_unitaire_ht
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
