# Flux simulation frontend

La page `Simulation.jsx` est le premier cockpit SP2I.

## Elle permet

```text
lancer une simulation
persister un scenario
afficher les KPI
afficher les decisions
afficher le risque
afficher container et ETA
```

## Payload de test

Le payload par defaut est defini dans :

```text
08_FRONTEND/src/services/simulationService.js
```

Il contient deux lignes metier :

```text
Luminaire Shanghai
Groupe electrogene
```

Ce jeu de donnees permet de tester rapidement :

```text
CAPEX
DecisionEngine
ProcurementEngine
LogisticsEngine
historisation PostgreSQL
```
