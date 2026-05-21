# SP2I_CAPEX - Governance UX Language Guide

Date : 2026-05-21

## Objectif

Rendre le Governance Cockpit compréhensible par un utilisateur non spécialiste sans retirer la rigueur procurement/CAPEX.

Le cockpit doit aider a comprendre en moins de 30 secondes :

- ce qui bloque ;
- pourquoi ca bloque ;
- ou est le risque ;
- quoi verifier ;
- qui doit intervenir ;
- si une decision est fiable.

## Principes de langage

- Utiliser des phrases metier courtes.
- Eviter le jargon IA, data et procurement dans l'interface visible.
- Preferer les verbes d'action : verifier, valider, refuser, demander, comparer.
- Expliquer les scores avec une phrase humaine.
- Ne jamais transformer un etat incertain en signal positif.

## Ton recommande

Le ton doit etre :

- sobre ;
- decisionnel ;
- pedagogique ;
- prudent ;
- credible pour direction, finance, chantier, achat et investisseurs.

## A eviter dans l'interface visible

- procurement score ;
- confidence score ;
- drift score ;
- escalation ;
- workflow ;
- benchmark ;
- governance ;
- AI recommendation ;
- review backlog.

Ces termes peuvent rester dans :

- code ;
- datasets ;
- logs ;
- backend ;
- documentation technique.

## Formulations recommandees

Pour un KPI faible :

- "Donnees encore partiellement verifiees"
- "Achats necessitant une validation humaine"
- "Prix a comparer au marche local"

Pour un blocage :

- "Importation non autorisee"
- "Validation superieure requise"
- "Controle technique requis"

Pour une explication :

- "Les prix semblent eloignes du marche local et les donnees fournisseur ne sont pas assez verifiees."
- "Une personne doit verifier avant decision."
- "Un responsable achat doit valider avant toute importation."

## Couleurs

- Vert : fiable ou valide.
- Orange : a surveiller.
- Rouge : critique.
- Rouge fonce : bloque.

Regle importante :

Ne pas afficher de vert si une validation humaine reste obligatoire.

## Vue simplifiee future

La future vue simplifiee devra afficher :

- 4 a 6 KPI maximum ;
- les familles bloquees ;
- les risques critiques ;
- les prochaines actions ;
- les validations attendues ;
- les decisions non fiables.

Elle ne devra pas afficher :

- colonnes techniques ;
- codes internes ;
- acronymes procurement ;
- scores sans explication.
