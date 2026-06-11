-- SP2I CAPEX - Validation 013 V5.2.1 Quantity Expansion
-- Requetes read-only post-migration.

-- 1. Objets V5.2.1.
SELECT
    relation_name,
    to_regclass(relation_name) IS NOT NULL AS exists_now
FROM (
    VALUES
        ('dim_quantity_expansion_rule'),
        ('fact_generation_expansion'),
        ('vw_sp2i_generated_quantities'),
        ('vw_sp2i_generated_network_quantities')
) AS expected(relation_name)
ORDER BY relation_name;

-- 2. Comptages principaux.
SELECT 'fact_generation_bim' AS object_name, COUNT(*) AS rows_count FROM fact_generation_bim
UNION ALL SELECT 'fact_generation_network', COUNT(*) FROM fact_generation_network
UNION ALL SELECT 'fact_generation_dqe', COUNT(*) FROM fact_generation_dqe
UNION ALL SELECT 'dim_quantity_expansion_rule', COUNT(*) FROM dim_quantity_expansion_rule
UNION ALL SELECT 'fact_generation_expansion', COUNT(*) FROM fact_generation_expansion
UNION ALL SELECT 'vw_sp2i_generated_quantities', COUNT(*) FROM vw_sp2i_generated_quantities
ORDER BY object_name;

-- 3. Objectif volume DQE detaille.
SELECT
    generation_batch,
    COUNT(*) AS nb_generation_dqe_detail,
    CASE
        WHEN COUNT(*) BETWEEN 1500 AND 3000 THEN 'OK'
        ELSE 'CHECK_VOLUME'
    END AS volume_status
FROM vw_sp2i_generated_quantities
GROUP BY generation_batch
ORDER BY generation_batch;

-- 4. Couverture par lot.
SELECT
    lot_code,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 2) AS quantite_totale
FROM vw_sp2i_generated_quantities
GROUP BY lot_code
ORDER BY nb_lignes DESC, lot_code;

-- 5. Reseaux estimes.
SELECT
    lot_code,
    SUM(nb_lignes) AS nb_lignes_quantite,
    SUM(network_rows_estimated) AS network_rows_estimated,
    ROUND(COALESCE(SUM(quantite_totale), 0)::NUMERIC, 2) AS quantite_totale
FROM vw_sp2i_generated_network_quantities
GROUP BY lot_code
ORDER BY network_rows_estimated DESC, lot_code;

-- 6. Detection doublons d expansion.
SELECT
    generation_id,
    generated_article_code,
    COUNT(*) AS duplicate_count
FROM fact_generation_expansion
GROUP BY generation_id, generated_article_code
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- 7. Securite: aucune ecriture attendue dans fact_metre par V5.2.1.
SELECT
    'fact_metre' AS object_name,
    COUNT(*) AS current_rows
FROM fact_metre;

-- 8. Performance smoke test.
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    generation_batch,
    lot_code,
    generated_article_code,
    quantity,
    unit
FROM vw_sp2i_generated_quantities
WHERE generation_batch = 'BAT_01_V52'
ORDER BY lot_code, generated_article_code
LIMIT 200;
