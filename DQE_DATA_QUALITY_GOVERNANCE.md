# DQE Data Quality Governance Engine

Cette evolution ajoute une couche legere de gouvernance au parser DQE existant.
Elle ne remplace pas le pipeline, les routes, le cockpit ou le moteur analytics.

## Regle metier principale

`WARNING` n'est pas une panne.

`REVIEW_REQUIRED` n'est pas une perte de donnees.

Seules les lignes classees `DATA_LOSS` ou `DATA_INTEGRITY` bloquantes peuvent
declencher un arret du pipeline. Les lignes a verifier restent tracees, mais ne
doivent pas alimenter les KPI, ROI, CAPEX ou arbitrages achat sans controle.

## Taxonomie gouvernance

| Categorie | Role |
| --- | --- |
| DATA_LOSS | Perte bloquante reelle, critique pour le pipeline. |
| DATA_INTEGRITY | Incoherence de structure qui peut fausser le dataset. |
| DATA_QUALITY | Donnee incomplete ou informative a verifier. |
| REVIEW_REQUIRED | Revue humaine necessaire avant decision. |
| IGNORED | Ligne structurelle normale : titre, total, vide, recap. |

## Champs ajoutes aux lignes classifiees

- `governance_status`
- `trust_score`
- `governance_issues`
- `review_required`
- `certification_status`
- `recoverable`
- `recommended_action`

Les champs historiques `row_type`, `reason` et `current_lot` sont conserves pour
compatibilite.

## Scoring

Le score de confiance reste volontairement simple :

- `DATA_LOSS` : -40
- `DATA_INTEGRITY` : -25
- `DATA_QUALITY` : -10
- `REVIEW_REQUIRED` : -3

Objectif : rendre le risque lisible sans reconstruire Analytics Engine V1.

## Effet sur le garde-fou parsing

Avant, le garde-fou pouvait assimiler une ligne ignoree ou a revoir a une perte
massive. Maintenant, il bloque uniquement si une perte stricte est detectee.

Les titres, sous-totaux, lignes vides, ratios et lignes de contexte sont traces
mais ne sont pas comptes comme rejets critiques.

## UX analytics

Le message de fallback simulation est remplace par :

`Snapshot analytics affiche. Synchronisation arriere-plan en cours.`

Le cockpit doit donner une impression de resilience, pas de panne.

## Compatibilite

- Routes FastAPI conservees.
- Payloads existants conserves.
- Champs ajoutes uniquement en enrichissement.
- Power BI peut continuer a lire les colonnes existantes.
- Les nouveaux champs peuvent etre exploites progressivement.
