# SP2I_CAPEX - Procurement Review Workbench

Date de generation : 2026-05-21
Source principale : `MASTER_REFERENCE_ENTERPRISE_CANDIDATES.xlsx`

## Objectif

Le `PROCUREMENT_REVIEW_WORKBENCH` est la couche de validation humaine enterprise de SP2I_CAPEX.

Il assiste la decision procurement, mais ne valide jamais automatiquement les decisions critiques.

## Principes

- L'IA et les pipelines governance recommandent, expliquent et priorisent.
- L'humain valide, rejette, escalade ou demande des donnees complementaires.
- Tout override doit etre trace avec justification, niveau d'approbation et risque accepte.
- Aucun `HIGH` ou statut d'integration n'est cree artificiellement.

## Livrables

| Fichier | Role |
| --- | --- |
| `PROCUREMENT_REVIEW_QUEUE.xlsx` | File de revue humaine avec priorite, statut, explication et actions recommandees. |
| `GOVERNANCE_OVERRIDE_LOG.xlsx` | Journal gouverne des overrides, avec template et regles d'approbation. |
| `PROCUREMENT_GOVERNANCE_COMMENTS.xlsx` | Support commentaires reviewer, procurement, finance et technique. |
| `PROCUREMENT_REVIEW_DASHBOARD_DATA.xlsx` | Structure future cockpit review sans modification frontend. |
| `PROCUREMENT_REVIEW_AUDIT.xlsx` | Audit trail initial de creation de queue et actions disponibles. |
| `PROCUREMENT_WORKBENCH_STATS.json` | Statistiques machine-readable du workbench. |

## Workflow de revue

Statuts officiels :

- `PENDING`
- `IN_REVIEW`
- `APPROVED`
- `REJECTED`
- `ESCALATED`
- `NEEDS_MORE_DATA`

Le statut initial est toujours `PENDING`.

## Actions humaines supportees

- `VALIDATE_SUPPLIER`
- `VALIDATE_BENCHMARK`
- `VALIDATE_FOB`
- `APPROVE_IMPORT`
- `REJECT_IMPORT`
- `OVERRIDE_AI_RECOMMENDATION`
- `REQUEST_TECHNICAL_REVIEW`
- `REQUEST_PROCUREMENT_REVIEW`
- `ADD_GOVERNANCE_COMMENT`

## Regles decisionnelles

| Condition | Regle |
| --- | --- |
| `CONFIDENCE_LEVEL = LOW` | Revue obligatoire. |
| `DRIFT_LEVEL = CRITICAL` | Escalation obligatoire. |
| `DECISION_BLOCKER = BLOCK_IMPORT` | Validation senior obligatoire. |
| `DECISION_BLOCKER = HIGH_RISK` | Double validation obligatoire. |

## Review Priority

`REVIEW_PRIORITY` peut valoir :

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Le score tient compte de :

- confidence ;
- drift ;
- blocker procurement ;
- validation technique ;
- readiness integration ;
- score procurement famille ;
- taux blockers famille.

## Procurement Explainability

Chaque reference recoit une explication lisible dans `PROCUREMENT_EXPLANATION`.

Exemple :

`Priorite CRITICAL: confiance faible + drift critique + import bloque + validation technique partial. Decision automatique interdite.`

L'explication doit permettre au reviewer de comprendre :

- pourquoi la reference est bloquee ;
- pourquoi elle est escaladee ;
- quelles validations sont attendues ;
- pourquoi l'automatisation est interdite.

## Governance Override

`GOVERNANCE_OVERRIDE_LOG.xlsx` contient la structure suivante :

- `OVERRIDE_ID`
- `REFERENCE_ID`
- `OLD_DECISION`
- `NEW_DECISION`
- `OVERRIDE_REASON`
- `OVERRIDE_BY`
- `OVERRIDE_DATE`
- `RISK_ACCEPTED`
- `APPROVAL_LEVEL`

Un override valide doit toujours avoir :

- une justification explicite ;
- un reviewer identifie ;
- un niveau d'approbation coherent ;
- un risque accepte ou refuse ;
- une date de decision.

## Commentaires de gouvernance

`PROCUREMENT_GOVERNANCE_COMMENTS.xlsx` prepare les commentaires :

- reviewers ;
- procurement ;
- finance ;
- technique.

Les commentaires doivent rester factuels : fournisseur, benchmark, FOB, drift, risque technique, decision.

## Preparation cockpit

Sans modifier le frontend actuel, les champs suivants sont prepares :

- `COCKPIT_REVIEW_STATUS`
- `COCKPIT_ESCALATION_LEVEL`
- `COCKPIT_GOVERNANCE_ALERT`
- `COCKPIT_MANUAL_VALIDATION`

## Resultats V1

| KPI | Valeur |
| --- | ---: |
| References en revue | 235 |
| Validation manuelle obligatoire | 235 |
| Statut initial `PENDING` | 235 |
| Priorite `CRITICAL` | 149 |
| Priorite `HIGH` | 83 |
| Priorite `MEDIUM` | 3 |
| Priorite `LOW` | 0 |
| Senior procurement approval | 93 |
| Double validation | 13 |
| Senior review | 43 |
| Procurement review | 83 |
| Standard review | 3 |
| Overrides actifs | 0 |
| Commentaires actifs | 0 |

## Conclusion

SP2I_CAPEX dispose maintenant d'une couche de revue procurement humaine, explicable et auditable.

Le workbench transforme les sorties governance en file de validation operationnelle, tout en conservant une separation stricte entre recommandation assistive et decision humaine.
