-- SP2I CAPEX - Validation 017 Pricing Strategy BPU V5.3
-- Requetes read-only post-migration.

-- 1. Audit pricing: articles et unites par lot.
SELECT
    lot_code,
    COUNT(*) AS nb_articles,
    COUNT(DISTINCT unite) AS nb_unites_distinctes,
    STRING_AGG(DISTINCT NULLIF(TRIM(unite), ''), ', ' ORDER BY NULLIF(TRIM(unite), '')) AS unites
FROM dim_bpu_v53
GROUP BY lot_code
ORDER BY lot_code;

-- 2. Existence des objets 017.
SELECT
    'dim_pricing_strategy_v53' AS relation_name,
    to_regclass('dim_pricing_strategy_v53') IS NOT NULL AS exists_now
UNION ALL
SELECT
    'vw_bpu_v53_priced',
    to_regclass('vw_bpu_v53_priced') IS NOT NULL;

-- 3. Couverture strategie par lot.
SELECT
    COUNT(*) AS nb_lots_strategie,
    COUNT(DISTINCT lot_code) AS nb_lots_distincts,
    CASE WHEN COUNT(*) = 18 THEN 'OK' ELSE 'CHECK_LOTS' END AS status
FROM dim_pricing_strategy_v53;

-- 4. Lots absents de la strategie.
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
)
SELECT
    e.lot_code,
    CASE WHEN s.lot_code IS NULL THEN 'MISSING' ELSE 'OK' END AS status
FROM expected_lots e
LEFT JOIN dim_pricing_strategy_v53 s ON s.lot_code = e.lot_code
ORDER BY e.lot_code;

-- 5. Lots inattendus dans la strategie.
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
)
SELECT
    s.lot_code
FROM dim_pricing_strategy_v53 s
LEFT JOIN expected_lots e ON e.lot_code = s.lot_code
WHERE e.lot_code IS NULL
ORDER BY s.lot_code;

-- 6. Couverture prix article.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT article_code) AS nb_articles_uniques,
    COUNT(DISTINCT lot_code) AS nb_lots,
    COUNT(*) FILTER (WHERE prix_local_fcfa <= 0) AS articles_sans_prix_local,
    COUNT(*) FILTER (WHERE prix_import_fcfa <= 0) AS articles_sans_prix_import,
    COUNT(*) FILTER (WHERE prix_optimise_fcfa <= 0) AS articles_sans_prix_optimise,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE prix_local_fcfa > 0
              AND prix_import_fcfa > 0
              AND prix_optimise_fcfa > 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS couverture_prix_pct
FROM vw_bpu_v53_priced;

-- 7. Articles sans lot ou sans strategie.
SELECT
    COUNT(*) FILTER (WHERE NULLIF(TRIM(b.lot_code), '') IS NULL) AS articles_sans_lot,
    COUNT(*) FILTER (WHERE s.lot_code IS NULL) AS articles_sans_strategie
FROM dim_bpu_v53 b
LEFT JOIN dim_pricing_strategy_v53 s ON s.lot_code = b.lot_code;

-- 8. Articles encore non valorises.
SELECT
    article_code,
    designation,
    lot_code,
    prix_local_fcfa,
    prix_import_fcfa,
    prix_optimise_fcfa
FROM vw_bpu_v53_priced
WHERE prix_local_fcfa <= 0
   OR prix_import_fcfa <= 0
   OR prix_optimise_fcfa <= 0
ORDER BY lot_code, article_code;

-- 9. Estimation CAPEX genere depuis le master V5.3.
SELECT
    m.lot_code,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT m.generated_article_code) AS nb_articles,
    ROUND(SUM(m.quantity * p.prix_local_fcfa), 2) AS capex_local_fcfa,
    ROUND(SUM(m.quantity * p.prix_import_fcfa), 2) AS capex_import_fcfa,
    ROUND(SUM(m.quantity * p.prix_optimise_fcfa), 2) AS capex_optimise_fcfa,
    ROUND(SUM(m.quantity * (p.prix_local_fcfa - p.prix_optimise_fcfa)), 2) AS economie_fcfa
FROM vw_sp2i_generated_dqe_master m
JOIN vw_bpu_v53_priced p
  ON p.article_code = m.generated_article_code
GROUP BY m.lot_code
ORDER BY m.lot_code;

-- 10. Estimation CAPEX globale.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT m.generated_article_code) AS nb_articles,
    COUNT(DISTINCT m.lot_code) AS nb_lots,
    ROUND(SUM(m.quantity * p.prix_local_fcfa), 2) AS capex_local_fcfa,
    ROUND(SUM(m.quantity * p.prix_import_fcfa), 2) AS capex_import_fcfa,
    ROUND(SUM(m.quantity * p.prix_optimise_fcfa), 2) AS capex_optimise_fcfa,
    ROUND(SUM(m.quantity * (p.prix_local_fcfa - p.prix_optimise_fcfa)), 2) AS economie_fcfa
FROM vw_sp2i_generated_dqe_master m
JOIN vw_bpu_v53_priced p
  ON p.article_code = m.generated_article_code;
