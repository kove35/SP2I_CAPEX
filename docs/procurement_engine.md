# Procurement Engine

Le `ProcurementEngine` ajoute une lecture supply chain au moteur CAPEX.

Il ne remplace pas `CalculateurCAPEX` et ne casse pas `DecisionEngine`. Il
enrichit chaque ligne avec des analyses operationnelles avant historisation :

```text
risque global
delai import
cashflow
MOQ
complexite import
```

## Flux progressif

```text
DataCleaner
  -> CalculateurCAPEX
  -> ProcurementEngine
  -> DecisionEngine
  -> RepositorySimulation
  -> PostgreSQL
  -> Power BI
```

## Moteurs internes

```text
RiskEngine
LeadTimeEngine
CashflowEngine
MOQEngine
ImportComplexityEngine
```

Chaque moteur retourne une analyse lisible. Le champ `PROCUREMENT_ANALYSIS`
contient le raisonnement complet, puis `fact_simulation` stocke les scores
principaux pour Power BI.

## Endpoints

```text
GET /procurement/risk-analysis/{simulation_id}
GET /procurement/lead-time/{simulation_id}
GET /procurement/cashflow/{simulation_id}
GET /procurement/import-complexity/{simulation_id}
```

Ces endpoints lisent PostgreSQL. Ils ne recalculent pas la simulation.
