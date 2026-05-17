# Roadmap frontend SP2I

## Objectif

Transformer progressivement le frontend SP2I en cockpit decisionnel immobilier
enterprise, sans casser l'architecture React actuelle.

---

## Etat deja realise

### Sprint 1 - Navigation cockpit

Fait :

- Landing page repositionnee sur le pilotage immobilier.
- Sidebar conservee et reorganisee autour du metier.
- Routes principales conservees :

```text
/app
/app/dqe
/app/simulation
/app/procurement
/app/logistics
/app/site
/app/analytics
```

- Sous-menus geres par contexte interne plutot que multiplication de pages.

### Sprint 2 - Topbar et contexte

Fait :

- Projet actif visible.
- Scenario actif visible.
- Quick actions :
  - Importer DQE.
  - Simulation.
  - Power BI.

### Sprint 3 - DQE cloud

Fait :

- Upload Excel connecte au backend Render.
- Mapping frontend corrige sur la reponse reelle :
  - `ai_preview`.
  - `lignes_normalisees_preview`.
  - `ai_anomalies`.
  - `analyses`.
- Gestion plus precise des erreurs API.

### Sprint 4 - Cockpits metier

Fait :

- Simulation en layout cockpit.
- Procurement avec tabs internes.
- Logistics avec tabs internes.
- Pilotage projet prepare.
- Analytics Power BI prepare.

### Sprint 5 - Fondation BI React

Fait :

- TanStack Query ajoute.
- Zustand ajoute pour filtres globaux.
- ECharts ajoute.
- AG Grid ajoute.
- Composants reutilisables :
  - `EnterpriseKpiCard`.
  - `BIChart`.
  - `SmartDataGrid`.
  - `GlobalFilterBar`.

---

## Sprint suivant recommande

### Sprint 6 - Brancher Analytics Engine V1

Objectif :

- remplacer progressivement les donnees fallback par `/analytics/*` ;
- faire reagir les KPI, charts et tables aux filtres globaux ;
- garder `/capex/summary` et `/fact_metre` comme compatibilite.

Actions :

1. Creer `analyticsService.js`.
2. Ajouter `useAnalyticsDashboard(filters)`.
3. Brancher `/analytics/dashboard` sur le cockpit.
4. Brancher `/analytics/kpis` sur les KPI cards.
5. Brancher `/analytics/drilldown` sur les vues detail.

### Sprint 7 - Cross-filtering

Objectif :

- rendre les filtres globaux actifs sur tous les dashboards.

Actions :

1. Normaliser les noms de filtres frontend/backend.
2. Ajouter les selections chart -> store Zustand.
3. Ajouter reset filtres.
4. Ajouter badges de filtres actifs.

### Sprint 8 - No-scroll strict

Objectif :

- limiter le scroll vertical global.

Actions :

1. Faire de `.saas-shell` un viewport strict.
2. Transformer les grandes pages en panels.
3. Mettre les tables dans des zones `panel-scroll`.
4. Reduire les hero sections dans `/app/*`.

### Sprint 9 - Drawers de detail

Objectif :

- eviter les changements de page inutiles.

Drawers cibles :

- ligne DQE ;
- ligne simulation ;
- fournisseur ;
- shipment ;
- alerte critique ;
- scenario.

### Sprint 10 - Power BI Embedded

Objectif :

- integrer les dashboards Power BI dans `/app/analytics`.

Pre-requis :

- URLs ou embed tokens Power BI configures ;
- strategie securite ;
- filtres projet/scenario transmis.

---

## Regles de priorisation

1. Toujours commencer par le workflow DQE -> PostgreSQL -> cockpit.
2. Ne pas refaire dans React ce que Power BI sait mieux faire.
3. Ne pas multiplier les pages si un panel ou une tab suffit.
4. Garder les KPI decisionnels visibles au premier ecran.
5. Favoriser les donnees reelles backend plutot que les mocks.
