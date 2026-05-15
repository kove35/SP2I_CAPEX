# Procurement Analytics

La phase Decision Engine transforme SP2I CAPEX en socle d'analyse procurement.

## Objectif

L'objectif n'est plus seulement de savoir si l'import est moins cher. Il faut
comprendre si l'import est une bonne decision achat :

```text
gain financier
risque fournisseur
delai
criticite chantier
confiance
```

## Tables et vues

Tables :

```text
fact_simulation
dim_scenario
dim_supplier
dim_country
dim_risk_level
simulation_run
```

Vues :

```text
v_decision_summary
v_decision_risk
v_supplier_performance
v_import_risk_analysis
```

## Pages Power BI conseillees

```text
Synthese decisionnelle
Analyse risques par scenario
Performance fournisseurs
Risque import par pays
Comparaison IMPORT / LOCAL / MIXTE
```

## Regle BI

Power BI visualise. PostgreSQL et FastAPI calculent.

Power BI peut faire :

```text
SUM
COUNT
filtrage
slicers
drill-down
formatage
```

Power BI ne doit pas faire :

```text
scoring decisionnel
arbitrage import/local
calcul risque
recalcul CAPEX
moyenne de ratios financiers
```

Cette separation rend le modele plus fiable, plus testable et plus facile a
industrialiser dans une architecture SaaS.
