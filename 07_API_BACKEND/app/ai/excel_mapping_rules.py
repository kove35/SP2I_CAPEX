from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def normaliser_libelle(valeur: object) -> str:
    """
    Transforme un en-tete Excel en texte comparable.

    Cette normalisation est volontairement deterministe. Elle sert de socle a la
    couche IA : un LLM pourra plus tard enrichir les suggestions, mais le
    backend garde une base explicable et testable.
    """
    texte = str(valeur or "").strip().lower()
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(caractere for caractere in texte if not unicodedata.combining(caractere))
    texte = re.sub(r"[^a-z0-9]+", "_", texte)
    return texte.strip("_")


@dataclass(frozen=True)
class MappingRule:
    champ_standard: str
    mots_cles: tuple[str, ...]


REGLES_MAPPING_EXCEL = (
    MappingRule("id_ligne", ("n", "numero", "num", "ref", "reference")),
    MappingRule("project_code", ("projet_id", "project_id")),
    MappingRule("batiment_code", ("batiment_id", "building_id", "bat_id")),
    MappingRule("niveau_code", ("niveau_id", "level_id", "floor_id")),
    MappingRule("appartement_code", ("appartement_id", "appart_id", "unit_id")),
    MappingRule("piece_code", ("piece_id", "room_id", "zone_id")),
    MappingRule("lot_code", ("lot_id", "trade_id")),
    MappingRule("sous_lot_code", ("sous_lot_id", "sub_lot_id")),
    MappingRule("article_id", ("article_id", "id_article", "object_article_id")),
    MappingRule("code_article", ("code_article", "code_bpu", "bpu_code")),
    MappingRule("lot", ("lot",)),
    MappingRule("sous_lot", ("sous_lot", "sous lot", "sub_lot", "sub trade")),
    MappingRule("batiment", ("batiment", "bat", "immeuble", "building", "bloc")),
    MappingRule("niveau", ("niveau", "etage", "floor")),
    MappingRule("appart", ("appart", "appartement", "logement")),
    MappingRule("piece", ("piece", "room", "espace", "zone", "zone_piece", "local_piece")),
    MappingRule("type_zone", ("type_zone", "type piece", "type local")),
    MappingRule("designation", ("designation", "designation_prestation", "libelle", "prestation", "description")),
    MappingRule("unite", ("unite", "u", "unit")),
    MappingRule("quantite", ("quantite", "qte", "qty")),
    MappingRule("formule", ("formule", "formula", "calcul")),
    MappingRule("bim_object_id", ("bim_object_id", "id_objet_bim", "bim_id")),
    MappingRule("bim_object", ("bim_object", "objet_bim", "ifc_object")),
    MappingRule("ifc_guid", ("ifc_guid", "guid_ifc", "globalid", "global_id")),
    MappingRule("type_objet", ("type_objet", "object_type", "type_bim")),
    MappingRule("famille_bim", ("famille_bim", "bim_family", "revit_family")),
    MappingRule("systeme", ("systeme", "system", "mep_system")),
    MappingRule("phase_chantier", ("phase_chantier", "phase")),
    MappingRule("altitude", ("altitude", "altimetrie", "cote", "niveau_altitude")),
    MappingRule("execution_status", ("execution_status", "statut_execution", "etat_execution", "remaining_work_status")),
    MappingRule("workflow_status", ("workflow_status", "statut_workflow", "etat_workflow")),
    MappingRule("eta", ("eta", "date_livraison", "date_pose", "echeance")),
    MappingRule("risque", ("risque", "risk", "risk_level", "niveau_risque")),
    MappingRule("fournisseur", ("fournisseur", "supplier", "vendor")),
    MappingRule("import_local", ("import_local", "decision_import", "mode_achat", "purchase_mode")),
    MappingRule("classification", ("classification", "classement")),
    MappingRule("omniclass", ("omniclass",)),
    MappingRule("uniclass", ("uniclass",)),
    MappingRule("ifc_type", ("ifc_type", "ifctype", "ifc_class")),
    MappingRule("prix_unitaire_ht", ("pu", "pu_local", "prix_unitaire", "prix_unitaire_fcfa", "pu_fcfa")),
    MappingRule("prix_total_ht", ("pt", "prix_total", "montant", "montant_ht", "pt_fcfa", "montant_local")),
    MappingRule("pu_import", ("pu_import", "prix_import", "prix_unitaire_import")),
    MappingRule("montant_import", ("montant_import", "capex_import", "total_import")),
    MappingRule("decision", ("decision", "decision_import", "mode_achat")),
    MappingRule("bim_maturity", ("bim_maturity", "maturite_bim", "bim_mode")),
    MappingRule("source", ("source", "source_donnee")),
    MappingRule("verification", ("verif", "verification", "audit", "statut")),
)


CHAMPS_DQE_MINIMUM = {"designation", "quantite", "prix_total_ht"}
