# SP2I Analytics Engine V1

## Objectif

SP2I Analytics Engine V1 ajoute une couche BI proprietaire au-dessus de
PostgreSQL sans casser les endpoints existants.

Le frontend React peut consommer des datasets deja agreges pour :

- KPI cards.
- ECharts.
- AG Grid.
- cross-filtering.
- drill-down.
- dashboards temps reel.

## Architecture

```text
React / Vercel
    |
    v
/analytics/*
    |
    v
AnalyticsService
    |
    v
AnalyticsRepository
    |
    v
PostgreSQL views + fact_metre
```

## Endpoints

Tous les endpoints retournent le contrat standard :

```json
{
  "status": "SUCCESS",
  "filters": {},
  "pagination": {},
  "kpis": {},
  "charts": {},
  "table": [],
  "metadata": {}
}
```

Endpoints disponibles :

- `/analytics/capex`
- `/analytics/kpis`
- `/analytics/risk`
- `/analytics/procurement`
- `/analytics/logistics`
- `/analytics/scenarios`
- `/analytics/heatmap`
- `/analytics/drilldown`
- `/analytics/timeline`
- `/analytics/dashboard`
- `/analytics/system-health`
- `/analytics/query-performance`
- `/analytics/cache-status`

## Filtres supportes

- projet
- scenario
- batiment
- niveau
- lot
- famille
- fournisseur
- decision_import
- periode_debut
- periode_fin
- criticite
- statut_chantier

## Drill-down

La hierarchie cible est :

```text
Projet -> Batiment -> Niveau -> Lot -> Famille -> Article
```

## Cache

La V1 contient un cache memoire simple dans `app/analytics/cache`.

Il prepare une future migration Redis sans changer les services consommateurs.

## Vues SQL

Les vues sont creees au startup par la migration douce :

- `vw_capex_summary`
- `vw_capex_by_lot`
- `vw_capex_by_building`
- `vw_import_analysis`
- `vw_procurement_risk`
- `vw_logistics_summary`
- `vw_project_kpis`
- `vw_dashboard_direction`
- `vw_dashboard_import`
- `vw_dashboard_chantier`

## Evolution V2

- materialized views.
- Redis.
- multi-tenant.
- JWT et permissions dashboard.
- refresh temps reel.
- exports AG Grid serveur.
