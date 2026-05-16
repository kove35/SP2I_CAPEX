# Flux frontend backend

SP2I suit une separation claire.

```text
React cockpit
  -> services Axios
  -> FastAPI
  -> moteurs metier
  -> PostgreSQL
  -> Power BI
```

## Services API

Les appels HTTP sont centralises :

```text
simulationService
scenarioService
decisionService
procurementService
logisticsService
```

Les pages React ne connaissent pas les details HTTP. Elles appellent des
fonctions metier comme `simulateCapex()` ou `getContainerPlan()`.

## Workflow principal

```text
Simulation React
  -> POST /simulation/simulate
  -> simulation_id
  -> /decision/*
  -> /procurement/*
  -> /logistics/*
```

Chaque analyse affichée provient du backend ou de PostgreSQL. React ne
recalcule pas le CAPEX, le risque ou la logistique.
