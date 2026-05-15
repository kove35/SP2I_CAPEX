# Decision Engine SP2I CAPEX

Le `DecisionEngine` transforme un calcul CAPEX en arbitrage procurement
explicable.

Il ne remplace pas `CalculateurCAPEX`. Le calculateur produit les montants
financiers : `PU_IMPORT`, `CAPEX_LOCAL`, `CAPEX_IMPORT`, `ECONOMIE`. Le
Decision Engine ajoute ensuite les criteres operationnels : risque fournisseur,
risque logistique, delai et criticite chantier.

## Flux

```text
DataCleaner
  -> CalculateurCAPEX
  -> DecisionEngine
  -> RepositorySimulation
  -> PostgreSQL
  -> Power BI
```

## Role du moteur

Pour chaque ligne, le moteur produit :

```text
DECISION_FINALE
DECISION_TYPE
FINAL_DECISION_SCORE
DECISION_CONFIDENCE
DECISION_REASON
RISK_SCORE
LEAD_TIME_SCORE
CRITICALITY_SCORE
```

Ces champs sont historises dans `fact_simulation`. Power BI les consomme comme
des donnees pre-calculees.

## Pourquoi c'est important

Un import moins cher n'est pas toujours le meilleur choix. Une economie peut
etre annulee par un risque fournisseur eleve, un delai trop long ou une forte
criticite chantier. Le moteur rend cet arbitrage lisible et auditable.

## Endpoints utiles

```text
GET /decision/rules
GET /decision/explain/{simulation_id}
GET /decision/risk-analysis/{scenario_id}
```

`/decision/explain/{simulation_id}` lit l'explication stockee en base. Il ne
recalcule pas la decision, ce qui garantit que l'audit reste coherent avec la
simulation historisee.
