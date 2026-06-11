-- SP2I CAPEX - Validation 015 V5.3 DQE Master
-- Requetes read-only post-migration.

-- 1. Existence de la vue master.
SELECT
    'vw_sp2i_generated_dqe_master' AS relation_name,
    to_regclass('vw_sp2i_generated_dqe_master') IS NOT NULL AS exists_now;

-- 2. Volumes globaux attendus.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT generated_article_code) AS nb_articles_uniques,
    COUNT(DISTINCT lot_code) AS nb_lots,
    CASE WHEN COUNT(*) = 4734 THEN 'OK' ELSE 'CHECK_VOLUME' END AS volume_status,
    CASE WHEN COUNT(DISTINCT generated_article_code) = 2524 THEN 'OK' ELSE 'CHECK_ARTICLES' END AS article_status,
    CASE WHEN COUNT(DISTINCT lot_code) = 18 THEN 'OK' ELSE 'CHECK_LOTS' END AS lot_status
FROM vw_sp2i_generated_dqe_master;

-- 3. Repartition par lot.
SELECT
    lot_code,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT generated_article_code) AS nb_articles_uniques
FROM vw_sp2i_generated_dqe_master
GROUP BY lot_code
ORDER BY lot_code;

-- 4. Repartition par source_view.
SELECT
    source_view,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT generated_article_code) AS nb_articles_uniques,
    COUNT(DISTINCT lot_code) AS nb_lots
FROM vw_sp2i_generated_dqe_master
GROUP BY source_view
ORDER BY source_view;

-- 5. Couverture des 18 lots officiels.
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
    FROM vw_sp2i_generated_dqe_master
    GROUP BY lot_code
)
SELECT
    e.lot_code,
    COALESCE(a.nb_lignes, 0) AS nb_lignes,
    CASE WHEN a.lot_code IS NULL THEN 'MISSING' ELSE 'OK' END AS status
FROM expected_lots e
LEFT JOIN actual_lots a ON a.lot_code = e.lot_code
ORDER BY e.lot_code;

-- 6. Lots inattendus.
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
    m.lot_code,
    COUNT(*) AS nb_lignes
FROM vw_sp2i_generated_dqe_master m
LEFT JOIN expected_lots e ON e.lot_code = m.lot_code
WHERE e.lot_code IS NULL
GROUP BY m.lot_code
ORDER BY m.lot_code;

-- 7. Controle qualite des champs critiques.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(*) FILTER (WHERE NULLIF(TRIM(lot_code), '') IS NULL) AS lot_code_vides,
    COUNT(*) FILTER (WHERE NULLIF(TRIM(generated_article_code), '') IS NULL) AS generated_article_code_vides,
    COUNT(*) FILTER (WHERE NULLIF(TRIM(generated_designation), '') IS NULL) AS generated_designation_vides,
    COUNT(*) FILTER (WHERE quantity IS NULL) AS quantity_nulles,
    COUNT(*) FILTER (WHERE NULLIF(TRIM(unit), '') IS NULL) AS unit_vides
FROM vw_sp2i_generated_dqe_master;

-- 8. Securite: objets metiers proteges non modifies par cette migration additive.
SELECT 'fact_metre' AS object_name, COUNT(*) AS current_rows FROM fact_metre
UNION ALL
SELECT 'fact_simulation', COUNT(*) FROM fact_simulation
UNION ALL
SELECT 'fact_approvals', COUNT(*) FROM fact_approvals
UNION ALL
SELECT 'procurement_decisions', COUNT(*) FROM procurement_decisions;
