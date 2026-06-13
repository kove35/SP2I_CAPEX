-- SP2I CAPEX - Phase 031 validation queries
-- Read-only validation for V6 production readiness.
-- Expected mode: V5 and V6 run in parallel.

-- 1. Object existence
SELECT
    object_name,
    to_regclass(object_name) AS resolved_object
FROM (
    VALUES
        ('dim_price_reference'),
        ('dim_article_price_mapping'),
        ('vw_bpu_v53_priced_v2'),
        ('vw_project_cost_summary'),
        ('vw_dashboard_direction_v6'),
        ('vw_cost_intelligence_v6'),
        ('vw_bpu_v53_priced'),
        ('vw_fact_metre_current'),
        ('vw_fact_metre_financial_canonical')
) AS objects(object_name);

-- 2. V5 preservation checks
SELECT 'vw_bpu_v53_priced' AS object_name, COUNT(*) AS nb_lignes
FROM vw_bpu_v53_priced
UNION ALL
SELECT 'vw_fact_metre_current', COUNT(*)
FROM vw_fact_metre_current
UNION ALL
SELECT 'vw_fact_metre_financial_canonical', COUNT(*)
FROM vw_fact_metre_financial_canonical;

-- 3. V6 price reference coverage
SELECT
    lot_code,
    scope_type,
    COUNT(*) AS nb_references,
    COUNT(*) FILTER (WHERE prix_local_fcfa > 0) AS prix_local_ok,
    COUNT(*) FILTER (WHERE prix_import_fcfa > 0) AS prix_import_ok,
    COUNT(*) FILTER (WHERE prix_optimise_fcfa > 0) AS prix_optimise_ok
FROM dim_price_reference
WHERE is_active = TRUE
GROUP BY lot_code, scope_type
ORDER BY lot_code, scope_type;

-- 4. V6 article mapping coverage
SELECT
    COUNT(*) AS nb_articles_bpu,
    COUNT(m.article_code) AS nb_articles_mapped,
    ROUND(100.0 * COUNT(m.article_code) / NULLIF(COUNT(*), 0), 2) AS mapping_coverage_pct
FROM dim_bpu_v53 b
LEFT JOIN dim_article_price_mapping m
    ON m.article_code = b.article_code
   AND m.is_active = TRUE;

SELECT
    COALESCE(p.pricing_scope, 'UNMAPPED') AS pricing_scope,
    COALESCE(p.pricing_confidence, 'UNMAPPED') AS pricing_confidence,
    COUNT(*) AS nb_articles
FROM dim_bpu_v53 b
LEFT JOIN vw_bpu_v53_priced_v2 p
    ON p.article_code = b.article_code
GROUP BY COALESCE(p.pricing_scope, 'UNMAPPED'), COALESCE(p.pricing_confidence, 'UNMAPPED')
ORDER BY nb_articles DESC;

-- 5. V6 financial direct CAPEX by pricing scope
WITH v6_lines AS (
    SELECT
        c.article_code,
        c.lot,
        c.quantite,
        p.pricing_scope,
        p.prix_local_fcfa,
        c.quantite * p.prix_local_fcfa AS capex_local_v6
    FROM vw_fact_metre_financial_canonical c
    JOIN vw_bpu_v53_priced_v2 p
        ON p.article_code = c.article_code
),
total AS (
    SELECT SUM(capex_local_v6) AS total_capex
    FROM v6_lines
)
SELECT
    pricing_scope,
    COUNT(*) AS nb_lignes,
    ROUND(SUM(capex_local_v6), 0) AS capex_local_v6,
    ROUND(100.0 * SUM(capex_local_v6) / NULLIF((SELECT total_capex FROM total), 0), 2) AS pct_capex
FROM v6_lines
GROUP BY pricing_scope
ORDER BY capex_local_v6 DESC;

-- 6. Project cost summary
SELECT
    capex_direct,
    indirect_costs,
    site_installation,
    import_logistics,
    contingency,
    total_project_cost,
    capex_direct_per_m2,
    total_project_cost_per_m2,
    total_project_cost_per_appartement,
    total_project_cost_per_niveau,
    fallback_legacy_lot_capex,
    fallback_legacy_lot_pct
FROM vw_project_cost_summary;

-- 7. Direction dashboard V6
SELECT
    lot,
    nb_lignes,
    nb_articles,
    capex_direct,
    pct_capex_direct,
    fallback_legacy_lot_lines,
    fallback_legacy_lot_capex
FROM vw_dashboard_direction_v6
ORDER BY capex_direct DESC;

-- 8. Cost intelligence V6
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT article_code) AS nb_articles,
    COUNT(DISTINCT lot) AS nb_lots,
    ROUND(SUM(capex_local), 0) AS capex_local,
    ROUND(SUM(capex_import), 0) AS capex_import,
    ROUND(SUM(capex_optimise), 0) AS capex_optimise,
    ROUND(SUM(economie), 0) AS economie
FROM vw_cost_intelligence_v6;

-- 9. V5 versus V6 comparison
WITH v5 AS (
    SELECT
        SUM(capex_local) AS capex_local_v5,
        COUNT(*) AS lignes_v5,
        COUNT(DISTINCT article_code) AS articles_v5,
        COUNT(DISTINCT lot) AS lots_v5
    FROM vw_fact_metre_financial_canonical
),
v6 AS (
    SELECT
        capex_direct AS capex_local_v6,
        total_project_cost,
        fallback_legacy_lot_pct
    FROM vw_project_cost_summary
)
SELECT
    v5.lignes_v5,
    v5.articles_v5,
    v5.lots_v5,
    ROUND(v5.capex_local_v5, 0) AS capex_local_v5,
    ROUND(v6.capex_local_v6, 0) AS capex_local_v6,
    ROUND(v6.total_project_cost, 0) AS total_project_cost_v6,
    ROUND(100.0 * (v5.capex_local_v5 - v6.capex_local_v6) / NULLIF(v5.capex_local_v5, 0), 2) AS capex_reduction_pct,
    v6.fallback_legacy_lot_pct
FROM v5
CROSS JOIN v6;

-- 10. Blocking validation flags
WITH checks AS (
    SELECT
        (SELECT COUNT(*) FROM vw_fact_metre_financial_canonical) AS canonical_lines,
        (SELECT COUNT(DISTINCT article_code) FROM vw_fact_metre_financial_canonical) AS canonical_articles,
        (SELECT COUNT(DISTINCT lot) FROM vw_fact_metre_financial_canonical) AS canonical_lots,
        (SELECT COUNT(*) FROM vw_bpu_v53_priced_v2 WHERE prix_local_fcfa <= 0 OR prix_local_fcfa IS NULL) AS articles_without_local_price,
        (SELECT COUNT(*) FROM vw_bpu_v53_priced_v2 WHERE prix_import_fcfa <= 0 OR prix_import_fcfa IS NULL) AS articles_without_import_price,
        (SELECT COUNT(*) FROM vw_project_cost_summary WHERE capex_direct <= 0 OR total_project_cost <= 0) AS invalid_project_cost_rows,
        (SELECT COUNT(*) FROM vw_project_cost_summary WHERE fallback_legacy_lot_pct >= 5.0) AS fallback_above_5pct
)
SELECT
    *,
    CASE
        WHEN canonical_lines = 1298
         AND canonical_articles = 198
         AND canonical_lots = 18
         AND articles_without_local_price = 0
         AND articles_without_import_price = 0
         AND invalid_project_cost_rows = 0
         AND fallback_above_5pct = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS validation_status
FROM checks;
