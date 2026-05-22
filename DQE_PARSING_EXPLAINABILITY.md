# SP2I_CAPEX - DQE Parsing Explainability

Date : 2026-05-21

## Source auditee

Fichier :

`03_DONNEES_REFERENCE/DQE_PROJECT_SP2I.xlsx`

Onglet :

`DQE_CLEAN`

## Objectif

Cette couche explique les lignes DQE avant qu'elles alimentent les KPI, ROI, CAPEX, dashboards ou arbitrages achats.

Elle ne rend pas le parser permissif. Elle ajoute :

- tracabilite ligne par ligne ;
- classification des rejets ;
- distinction entre ignore, warning, revue et rejet ;
- messages metier lisibles ;
- recommandations de nettoyage.

## Statuts de parsing

| Statut | Sens metier |
| --- | --- |
| `VALID` | Ligne exploitable pour les calculs. |
| `WARNING` | Ligne partiellement exploitable, a relire. |
| `REVIEW_REQUIRED` | Ligne ambigue, validation humaine requise. |
| `IGNORED_TITLE` | Titre ou section, a exclure sans erreur. |
| `IGNORED_SUBTOTAL` | Total ou sous-total, a exclure pour eviter double comptage. |
| `IGNORED_EMPTY` | Ligne vide. |
| `REJECTED` | Ligne invalide, interdite pour les calculs. |

## Causes expliquees

| Code | Message metier |
| --- | --- |
| `MISSING_DESIGNATION` | La designation est absente sur cette ligne. |
| `MISSING_QTE` | La quantite est absente sur cette ligne. |
| `MISSING_UNITE` | L'unite est absente sur cette ligne. |
| `INVALID_QTE` | La quantite semble invalide ou non numerique. |
| `INVALID_UNIT` | L'unite n'est pas reconnue. |
| `MERGED_CELL_ERROR` | La ligne contient ou touche une cellule fusionnee qui peut fausser la lecture. |
| `UNKNOWN_FAMILY` | La famille metier n'a pas pu etre identifiee. |
| `PARSER_SHIFT_DETECTED` | Le format Excel semble decale ou mal structure. |
| `HEADER_REPEATED` | Une ligne d'en-tete est repetee dans le tableau. |
| `SUBTOTAL_DETECTED` | La ligne correspond a un total ou sous-total. |
| `EMPTY_LINE` | La ligne est vide. |
| `AMBIGUOUS_LINE` | La ligne est ambigue et doit etre revue manuellement. |
| `INVALID_PRICE` | Le prix est absent, nul ou incoherent. |
| `MULTI_ARTICLE_LINE` | La ligne semble contenir plusieurs articles. |
| `LOW_CONFIDENCE_MAPPING` | Le rattachement metier est trop faible. |

## Resultats sur le DQE fourni

| KPI | Valeur |
| --- | ---: |
| Total lignes auditees | 210 |
| Lignes validees | 123 |
| Warnings | 70 |
| Revue humaine requise | 17 |
| Rejetees strictes | 0 |
| Ignorees | 0 |
| Taux perte stricte | 0.00% |
| Taux non exploitable KPI sans revue | 8.10% |

## Familles impactees

| Famille | Lignes impactees |
| --- | ---: |
| PLOMBERIE | 33 |
| MENUISERIE_ALU | 30 |
| UNKNOWN | 14 |
| GROS_OEUVRE | 9 |
| ELECTRICITE | 1 |

## Principales causes

| Cause | Volume |
| --- | ---: |
| `MISSING_UNITE` | 76 |
| `UNKNOWN_FAMILY` | 14 |
| `MISSING_QTE` | 3 |

## Lecture du blocage actuel

Sur le fichier fourni, la couche explainability ne detecte pas de rejet strict massif.

Elle detecte surtout :

- des unites absentes ;
- des familles non reconnues ;
- quelques quantites absentes.

Conclusion :

Le message "Perte massive de lignes detectee pendant le parsing DQE" vient probablement d'une etape du parser qui assimile certaines lignes `WARNING` ou `REVIEW_REQUIRED` a des lignes perdues.

Le comportement strict reste utile, mais le message final devrait distinguer :

- lignes vraiment rejetees ;
- lignes a revoir ;
- lignes ignorees volontairement ;
- lignes valides mais incomplètes.

## Livrables

- `DQE_PARSING_AUDIT.xlsx`
- `DQE_REJECTION_HEATMAP.xlsx`
- `DQE_PARSING_STATS.json`
- `devtools/audit_dqe_parsing_explainability.py`

## Politique governance

Les lignes `REJECTED` et `REVIEW_REQUIRED` ne doivent pas alimenter automatiquement :

- KPI ;
- ROI ;
- CAPEX ;
- dashboards ;
- arbitrages achats.

Les lignes `WARNING` peuvent rester visibles, mais ne doivent pas declencher de decision automatique sans revue.
