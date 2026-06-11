from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.cleaner import nettoyer_nombre
from app.models import DimFamille, FactMetre
from app.utils.id_normalizer import normalize_id, normalize_optional_id


def _nombre(valeur: Any) -> float:
    return float(nettoyer_nombre(valeur, 0) or 0)


def _texte(valeur: Any) -> str:
    return str(valeur or "").strip()


def _id(valeur: Any, fallback: Any = "") -> str:
    return normalize_optional_id(valeur, fallback)


def _optionnel(valeur: Any) -> Any | None:
    if valeur in (None, ""):
        return None
    return valeur


def _nombre_optionnel(valeur: Any) -> float | None:
    if valeur in (None, ""):
        return None
    return _nombre(valeur)


class RepositorySimulation:
    """
    Repository PostgreSQL pour les tables analytiques CAPEX.

    Il remplace progressivement `ServiceDB` comme couche d'acces aux donnees :
    les services pilotent les cas d'usage, le repository execute les requetes.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def insert_fact_metre(self, data: list[dict[str, Any]]) -> int:
        inserted = 0
        seen: set[str] = set()

        for ligne in data:
            id_ligne = self._fact_metre_key(ligne)
            if not id_ligne or id_ligne in seen:
                continue
            seen.add(id_ligne)

            ids = self._resolve_dimension_ids(ligne, projet_id=None)
            quantite = _nombre(ligne.get("quantite") or ligne.get("QTE"))
            prix_total_ht = _nombre(ligne.get("prix_total_ht") or ligne.get("montant_local") or ligne.get("montant_total"))
            pu_local = _nombre(ligne.get("PU_LOCAL") or ligne.get("pu_local") or ligne.get("prix_unitaire_ht") or ligne.get("prix_unitaire"))
            if prix_total_ht <= 0 and quantite > 0 and pu_local > 0:
                prix_total_ht = quantite * pu_local
            if pu_local <= 0 and quantite > 0 and prix_total_ht > 0:
                pu_local = prix_total_ht / quantite

            capex_local = _nombre(ligne.get("CAPEX_LOCAL") or ligne.get("capex_local") or prix_total_ht)
            if capex_local <= 0 and quantite > 0 and pu_local > 0:
                capex_local = quantite * pu_local
            capex_import = _nombre(ligne.get("CAPEX_IMPORT") or ligne.get("capex_import") or ligne.get("MONTANT_IMPORT") or ligne.get("montant_import"))
            capex_optimise = _nombre(ligne.get("CAPEX_OPTIMISE") or ligne.get("capex_optimise") or capex_local or capex_import)
            economie = _nombre(ligne.get("ECONOMIE_NETTE") or ligne.get("economie") or ligne.get("economie_nette"))
            taux_economie = (economie / capex_local) if capex_local else 0

            self.db.execute(
                text(
                    """
                    INSERT INTO fact_metre (
                        id_ligne,
                        designation,
                        quantite,
                        prix_total_ht,
                        capex_optimise,
                        economie_nette,
                        decision_import,
                        pu_local,
                        pu_import,
                        capex_local,
                        capex_import,
                        economie,
                        taux_economie,
                        lot,
                        lot_id,
                        sous_lot,
                        sous_lot_id,
                        famille,
                        famille_id,
                        article_id,
                        code_article,
                        marque,
                        unite,
                        batiment,
                        batiment_id,
                        batiment_code,
                        niveau,
                        niveau_id,
                        niveau_code,
                        appart,
                        appart_id,
                        appartement_id,
                        appartement_code,
                        piece,
                        piece_id,
                        piece_code,
                        zone_id,
                        type_zone,
                        formule,
                        bim_object_id,
                        objet_bim_id,
                        bim_object,
                        ifc_guid,
                        type_objet,
                        famille_bim,
                        systeme,
                        phase_chantier,
                        altitude,
                        execution_status,
                        workflow_status,
                        eta,
                        risque,
                        fournisseur,
                        import_local,
                        montant_import,
                        decision,
                        bim_maturity,
                        source_file_type,
                        classification,
                        omniclass,
                        uniclass,
                        ifc_type,
                        statut_ligne,
                        projet_id,
                        scenario_id,
                        date_import
                    )
                    VALUES (
                        :id_ligne,
                        :designation,
                        :quantite,
                        :prix_total_ht,
                        :capex_optimise,
                        :economie_nette,
                        :decision_import,
                        :pu_local,
                        :pu_import,
                        :capex_local,
                        :capex_import,
                        :economie,
                        :taux_economie,
                        :lot,
                        :lot_id,
                        :sous_lot,
                        :sous_lot_id,
                        :famille,
                        :famille_id,
                        :article_id,
                        :code_article,
                        :marque,
                        :unite,
                        :batiment,
                        :batiment_id,
                        :batiment_code,
                        :niveau,
                        :niveau_id,
                        :niveau_code,
                        :appart,
                        :appart_id,
                        :appartement_id,
                        :appartement_code,
                        :piece,
                        :piece_id,
                        :piece_code,
                        NULL,
                        :type_zone,
                        :formule,
                        :bim_object_id,
                        NULL,
                        :bim_object,
                        :ifc_guid,
                        :type_objet,
                        :famille_bim,
                        :systeme,
                        :phase_chantier,
                        :altitude,
                        :execution_status,
                        :workflow_status,
                        :eta,
                        :risque,
                        :fournisseur,
                        :import_local,
                        :montant_import,
                        :decision,
                        :bim_maturity,
                        :source_file_type,
                        :classification,
                        :omniclass,
                        :uniclass,
                        :ifc_type,
                        :statut_ligne,
                        :projet_id,
                        NULL,
                        now()
                    )
                    ON CONFLICT (id_ligne) DO UPDATE SET
                        designation = EXCLUDED.designation,
                        quantite = EXCLUDED.quantite,
                        prix_total_ht = EXCLUDED.prix_total_ht,
                        capex_optimise = EXCLUDED.capex_optimise,
                        economie_nette = EXCLUDED.economie_nette,
                        decision_import = EXCLUDED.decision_import,
                        pu_local = EXCLUDED.pu_local,
                        pu_import = EXCLUDED.pu_import,
                        capex_local = EXCLUDED.capex_local,
                        capex_import = EXCLUDED.capex_import,
                        economie = EXCLUDED.economie,
                        taux_economie = EXCLUDED.taux_economie,
                        lot = EXCLUDED.lot,
                        lot_id = EXCLUDED.lot_id,
                        sous_lot = EXCLUDED.sous_lot,
                        sous_lot_id = EXCLUDED.sous_lot_id,
                        famille = EXCLUDED.famille,
                        famille_id = EXCLUDED.famille_id,
                        article_id = EXCLUDED.article_id,
                        code_article = EXCLUDED.code_article,
                        marque = EXCLUDED.marque,
                        unite = EXCLUDED.unite,
                        batiment = EXCLUDED.batiment,
                        batiment_id = EXCLUDED.batiment_id,
                        batiment_code = EXCLUDED.batiment_code,
                        niveau = EXCLUDED.niveau,
                        niveau_id = EXCLUDED.niveau_id,
                        niveau_code = EXCLUDED.niveau_code,
                        appart = EXCLUDED.appart,
                        appart_id = EXCLUDED.appart_id,
                        appartement_id = EXCLUDED.appartement_id,
                        appartement_code = EXCLUDED.appartement_code,
                        piece = EXCLUDED.piece,
                        piece_id = EXCLUDED.piece_id,
                        piece_code = EXCLUDED.piece_code,
                        type_zone = EXCLUDED.type_zone,
                        formule = EXCLUDED.formule,
                        bim_object_id = EXCLUDED.bim_object_id,
                        bim_object = EXCLUDED.bim_object,
                        ifc_guid = EXCLUDED.ifc_guid,
                        type_objet = EXCLUDED.type_objet,
                        famille_bim = EXCLUDED.famille_bim,
                        systeme = EXCLUDED.systeme,
                        phase_chantier = EXCLUDED.phase_chantier,
                        altitude = EXCLUDED.altitude,
                        execution_status = EXCLUDED.execution_status,
                        workflow_status = EXCLUDED.workflow_status,
                        eta = EXCLUDED.eta,
                        risque = EXCLUDED.risque,
                        fournisseur = EXCLUDED.fournisseur,
                        import_local = EXCLUDED.import_local,
                        montant_import = EXCLUDED.montant_import,
                        decision = EXCLUDED.decision,
                        bim_maturity = EXCLUDED.bim_maturity,
                        source_file_type = EXCLUDED.source_file_type,
                        classification = EXCLUDED.classification,
                        omniclass = EXCLUDED.omniclass,
                        uniclass = EXCLUDED.uniclass,
                        ifc_type = EXCLUDED.ifc_type,
                        statut_ligne = EXCLUDED.statut_ligne,
                        projet_id = EXCLUDED.projet_id,
                        date_import = EXCLUDED.date_import,
                        updated_at = now()
                    """
                ),
                {
                    "id_ligne": id_ligne,
                    "designation": _texte(ligne.get("designation")),
                    "quantite": quantite,
                    "prix_total_ht": prix_total_ht,
                    "capex_optimise": capex_optimise,
                    "economie_nette": economie,
                    "decision_import": _texte(ligne.get("DECISION_IMPORT") or ligne.get("decision_import") or ligne.get("DECISION") or ligne.get("decision") or "LOCAL"),
                    "pu_local": pu_local,
                    "pu_import": _nombre(ligne.get("PU_IMPORT_HT") or ligne.get("pu_import") or ligne.get("PU_IMPORT")),
                    "capex_local": capex_local,
                    "capex_import": capex_import,
                    "economie": economie,
                    "taux_economie": taux_economie,
                    "lot": _texte(ligne.get("lot")),
                    "lot_id": ids["lot_id"],
                    "sous_lot": _texte(ligne.get("sous_lot")),
                    "sous_lot_id": _id(ligne.get("sous_lot_code") or ligne.get("SOUS_LOT_ID"), ligne.get("sous_lot")),
                    "famille": _texte(ligne.get("famille") or "default"),
                    "famille_id": ids["famille_id"],
                    "article_id": _id(ligne.get("article_id") or ligne.get("ARTICLE_ID"), id_ligne),
                    "code_article": _id(ligne.get("code_article") or ligne.get("CODE_ARTICLE")),
                    "marque": _texte(ligne.get("MARQUE") or ligne.get("marque")),
                    "unite": _texte(ligne.get("unite") or ligne.get("UNITE") or ligne.get("unit")),
                    "batiment": _texte(ligne.get("batiment")),
                    "batiment_id": ids["batiment_id"],
                    "batiment_code": _id(ligne.get("batiment_code") or ligne.get("BATIMENT_ID"), ligne.get("batiment")),
                    "niveau": _texte(ligne.get("niveau")),
                    "niveau_id": ids["niveau_id"],
                    "niveau_code": _id(ligne.get("niveau_code") or ligne.get("NIVEAU_ID"), ligne.get("niveau")),
                    "appart": _texte(
                        ligne.get("appart")
                        or _id(ligne.get("appartement_code") or ligne.get("APPARTEMENT_ID"), ligne.get("appart"))
                    ),
                    "appart_id": ids.get("appart_id"),
                    "appartement_id": _id(ligne.get("appartement_code") or ligne.get("APPARTEMENT_ID"), ligne.get("appart")),
                    "appartement_code": _id(ligne.get("appartement_code") or ligne.get("APPARTEMENT_ID"), ligne.get("appart")),
                    "piece": _texte(
                        ligne.get("piece")
                        or _id(ligne.get("piece_code") or ligne.get("PIECE_ID"), ligne.get("piece"))
                    ),
                    "piece_id": ids.get("piece_id"),
                    "piece_code": _id(ligne.get("piece_code") or ligne.get("PIECE_ID"), ligne.get("piece")),
                    "type_zone": _texte(ligne.get("type_zone")),
                    "formule": _texte(ligne.get("formule")),
                    "bim_object_id": _texte(ligne.get("bim_object_id")),
                    "bim_object": _texte(ligne.get("bim_object") or ligne.get("BIM_OBJECT")),
                    "ifc_guid": _texte(ligne.get("ifc_guid")),
                    "type_objet": _texte(ligne.get("type_objet")),
                    "famille_bim": _texte(ligne.get("famille_bim")),
                    "systeme": _texte(ligne.get("systeme")),
                    "phase_chantier": _texte(ligne.get("phase_chantier")),
                    "altitude": _nombre_optionnel(ligne.get("ALTITUDE") or ligne.get("altitude")),
                    "execution_status": _texte(ligne.get("EXECUTION_STATUS") or ligne.get("execution_status")),
                    "workflow_status": _texte(ligne.get("WORKFLOW_STATUS") or ligne.get("workflow_status")),
                    "eta": _optionnel(ligne.get("ETA") or ligne.get("eta")),
                    "risque": _texte(ligne.get("RISQUE") or ligne.get("risque") or ligne.get("RISK_LEVEL") or ligne.get("risk_level")),
                    "fournisseur": _texte(ligne.get("FOURNISSEUR") or ligne.get("fournisseur") or ligne.get("supplier")),
                    "import_local": _texte(ligne.get("IMPORT_LOCAL") or ligne.get("import_local") or ligne.get("DECISION") or ligne.get("decision") or ligne.get("DECISION_IMPORT") or ligne.get("decision_import")),
                    "montant_import": _nombre(ligne.get("MONTANT_IMPORT") or ligne.get("montant_import") or ligne.get("capex_import")),
                    "decision": _texte(ligne.get("DECISION") or ligne.get("decision") or ligne.get("DECISION_IMPORT") or ligne.get("decision_import")),
                    "bim_maturity": _texte(ligne.get("BIM_MATURITY") or ligne.get("bim_maturity")),
                    "source_file_type": _texte(ligne.get("SOURCE") or ligne.get("source_file_type")),
                    "classification": _texte(ligne.get("classification")),
                    "omniclass": _texte(ligne.get("omniclass")),
                    "uniclass": _texte(ligne.get("uniclass")),
                    "ifc_type": _texte(ligne.get("ifc_type")),
                    "statut_ligne": _texte(ligne.get("statut_ligne") or "OK"),
                    "projet_id": ids["projet_id"],
                },
            )
            inserted += 1

        self.db.commit()
        return inserted

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
            text(
                """
                SELECT
                    COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0) AS capex_local,
                    COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0) AS capex_optimise,
                    COALESCE(SUM(economie), 0) AS economie,
                    COUNT(*) AS lignes
                FROM fact_metre
                """
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

    def save_simulation_lines(
        self,
        simulation_id: str,
        scenario_id: str,
        run_id: str,
        lignes: list[dict[str, Any]],
        projet_id: int | None = None,
    ) -> int:
        """
        Sauvegarde les lignes simulees dans fact_simulation.

        Les dimensions sont creees/retrouvees par texte pour garder le service
        simple et compatible avec les simulations ad hoc du frontend.
        """
        simulation_uuid = str(UUID(simulation_id.replace("sim_", ""))) if simulation_id.startswith("sim_") else str(UUID(simulation_id))
        scenario_uuid = str(UUID(scenario_id.replace("scenario_", ""))) if scenario_id.startswith("scenario_") else str(UUID(scenario_id))
        run_uuid = str(UUID(run_id.replace("run_", ""))) if run_id.startswith("run_") else str(UUID(run_id))

        inserted = 0
        for ligne in lignes:
            ids = self._resolve_dimension_ids(ligne, projet_id)
            self.db.execute(
                text(
                    """
                    INSERT INTO fact_simulation (
                        simulation_id,
                        scenario_id,
                        run_id,
                        projet_id,
                        id_ligne,
                        lot_id,
                        famille_id,
                        niveau_id,
                        batiment_id,
                        designation,
                        quantite,
                        pu_local,
                        pu_import,
                        capex_local,
                        capex_import,
                        capex_optimise,
                        economie,
                        taux_economie,
                        decision_import,
                        score_confiance,
                        statut_qualite,
                        decision_score,
                        risk_score,
                        lead_time_score,
                        criticality_score,
                        decision_reason,
                        decision_type,
                        decision_confidence,
                        global_risk_score,
                        lead_time_days,
                        cashflow_score,
                        moq_risk_score,
                        complexity_score,
                        procurement_reason,
                        container_strategy,
                        shipment_strategy,
                        fill_rate,
                        shipment_cost,
                        lead_time_total,
                        storage_cost,
                        delivery_risk,
                        logistics_reason,
                        supplier_id,
                        country_id
                    )
                    VALUES (
                        CAST(:simulation_id AS uuid),
                        CAST(:scenario_id AS uuid),
                        CAST(:run_id AS uuid),
                        :projet_id,
                        :id_ligne,
                        :lot_id,
                        :famille_id,
                        :niveau_id,
                        :batiment_id,
                        :designation,
                        :quantite,
                        :pu_local,
                        :pu_import,
                        :capex_local,
                        :capex_import,
                        :capex_optimise,
                        :economie,
                        :taux_economie,
                        :decision_import,
                        :score_confiance,
                        :statut_qualite,
                        :decision_score,
                        :risk_score,
                        :lead_time_score,
                        :criticality_score,
                        CAST(:decision_reason AS jsonb),
                        :decision_type,
                        :decision_confidence,
                        :global_risk_score,
                        :lead_time_days,
                        :cashflow_score,
                        :moq_risk_score,
                        :complexity_score,
                        CAST(:procurement_reason AS jsonb),
                        :container_strategy,
                        :shipment_strategy,
                        :fill_rate,
                        :shipment_cost,
                        :lead_time_total,
                        :storage_cost,
                        :delivery_risk,
                        CAST(:logistics_reason AS jsonb),
                        :supplier_id,
                        :country_id
                    )
                    """
                ),
                {
                    "simulation_id": simulation_uuid,
                    "scenario_id": scenario_uuid,
                    "run_id": run_uuid,
                    "projet_id": ids["projet_id"],
                    "id_ligne": _texte(ligne.get("id_ligne")),
                    "lot_id": ids["lot_id"],
                    "famille_id": ids["famille_id"],
                    "niveau_id": ids["niveau_id"],
                    "batiment_id": ids["batiment_id"],
                    "designation": _texte(ligne.get("designation")),
                    "quantite": _nombre(ligne.get("QTE") or ligne.get("quantite")),
                    "pu_local": _nombre(ligne.get("PU_LOCAL") or ligne.get("pu_local")),
                    "pu_import": _nombre(ligne.get("PU_IMPORT_HT") or ligne.get("pu_import")),
                    "capex_local": _nombre(ligne.get("CAPEX_LOCAL") or ligne.get("capex_local")),
                    "capex_import": _nombre(ligne.get("CAPEX_IMPORT") or ligne.get("capex_import")),
                    "capex_optimise": _nombre(ligne.get("CAPEX_OPTIMISE") or ligne.get("capex_optimise")),
                    "economie": _nombre(ligne.get("ECONOMIE_NETTE") or ligne.get("economie")),
                    "taux_economie": _nombre(ligne.get("TAUX_ECONOMIE") or 0),
                    "decision_import": _texte(ligne.get("DECISION_IMPORT") or ligne.get("decision_import") or "LOCAL"),
                    "score_confiance": _nombre(ligne.get("SCORE_CONFIANCE") or ligne.get("score_confiance")),
                    "statut_qualite": _texte(ligne.get("statut_ligne") or "OK"),
                    "decision_score": _nombre(ligne.get("FINAL_DECISION_SCORE") or ligne.get("decision_score")),
                    "risk_score": _nombre(ligne.get("RISK_SCORE") or ligne.get("risk_score")),
                    "lead_time_score": _nombre(ligne.get("LEAD_TIME_SCORE") or ligne.get("lead_time_score")),
                    "criticality_score": _nombre(ligne.get("CRITICALITY_SCORE") or ligne.get("criticality_score")),
                    "decision_reason": json.dumps(ligne.get("DECISION_REASON") or {}, ensure_ascii=True),
                    "decision_type": _texte(ligne.get("DECISION_TYPE") or ligne.get("decision_type")),
                    "decision_confidence": _texte(ligne.get("DECISION_CONFIDENCE") or ligne.get("decision_confidence")),
                    "global_risk_score": _nombre(ligne.get("GLOBAL_RISK_SCORE") or ligne.get("global_risk_score")),
                    "lead_time_days": _nombre(ligne.get("TOTAL_IMPORT_LEAD_TIME") or ligne.get("lead_time_days")),
                    "cashflow_score": _nombre(ligne.get("CASHFLOW_SCORE") or ligne.get("cashflow_score")),
                    "moq_risk_score": _nombre(ligne.get("MOQ_RISK_SCORE") or ligne.get("moq_risk_score")),
                    "complexity_score": _nombre(ligne.get("IMPORT_COMPLEXITY_SCORE") or ligne.get("complexity_score")),
                    "procurement_reason": json.dumps(ligne.get("PROCUREMENT_ANALYSIS") or {}, ensure_ascii=True),
                    "container_strategy": _texte(ligne.get("CONTAINER_STRATEGY") or ligne.get("container_strategy")),
                    "shipment_strategy": _texte(ligne.get("SHIPMENT_STRATEGY") or ligne.get("shipment_strategy")),
                    "fill_rate": _nombre(ligne.get("FILL_RATE") or ligne.get("fill_rate")),
                    "shipment_cost": _nombre(ligne.get("SHIPMENT_COST") or ligne.get("shipment_cost")),
                    "lead_time_total": _nombre(ligne.get("LEAD_TIME_TOTAL") or ligne.get("lead_time_total")),
                    "storage_cost": _nombre(ligne.get("STORAGE_COST") or ligne.get("storage_cost")),
                    "delivery_risk": _texte(ligne.get("DELIVERY_RISK") or ligne.get("delivery_risk")),
                    "logistics_reason": json.dumps(ligne.get("LOGISTICS_ANALYSIS") or {}, ensure_ascii=True),
                    "supplier_id": ids["supplier_id"],
                    "country_id": ids["country_id"],
                },
            )
            inserted += 1
        return inserted

    def get_simulation(self, scenario_id: str, limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT *
                FROM fact_simulation
                WHERE scenario_id = CAST(:scenario_id AS uuid)
                ORDER BY simulation_line_id
                LIMIT :limit OFFSET :offset
                """
            ),
            {"scenario_id": scenario_id, "limit": limit, "offset": offset},
        ).mappings().all()
        return [dict(row) for row in rows]

    def compare_simulations(self, scenario_a: str, scenario_b: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT *
                FROM v_kpi_scenario
                WHERE scenario_id IN (CAST(:scenario_a AS uuid), CAST(:scenario_b AS uuid))
                ORDER BY scenario_nom
                """
            ),
            {"scenario_a": scenario_a, "scenario_b": scenario_b},
        ).mappings().all()
        return [dict(row) for row in rows]

    def _fact_metre_key(self, ligne: dict[str, Any]) -> str:
        explicit = _id(ligne.get("id_ligne"))
        if explicit:
            return explicit
        article_id = _id(ligne.get("article_id") or ligne.get("ARTICLE_ID"))
        ifc_guid = _id(ligne.get("ifc_guid") or ligne.get("IFC_GUID"))
        niveau = _id(ligne.get("niveau_code") or ligne.get("NIVEAU_ID") or ligne.get("niveau"))
        appartement = _id(ligne.get("appartement_code") or ligne.get("APPARTEMENT_ID") or ligne.get("appart"))
        piece = _id(ligne.get("piece_code") or ligne.get("PIECE_ID") or ligne.get("piece"))
        key = "|".join(part for part in (article_id, ifc_guid, niveau, appartement, piece) if part)
        return key or _id(ligne.get("designation"))

    def _resolve_dimension_ids(self, ligne: dict[str, Any], projet_id: int | None) -> dict[str, int | None]:
        projet = self.db.execute(
            text("SELECT COALESCE(:projet_id, (SELECT projet_id FROM dim_projet ORDER BY projet_id LIMIT 1))"),
            {"projet_id": projet_id},
        ).scalar_one_or_none()
        lot = _texte(ligne.get("lot") or "NON_RENSEIGNE")
        famille = _texte(ligne.get("famille") or "default")
        niveau = _texte(ligne.get("niveau") or ligne.get("niveau_code") or ligne.get("NIVEAU_ID") or "GLOBAL")
        batiment = _texte(ligne.get("batiment") or ligne.get("batiment_code") or ligne.get("BATIMENT_ID") or "NON_RENSEIGNE")
        appart_code = _id(ligne.get("appartement_code") or ligne.get("APPARTEMENT_ID"), ligne.get("appart") or "NON_RENSEIGNE")
        piece_code = _id(ligne.get("piece_code") or ligne.get("PIECE_ID"), ligne.get("piece") or "NON_RENSEIGNE")

        lot_id = self.db.execute(
            text(
                """
                INSERT INTO dim_lot (lot, ordre_lot)
                VALUES (
                    CAST(:lot AS varchar),
                    COALESCE(NULLIF(regexp_replace(CAST(:lot AS text), '\\D', '', 'g'), '')::INTEGER, 999)
                )
                ON CONFLICT (lot) DO UPDATE SET updated_at = now()
                RETURNING lot_id
                """
            ),
            {"lot": lot},
        ).scalar_one()
        famille_id = self.db.execute(
            text(
                """
                INSERT INTO dim_famille (famille, libelle_famille, categorie_achat, categorie, importable)
                VALUES (
                    CAST(:famille AS varchar),
                    initcap(replace(CAST(:famille AS text), '_', ' ')),
                    'A_ANALYSER',
                    'A_ANALYSER',
                    false
                )
                ON CONFLICT (famille) DO UPDATE SET updated_at = now()
                RETURNING famille_id
                """
            ),
            {"famille": famille},
        ).scalar_one()
        niveau_id = self.db.execute(
            text(
                """
                INSERT INTO dim_niveau (niveau, ordre_niveau)
                VALUES (CAST(:niveau AS varchar), 999)
                ON CONFLICT (niveau) DO UPDATE SET updated_at = now()
                RETURNING niveau_id
                """
            ),
            {"niveau": niveau},
        ).scalar_one()
        batiment_id = self.db.execute(
            text(
                """
                INSERT INTO dim_batiment (batiment, type_batiment)
                VALUES (CAST(:batiment AS varchar), 'A_CLASSER')
                ON CONFLICT (batiment) DO UPDATE SET updated_at = now()
                RETURNING batiment_id
                """
            ),
            {"batiment": batiment},
        ).scalar_one()
        appart_id = self.db.execute(
            text(
                """
                INSERT INTO dim_appart (appart_code, batiment, niveau, appart, type_appart)
                VALUES (CAST(:appart_code AS varchar), CAST(:batiment AS varchar), CAST(:niveau AS varchar), CAST(:appart AS varchar), 'A_CLASSER')
                ON CONFLICT (appart_code) DO UPDATE SET updated_at = now()
                RETURNING appart_id
                """
            ),
            {"appart_code": appart_code, "batiment": batiment, "niveau": niveau, "appart": appart_code},
        ).scalar_one()
        piece_id = self.db.execute(
            text(
                """
                INSERT INTO dim_piece (piece_code, batiment, niveau, appart, piece, type_piece)
                VALUES (CAST(:piece_code AS varchar), CAST(:batiment AS varchar), CAST(:niveau AS varchar), CAST(:appart AS varchar), CAST(:piece AS varchar), 'A_CLASSER')
                ON CONFLICT (piece_code) DO UPDATE SET updated_at = now()
                RETURNING piece_id
                """
            ),
            {"piece_code": piece_code, "batiment": batiment, "niveau": niveau, "appart": appart_code, "piece": piece_code},
        ).scalar_one()

        return {
            "projet_id": projet,
            "lot_id": lot_id,
            "famille_id": famille_id,
            "niveau_id": niveau_id,
            "batiment_id": batiment_id,
            "appart_id": appart_id,
            "piece_id": piece_id,
            "supplier_id": self._default_supplier_id(),
            "country_id": self._default_country_id(),
        }

    def _default_supplier_id(self) -> int | None:
        """
        Retourne le fournisseur technique par defaut.

        Les simulations temps reel ne connaissent pas toujours le fournisseur.
        On renseigne donc une dimension stable `NON_RENSEIGNE` afin de garder
        des relations Power BI propres sans inventer une information metier.
        """
        return self.db.execute(
            text("SELECT supplier_id FROM dim_supplier WHERE supplier_name = 'NON_RENSEIGNE' LIMIT 1")
        ).scalar_one_or_none()

    def _default_country_id(self) -> int | None:
        """Retourne le pays technique par defaut pour les simulations ad hoc."""
        return self.db.execute(
            text("SELECT country_id FROM dim_country WHERE country_name = 'NON_RENSEIGNE' LIMIT 1")
        ).scalar_one_or_none()
