# Power BI - Vues Neon SP2I CAPEX

Power BI doit se connecter a Neon et consommer uniquement les vues de ce dossier.

## Vues exposees

- `vw_capex_summary`
- `vw_project_kpis`
- `vw_dashboard_direction`
- `vw_dashboard_import`
- `vw_dashboard_chantier`

## Installation sur Neon

PowerShell :

```powershell
$NEON_URL="postgresql://USER:PASSWORD@HOST.neon.tech/neondb?sslmode=require"
psql $NEON_URL -f sql/powerbi/001_powerbi_views.sql
```

## Controle

```sql
SELECT * FROM vw_capex_summary;
SELECT * FROM vw_project_kpis;
SELECT * FROM vw_dashboard_direction;
SELECT * FROM vw_dashboard_import;
SELECT * FROM vw_dashboard_chantier LIMIT 20;
```

