from __future__ import annotations

import re
import unicodedata
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.errors import DataQualityError
from app.core.global_parameters import DEFAULT_SIMULATION_MODE, VALID_SIMULATION_MODES
from app.utils.id_normalizer import normalize_optional_id


logger = logging.getLogger("sp2i.simulation")

def nettoyer_nombre(valeur: Any, defaut: float | None = None) -> float | None:
    """
    Convertit une valeur metier heterogene en nombre fiable.

    Les DQE melangent souvent espaces, virgules decimales, devises et champs
    vides. Cette fonction reste volontairement pure : elle ne lit aucun fichier
    et ne depend pas de FastAPI, ce qui la rend testable seule.
    """
    if valeur is None or valeur == "":
        return defaut

    texte = str(valeur).strip()
    if not texte:
        return defaut

    texte = (
        texte.replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
        .replace("XAF", "")
        .replace("FCFA", "")
    )

    try:
        return float(Decimal(texte))
    except (InvalidOperation, ValueError):
        return defaut


def arrondir_montant(valeur: Any, precision: int = 2) -> float:
    """Arrondit un montant apres conversion defensive."""
    nombre = nettoyer_nombre(valeur, 0) or 0
    return round(nombre, precision)


def _texte_ascii(valeur: Any) -> str:
    texte = str(valeur or "").strip()
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(caractere for caractere in texte if not unicodedata.combining(caractere))
    return re.sub(r"\s+", " ", texte).strip()


def clean_lot(valeur: Any, libelle: Any | None = None) -> str:
    """
    Normalise les variantes de lots sans perdre le numero.

    Exemples :
    - `LOT1`
    - `Lot 1`
    - `LOT 1 : Gros oeuvre`
    deviennent un format stable `LOT 1` ou `LOT 1 : LIBELLE`.
    """
    texte = _texte_ascii(valeur).upper()
    if not texte:
        return ""

    match = re.search(r"\bLOT\s*(\d+)\b", texte)
    if not match:
        return texte

    numero = int(match.group(1))
    suffixe = ""
    apres_numero = texte[match.end() :].strip(" :-–—")
    if apres_numero:
        suffixe = f" : {apres_numero}"
    elif libelle:
        libelle_clean = _texte_ascii(libelle).upper().strip(" :-–—")
        if libelle_clean:
            suffixe = f" : {libelle_clean}"

    return f"LOT {numero}{suffixe}"


def clean_famille(valeur: Any) -> str:
    """Normalise une famille en cle stable utilisable dans les mappings."""
    texte = _texte_ascii(valeur).lower()
    texte = re.sub(r"[^a-z0-9]+", "_", texte)
    return texte.strip("_") or "default"


def clean_niveau(valeur: Any) -> str:
    """Normalise les niveaux pour eviter `RDC`, `rdc`, `R.D.C.` disperses."""
    texte = _texte_ascii(valeur).upper()
    if not texte:
        return "GLOBAL"
    if "RDC" in texte or "REZ" in texte:
        return "RDC"
    match = re.search(r"(?:ETAGE|NIVEAU)\s*(\d+)", texte)
    if match:
        return f"ETAGE {int(match.group(1))}"
    if "TERRASSE" in texte:
        return "TERRASSE"
    if "GLOBAL" in texte:
        return "GLOBAL"
    return texte


