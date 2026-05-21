from __future__ import annotations

import re
from typing import Any

from app.core.price_reference_repository import PriceReferenceRepository
from app.core.semantic_normalization_engine import SemanticNormalizationEngine


class CAPEXTaxonomyEngine:
    """Classifie une designation dans la taxonomie CAPEX enterprise existante."""

    OFFICIAL_TYPE_LINES = {
        "ARTICLE",
        "PRESTATION",
        "TRAVAUX",
        "FOURNITURE",
        "EQUIPEMENT",
        "TOTAL",
        "DOCUMENTAIRE",
        "VALIDATION",
        "TITRE_SECTION",
    }
    EXCLUDED_TYPE_LINES = {"TOTAL", "DOCUMENTAIRE", "VALIDATION", "TITRE_SECTION"}
    GENERIC_TERMS = {"materiel", "divers", "accessoires", "ensemble", "fourniture", "pose", "travaux", "installation", "raccordement"}

    FAMILY_ALIASES = {
        "RESEAUX_IT": "IT_RESEAUX",
        "ENERGIE_SOLAIRE": "SOLAIRE",
        "MENUISERIE_ALU": "MENUISERIE",
        "MENUISERIE_BOIS": "MENUISERIE",
        "EQUIPEMENTS_MEDICAUX": "MEDICAL",
        "REVETEMENTS": "REVETEMENTS",
    }

    FAMILY_CONTEXT_RULES = {
        "INSTALLATION_CHANTIER": ["installation chantier", "mobilisation", "base vie", "cloture provisoire", "panneau chantier"],
        "LOGISTIQUE_CHANTIER": ["logistique", "manutention", "transport chantier", "approvisionnement"],
        "SECURITE_HSE": ["hse", "securite chantier", "epi", "signalisation", "gardiennage"],
        "ETUDES_CONTROLES": ["etude", "controle", "essai", "visa", "rapport", "plan", "doe"],
        "DEMOLITION": ["demolition", "depose", "curage"],
        "GROS_OEUVRE": ["gros oeuvre", "beton", "coffrage", "acier", "armature", "maconnerie", "linteau", "dalle"],
        "REVETEMENTS": ["revetement", "carrelage", "faience", "faux plafond", "sol pvc", "placo", "enduit"],
        "PEINTURE": ["peinture", "impression", "enduit de finition"],
        "MENUISERIE": ["menuiserie", "porte", "fenetre", "placard", "aluminium", "bois"],
        "PLOMBERIE": ["plomberie", "sanitaire", "evacuation", "alimentation eau", "pvc", "cuivre", "pompe"],
        "HVAC": ["hvac", "cvc", "climatisation", "climatiseur", "split", "vrv", "cta", "ventilation"],
        "ELECTRICITE": ["electricite", "courant fort", "courant faible", "tgbt", "tableau", "disjoncteur", "cable", "eclairage"],
        "SECURITE": ["incendie", "videosurveillance", "intrusion", "controle acces"],
        "IT_RESEAUX": ["informatique", "reseau", "wifi", "switch", "baie informatique", "rj45"],
        "SOLAIRE": ["solaire", "photovoltaique", "panneau", "batterie", "onduleur"],
        "VRD": ["vrd", "voirie", "drainage", "reseaux divers", "terrassement"],
        "MEDICAL": ["medical", "laboratoire", "radiologie", "dentaire", "sterilisation"],
        "ETANCHEITE": ["etancheite", "waterproof", "membrane", "adeproof"],
        "FACADE": ["facade", "bardage", "alucobond", "mur rideau"],
    }

    SUBLOT_RULES = {
        "GROUPE_ELECTROGENE": ["groupe electrogene", "generateur", "kva"],
        "TGBT": ["tgbt", "tableau general basse tension", "table distribution", "tableau distribution"],
        "ECLAIRAGE": ["eclairage", "luminaire", "dalle led", "projecteur", "baes"],
        "PRISES": ["prise", "interrupteur"],
        "ONDULEURS": ["onduleur", "ups"],
        "PANNEAUX": ["panneau", "photovoltaique", "module"],
        "CLIMATISATION": ["climatisation", "climatiseur", "split", "vrv"],
        "VENTILATION": ["ventilation", "extraction", "cta"],
        "SANITAIRE": ["sanitaire", "wc", "lavabo", "douche"],
        "EVACUATION": ["evacuation", "eaux usees", "pvc"],
        "ALIMENTATION_EAU": ["alimentation eau", "surpresseur", "pompe"],
        "ALUCOBOND": ["alucobond", "bardage"],
        "PEINTURE_INTERIEURE": ["peinture", "interieure"],
        "RESEAUX_DIVERS": ["reseaux divers", "vrd"],
        "VIDEOSURVEILLANCE": ["videosurveillance", "camera", "cctv"],
        "CONTROLE_ACCES": ["controle acces", "badge", "lecteur"],
    }

    FALSE_POSITIVE_RULES = [
        {"family": "IT_RESEAUX", "terms": ["materiel", "mobilisation", "reservations", "calfeutrements"], "reason": "Mot generique chantier, pas un equipement IT."},
        {"family": "ELECTRICITE", "terms": ["local groupe electrogene", "porte metallique", "grille de protection"], "reason": "Ouvrage de local technique, pas groupe electrogene."},
        {"family": "SOLAIRE", "terms": ["fourniture pose systeme", "isolation"], "reason": "Formulation travaux/isolation, pas equipement solaire."},
    ]

    def __init__(
        self,
        repository: PriceReferenceRepository | None = None,
        normalizer: SemanticNormalizationEngine | None = None,
    ) -> None:
        self.repository = repository or PriceReferenceRepository()
        self.normalizer = normalizer or SemanticNormalizationEngine()

    def classify(self, designation: str | None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        normalized = self.normalizer.normalize(designation)
        text = normalized["normalized_designation"]
        context_text = self._normalize_context(context)
        full_text = f"{context_text} {text}".strip()
        tokens = set(normalized["tokens"])
        best: dict[str, Any] = {}
        best_score = 0.0
        reasons: list[str] = []

        for family, payload in self.repository.load_taxonomy().items():
            for entry in payload.get("entries", []):
                score, entry_reasons = self._score_entry(text, full_text, tokens, entry)
                score += self._family_context_bonus(full_text, family)
                score -= self._generic_penalty(text, entry)
                if score > best_score:
                    best_score = score
                    reasons = entry_reasons
                    best = {
                        "family": self._canonical_family(family),
                        "subcategory": entry.get("subcategory"),
                        "equipment_type": entry.get("equipment_type"),
                        "equipment_class": entry.get("equipment_class"),
                    }

        type_ligne, type_reason = self.detect_type_ligne(text, context)
        false_positive_reason = self._false_positive_reason(best.get("family"), text)
        if false_positive_reason:
            best = {}
            best_score = 0.0
            reasons = [false_positive_reason]

        context_family, context_family_reason = self.detect_family_from_context(full_text)
        explicit_family, explicit_family_reason = self._explicit_family_from_context(context)
        if explicit_family != "GENERAL":
            context_family = explicit_family
            context_family_reason = explicit_family_reason
        if not best and context_family != "GENERAL":
            best = {
                "family": context_family,
                "subcategory": self.detect_sublot(full_text),
                "equipment_type": "UNKNOWN",
                "equipment_class": "NON_CLASSE",
            }
            best_score = 64.0
            reasons = [context_family_reason]

        if best and context_family != "GENERAL" and best.get("family") != context_family:
            if best_score < 70 or type_ligne in {"TRAVAUX", "PRESTATION"}:
                reasons.append(f"Famille corrigee par contexte lot/sous-lot: {context_family}.")
                best["family"] = context_family
                best["subcategory"] = self.detect_sublot(full_text) or best.get("subcategory")
                best_score = max(best_score, 70.0)

        if best and not best.get("subcategory"):
            best["subcategory"] = self.detect_sublot(full_text) or "GENERAL"

        if type_ligne in self.EXCLUDED_TYPE_LINES:
            best = {
                "family": "GENERAL",
                "subcategory": type_ligne,
                "equipment_type": "NON_IMPORTABLE",
                "equipment_class": "DOCUMENTAIRE",
            }
            best_score = max(best_score, 82.0)
            reasons = [type_reason or f"TYPE_LIGNE {type_ligne} exclu des equipements."]

        confidence = min(max(best_score, 0.0), 100.0)
        if not best:
            best = {
                "family": "GENERAL",
                "subcategory": self.detect_sublot(full_text) or "GENERAL",
                "equipment_type": "UNKNOWN",
                "equipment_class": "NON_CLASSE",
            }
            reasons = ["Aucune regle technique specifique suffisamment fiable."]

        return {
            **best,
            **normalized["attributes"],
            "semantic_confidence_score": round(confidence, 2),
            "normalization_confidence_score": normalized["normalization_confidence_score"],
            "normalized_designation": text,
            "type_ligne": type_ligne,
            "classification_confidence": self._confidence_label(confidence, best.get("family"), type_ligne),
            "classification_reason": " ".join([reason for reason in reasons if reason] + ([type_reason] if type_reason else [])),
        }

    def list_families(self) -> list[str]:
        return sorted(self.repository.load_taxonomy())

    def detect_type_ligne(self, text: str, context: dict[str, Any] | None = None) -> tuple[str, str]:
        explicit = str((context or {}).get("TYPE_LIGNE") or (context or {}).get("type_ligne") or "").upper().strip()
        if explicit in self.OFFICIAL_TYPE_LINES:
            return explicit, f"TYPE_LIGNE explicite DQE: {explicit}."
        if any(term in text for term in ["total", "sous total", "sous-total"]):
            return "TOTAL", "Detection TOTAL via libelle."
        if any(term in text for term in ["validation", "visa", "bon pour accord"]):
            return "VALIDATION", "Detection VALIDATION via libelle."
        if any(term in text for term in ["rapport", "plan", "doe", "fiche technique", "manuel"]):
            return "DOCUMENTAIRE", "Detection DOCUMENTAIRE via libelle."
        if any(term in text for term in ["chapitre", "section", "generalites", "prescriptions"]):
            return "TITRE_SECTION", "Detection TITRE_SECTION via libelle."
        if any(term in text for term in ["pose", "mise en service", "essai", "maintenance", "formation"]):
            return "PRESTATION", "Detection PRESTATION via verbes de service."
        if any(term in text for term in ["beton", "coffrage", "maconnerie", "terrassement", "peinture", "enduit"]):
            return "TRAVAUX", "Detection TRAVAUX via vocabulaire chantier."
        if any(term in text for term in ["groupe electrogene", "climatiseur", "tableau", "camera", "onduleur", "batterie"]):
            return "EQUIPEMENT", "Detection EQUIPEMENT via equipement technique."
        return "ARTICLE", "TYPE_LIGNE par defaut ARTICLE."

    def detect_family_from_context(self, text: str) -> tuple[str, str]:
        scores = {
            family: sum(1 for keyword in keywords if keyword in text)
            for family, keywords in self.FAMILY_CONTEXT_RULES.items()
        }
        family, score = max(scores.items(), key=lambda item: item[1])
        if not score:
            return "GENERAL", ""
        return family, f"Famille {family} detectee via {score} indice(s) contexte/metier."

    def detect_sublot(self, text: str) -> str:
        scores = {
            sublot: sum(1 for keyword in keywords if keyword in text)
            for sublot, keywords in self.SUBLOT_RULES.items()
        }
        sublot, score = max(scores.items(), key=lambda item: item[1])
        return sublot if score else "GENERAL"

    def _score_entry(self, text: str, full_text: str, tokens: set[str], entry: dict[str, Any]) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        keywords = [str(item).lower() for item in entry.get("keywords", [])]
        synonyms = [str(item).lower() for item in entry.get("synonyms", [])]
        for keyword in keywords:
            if keyword in tokens or keyword in text:
                weight = 30.0 if self._is_precise_keyword(keyword) else 12.0
                score += weight
                reasons.append(f"Mot-cle detecte: {keyword}.")
        for synonym in synonyms:
            if synonym in full_text:
                score += 24.0
                reasons.append(f"Synonyme detecte: {synonym}.")
        equipment_type = str(entry.get("equipment_type", "")).lower().replace("_", " ")
        if equipment_type and equipment_type in full_text:
            score += 25.0
            reasons.append(f"Type equipement detecte: {equipment_type}.")
        if re.search(r"\b\d+(?:[.,]\d+)?\s*kva\b", text) and any(term in text for term in ["groupe", "electrogene", "onduleur"]):
            score += 28.0
            reasons.append("Puissance KVA detectee avec equipement electrique.")
        if re.search(r"\b\d+(?:[.,]\d+)?\s*wc\b", text) and any(term in text for term in ["module", "panneau", "photovoltaique"]):
            score += 28.0
            reasons.append("Puissance Wc detectee avec equipement solaire.")
        return score, reasons

    def _normalize_context(self, context: dict[str, Any]) -> str:
        values = [
            context.get("LOT"),
            context.get("lot"),
            context.get("SOUS_LOT"),
            context.get("sous_lot"),
            context.get("FAMILLE"),
            context.get("famille"),
        ]
        normalized = self.normalizer.normalize(" ".join(str(value or "") for value in values))
        return normalized["normalized_designation"]

    def _explicit_family_from_context(self, context: dict[str, Any]) -> tuple[str, str]:
        values = [context.get("LOT"), context.get("lot"), context.get("FAMILLE"), context.get("famille")]
        text = self.normalizer.normalize(" ".join(str(value or "") for value in values))["normalized_designation"]
        for family, keywords in self.FAMILY_CONTEXT_RULES.items():
            if any(keyword in text for keyword in keywords) or family.lower().replace("_", " ") in text:
                return family, f"Famille {family} priorisee depuis LOT/FAMILLE DQE."
        if "finition" in text:
            return "REVETEMENTS", "Famille REVETEMENTS priorisee depuis FINITIONS DQE."
        if "bardage" in text:
            return "FACADE", "Famille FACADE priorisee depuis BARDAGE DQE."
        return "GENERAL", ""

    def _family_context_bonus(self, full_text: str, family: str) -> float:
        canonical = self._canonical_family(family)
        keywords = self.FAMILY_CONTEXT_RULES.get(canonical, [])
        return min(sum(1 for keyword in keywords if keyword in full_text) * 10.0, 25.0)

    def _generic_penalty(self, text: str, entry: dict[str, Any]) -> float:
        generic_hits = sum(1 for term in self.GENERIC_TERMS if term in text)
        precise_hits = sum(1 for term in entry.get("keywords", []) if self._is_precise_keyword(str(term)) and str(term).lower() in text)
        return 18.0 * generic_hits if generic_hits and not precise_hits else 0.0

    def _false_positive_reason(self, family: str | None, text: str) -> str:
        if not family:
            return ""
        family = self._canonical_family(family)
        for rule in self.FALSE_POSITIVE_RULES:
            if rule["family"] == family and any(term in text for term in rule["terms"]):
                return rule["reason"]
        return ""

    def _canonical_family(self, family: str | None) -> str:
        raw = str(family or "GENERAL").upper().replace(" ", "_")
        return self.FAMILY_ALIASES.get(raw, raw)

    def _is_precise_keyword(self, keyword: str) -> bool:
        return keyword not in self.GENERIC_TERMS and len(keyword) >= 4

    def _confidence_label(self, score: float, family: str | None, type_ligne: str) -> str:
        if type_ligne in self.EXCLUDED_TYPE_LINES:
            return "HIGH"
        if family in {"GENERAL", "UNKNOWN"} or score < 45:
            return "LOW"
        if score < 75:
            return "MEDIUM"
        return "HIGH"
