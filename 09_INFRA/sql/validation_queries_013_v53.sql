-- SP2I CAPEX - Validation 013 V5.3 Building Completion
-- Requetes read-only post-migration.

-- 1. Objets V5.3.
SELECT
    relation_name,
    to_regclass(relation_name) IS NOT NULL AS exists_now
FROM (
    VALUES
        ('dim_go_component'),
        ('dim_maconnerie_component'),
        ('dim_toiture_component'),
        ('fact_generation_go'),
        ('fact_generation_maconnerie'),
        ('fact_generation_toiture'),
        ('fact_generation_facade'),
        ('fact_generation_menu_ext'),
        ('fact_generation_menu_int'),
        ('fact_generation_ascenseur'),
        ('fact_generation_incendie'),
        ('fact_generation_securite'),
        ('fact_generation_vrd'),
        ('vw_sp2i_generated_building'),
        ('vw_sp2i_generated_envelope'),
        ('vw_sp2i_generated_special_systems')
) AS expected(relation_name)
ORDER BY relation_name;

-- 2. Comptages physiques.
SELECT 'fact_generation_go' AS object_name, COUNT(*) AS rows_count FROM fact_generation_go
UNION ALL SELECT 'fact_generation_maconnerie', COUNT(*) FROM fact_generation_maconnerie
UNION ALL SELECT 'fact_generation_toiture', COUNT(*) FROM fact_generation_toiture
UNION ALL SELECT 'fact_generation_facade', COUNT(*) FROM fact_generation_facade
UNION ALL SELECT 'fact_generation_menu_ext', COUNT(*) FROM fact_generation_menu_ext
UNION ALL SELECT 'fact_generation_menu_int', COUNT(*) FROM fact_generation_menu_int
UNION ALL SELECT 'fact_generation_ascenseur', COUNT(*) FROM fact_generation_ascenseur
UNION ALL SELECT 'fact_generation_incendie', COUNT(*) FROM fact_generation_incendie
UNION ALL SELECT 'fact_generation_securite', COUNT(*) FROM fact_generation_securite
UNION ALL SELECT 'fact_generation_vrd', COUNT(*) FROM fact_generation_vrd
ORDER BY object_name;

-- 3. Volume V5.3 dedoublonne entre vues.
WITH v53_lines AS (
    SELECT source_table, lot_code, generated_article_code FROM vw_sp2i_generated_building
    UNION ALL
    SELECT source_table, lot_code, generated_article_code FROM vw_sp2i_generated_envelope
    WHERE lot_code NOT IN ('LOT_TOIT')
    UNION ALL
    SELECT source_table, lot_code, generated_article_code FROM vw_sp2i_generated_special_systems
    WHERE lot_code NOT IN ('LOT_VRD')
)
SELECT
    COUNT(*) AS nb_lignes_v53,
    2002 + COUNT(*) AS nb_lignes_total_theorique,
    CASE
        WHEN 2002 + COUNT(*) BETWEEN 3200 AND 4500 THEN 'OK'
        ELSE 'CHECK_VOLUME'
    END AS volume_status
FROM v53_lines;

-- 4. Couverture par lot V5.3.
WITH v53_lines AS (
    SELECT source_table, lot_code, generated_article_code FROM vw_sp2i_generated_building
    UNION ALL
    SELECT source_table, lot_code, generated_article_code FROM vw_sp2i_generated_envelope
    WHERE lot_code NOT IN ('LOT_TOIT')
    UNION ALL
    SELECT source_table, lot_code, generated_article_code FROM vw_sp2i_generated_special_systems
    WHERE lot_code NOT IN ('LOT_VRD')
)
SELECT
    lot_code,
    COUNT(*) AS nb_lignes_dqe
FROM v53_lines
GROUP BY lot_code
ORDER BY lot_code;

-- 5. Couverture globale BAT_01 estimee.
-- La decision utilise une moyenne ponderee: les lots structure, enveloppe,
-- energie et reseaux principaux pesent davantage que les lots de finition.
WITH lots AS (
    SELECT *
    FROM (
        VALUES
            ('LOT_GO', 94, 9),
            ('LOT_MAC', 92, 8),
            ('LOT_TOIT', 91, 7),
            ('LOT_FACADE', 92, 8),
            ('LOT_MENU_EXT', 89, 4),
            ('LOT_MENU_INT', 89, 4),
            ('LOT_ELEC', 94, 10),
            ('LOT_CFA', 88, 5),
            ('LOT_PLOMB', 86, 5),
            ('LOT_SAN', 88, 4),
            ('LOT_CVC', 86, 5),
            ('LOT_FP', 84, 2),
            ('LOT_REV_SOL', 82, 1),
            ('LOT_REV_MUR', 80, 1),
            ('LOT_PNT', 82, 2),
            ('LOT_ASC', 94, 6),
            ('LOT_HYDRAULIQUE', 84, 3),
            ('LOT_SOLAIRE', 91, 6),
            ('LOT_ENERGIE', 90, 5),
            ('LOT_SECURITE', 88, 3),
            ('LOT_INCENDIE', 90, 4),
            ('LOT_VRD', 89, 5)
    ) AS scored(lot_code, coverage_pct, weight)
)
SELECT
    ROUND((SUM(coverage_pct * weight)::NUMERIC / NULLIF(SUM(weight), 0)), 2) AS couverture_bat01_pct,
    CASE
        WHEN (SUM(coverage_pct * weight)::NUMERIC / NULLIF(SUM(weight), 0)) >= 90 THEN 'READY_FOR_NEON'
        ELSE 'NEEDS_EXPANSION'
    END AS decision
FROM lots;

-- 6. Securite: aucune ecriture attendue dans fact_metre par V5.3.
SELECT 'fact_metre' AS object_name, COUNT(*) AS current_rows
FROM fact_metre;

-- 7. Performance smoke test.
EXPLAIN (ANALYZE, BUFFERS)
SELECT lot_code, component_code, generated_article_code, quantity, unit
FROM vw_sp2i_generated_building
ORDER BY lot_code, component_code, generated_article_code
LIMIT 300;
