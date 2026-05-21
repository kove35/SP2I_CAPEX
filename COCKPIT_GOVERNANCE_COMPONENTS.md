# SP2I_CAPEX - Cockpit Governance Components

Ce document prepare la structure React future sans modifier le frontend actuel.

## Objectif UX

Le cockpit governance doit ressembler a une console decisionnelle enterprise :

- lisible en quelques secondes ;
- focalisee sur les risques ;
- orientee validation humaine ;
- explicable ;
- audit-able ;
- sans faux signal de confiance.

## Composants prepares

### GovernanceKpiStrip

Role :

- afficher scores globaux ;
- backlog review ;
- escalations ;
- imports bloques ;
- high risk.

Dataset :

- `GOVERNANCE_COCKPIT_DATASET.xlsx` / sheet `GLOBAL_KPIS`

UX :

- KPI critiques en premier ;
- pas de vert si backlog non traite ;
- afficher les scores faibles sans maquillage visuel.

### GovernanceFamilyStatusBoard

Role :

- afficher statut par famille ;
- readiness score ;
- blockers ;
- drift critique ;
- references verifiees.

Dataset :

- `GOVERNANCE_COCKPIT_DATASET.xlsx` / sheet `FAMILY_KPIS`

UX :

- familles `BLOCKED` et `HIGH_RISK` visuellement dominantes ;
- familles non pretes clairement separees des candidates.

### GovernanceReviewQueue

Role :

- piloter la queue humaine ;
- trier par priorite ;
- suivre les statuts ;
- assigner les reviewers dans une future UI.

Dataset :

- `GOVERNANCE_COCKPIT_DATASET.xlsx` / sheet `COCKPIT_REFERENCES`

Colonnes cles :

- `REFERENCE_ID`
- `FAMILY_NAME`
- `REVIEW_PRIORITY`
- `REVIEW_STATUS`
- `ESCALATION_LEVEL`
- `MANUAL_VALIDATION_REQUIRED`

UX :

- tri par `CRITICAL`, puis `HIGH`, puis `MEDIUM` ;
- filtre famille ;
- filtre blocker ;
- filtre escalation ;
- aucune validation inline sans audit trail.

### GovernanceEscalationPanel

Role :

- visualiser senior approvals ;
- double validation ;
- senior review ;
- procurement review.

Dataset :

- `GOVERNANCE_ESCALATION_MATRIX.xlsx`

UX :

- escalations critiques visibles dans le premier viewport ;
- distinction claire entre escalation et approbation.

### GovernanceDriftHeatmap

Role :

- visualiser drift par reference et famille ;
- isoler drift critique ;
- preparer exploration marche.

Dataset :

- `GOVERNANCE_COCKPIT_DATASET.xlsx` / sheet `COCKPIT_REFERENCES`

UX :

- `DARK_RED` uniquement pour critique ;
- `RED` pour high ;
- `ORANGE` pour medium ;
- `GREEN` seulement si risque faible et validation humaine compatible.

### GovernanceConfidenceMatrix

Role :

- croiser confidence, procurement, readiness et validation humaine.

Dataset :

- `GOVERNANCE_COCKPIT_DATASET.xlsx`

UX :

- montrer les references LOW sans les noyer ;
- separer confidence technique et decision procurement ;
- ne jamais convertir MEDIUM en signal positif.

### GovernanceExplainabilityPanel

Role :

- expliquer pourquoi une reference est bloquee ;
- expliquer pourquoi elle est escaladee ;
- expliquer pourquoi elle est en revue ;
- proposer la prochaine action humaine.

Dataset :

- `GOVERNANCE_EXPLAINABILITY_DATA.xlsx`

UX :

- cartes courtes ;
- phrases actionnables ;
- afficher la justification avant les chiffres secondaires.

### GovernanceAuditTimeline

Role :

- visualiser overrides ;
- validations ;
- commentaires ;
- reviewers ;
- historique decisions.

Dataset :

- `GOVERNANCE_AUDIT_TIMELINE.xlsx`

UX :

- toujours afficher qui, quand, pourquoi ;
- distinguer system event, human comment, override ;
- rendre les risques acceptes visibles.

## Etats UI recommandes

### Loading

- skeleton compact ;
- pas de faux KPI a zero ;
- afficher "chargement governance".

### Empty

- expliquer l'absence de donnees ;
- ne pas afficher de score positif par defaut.

### Error

- montrer source manquante ;
- proposer relance du pipeline devtools ;
- ne pas masquer les erreurs d'audit.

### Review Required

- badge `ORANGE` ou `RED` ;
- action humaine visible ;
- lien vers explainability.

### Blocked

- badge `DARK_RED` ;
- import interdit sans validation senior ;
- justification obligatoire.

## Performance future

Quand le cockpit sera implemente :

- virtualiser la review queue ;
- memoizer les selectors ;
- charger explainability a la demande ;
- filtrer par famille cote state ;
- eviter les recalculs de matrices dans le render ;
- preparer export Power BI compatible.

## Regles anti-faux optimisme

- Ne pas utiliser de vert si `MANUAL_VALIDATION_REQUIRED = true`.
- Ne pas masquer les `BLOCK_IMPORT`.
- Ne pas moyenner les risques critiques jusqu'a les rendre acceptables.
- Ne pas afficher un score global sans backlog et escalations.
- Ne pas presenter `MEDIUM` comme une validation.

## Integration future

Cette phase ne modifie pas le frontend.

Les composants pourront etre ajoutes plus tard en lisant :

- `GOVERNANCE_COCKPIT_DATASET.xlsx`
- `GOVERNANCE_WORKFLOW_TIMELINE.xlsx`
- `GOVERNANCE_ESCALATION_MATRIX.xlsx`
- `GOVERNANCE_EXPLAINABILITY_DATA.xlsx`
- `GOVERNANCE_AUDIT_TIMELINE.xlsx`

Le cockpit devra rester une interface de supervision humaine, pas un automate de decision.
