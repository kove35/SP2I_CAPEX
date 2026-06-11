-- SP2I CAPEX - Validation 021 V5.3 read cutover
-- Requetes read-only post-migration.

-- 1. Existence de la source canonique de lecture.
SELECT
    'vw_fact_metre_current' AS relation_name,
    to_regclass('vw_fact_metre_current') IS NOT NULL AS exists_now;

-- 2. Volumes attendus.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT article_code) AS nb_articles,
    COUNT(DISTINCT lot_code) AS nb_lots,
    CASE WHEN COUNT(*) = 4734 THEN 'OK' ELSE 'CHECK_VOLUME' END AS volume_status,
    CASE WHEN COUNT(DISTINCT lot_code) = 18 THEN 'OK' ELSE 'CHECK_LOTS' END AS lot_status
FROM vw_fact_metre_current;

-- 3. Totaux financiers.
SELECT
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie,
    CASE WHEN COALESCE(SUM(capex_local), 0) > 0 THEN 'OK' ELSE 'NO_CAPEX_LOCAL' END AS capex_local_status,
    CASE WHEN COALESCE(SUM(capex_import), 0) > 0 THEN 'OK' ELSE 'NO_CAPEX_IMPORT' END AS capex_import_status,
    CASE WHEN COALESCE(SUM(capex_optimise), 0) > 0 THEN 'OK' ELSE 'NO_CAPEX_OPTIMISE' END AS capex_optimise_status,
    CASE WHEN COALESCE(SUM(economie), 0) > 0 THEN 'OK' ELSE 'NO_ECONOMIE' END AS economie_status
FROM vw_fact_metre_current;

-- 4. Lignes sans lot, article ou prix.
SELECT
    COUNT(*) FILTER (WHERE NULLIF(TRIM(lot_code), '') IS NULL) AS lignes_sans_lot,
    COUNT(*) FILTER (WHERE NULLIF(TRIM(article_code), '') IS NULL) AS lignes_sans_article,
    COUNT(*) FILTER (WHERE COALESCE(prix_local_fcfa, 0) <= 0) AS lignes_sans_prix_local,
    COUNT(*) FILTER (WHERE COALESCE(prix_import_fcfa, 0) <= 0) AS lignes_sans_prix_import,
    COUNT(*) FILTER (WHERE COALESCE(prix_optimise_fcfa, 0) <= 0) AS lignes_sans_prix_optimise
FROM vw_fact_metre_current;

-- 5. Couverture financiere.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(*) FILTER (
        WHERE NULLIF(TRIM(lot_code), '') IS NOT NULL
          AND NULLIF(TRIM(article_code), '') IS NOT NULL
          AND COALESCE(prix_local_fcfa, 0) > 0
          AND COALESCE(prix_import_fcfa, 0) > 0
          AND COALESCE(prix_optimise_fcfa, 0) > 0
          AND COALESCE(capex_local, 0) > 0
          AND COALESCE(capex_import, 0) > 0
          AND COALESCE(capex_optimise, 0) > 0
    ) AS lignes_valorisees,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE NULLIF(TRIM(lot_code), '') IS NOT NULL
              AND NULLIF(TRIM(article_code), '') IS NOT NULL
              AND COALESCE(prix_local_fcfa, 0) > 0
              AND COALESCE(prix_import_fcfa, 0) > 0
              AND COALESCE(prix_optimise_fcfa, 0) > 0
              AND COALESCE(capex_local, 0) > 0
              AND COALESCE(capex_import, 0) > 0
              AND COALESCE(capex_optimise, 0) > 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS couverture_financiere_pct
FROM vw_fact_metre_current;

-- 6. Repartition par lot.
SELECT
    lot_code,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT article_code) AS nb_articles,
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie
FROM vw_fact_metre_current
GROUP BY lot_code
ORDER BY lot_code;

-- 7. Controle des vues Power BI basculees.
SELECT 'vw_capex_summary' AS view_name, COUNT(*) AS nb_lignes FROM vw_capex_summary
UNION ALL
SELECT 'vw_project_kpis', COUNT(*) FROM vw_project_kpis
UNION ALL
SELECT 'vw_dashboard_direction', COUNT(*) FROM vw_dashboard_direction
UNION ALL
SELECT 'vw_dashboard_import', COUNT(*) FROM vw_dashboard_import
UNION ALL
SELECT 'vw_dashboard_chantier', COUNT(*) FROM vw_dashboard_chantier
UNION ALL
SELECT 'vw_bim_dashboard', COUNT(*) FROM vw_bim_dashboard
UNION ALL
SELECT 'vw_spatial_dashboard', COUNT(*) FROM vw_spatial_dashboard
UNION ALL
SELECT 'vw_spatial_analytics', COUNT(*) FROM vw_spatial_analytics
UNION ALL
SELECT 'vw_cost_intelligence', COUNT(*) FROM vw_cost_intelligence
UNION ALL
SELECT 'vw_dim_lot_active', COUNT(*) FROM vw_dim_lot_active
UNION ALL
SELECT 'vw_dim_sous_lot_active', COUNT(*) FROM vw_dim_sous_lot_active
UNION ALL
SELECT 'vw_dim_article_bpu_active', COUNT(*) FROM vw_dim_article_bpu_active;

-- 8. Controle non-regression: fact_metre historique reste present.
SELECT
    'fact_metre' AS object_name,
    COUNT(*) AS current_rows,
    COUNT(DISTINCT lot) AS current_lots
FROM fact_metre;
