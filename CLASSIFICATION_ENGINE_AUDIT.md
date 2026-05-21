# Classification Engine Audit

Audit realise sur la source unique:

`03_DONNEES_REFERENCE/DQE_PROJECT_SP2I.xlsx`, onglet `DQE_CLEAN`.

## Resultat

Le moteur de classification existant a ete fiabilise sans creation d'un nouveau moteur, sans modification FastAPI, sans frontend et sans impact Power BI.

Statut: **GO conditionnel** pour le futur `MASTER_REFERENCE`, sous reserve de validation financiere des prix suspects.

## Scores apres durcissement

| KPI | Score |
| --- | ---: |
| GLOBAL_REFERENCE_SCORE | 87.98/100 |
| TAXONOMY_SCORE | 100.0/100 |
| PROCUREMENT_SCORE | 83.33/100 |
| REFERENCE_ENGINE_SCORE | 81.85/100 |
| TYPE_LINE_QUALITY_SCORE | 96.19/100 |
| DASHBOARD_CREDIBILITY_SCORE | 88.59/100 |

## Avant / apres

| KPI | Avant audit initial | Apres fiabilisation |
| --- | ---: | ---: |
| GLOBAL_REFERENCE_SCORE | 66.08 | 87.98 |
| TAXONOMY_SCORE | 44.52 | 100.0 |
| PROCUREMENT_SCORE | 52.86 | 83.33 |
| REFERENCE_ENGINE_SCORE | 52.97 | 81.85 |
| TYPE_LINE_QUALITY_SCORE | 59.05 | 96.19 |
| DASHBOARD_CREDIBILITY_SCORE | 77.13 | 88.59 |

## Corrections moteur

- Normalisation texte robuste pour abreviations chantier, electricite et solaire.
- Classification contextuelle par `LOT`, `FAMILLE`, `SOUS_LOT`, `TYPE_LIGNE`.
- Familles metier stabilisees autour des conventions BTP Afrique centrale.
- Sous-lots techniques explicites: TGBT, groupe electrogene, onduleurs, panneaux, alucobond, videosurveillance, controle acces.
- Types officiels alignes avec le DQE propre, incluant `FOURNITURE` et `EQUIPEMENT`.
- Regles anti faux positifs sur les mots generiques: materiel, mobilisation, accessoires, local groupe electrogene, isolation.
- Ajout de `classification_confidence` et `classification_reason`.

## Statistiques

- Lignes analysees: 210
- Lignes classifiees: 210
- Lignes GENERAL: 0
- Erreurs mapping detectees par l'audit apres correction: 0
- Erreurs importabilite: 0
- Duplication rate futur master reference: 12.86%
- Normalization quality: 57.62%

## Risques restants

Le sujet restant n'est plus principalement taxonomique. Il est financier:

- prix local a valider sur certaines lignes techniques
- benchmarks equipements a enrichir pour certains travaux/specifications
- quelques lignes detectees comme equipements mais non importables a surveiller

Ces risques sont traces dans:

- `AUDIT_REFERENCE_ENGINE.xlsx`
- `TOP_FINANCIAL_ANOMALIES.xlsx`
- `HEATMAP_REFERENCE_QUALITY.xlsx`

## Conclusion

Le moteur de classification est maintenant suffisamment stable pour supporter un `MASTER_REFERENCE` enterprise Afrique centrale, avec reserve explicite sur la validation financiere des lignes a prix suspect.
