# Architecture frontend SP2I

SP2I est une plateforme decisionnelle de pilotage des investissements
immobiliers.

## Positionnement

React devient le cockpit operationnel :

```text
piloter les projets
simuler le CAPEX
orchestrer les decisions
suivre le chantier
declencher les moteurs d'optimisation
```

Power BI reste la couche analytique strategique. Les moteurs import,
procurement et logistique sont des leviers d'optimisation integres, pas le coeur
du produit.

## Structure

```text
08_FRONTEND/src/
  marketing/
  routes/
  layouts/
  navigation/
  services/
  store/
  modules/
    cockpit/
    simulation/
    procurement/
    logistics/
    chantier/
    dqe/
    analytics/
  ui/
  shared/
  components/
```

## Routes

```text
/                  Landing marketing
/app               Cockpit decisionnel immobilier
/app/simulation    Investissements & CAPEX
/app/scenarios     Comparaison scenarios
/app/procurement   Procurement & supply chain
/app/logistics     Logistique chantier integree
/app/site          Pilotage projet
/app/dqe           DQE & Data
/app/analytics     Power BI Embedded
```
