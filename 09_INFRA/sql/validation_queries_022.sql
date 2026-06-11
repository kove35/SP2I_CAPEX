-- SP2I CAPEX - Validation 022 V5.3 dimensions rebuild
-- Requetes read-only post-migration.

-- 1. Existence des vues reconstruites.
SELECT
    'vw_dim_lot_active' AS relation_name,
    to_regclass('vw_dim_lot_active') IS NOT NULL AS exists_now
UNION ALL
SELECT
    'vw_dim_sous_lot_active',
    to_regclass('vw_dim_sous_lot_active') IS NOT NULL
UNION ALL
SELECT
    'vw_dim_article_bpu_active',
    to_regclass('vw_dim_article_bpu_active') IS NOT NULL;

-- 2. Lots actifs V5.3.
SELECT
    COUNT(*) AS nb_lots,
    COUNT(DISTINCT lot) AS nb_lots_distincts,
    CASE WHEN COUNT(*) = 18 THEN 'OK' ELSE 'CHECK_VOLUME' END AS volume_status,
    CASE WHEN COUNT(DISTINCT lot) = 18 THEN 'OK' ELSE 'CHECK_DISTINCT_LOTS' END AS distinct_status
FROM vw_dim_lot_active;

-- 3. Articles BPU actifs V5.3.
SELECT
    COUNT(*) AS nb_articles,
    COUNT(DISTINCT code_article) AS nb_articles_distincts,
    COUNT(DISTINCT lot) AS nb_lots,
    CASE WHEN COUNT(*) = 2524 THEN 'OK' ELSE 'CHECK_ARTICLES' END AS article_status,
    CASE WHEN COUNT(DISTINCT lot) = 18 THEN 'OK' ELSE 'CHECK_LOTS' END AS lot_status
FROM vw_dim_article_bpu_active;

-- 4. Couverture des 18 lots officiels.
WITH expected_lots(lot) AS (
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
    SELECT lot, COUNT(*) AS nb_lignes
    FROM vw_dim_lot_active
    GROUP BY lot
)
SELECT
    e.lot,
    COALESCE(a.nb_lignes, 0) AS nb_lignes,
    CASE WHEN a.lot IS NULL THEN 'MISSING' ELSE 'OK' END AS status
FROM expected_lots e
LEFT JOIN actual_lots a ON a.lot = e.lot
ORDER BY e.lot;

-- 5. Lots inattendus.
WITH expected_lots(lot) AS (
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
    a.lot,
    COUNT(*) AS nb_lignes
FROM vw_dim_lot_active a
LEFT JOIN expected_lots e ON e.lot = a.lot
WHERE e.lot IS NULL
GROUP BY a.lot
ORDER BY a.lot;

-- 6. Sous-lots actifs.
SELECT
    COUNT(*) AS nb_sous_lots,
    COUNT(DISTINCT sous_lot_id) AS nb_sous_lots_distincts,
    COUNT(DISTINCT lot_id) AS nb_lots
FROM vw_dim_sous_lot_active;

-- 7. Qualite des champs critiques.
SELECT
    COUNT(*) FILTER (WHERE NULLIF(TRIM(lot), '') IS NULL) AS lots_vides,
    COUNT(*) FILTER (WHERE NULLIF(TRIM(code_article), '') IS NULL) AS articles_vides,
    COUNT(*) FILTER (WHERE NULLIF(TRIM(designation), '') IS NULL) AS designations_vides,
    COUNT(*) FILTER (WHERE NULLIF(TRIM(unite), '') IS NULL) AS unites_vides
FROM vw_dim_article_bpu_active;

-- 8. Contrat colonnes Power BI.
SELECT
    table_name,
    ordinal_position,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
      'vw_dim_lot_active',
      'vw_dim_sous_lot_active',
      'vw_dim_article_bpu_active'
  )
ORDER BY table_name, ordinal_position;

-- 9. Non-regression historique: fact_metre reste present.
SELECT
    COUNT(*) AS fact_metre_rows,
    COUNT(DISTINCT lot) AS fact_metre_lots
FROM fact_metre;
