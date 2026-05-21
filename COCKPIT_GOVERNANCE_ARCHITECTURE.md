# SP2I_CAPEX - Cockpit Governance Enterprise Architecture

Date de generation : 2026-05-21

## Objectif

Le futur Cockpit Governance Enterprise sera la couche visuelle de pilotage decisionnel procurement/CAPEX.

Cette phase prepare les datasets, les KPIs, les alertes, les badges, les workflows et les timelines sans modifier le frontend React actuel.

## Principes directeurs

- Montrer l'incertitude.
- Montrer les risques.
- Montrer les blocages.
- Montrer les validations humaines.
- Eviter les faux signaux optimistes.
- Ne jamais sur-vendre la confiance.
- Rendre chaque decision explicable et audit-able.

## Sources de donnees

| Source | Role |
| --- | --- |
| `PROCUREMENT_REVIEW_QUEUE.xlsx` | Queue humaine, priorites, escalations et explications. |
| `FAMILY_GOVERNANCE_INDEX.xlsx` | Statuts et scores par famille. |
| `GOVERNANCE_OVERRIDE_LOG.xlsx` | Overrides gouvernes. |
| `PROCUREMENT_GOVERNANCE_COMMENTS.xlsx` | Commentaires reviewers, procurement, finance, technique. |
| `PROCUREMENT_REVIEW_AUDIT.xlsx` | Audit trail initial. |
| `MULTI_FAMILY_GOVERNANCE_STATS.json` | KPIs globaux governance. |
| `PROCUREMENT_WORKBENCH_STATS.json` | KPIs de backlog et escalations. |

## Livrables cockpit

| Livrable | Contenu |
| --- | --- |
| `GOVERNANCE_COCKPIT_DATASET.xlsx` | KPIs globaux, KPIs famille, references cockpit, regles badges. |
| `GOVERNANCE_WORKFLOW_TIMELINE.xlsx` | Etats workflow : PENDING, IN_REVIEW, ESCALATED, APPROVED, REJECTED, NEEDS_MORE_DATA. |
| `GOVERNANCE_ESCALATION_MATRIX.xlsx` | Matrice familles x niveaux escalation. |
| `GOVERNANCE_EXPLAINABILITY_DATA.xlsx` | Raisons de blocage, escalation, revue, confidence faible et drift critique. |
| `GOVERNANCE_AUDIT_TIMELINE.xlsx` | Evenements auditables : creation queue, overrides, commentaires. |
| `COCKPIT_GOVERNANCE_STATS.json` | Synthese machine-readable. |

## KPIs globaux

Le cockpit prepare les KPIs suivants :

- `GLOBAL_GOVERNANCE_SCORE`
- `GLOBAL_CONFIDENCE_SCORE`
- `GLOBAL_PROCUREMENT_SCORE`
- `GLOBAL_DRIFT_SCORE`
- `GLOBAL_TCO_SCORE`
- `GLOBAL_REVIEW_BACKLOG`
- `GLOBAL_ESCALATION_COUNT`
- `GLOBAL_BLOCK_IMPORT_COUNT`
- `GLOBAL_HIGH_RISK_COUNT`

## KPIs famille

Par famille :

- `FAMILY_STATUS`
- `READINESS_SCORE`
- `REVIEW_REQUIRED_COUNT`
- `BLOCK_IMPORT_COUNT`
- `DRIFT_CRITICAL_COUNT`
- `VERIFIED_REFERENCE_COUNT`
- `HIGH_RISK_COUNT`

## Alertes cockpit

Les alertes preparees :

- `COCKPIT_GOVERNANCE_ALERT`
- `COCKPIT_DRIFT_ALERT`
- `COCKPIT_PROCUREMENT_ALERT`
- `COCKPIT_TECHNICAL_ALERT`
- `COCKPIT_BLOCK_IMPORT_ALERT`

Niveaux :

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## Badges

Badges prepares :

- `CONFIDENCE_BADGE`
- `PROCUREMENT_BADGE`
- `DRIFT_BADGE`
- `RISK_BADGE`
- `REVIEW_BADGE`

Couleurs :

- `GREEN` : stable ou valide.
- `ORANGE` : revue requise.
- `RED` : risque eleve.
- `DARK_RED` : critique ou bloque.

Regle UX : aucun badge vert ne doit etre affiche si la validation humaine est absente.

## Workflow governance

Etats supportes :

- `PENDING`
- `IN_REVIEW`
- `ESCALATED`
- `APPROVED`
- `REJECTED`
- `NEEDS_MORE_DATA`

Le cockpit devra rendre le backlog visible des le premier niveau de lecture.

## Escalation layer

Niveaux prepares :

- `SENIOR_PROCUREMENT_APPROVAL`
- `DOUBLE_VALIDATION`
- `PROCUREMENT_REVIEW`
- `SENIOR_REVIEW`
- `STANDARD_REVIEW`

Une escalation n'est pas une validation. Elle signifie qu'une decision humaine renforcee est necessaire.

## Explainability

Chaque reference peut afficher :

- pourquoi elle est bloquee ;
- pourquoi elle est escaladee ;
- pourquoi elle est en revue obligatoire ;
- pourquoi la confidence est faible ;
- pourquoi le drift est critique ;
- quelle action humaine est recommandee.

## Resultats V1

| KPI | Valeur |
| --- | ---: |
| References cockpit | 235 |
| Familles | 4 |
| Workflow PENDING | 235 |
| Governance alert CRITICAL | 149 |
| Governance alert HIGH | 83 |
| Governance alert MEDIUM | 3 |
| Procurement alert CRITICAL | 93 |
| Procurement alert HIGH | 13 |
| Technical alert HIGH | 235 |
| Audit events | 235 |
| Composants prepares | 8 |

## Conclusion

La structure du futur cockpit governance est prete.

Le systeme reste volontairement prudent : il expose les risques, les blocages et les validations humaines avant toute promesse de performance ou de confiance.
