from __future__ import annotations


ISSUE_MESSAGES = {
    "VALID_ARTICLE": "La ligne est exploitable pour les KPI, le CAPEX et la simulation.",
    "IGNORED_EMPTY": "La ligne est vide et ignoree sans impact sur les calculs.",
    "IGNORED_TITLE": "La ligne sert de titre ou de contexte de lot. Elle est tracee mais ne doit pas alimenter les KPI.",
    "IGNORED_SUBTOTAL": "La ligne est un total ou sous-total. Elle est ignoree pour eviter un double comptage.",
    "IGNORED_ANALYTICS": "La ligne ressemble a un ratio ou recap analytique. Elle reste hors FACT_METRE.",
    "REVIEW_NO_LOT": "La ligne ressemble a un article mais aucun lot courant fiable n'a ete detecte.",
    "DATA_QUALITY_INFORMATIONAL": "La ligne est informative ou incomplete. Elle ne correspond pas a un article DQE complet.",
    "DATA_LOSS_BLOCKING": "La ligne semble critique et ne peut pas etre exploitee sans correction.",
}


RECOMMENDED_ACTIONS = {
    "VALID_ARTICLE": "Aucune action requise.",
    "IGNORED_EMPTY": "Aucune action requise.",
    "IGNORED_TITLE": "Conserver comme contexte; ne pas comptabiliser comme rejet.",
    "IGNORED_SUBTOTAL": "Conserver hors KPI pour eviter les doubles comptes.",
    "IGNORED_ANALYTICS": "Conserver hors FACT_METRE; verifier uniquement si une ligne article est attendue.",
    "REVIEW_NO_LOT": "Rattacher la ligne a un lot ou confirmer qu'elle doit rester hors calcul.",
    "DATA_QUALITY_INFORMATIONAL": "Verifier si la ligne est une note ou si une quantite/un montant manque.",
    "DATA_LOSS_BLOCKING": "Corriger la ligne avant synchronisation analytique.",
}


def issue_message(code: str) -> str:
    return ISSUE_MESSAGES.get(code, "Controle gouvernance a verifier.")


def recommended_action(code: str) -> str:
    return RECOMMENDED_ACTIONS.get(code, "Verifier la ligne source.")
