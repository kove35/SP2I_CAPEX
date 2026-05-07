from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from utils.clean_numbers import nettoyer_nombre
from utils.helpers import ecrire_json, extraire_lignes, lire_json


class NormalisateurDQE:
    """Normalise un DQE brut vers un contrat stable pour CAPEX et BI."""

    UNITES = {
        "m²": "m2",
        "m2": "m2",
        "m³": "m3",
        "m3": "m3",
        "ml": "ml",
        "kg": "kg",
        "u": "u",
        "U": "u",
        "ens": "ens",
        "Ens": "ens",
        "forfait": "forfait",
        "pm": "forfait"
    }

    def __init__(self) -> None:
        self.lot_courant = "INCONNU"
        self.batiment_courant = "BATIMENT PRINCIPAL"
        self.niveau_courant = "GLOBAL"

    def normaliser_fichier(self, entree: str | Path, sortie: str | Path) -> list[dict[str, Any]]:
        lignes = self.normaliser_lignes(extraire_lignes(lire_json(entree)))
        ecrire_json(sortie, {"lignes": lignes})
        return lignes

    def normaliser_lignes(self, lignes_brutes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        lignes: list[dict[str, Any]] = []
        for index, ligne in enumerate(lignes_brutes, start=1):
            ligne_normale = self.normaliser_ligne(ligne, index)
            if ligne_normale:
                lignes.append(ligne_normale)
        return lignes

    def normaliser_ligne(self, ligne: dict[str, Any], index: int) -> dict[str, Any] | None:
        ligne = {str(cle).lower().strip(): valeur for cle, valeur in ligne.items()}
        designation = str(ligne.get("designation", "")).strip()
        if not designation:
            return None

        self._maj_contexte(ligne)

        quantite = nettoyer_nombre(ligne.get("quantite"), 0) or 0
        prix_unitaire = nettoyer_nombre(ligne.get("prix_unitaire_ht"), 0) or 0
        prix_total = nettoyer_nombre(ligne.get("prix_total_ht"), None)
        if prix_total is None and quantite and prix_unitaire:
            prix_total = quantite * prix_unitaire
        prix_total = prix_total or 0

        designation_normalisee = self._normaliser_designation(designation)
        lot = str(ligne.get("lot") or self.lot_courant).strip()
        batiment = str(ligne.get("batiment") or self.batiment_courant).strip()
        niveau = self._normaliser_niveau(ligne.get("niveau") or self.niveau_courant)
        famille = self._classifier_famille(ligne.get("famille"), designation, lot)

        return {
            "id_ligne": f"DQE-{index:06d}",
            "designation": designation,
            "designation_normalisee": designation_normalisee,
            "quantite": round(quantite, 4),
            "unite": self._normaliser_unite(ligne.get("unite")),
            "prix_unitaire_ht": round(prix_unitaire, 2),
            "prix_total_ht": round(prix_total, 2),
            "lot": lot,
            "famille": famille,
            "batiment": batiment,
            "niveau": niveau,
            "type_zone": self._classifier_zone(designation, lot),
            "statut_ligne": self._statut_ligne(quantite, prix_unitaire, prix_total),
            "cle_metier": f"{lot}|{batiment}|{niveau}|{designation_normalisee}"
        }

    def _maj_contexte(self, ligne: dict[str, Any]) -> None:
        if ligne.get("lot"):
            self.lot_courant = str(ligne["lot"]).strip()
        if ligne.get("batiment"):
            self.batiment_courant = str(ligne["batiment"]).strip()
        if ligne.get("niveau"):
            self.niveau_courant = self._normaliser_niveau(ligne["niveau"])

    def _normaliser_unite(self, unite: Any) -> str:
        if not unite:
            return "u"
        texte = str(unite).strip()
        return self.UNITES.get(texte, texte.lower())

    def _normaliser_niveau(self, niveau: Any) -> str:
        texte = str(niveau or "GLOBAL").upper()
        if "RDC" in texte:
            return "RDC"
        match = re.search(r"ETAGE\s*\d+", texte)
        if match:
            return match.group(0)
        if "TERRASSE" in texte:
            return "TERRASSE"
        return "GLOBAL"

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
            "ascenseur": "ASCENSEUR"
        }
        for mot, valeur in mots_cles.items():
            if mot in texte:
                return valeur
        return re.sub(r"\s+", " ", designation).strip().upper()

    def _classifier_famille(self, famille: Any, designation: str, lot: str) -> str:
        if famille:
            return str(famille).lower().strip()
        texte = f"{designation} {lot}".lower()
        regles = {
            "gros_oeuvre": ["beton", "coffrage", "acier", "demolition", "gros oeuvre"],
            "electricite": ["cable", "tableau", "courant", "electric"],
            "plomberie": ["wc", "eau", "evacuation", "plomberie"],
            "climatisation": ["climatisation", "ventilation"],
            "menuiserie": ["menuiserie", "porte", "fenetre", "aluminium"],
            "peinture": ["peinture", "enduit"],
            "ascenseur": ["ascenseur"]
        }
        for famille_cible, mots in regles.items():
            if any(mot in texte for mot in mots):
                return famille_cible
        return "default"

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalisation DQE SP2I")
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", required=True)
    args = parser.parse_args()

    lignes = NormalisateurDQE().normaliser_fichier(args.input, args.output)
    print(f"Normalisation terminee: {len(lignes)} lignes -> {args.output}")


if __name__ == "__main__":
    main()
