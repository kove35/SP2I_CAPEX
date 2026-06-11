-- SP2I CAPEX - Validation 016 BPU V5.3
-- Requetes read-only post-migration.

-- 1. Audit articles par vue generative source.
SELECT
    'vw_sp2i_generated_quantities' AS source_view,
    COUNT(DISTINCT generated_article_code) AS nb_articles_uniques
FROM vw_sp2i_generated_quantities
WHERE NULLIF(TRIM(generated_article_code), '') IS NOT NULL
UNION ALL
SELECT
    'vw_sp2i_generated_building',
    COUNT(DISTINCT generated_article_code)
FROM vw_sp2i_generated_building
WHERE NULLIF(TRIM(generated_article_code), '') IS NOT NULL
UNION ALL
SELECT
    'vw_sp2i_generated_envelope',
    COUNT(DISTINCT generated_article_code)
FROM vw_sp2i_generated_envelope
WHERE NULLIF(TRIM(generated_article_code), '') IS NOT NULL
UNION ALL
SELECT
    'vw_sp2i_generated_special_systems',
    COUNT(DISTINCT generated_article_code)
FROM vw_sp2i_generated_special_systems
WHERE NULLIF(TRIM(generated_article_code), '') IS NOT NULL
ORDER BY source_view;

-- 2. Existence de la table BPU V5.3.
SELECT
    'dim_bpu_v53' AS relation_name,
    to_regclass('dim_bpu_v53') IS NOT NULL AS exists_now;

-- 3. Volumes globaux attendus: 2524 articles et 18 lots.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT article_code) AS nb_articles_uniques,
    COUNT(DISTINCT lot_code) AS nb_lots,
    CASE WHEN COUNT(*) = 2524 THEN 'OK' ELSE 'CHECK_VOLUME' END AS volume_status,
    CASE WHEN COUNT(DISTINCT article_code) = 2524 THEN 'OK' ELSE 'CHECK_ARTICLES' END AS article_status,
    CASE WHEN COUNT(DISTINCT lot_code) = 18 THEN 'OK' ELSE 'CHECK_LOTS' END AS lot_status
FROM dim_bpu_v53;

-- 4. Articles sans lot.
SELECT
    COUNT(*) AS articles_sans_lot
FROM dim_bpu_v53
WHERE NULLIF(TRIM(lot_code), '') IS NULL;

-- 5. Articles sans unite.
SELECT
    COUNT(*) AS articles_sans_unite
FROM dim_bpu_v53
WHERE NULLIF(TRIM(unite), '') IS NULL;

-- 6. Articles dupliques.
SELECT
    article_code,
    COUNT(*) AS nb_occurrences
FROM dim_bpu_v53
GROUP BY article_code
HAVING COUNT(*) > 1
ORDER BY article_code;

-- 7. Articles master presents dans plusieurs lots avant seed BPU.
SELECT
    generated_article_code AS article_code,
    COUNT(DISTINCT lot_code) AS nb_lots,
    STRING_AGG(DISTINCT lot_code, ', ' ORDER BY lot_code) AS lots
FROM vw_sp2i_generated_dqe_master
WHERE NULLIF(TRIM(generated_article_code), '') IS NOT NULL
GROUP BY generated_article_code
HAVING COUNT(DISTINCT lot_code) > 1
ORDER BY generated_article_code;

-- 8. Repartition par lot.
SELECT
    lot_code,
    COUNT(*) AS nb_articles
FROM dim_bpu_v53
GROUP BY lot_code
ORDER BY lot_code;

-- 9. Couverture des 18 lots officiels.
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
    SELECT lot_code, COUNT(*) AS nb_articles
    FROM dim_bpu_v53
    GROUP BY lot_code
)
SELECT
    e.lot_code,
    COALESCE(a.nb_articles, 0) AS nb_articles,
    CASE WHEN a.lot_code IS NULL THEN 'MISSING' ELSE 'OK' END AS status
FROM expected_lots e
LEFT JOIN actual_lots a ON a.lot_code = e.lot_code
ORDER BY e.lot_code;

-- 10. Controle attendu avant enrichissement prix: tous les prix a 0.
SELECT
    COUNT(*) FILTER (WHERE prix_local_fcfa <> 0) AS prix_local_non_zero,
    COUNT(*) FILTER (WHERE prix_import_fcfa <> 0) AS prix_import_non_zero,
    COUNT(*) FILTER (WHERE prix_optimise_fcfa <> 0) AS prix_optimise_non_zero
FROM dim_bpu_v53;
