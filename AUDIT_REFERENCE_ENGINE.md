# AUDIT REFERENCE ENGINE - SP2I_CAPEX

- Date audit: 2026-05-21T15:09:08
- Source unique: `C:\Users\Geoffrey\Documents\DEVELOPPEMENT\SP2I_CAPEX\03_DONNEES_REFERENCE\DQE_PROJECT_SP2I.xlsx`
- Onglet: `DQE_CLEAN`
- Lignes analysees: 210
- Decision: **GO conditionnel**

## KPIs finaux

- **TAXONOMY_SCORE**: 100.0/100
- **PROCUREMENT_SCORE**: 83.33/100
- **FINANCIAL_SCORE**: 72.35/100
- **ROI_RELIABILITY_SCORE**: 98.33/100
- **TYPE_LINE_QUALITY_SCORE**: 96.19/100
- **CONTEXT_PROPAGATION_SCORE**: 96.19/100
- **REFERENCE_ENGINE_SCORE**: 81.85/100
- **DASHBOARD_CREDIBILITY_SCORE**: 88.59/100
- **GLOBAL_REFERENCE_SCORE**: 87.98/100

## Synthese executive

Le score global du moteur de reference est de **87.98/100**. L'audit mesure la fiabilite du DQE propre comme base d'un futur MASTER_REFERENCE enterprise Afrique centrale, sans modifier les donnees ni les routes.

## Principaux risques

- Prix suspect majeur ligne 146: Prises terre complètes + barrette (989,000 FCFA).
- Faux gain potentiel ligne 147: 483,805 FCFA.

## Recommandations

- Valider manuellement les lignes a prix local inferieur aux benchmarks Afrique centrale.
- Exclure explicitement TOTAL, VALIDATION, DOCUMENTAIRE et TITRE_SECTION des aggregations cockpit.
- Degrader les recommandations ROI lorsque le prix local ou le FOB est marque suspect.
- Utiliser la heatmap qualite comme backlog de remediation avant construction du MASTER_REFERENCE.

## Livrables generes

- `AUDIT_REFERENCE_ENGINE.json`
- `AUDIT_REFERENCE_ENGINE.xlsx`
- `HEATMAP_REFERENCE_QUALITY.xlsx`
- `TOP_FINANCIAL_ANOMALIES.xlsx`
- `TOP_MAPPING_ERRORS.xlsx`