class DataCleaner:
    """
    Normalise une ligne DQE brute vers un contrat stable pour le moteur CAPEX.

    Cette classe reprend progressivement le role de l'ancien normalisateur dans
    `04_TRAITEMENT`, mais elle reste centree sur la logique pure. Les chemins,
    CSV, JSON et bases de donnees appartiennent aux repositories/services.
    """

    UNITES = {
        "mÂ²": "m2",
        "m2": "m2",
        "mÂ³": "m3",
        "m3": "m3",
        "ml": "ml",
        "kg": "kg",
        "u": "u",
        "U": "u",
        "ens": "ens",
        "Ens": "ens",
        "forfait": "forfait",
        "pm": "forfait",
    }

    STRICT_WARNING_CODES = {
        "PRIX_UNITAIRE_INVALIDE",
        "PRIX_TOTAL_INVALIDE",
    }

    def __init__(self, mode: str = DEFAULT_SIMULATION_MODE) -> None:
        if mode not in VALID_SIMULATION_MODES:
            raise DataQualityError(
                "Mode DataCleaner invalide.",
                details={"mode": mode, "valid_modes": sorted(VALID_SIMULATION_MODES)},
            )
        self.mode = mode
        self.warnings: list[dict[str, Any]] = []
        self.lot_courant = "INCONNU"
        self.batiment_courant = "BATIMENT PRINCIPAL"
        self.niveau_courant = "GLOBAL"

    def normaliser_lignes(self, lignes_brutes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        lignes: list[dict[str, Any]] = []
        for index, ligne in enumerate(lignes_brutes, start=1):
            ligne_normale = self.normaliser_ligne(ligne, index)
            if ligne_normale:
                lignes.append(ligne_normale)
        return lignes

    def normaliser_ligne(self, ligne: dict[str, Any], index: int = 1) -> dict[str, Any] | None:
        ligne = {str(cle).lower().strip(): valeur for cle, valeur in ligne.items()}
        designation = str(ligne.get("designation", "")).strip()
        if not designation:
            self._signaler_anomalie(index, "DESIGNATION_VIDE", "Ligne rejetee : designation vide.", ligne)
            return None

        self._maj_contexte(ligne)

        quantite = nettoyer_nombre(ligne.get("quantite"), 0) or 0
        prix_unitaire = nettoyer_nombre(ligne.get("prix_unitaire_ht"), 0) or 0
        prix_total = nettoyer_nombre(ligne.get("prix_total_ht"), None)
        if prix_total is None and quantite and prix_unitaire:
            prix_total = quantite * prix_unitaire
        prix_total = prix_total or 0
        self._valider_ligne(index, designation, quantite, prix_unitaire, prix_total, ligne)

        lot = clean_lot(ligne.get("lot") or self.lot_courant)
        batiment = str(ligne.get("batiment") or self.batiment_courant).strip()
        niveau = clean_niveau(ligne.get("niveau") or self.niveau_courant)
        designation_normalisee = self._normaliser_designation(designation)

        return {
            "id_ligne": str(ligne.get("id_ligne") or f"DQE-{index:06d}"),
            "project_code": normalize_optional_id(ligne.get("project_code") or ligne.get("projet_id")),
            "batiment_code": normalize_optional_id(ligne.get("batiment_code") or ligne.get("batiment_id"), ligne.get("batiment")),
            "niveau_code": normalize_optional_id(ligne.get("niveau_code") or ligne.get("niveau_id"), ligne.get("niveau")),
            "appartement_code": normalize_optional_id(ligne.get("appartement_code") or ligne.get("appartement_id"), ligne.get("appart")),
            "piece_code": normalize_optional_id(ligne.get("piece_code") or ligne.get("piece_id"), ligne.get("piece")),
            "lot_code": normalize_optional_id(ligne.get("lot_code") or ligne.get("lot_id"), ligne.get("lot")),
            "sous_lot_code": normalize_optional_id(ligne.get("sous_lot_code") or ligne.get("sous_lot_id"), ligne.get("sous_lot")),
            "article_id": normalize_optional_id(ligne.get("article_id"), ligne.get("id_ligne")),
            "code_article": normalize_optional_id(ligne.get("code_article") or ligne.get("code_bpu")),
            "designation": designation,
            "designation_normalisee": designation_normalisee,
            "quantite": round(quantite, 4),
            "unite": self._normaliser_unite(ligne.get("unite")),
            "prix_unitaire_ht": round(prix_unitaire, 2),
            "prix_total_ht": round(prix_total, 2),
            "lot": lot,
            "sous_lot": str(ligne.get("sous_lot") or "").strip(),
            "famille": self.classifier_famille(ligne.get("famille"), designation, lot),
            "batiment": batiment,
            "niveau": niveau,
            "appart": str(ligne.get("appart") or "").strip(),
            "piece": str(ligne.get("piece") or "").strip(),
            "type_zone": self._classifier_zone(designation, lot),
            "formule": str(ligne.get("formule") or "").strip(),
            "bim_object_id": str(ligne.get("bim_object_id") or "").strip(),
            "ifc_guid": str(ligne.get("ifc_guid") or "").strip(),
            "type_objet": str(ligne.get("type_objet") or "").strip(),
            "famille_bim": str(ligne.get("famille_bim") or "").strip(),
            "systeme": str(ligne.get("systeme") or "").strip(),
            "phase_chantier": str(ligne.get("phase_chantier") or "").strip(),
            "classification": str(ligne.get("classification") or "").strip(),
            "omniclass": str(ligne.get("omniclass") or "").strip(),
            "uniclass": str(ligne.get("uniclass") or "").strip(),
            "ifc_type": str(ligne.get("ifc_type") or "").strip(),
            "bim_object": str(ligne.get("bim_object") or "").strip(),
            "pu_import": nettoyer_nombre(ligne.get("pu_import"), 0) or 0,
            "montant_import": nettoyer_nombre(ligne.get("montant_import"), 0) or 0,
            "decision": str(ligne.get("decision") or ligne.get("decision_import") or "").strip(),
            "fournisseur": str(ligne.get("fournisseur") or "").strip(),
            "execution_status": str(ligne.get("execution_status") or "").strip(),
            "workflow_status": str(ligne.get("workflow_status") or "").strip(),
            "risque": str(ligne.get("risque") or "").strip(),
            "eta": str(ligne.get("eta") or "").strip(),
            "bim_maturity": str(ligne.get("bim_maturity") or "").strip(),
            "statut_ligne": self._statut_ligne(quantite, prix_unitaire, prix_total),
            "cle_metier": f"{lot}|{batiment}|{niveau}|{designation_normalisee}",
        }

    def _valider_ligne(
        self,
        index: int,
        designation: str,
        quantite: float,
        prix_unitaire: float,
        prix_total: float,
        ligne: dict[str, Any],
    ) -> None:
        anomalies: list[str] = []
        if quantite <= 0:
            anomalies.append("QUANTITE_INVALIDE")
        if prix_total < 0 or prix_unitaire < 0:
            anomalies.append("PRIX_NEGATIF")
        if prix_total <= 0:
            anomalies.append("PRIX_TOTAL_INVALIDE")

        for code in anomalies:
            self._signaler_anomalie(
                index,
                code,
                f"Ligne '{designation}' avec anomalie {code}.",
                ligne,
            )

    def _signaler_anomalie(
        self,
        index: int,
        code: str,
        message: str,
        ligne: dict[str, Any],
    ) -> None:
        warning = {
            "index": index,
            "code": code,
            "message": message,
            "ligne": {
                "id_ligne": ligne.get("id_ligne"),
                "designation": ligne.get("designation"),
                "lot": ligne.get("lot"),
            },
        }
        self.warnings.append(warning)

        if self.mode == "strict":
            if code in self.STRICT_WARNING_CODES:
                logger.warning("%s | %s", code, message)
                return
            logger.error("%s | %s", code, message)
            raise DataQualityError(message, details=warning)

        logger.warning("%s | %s", code, message)

    def classifier_famille(self, famille: Any, designation: str, lot: str) -> str:
        if famille:
            return clean_famille(famille)
        texte = f"{designation} {lot}".lower()
        regles = {
            "gros_oeuvre": ["beton", "coffrage", "acier", "demolition", "gros oeuvre"],
            "electricite": ["cable", "tableau", "courant", "electric"],
            "plomberie": ["wc", "eau", "evacuation", "plomberie"],
            "climatisation": ["climatisation", "ventilation"],
            "menuiserie": ["menuiserie", "porte", "fenetre", "aluminium"],
            "peinture": ["peinture", "enduit"],
            "ascenseur": ["ascenseur"],
        }
        for famille_cible, mots in regles.items():
            if any(mot in texte for mot in mots):
                return famille_cible
        return "default"

    def _maj_contexte(self, ligne: dict[str, Any]) -> None:
        if ligne.get("lot"):
            self.lot_courant = clean_lot(ligne["lot"])
        if ligne.get("batiment"):
            self.batiment_courant = str(ligne["batiment"]).strip()
        if ligne.get("niveau"):
            self.niveau_courant = clean_niveau(ligne["niveau"])

    def _normaliser_unite(self, unite: Any) -> str:
        if not unite:
            return "u"
        texte = str(unite).strip()
        return self.UNITES.get(texte, texte.lower())

    def _normaliser_niveau(self, niveau: Any) -> str:
        return clean_niveau(niveau)

    def _normaliser_designation(self, designation: str) -> str:
        texte = designation.lower()
        mots_cles = {
            "beton": "BETON",
            "acier": "ACIER",
            "coffrage": "COFFRAGE",
            "enduit": "ENDUIT",
            "faience": "FAIENCE",
            "cable": "CABLE",
            "climatisation": "CLIMATISATION",
            "ascenseur": "ASCENSEUR",
        }
        for mot, valeur in mots_cles.items():
            if mot in texte:
                return valeur
        return re.sub(r"\s+", " ", designation).strip().upper()

    def _classifier_zone(self, designation: str, lot: str) -> str:
        texte = f"{designation} {lot}".lower()
        if any(mot in texte for mot in ["chantier", "vrd", "cloture", "installation"]):
            return "COMMUN_COMPLEXE"
        if any(mot in texte for mot in ["wc", "cuisine", "chambre"]):
            return "PRIVATIF"
        return "COMMUN_BATIMENT"

    def _statut_ligne(self, quantite: float, prix_unitaire: float, prix_total: float) -> str:
        statuts: list[str] = []
        if quantite <= 0:
            statuts.append("QUANTITE_INVALIDE")
        if prix_unitaire <= 0:
            statuts.append("PRIX_UNITAIRE_INVALIDE")
        if prix_total <= 0:
            statuts.append("PRIX_TOTAL_INVALIDE")
        if quantite > 0 and prix_unitaire > 0 and prix_total > 0:
            attendu = quantite * prix_unitaire
            if attendu and abs(prix_total - attendu) / attendu > 0.2:
                statuts.append("ECART_PRIX_SUP_20")
        return "|".join(statuts) if statuts else "OK"
