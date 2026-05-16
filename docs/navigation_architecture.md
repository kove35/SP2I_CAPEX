# Architecture navigation

La navigation est un cockpit SaaS enterprise oriente pilotage immobilier et
decision CAPEX.

## Fichiers

```text
src/navigation/sidebarConfig.js
src/layouts/AppShell.jsx
```

## Sections

```text
Cockpit
Investissements & CAPEX
Pilotage Projet
DQE & Data
Procurement & Supply Chain
Analytics
Administration
```

La supply chain est volontairement placee apres le CAPEX, le pilotage projet et
le DQE. Elle reste un moteur d'optimisation au service de la decision
immobiliere.

## Strategie

Chaque entree de navigation pointe vers un module metier. La sidebar raconte le
cycle de pilotage immobilier :

```text
investissement
projet
donnees
optimisation
analytics
```
