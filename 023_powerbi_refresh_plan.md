# SP2I CAPEX - Power BI Refresh Plan 023

Mode: plan only. No SQL execution from this document.

## Objective

Switch Power BI reads to the V5.3 canonical model:

- `vw_fact_metre_current`
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

Expected model:

- 4734 fact rows
- 2524 active BPU articles
- 18 official lots

## Preconditions

1. `021_v53_read_cutover.sql` executed successfully.
2. `022_v53_dimensions_rebuild_fixed.sql` executed successfully.
3. `validation_queries_021.sql`, `validation_queries_022.sql`, and `023_v53_backend_cutover.sql` pass.
4. `fact_metre` still has 290 rows and 7 historical lots.

## Refresh Steps

1. Open Power BI Desktop or Power BI Service dataset settings.
2. Confirm Neon connection still points to `neondb` on branch `br-floral-silence-alweph5n`.
3. Refresh schema metadata for the listed views.
4. Confirm relationships:
   - fact lot key: `vw_fact_metre_current.lot_code` to `vw_dim_lot_active.lot`
   - fact article key: `vw_fact_metre_current.article_code` to `vw_dim_article_bpu_active.code_article`
   - sous-lot key when used: `vw_fact_metre_current.sous_lot_code` to `vw_dim_sous_lot_active.sous_lot_id`
5. Run full dataset refresh.
6. Validate dashboards:
   - Direction
   - Import
   - Chantier
   - BIM
   - Spatial
   - Cost Intelligence

## Expected Checks

- `vw_dim_lot_active`: 18 rows.
- `vw_dim_article_bpu_active`: 2524 rows.
- No visual filtered down to the legacy 7 lots.
- No relationship pointing to historical `dim_lot` or `fact_metre`.
- CAPEX local, import, optimised, and savings are positive.

## Risks

- Existing Power BI model may cache old column metadata.
- Relationships may still target old dimensions if manually configured.
- `vw_dim_sous_lot_active` contract must match existing Power BI column names exactly.

## Rollback

1. Set backend env back to `SP2I_FACT_SOURCE=fact_metre`.
2. Re-run historical Power BI baseline if needed:
   - `09_INFRA/sql/011_powerbi_neon_integrity_fix.sql`
   - or `sql/powerbi/001_powerbi_views.sql`
3. Refresh Power BI dataset.
