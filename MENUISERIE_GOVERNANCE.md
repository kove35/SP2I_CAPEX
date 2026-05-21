# SP2I_CAPEX - Menuiserie Aluminium Governance

Date de generation : 2026-05-21
Famille auditee : MENUISERIE_ALUMINIUM
Source unique : `03_DONNEES_REFERENCE/DQE_PROJECT_SP2I.xlsx` / onglet `DQE_CLEAN`

## Objectif

Cette phase cree un pipeline de validation gouvernee pour la menuiserie aluminium, sans integration immediate dans `MASTER_REFERENCE_ENTERPRISE`.

Le perimetre reste volontairement isole afin de ne pas impacter :

- ELECTRICITE
- HVAC
- PLOMBERIE
- routes FastAPI
- frontend React
- Power BI
- AG Grid
- cockpit procurement

## Livrables generes

| Livrable | Role |
| --- | --- |
| `DQE_MENUISERIE_ALU_TEST.xlsx` | Extraction controlee des lignes menuiserie aluminium depuis `DQE_CLEAN`. |
| `MASTER_REFERENCE_MENUISERIE.xlsx` | References compactes et normalisees pour revue famille. |
| `MENUISERIE_SUPPLIER_REGISTRY.xlsx` | Registre fournisseurs candidats non verifies. |
| `MENUISERIE_PROCUREMENT_AUDIT.xlsx` | Audit importabilite, FOB, MOQ, fournisseur, decision blocker. |
| `MENUISERIE_DRIFT_ANALYSIS.xlsx` | Analyse derive aluminium, verre, energie, fret, USD, inflation import. |
| `MENUISERIE_TCO_ANALYSIS.xlsx` | Analyse cout total achat, maintenance, corrosion, etancheite, remplacement vitrage, duree de vie. |
| `MENUISERIE_FACADE_GOVERNANCE.xlsx` | Gouvernance facade et score de risque. |
| `MENUISERIE_LOW_CONFIDENCE_REFERENCES.xlsx` | References a faible confiance ou revue obligatoire. |
| `MENUISERIE_VALIDATION_STATS.json` | Statistiques machine-readable du pipeline. |

## Extraction

La detection cible les lignes contenant des signaux metier menuiserie aluminium :

- fenetres aluminium
- portes aluminium
- coulissants
- battants
- chassis
- facade rideau
- vitrage et double vitrage
- quincaillerie
- profiles aluminium
- accessoires aluminium
- etancheite facade
- garde-corps aluminium/verre

## Champs techniques ajoutes

Les champs suivants structurent la validation :

- `TYPE_MENUISERIE`
- `EPAISSEUR_MM`
- `TYPE_VITRAGE`
- `FINITION`
- `RUPTURE_THERMIQUE`
- `DIMENSIONS`
- `SYSTEME_OUVERTURE`
- `TYPE_FACADE`

## Validation technique

Le pipeline signale les incoherences suivantes :

- epaisseurs absentes ou incoherentes
- vitrages non qualifies
- faux profiles ou designation trop generale
- incompatibilites facade / vitrage / ouverture
- dimensions absentes
- rupture thermique absente pour elements exposes

Le statut `PARTIAL` est conserve tant qu'une validation technique humaine n'a pas confirme les caracteristiques critiques.

## Facade Governance

`FACADE_RISK_SCORE` est calcule selon :

- exposition climatique Afrique centrale
- corrosion aluminium
- qualite profile
- type vitrage
- etancheite
- besoin de maintenance
- durabilite attendue

Valeurs possibles :

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## Fourniture vs Pose

Le pipeline separe :

- `FOURNITURE_MENUISERIE` : importabilite possible sous reserve fournisseur / FOB / benchmark.
- `POSE_MENUISERIE` : non importable, a traiter localement.
- `MIXED_MENUISERIE` : revue obligatoire, car fourniture et pose sont melangees.

Les lignes de pose, travaux, scellement, installation ou main-d'oeuvre ne sont pas considerees comme importables.

## Procurement Governance

Les validations couvrent :

- fournisseur candidat
- statut fournisseur
- FOB estime
- MOQ
- delai
- coherence vitrage / profile
- benchmark local
- importabilite

Politique stricte : aucun `HIGH` n'est produit sans fournisseur verifie, benchmark verifie, vitrage coherent, drift acceptable et procurement stable.

## Drift Governance

`MENUISERIE_DRIFT_ALERT_LEVEL` prend en compte :

- aluminium mondial
- energie
- verre
- fret maritime
- USD
- inflation import

Valeurs possibles :

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## TCO Menuiserie

Le TCO integre :

- cout achat
- cout maintenance
- risque corrosion
- risque etancheite
- remplacement vitrage
- duree de vie estimee

Cette couche prepare la decision enterprise sans modifier le cockpit actuel.

## Decision Governance

`DECISION_BLOCKER` peut valoir :

- `NONE`
- `REVIEW_REQUIRED`
- `BLOCK_IMPORT`
- `HIGH_RISK`
- `TECHNICAL_VALIDATION_REQUIRED`

Une ligne peut donc rester exploitable analytiquement tout en etant bloquee pour decision procurement.

## Resultats V1

| KPI | Valeur |
| --- | ---: |
| Lignes menuiserie aluminium extraites | 41 |
| References master famille | 41 |
| Fournisseurs candidats | 3 |
| Confidence MEDIUM | 39 |
| Confidence LOW | 2 |
| Confidence HIGH | 0 |
| Facade risk MEDIUM | 18 |
| Facade risk HIGH | 21 |
| Facade risk CRITICAL | 2 |
| Technical validation PARTIAL | 41 |
| Drift MEDIUM | 39 |
| Drift HIGH | 2 |
| BLOCK_IMPORT | 16 |
| REVIEW_REQUIRED | 13 |
| HIGH_RISK | 12 |

## Conclusion

La famille MENUISERIE ALUMINIUM est prete pour revue gouvernance progressive, mais pas pour integration directe dans `MASTER_REFERENCE_ENTERPRISE`.

Le comportement est volontairement prudent :

- aucun fournisseur n'est marque verifie ;
- aucun benchmark n'est considere definitivement valide ;
- aucun `HIGH` n'est genere artificiellement ;
- les lignes mixtes fourniture / pose restent bloquees ou en revue ;
- les risques facade et drift restent visibles pour decision humaine.

Prochaine etape recommandee : validation humaine des fournisseurs, vitrages, profiles, dimensions et benchmarks locaux avant toute montee de confiance.
