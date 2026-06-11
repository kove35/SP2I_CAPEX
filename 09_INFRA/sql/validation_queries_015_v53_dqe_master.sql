-- SP2I CAPEX - Validation 015 V5.3 DQE Master
-- Requetes read-only post-migration.

-- 1. Existence de la vue master.
SELECT
    'vw_sp2i_generated_dqe_master' AS relation_name,
    to_regclass('vw_sp2i_generated_dqe_master') IS NOT NULL AS exists_now;

-- 2. Volumes globaux attendus: environ 4734 lignes et 18 lots.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT lot_code) AS nb_lots,
    CASE
        WHEN COUNT(DISTINCT lot_code) = 18 THEN 'OK'
        ELSE 'CHECK_LOTS'
    END AS lot_status,
    CASE
        WHEN COUNT(*) BETWEEN 4500 AND 5000 THEN 'OK'
        ELSE 'CHECK_VOLUME'
    END AS volume_status
FROM vw_sp2i_generated_dqe_master;

-- 3. Couverture exacte des 18 lots officiels.
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
LEFT JOIN actual_lots a
  ON a.lot_code = e.lot_code
ORDER BY e.lot_code;

-- 4. Lots inattendus.
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
LEFT JOIN expected_lots e
  ON e.lot_code = m.lot_code
WHERE e.lot_code IS NULL
GROUP BY m.lot_code
ORDER BY m.lot_code;

-- 5. Repartition par vue source.
SELECT
    source_view,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT lot_code) AS nb_lots
FROM vw_sp2i_generated_dqe_master
GROUP BY source_view
ORDER BY source_view;

-- 6. Controle des identifiants article.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(*) FILTER (
        WHERE NULLIF(TRIM(generated_article_code), '') IS NULL
    ) AS generated_article_code_vides,
    COUNT(*) FILTER (
        WHERE NULLIF(TRIM(generated_designation), '') IS NULL
    ) AS generated_designation_vides
FROM vw_sp2i_generated_dqe_master;

-- 7. Securite: fact_metre reste inchange par cette migration additive.
SELECT
    'fact_metre' AS object_name,
    COUNT(*) AS current_rows
FROM fact_metre;
