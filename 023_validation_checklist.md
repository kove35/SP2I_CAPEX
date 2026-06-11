# SP2I CAPEX - Validation Checklist 023

Mode: audit and cutover checklist. Do not execute SQL from this document unless explicitly approved.

## Database Validation

Run only after SQL execution is approved:

```sql
SELECT COUNT(*) FROM vw_fact_metre_current;
SELECT COUNT(DISTINCT article_code) FROM vw_fact_metre_current;
SELECT COUNT(DISTINCT lot_code) FROM vw_fact_metre_current;
SELECT COUNT(*) FROM vw_dim_lot_active;
SELECT COUNT(*) FROM vw_dim_article_bpu_active;
```

Expected:

- `vw_fact_metre_current`: 4734 rows
- distinct articles: 2524
- distinct lots: 18
- `vw_dim_lot_active`: 18 rows
- `vw_dim_article_bpu_active`: 2524 rows

## Backend Static Validation

Completed locally:

```powershell
python -m compileall -q 07_API_BACKEND\app
```

Expected: no output, exit code 0.

Confirmed configuration module:

- `FACT_SOURCE = os.getenv("SP2I_FACT_SOURCE", "vw_fact_metre_current")`
- whitelist:
  - `fact_metre`
  - `vw_fact_metre_current`
  - `vw_fact_metre_v53_financial`

Confirmed no hardcoded SQL reads in target files:

- `analytics_repository.py`
- `analytics_service.py`
- `views.py`
- `schema_utils.py`

Pattern checked:

```text
FROM fact_metre
JOIN fact_metre
```

## Backend Runtime Validation

Test twice:

1. Historical mode:

```text
SP2I_FACT_SOURCE=fact_metre
```

2. V5.3 mode:

```text
SP2I_FACT_SOURCE=vw_fact_metre_current
```

Endpoints:

- `/analytics/dashboard`
- `/analytics/risk`
- `/analytics/drilldown`
- `/analytics/heatmap`
- `/analytics/timeline`
- `/analytics/cost-intelligence`
- `/analytics/spatial`
- `/analytics/spatial/dashboard`

Capture:

- HTTP code
- response time
- payload bytes
- SQL/backend exception status
- lots count
- article count when exposed
- CAPEX local/import/optimised/savings

## Power BI Validation

Views:

- `vw_capex_summary`
- `vw_project_kpis`
- `vw_dashboard_direction`
- `vw_dashboard_import`
- `vw_dashboard_chantier`
- `vw_bim_dashboard`
- `vw_spatial_dashboard`
- `vw_spatial_analytics`
- `vw_cost_intelligence`
- `vw_dim_lot_active`
- `vw_dim_sous_lot_active`
- `vw_dim_article_bpu_active`

Checks:

- view reads without SQL error
- expected row count
- 18 lots exposed
- 2524 articles exposed
- no relationship remains bound to the 7-lot historical dimension

## GO Criteria

- SQL validations 021, 022, 023 pass.
- Backend compileall passes.
- Backend endpoints return HTTP 200 in V5.3 mode.
- Power BI dimensions expose 18 lots and 2524 articles.
- `fact_metre` remains 290 rows / 7 lots.

## NO GO Criteria

- `vw_fact_metre_current` missing.
- `vw_dim_lot_active` not equal to 18 rows.
- `vw_dim_article_bpu_active` not equal to 2524 rows.
- Any target endpoint raises SQL errors in V5.3 mode.
- Power BI still displays only the legacy 7 lots.
