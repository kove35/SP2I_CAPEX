# Roadmap Frontend SP2I - Execution Progressive

## Objectif

Transformer le frontend SP2I en cockpit decisionnel immobilier enterprise, sans
casser l'architecture React actuelle.

## Etat execute dans cette passe

### 1. Navigation module + contexte

Fait :

- Sidebar conservee.
- Routes principales conservees.
- Sous-menus convertis en contextes `?tab=` ou `?dashboard=`.
- Administration sortie du groupe Analytics.

Routes principales conservees :

```text
/app
/app/simulation
/app/dqe
/app/site
/app/procurement
/app/logistics
/app/analytics
```

### 2. Topbar de pilotage

Fait :

- Projet actif visible.
- Scenario actif visible.
- Quick actions ajoutees :
  - Importer DQE
  - Simulation
  - Power BI

### 3. Simulation cockpit

Fait :

- Tabs internes :
  - Simulation
  - Scenarios
  - Historique
  - Comparaison
- Layout split-screen :
  - table simulation
  - panneau contexte / parametres / decision summary
- Scroll local sur la table.

### 4. Procurement cockpit

Fait :

- Tabs internes :
  - Fournisseurs
  - Import
  - Cashflow
  - MOQ
  - Risques
- Panneau contexte pour garder le CAPEX comme priorite.

### 5. Logistics cockpit

Fait :

- Tabs internes :
  - Containers
  - Shipments
  - Freight
  - ETA chantier
- Layout split-screen.
- La logistique reste un levier de securisation CAPEX.

### 6. Pilotage Projet

Fait :

- Tabs internes :
  - Planning
  - Dependances
  - Livraisons
  - Criticite
- Actions chantier visibles dans un panneau contexte.

### 7. DQE & Data

Fait :

- Le module conserve l'import existant.
- Les vues Analyse, Normalisation et Qualite sont preparees en cockpit.

### 8. Power BI

Fait :

- Remplacement du modele multi-cards par un seul dashboard actif.
- Selector dashboard :
  - Direction
  - CAPEX
  - Projet
  - Procurement
  - Logistics
  - Risks
- React garde le contexte, Power BI reste le moteur analytics.

## Prochain sprint recommande

### Sprint 2 - No-scroll strict

- Faire de `.saas-shell` un viewport strict `height: 100vh`.
- Transformer `.content-area` en zone sans scroll global.
- Ajouter des conteneurs `.panel-scroll` sur toutes les tables.
- Reduire la hauteur des `page-hero` en mode dense.

### Sprint 3 - DQE cockpit complet

- Extraire les styles inline de `pages/Import.jsx`.
- Transformer l'import DQE en layout 3 panels :
  - upload / source
  - preview table
  - qualite / mapping / anomalies
- Ajouter action directe `Envoyer vers simulation`.

### Sprint 4 - Drawers de details

- Drawer ligne simulation.
- Drawer alerte critique.
- Drawer shipment.
- Drawer fournisseur.

### Sprint 5 - Cache API

- Ajouter React Query.
- Eviter de relancer `simulateCapex` sur chaque changement de page.
- Mutualiser scenario actif et derniere simulation.

### Sprint 6 - Power BI Embedded reel

- Configurer `workspaceId`, `reportId`, `embedToken`.
- Appliquer les filtres projet/scenario.
- Charger uniquement le dashboard actif.

