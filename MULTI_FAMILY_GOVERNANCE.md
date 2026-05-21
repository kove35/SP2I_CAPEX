# SP2I_CAPEX - Multi-Family Governance Layer

Date de generation : 2026-05-21
Familles couvertes : ELECTRICITE, HVAC, PLOMBERIE, MENUISERIE_ALU

## Objectif

Cette couche transverse pilote les familles deja traitees par pipeline governance sans fusion brutale dans `MASTER_REFERENCE_ENTERPRISE`.

Elle sert a :

- comparer les familles sous une grille commune ;
- preparer les references candidates a integration ;
- exposer les risques inter-familles ;
- produire des KPIs de gouvernance enterprise ;
- preparer les champs cockpit governance sans modifier le frontend.

## Contraintes respectees

Le pipeline ne modifie pas :

- routes FastAPI ;
- frontend React ;
- Power BI ;
- AG Grid ;
- moteurs backend existants ;
- architecture existante ;
- `MASTER_REFERENCE_ENTERPRISE`.

Il lit uniquement les livrables famille existants et produit une couche d'audit transverse.

## Livrables generes

| Livrable | Role |
| --- | --- |
| `FAMILY_GOVERNANCE_INDEX.xlsx` | Index de gouvernance par famille avec scores, statut et readiness. |
| `MASTER_REFERENCE_ENTERPRISE_CANDIDATES.xlsx` | References candidates a integration supervisee, sans integration automatique. |
| `CROSS_FAMILY_GOVERNANCE_AUDIT.xlsx` | Audit des incoherences inter-familles, drift, conflits et doublons fournisseurs. |
| `GOVERNANCE_MONITORING_REPORT.xlsx` | Rapport de monitoring global et suivi famille par famille. |
| `MULTI_FAMILY_GOVERNANCE_STATS.json` | Synthese machine-readable des KPIs globaux. |

## Statuts officiels famille

| Statut | Definition |
| --- | --- |
| `VERIFIED` | Gouvernance stable, integration possible. |
| `CONDITIONALLY_READY` | Integration possible avec supervision. |
| `REVIEW_REQUIRED` | Validation metier requise. |
| `HIGH_RISK` | Risques importants, integration non recommandee sans arbitrage. |
| `BLOCKED` | Non integrable en l'etat. |

## Integration Readiness Score

`INTEGRATION_READINESS_SCORE` est calcule a partir de :

- confidence ;
- procurement ;
- drift ;
- maturite TCO ;
- validation technique ;
- stabilite benchmark ;
- taux de decision blockers.

Regles de gate :

| Score | Gate |
| ---: | --- |
| `> 85` | `READY` |
| `70 - 85` | `REVIEW` |
| `< 70` | `BLOCKED` |

## Decision Governance

Regles globales appliquees :

- taux `BLOCK_IMPORT` ou blockers critiques eleve : famille bloquee ;
- drift critique eleve : statut `HIGH_RISK` ou `BLOCKED` ;
- confidence faible : revue manuelle obligatoire ;
- validation technique partielle ou rejetee : integration interdite sans arbitrage ;
- aucun `HIGH` global n'est genere artificiellement.

## Structure cockpit governance preparee

Les references candidates exposent les champs suivants pour une future integration cockpit :

- `COCKPIT_GOVERNANCE_STATUS`
- `COCKPIT_RISK_BADGE`
- `COCKPIT_CONFIDENCE_BADGE`
- `COCKPIT_DRIFT_ALERT`
- `COCKPIT_REVIEW_REQUIRED`

Cette preparation ne modifie pas le frontend actuel.

## Resultats globaux V1

| KPI | Valeur |
| --- | ---: |
| `GLOBAL_GOVERNANCE_SCORE` | 55.27 |
| `GLOBAL_PROCUREMENT_SCORE` | 37.88 |
| `GLOBAL_CONFIDENCE_SCORE` | 51.34 |
| `GLOBAL_DRIFT_SCORE` | 51.06 |
| `GLOBAL_TCO_SCORE` | 81.25 |
| `GLOBAL_TECHNICAL_VALIDATION_SCORE` | 62.27 |
| Familles suivies | 4 |
| References candidates | 235 |
| References en revue manuelle | 235 |
| Familles READY | 0 |
| Familles REVIEW | 0 |
| Familles BLOCKED | 4 |
| Findings cross-family | 71 |

## Statut par famille

| Famille | Statut | Gate integration |
| --- | --- | --- |
| ELECTRICITE | `HIGH_RISK` | `BLOCKED` |
| HVAC | `HIGH_RISK` | `BLOCKED` |
| PLOMBERIE | `BLOCKED` | `BLOCKED` |
| MENUISERIE_ALU | `BLOCKED` | `BLOCKED` |

## Lecture decisionnelle

La couche transverse confirme que les pipelines famille sont exploitables pour la gouvernance, mais pas encore pour une integration automatique dans le master enterprise.

Le blocage est sain et voulu :

- les fournisseurs restent insuffisamment verifies ;
- les benchmarks locaux ne sont pas encore assez confirmes ;
- le drift reste trop important sur plusieurs familles ;
- les lignes mixtes fourniture / installation / pose declenchent des blockers ;
- la confidence reste majoritairement LOW ou MEDIUM ;
- la revue humaine reste obligatoire pour toutes les references candidates.

## Recommandations

1. Valider les fournisseurs par famille avant toute montee en confidence.
2. Stabiliser les benchmarks Congo, Cameroun, Gabon et Afrique centrale.
3. Traiter les `BLOCK_IMPORT` avant integration master.
4. Reduire les drifts critiques par verification marche, fret, USD et matieres premieres.
5. Ne promouvoir une famille en `CONDITIONALLY_READY` qu'apres validation procurement et technique documentee.

## Conclusion

SP2I_CAPEX dispose maintenant d'une couche de gouvernance multi-familles enterprise, prudente et auditable.

Le systeme est pret pour piloter la validation progressive, mais pas pour fusionner automatiquement les references dans `MASTER_REFERENCE_ENTERPRISE`.
