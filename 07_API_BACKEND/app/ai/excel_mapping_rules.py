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
    MappingRule("ifc_guid", ("ifc_guid", "guid_ifc", "globalid", "global_id")),
    MappingRule("type_objet", ("type_objet", "object_type", "type_bim")),
    MappingRule("famille_bim", ("famille_bim", "bim_family", "revit_family")),
    MappingRule("systeme", ("systeme", "system", "mep_system")),
    MappingRule("phase_chantier", ("phase_chantier", "phase")),
    MappingRule("classification", ("classification", "classement")),
    MappingRule("omniclass", ("omniclass",)),
    MappingRule("uniclass", ("uniclass",)),
    MappingRule("ifc_type", ("ifc_type", "ifctype", "ifc_class")),
    MappingRule("prix_unitaire_ht", ("pu", "prix_unitaire", "prix_unitaire_fcfa", "pu_fcfa")),
    MappingRule("prix_total_ht", ("pt", "prix_total", "montant", "montant_ht", "pt_fcfa")),
    MappingRule("verification", ("verif", "verification", "audit", "statut")),
)


CHAMPS_DQE_MINIMUM = {"designation", "quantite", "prix_total_ht"}
