# Power BI - Vues Neon SP2I CAPEX

Power BI doit se connecter a Neon et consommer uniquement les vues de ce dossier.

## Vues exposees

- `vw_capex_summary`
- `vw_project_kpis`
- `vw_dashboard_direction`
- `vw_dashboard_import`
- `vw_dashboard_chantier`
- `vw_bim_dashboard`
- `vw_spatial_dashboard`
- `vw_spatial_analytics`
- `vw_cost_intelligence`

## Installation sur Neon

PowerShell :

```powershell
$NEON_URL="postgresql://USER:PASSWORD@HOST.neon.tech/neondb?sslmode=require"
psql $NEON_URL -f 09_INFRA/sql/009_plan_ready_schema.sql
psql $NEON_URL -f 09_INFRA/sql/010_spatial_analytics_schema.sql
psql $NEON_URL -f sql/powerbi/001_powerbi_views.sql
```

## Controle

```sql
SELECT * FROM vw_capex_summary;
SELECT * FROM vw_project_kpis;
SELECT * FROM vw_dashboard_direction;
SELECT * FROM vw_dashboard_import;
SELECT * FROM vw_dashboard_chantier LIMIT 20;
SELECT * FROM vw_bim_dashboard LIMIT 20;
SELECT * FROM vw_spatial_dashboard LIMIT 20;
SELECT * FROM vw_spatial_analytics LIMIT 20;
SELECT * FROM vw_cost_intelligence LIMIT 20;
```

## BIM_READY

`vw_bim_dashboard` expose le chemin Projet / Batiment / Niveau / Appartement / Piece / Lot / Famille / Article.

Mesures disponibles : `capex_local`, `capex_import`, `economie`, `nb_lignes`.

## PLAN_READY

`vw_spatial_dashboard` expose le pilotage plans 2D / DQE sans dependance IFC/Revit.

Chemin disponible : Projet / Batiment / Niveau / Appartement / Piece / Type piece / Lot / Famille / Article.

Mesures disponibles : `surface_m2`, `capex_local`, `capex_import`, `capex_optimise`, `economie`, `capex_m2`, `nb_lignes`.

## SPATIAL_ANALYTICS

`vw_spatial_analytics` expose le pilotage Projet / Batiment / Niveau / Appartement / Zone / Piece / Lot / Sous-lot / Article.

Mesures disponibles : `surface_m2`, `capex_local`, `capex_import`, `capex_optimise`, `economie`, `capex_m2`, `nb_lignes`.

## COST_INTELLIGENCE_V1

`vw_cost_intelligence` expose les colonnes economiques pretes pour Pareto, benchmark, CAPEX/m2 et detection d'anomalies.

Mesures disponibles : `capex_local`, `capex_import`, `capex_optimise`, `economie`, `capex_m2`, `roi`, `nb_lignes`.
