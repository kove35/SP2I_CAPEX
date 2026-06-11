-- SP2I CAPEX - Phase 023 V5.3 backend cutover validation
-- Migration/Runbook SQL: 023_v53_backend_cutover.sql
--
-- Mode: read-only validation.
-- This file does not modify data, does not drop objects and does not update
-- fact_metre. It validates that Analytics and Power BI can safely switch
-- reads to vw_fact_metre_current through SP2I_FACT_SOURCE.

BEGIN READ ONLY;

-- 1. Target and prerequisites.
SELECT
    current_database() AS database_name,
    current_user AS user_name,
    current_setting('neon.branch_id', true) AS neon_branch_id;

SELECT
    'vw_fact_metre_current' AS object_name,
    to_regclass('vw_fact_metre_current') IS NOT NULL AS exists_now
UNION ALL
SELECT 'vw_fact_metre_v53_financial', to_regclass('vw_fact_metre_v53_financial') IS NOT NULL
UNION ALL
SELECT 'vw_sp2i_generated_dqe_master', to_regclass('vw_sp2i_generated_dqe_master') IS NOT NULL
UNION ALL
SELECT 'dim_bpu_v53', to_regclass('dim_bpu_v53') IS NOT NULL
UNION ALL
SELECT 'vw_bpu_v53_priced', to_regclass('vw_bpu_v53_priced') IS NOT NULL
UNION ALL
SELECT 'vw_dim_lot_active', to_regclass('vw_dim_lot_active') IS NOT NULL
UNION ALL
SELECT 'vw_dim_sous_lot_active', to_regclass('vw_dim_sous_lot_active') IS NOT NULL
UNION ALL
SELECT 'vw_dim_article_bpu_active', to_regclass('vw_dim_article_bpu_active') IS NOT NULL;

-- 2. V5.3 canonical source.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT article_code) AS nb_articles,
    COUNT(DISTINCT lot_code) AS nb_lots,
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie,
    CASE WHEN COUNT(*) = 4734 THEN 'OK' ELSE 'CHECK_ROWS' END AS rows_status,
    CASE WHEN COUNT(DISTINCT article_code) = 2524 THEN 'OK' ELSE 'CHECK_ARTICLES' END AS articles_status,
    CASE WHEN COUNT(DISTINCT lot_code) = 18 THEN 'OK' ELSE 'CHECK_LOTS' END AS lots_status
FROM vw_fact_metre_current;

-- 3. Active Power BI dimensions rebuilt on V5.3.
SELECT
    COUNT(*) AS dim_lot_rows,
    COUNT(DISTINCT lot) AS dim_lot_distinct_lots,
    CASE WHEN COUNT(*) = 18 AND COUNT(DISTINCT lot) = 18 THEN 'OK' ELSE 'CHECK_DIM_LOTS' END AS status
FROM vw_dim_lot_active;

SELECT
    COUNT(*) AS dim_article_rows,
    COUNT(DISTINCT code_article) AS dim_article_distinct_articles,
    COUNT(DISTINCT lot) AS dim_article_lots,
    CASE WHEN COUNT(*) = 2524 THEN 'OK' ELSE 'CHECK_DIM_ARTICLES' END AS article_status,
    CASE WHEN COUNT(DISTINCT lot) = 18 THEN 'OK' ELSE 'CHECK_DIM_ARTICLE_LOTS' END AS lot_status
FROM vw_dim_article_bpu_active;

-- 4. Power BI views smoke test.
SELECT 'vw_capex_summary' AS view_name, COUNT(*) AS nb_lignes FROM vw_capex_summary
UNION ALL SELECT 'vw_project_kpis', COUNT(*) FROM vw_project_kpis
UNION ALL SELECT 'vw_dashboard_direction', COUNT(*) FROM vw_dashboard_direction
UNION ALL SELECT 'vw_dashboard_import', COUNT(*) FROM vw_dashboard_import
UNION ALL SELECT 'vw_dashboard_chantier', COUNT(*) FROM vw_dashboard_chantier
UNION ALL SELECT 'vw_bim_dashboard', COUNT(*) FROM vw_bim_dashboard
UNION ALL SELECT 'vw_spatial_dashboard', COUNT(*) FROM vw_spatial_dashboard
UNION ALL SELECT 'vw_spatial_analytics', COUNT(*) FROM vw_spatial_analytics
UNION ALL SELECT 'vw_cost_intelligence', COUNT(*) FROM vw_cost_intelligence
UNION ALL SELECT 'vw_dim_lot_active', COUNT(*) FROM vw_dim_lot_active
UNION ALL SELECT 'vw_dim_sous_lot_active', COUNT(*) FROM vw_dim_sous_lot_active
UNION ALL SELECT 'vw_dim_article_bpu_active', COUNT(*) FROM vw_dim_article_bpu_active;

-- 5. Expected official lots.
WITH expected_lots(lot_code) AS (
    VALUES
        ('LOT_ASC'),
        ('LOT_CAR'),
        ('LOT_CFA'),
        ('LOT_CVC'),
        ('LOT_ELEC'),
        ('LOT_FACADE'),
        ('LOT_FP'),
        ('LOT_GO'),
        ('LOT_INCENDIE'),
        ('LOT_MAC'),
        ('LOT_MENU_EXT'),
        ('LOT_MENU_INT'),
        ('LOT_PLOMB'),
        ('LOT_PNT'),
        ('LOT_SAN'),
        ('LOT_SECURITE'),
        ('LOT_TOIT'),
        ('LOT_VRD')
),
actual_lots AS (
    SELECT lot_code, COUNT(*) AS nb_lignes
    FROM vw_fact_metre_current
    GROUP BY lot_code
)
SELECT
    e.lot_code,
    COALESCE(a.nb_lignes, 0) AS nb_lignes,
    CASE WHEN a.lot_code IS NULL THEN 'MISSING' ELSE 'OK' END AS status
FROM expected_lots e
LEFT JOIN actual_lots a ON a.lot_code = e.lot_code
ORDER BY e.lot_code;

-- 6. Historical source remains intact.
SELECT
    COUNT(*) AS fact_metre_rows,
    COUNT(DISTINCT lot) AS fact_metre_lots,
    CASE WHEN COUNT(*) = 290 THEN 'OK' ELSE 'CHECK_HISTORICAL_ROWS' END AS rows_status,
    CASE WHEN COUNT(DISTINCT lot) = 7 THEN 'OK' ELSE 'CHECK_HISTORICAL_LOTS' END AS lots_status
FROM fact_metre;

ROLLBACK;
