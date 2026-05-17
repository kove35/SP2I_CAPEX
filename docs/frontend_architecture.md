# Architecture frontend SP2I

## Role du frontend

Le frontend SP2I est le **cockpit operationnel** de la plateforme.

Il sert a :

- importer et controler les DQE ;
- piloter les simulations CAPEX ;
- afficher les KPI operationnels ;
- naviguer dans les scenarios ;
- consulter les analyses procurement, logistique et chantier ;
- ouvrir les dashboards Power BI quand l'utilisateur veut une analyse BI longue.

React ne doit pas devenir la source de verite metier. Les calculs critiques
restent dans FastAPI, PostgreSQL et les vues analytics.

---

## Stack actuelle

| Brique | Technologie | Usage |
|---|---|---|
| Framework | React + Vite | Application SPA |
| Hebergement | Vercel | Production frontend |
| API client | Axios | Appels FastAPI |
| Cache API | TanStack Query | Chargement, retry, cache |
| Etat global | Zustand | Filtres cockpit |
| Charts | ECharts | Visualisations cockpit |
| Tables | AG Grid | Tableaux BI interactifs |
| Routing | React Router | Navigation `/app/*` |
| Style | CSS/Tailwind existant | Cockpit enterprise dark |

---

## Structure actuelle

```text
08_FRONTEND/src/
  app/
    QueryProvider.jsx
  components/
    charts/
      BIChart.jsx
      CapexWaterfall.jsx
      ImportDecisionSankey.jsx
      RiskMatrix.jsx
    filters/
      GlobalFilterBar.jsx
    grids/
      SmartDataGrid.jsx
    kpi/
      EnterpriseKpiCard.jsx
  layouts/
    AppLayout.jsx
  marketing/
    LandingPage.jsx
  modules/
    cockpit/
    analytics/
    dqe/
    logistics/
    procurement/
    simulation/
  navigation/
  pages/
  routes/
  services/
    apiClient.js
    dashboardService.js
    excelUploadService.js
    simulationService.js
    scenarioService.js
    decisionService.js
    procurementService.js
    logisticsService.js
  store/
    dashboardStore.js
  styles.css
```

---

## Routes principales

```text
/                  Landing marketing
/app               Cockpit decisionnel
/app/dqe           Import et controle DQE
/app/simulation    Investissements & CAPEX
/app/scenarios     Scenarios et comparaison
/app/procurement   Procurement & Supply Chain
/app/logistics     Containers, shipments, freight
/app/site          Pilotage projet / chantier
/app/analytics     Power BI et dashboards analytiques
```

La route `/app/dqe` est le bon point de depart pour un nouvel utilisateur qui
veut importer un fichier Excel.

---

## Providers React

`main.jsx` monte l'application avec :

- `QueryProvider` pour TanStack Query ;
- le store existant de l'application ;
- le routeur React.

`QueryProvider.jsx` centralise la configuration React Query :

- cache court pour donnees cockpit ;
- retry limite ;
- comportement stable en production Vercel.

---

## Etat global cockpit

Le store Zustand `dashboardStore.js` contient :

- projet actif ;
- scenario actif ;
- filtres globaux ;
- parametres CAPEX ;
- actions de modification des filtres.

Les filtres globaux cibles sont :

```text
projet
scenario
batiment
niveau
lot
famille
fournisseur
decision import/local
periode
```

L'objectif est de rapprocher l'experience de Power BI : un filtre modifie les
widgets, les graphiques et les tableaux du cockpit.

---

## Composants BI reutilisables

### `EnterpriseKpiCard`

Affiche un KPI prioritaire avec :

- libelle ;
- valeur ;
- tendance ;
- statut ;
- accent visuel.

### `BIChart`

Wrapper ECharts pour eviter de dupliquer la configuration :

- theme sombre ;
- responsive ;
- tooltip coherente ;
- etat vide.

### `SmartDataGrid`

Wrapper AG Grid pour les tableaux analytiques :

- tri ;
- filtres ;
- export ;
- pagination ;
- colonnes configurables.

### `GlobalFilterBar`

Barre de filtres cockpit qui pilote le store Zustand.

---

## Regles UX

1. Eviter les pages verticales interminables.
2. Preferer les panels, tabs, drawers et scrolls locaux.
3. Garder les KPI critiques visibles en haut de page.
4. Mettre les actions metier dans le contexte de la page.
5. Ne pas dupliquer Power BI dans React.
6. Utiliser React pour piloter, simuler et surveiller.
7. Utiliser Power BI pour les dashboards decisionnels complets.

---

## Deploiement Vercel

Le dossier frontend de production est :

```text
08_FRONTEND
```

Variables Vercel importantes :

```text
VITE_API_URL=https://sp2i-backend.onrender.com
```

`vercel.json` doit garder une rewrite SPA pour que les routes comme
`/app/dqe` ou `/app/analytics` fonctionnent apres rafraichissement navigateur.

---

## Roadmap frontend courte

### V1 realisee

- Landing repositionnee sur le pilotage immobilier.
- Navigation cockpit enterprise.
- Services API centralises.
- DQE upload connecte au backend Render.
- React Query, Zustand, ECharts et AG Grid integres.
- Premier cockpit BI React connecte aux endpoints existants.

### V2 recommandee

- Brancher progressivement les endpoints `/analytics/*`.
- Remplacer les fallbacks par des datasets PostgreSQL reels.
- Ajouter le cross-filtering complet.
- Ajouter les drawers de detail ligne DQE, simulation et scenario.
- Ajouter les dashboards Power BI Embedded quand les URLs/tokens seront prets.
