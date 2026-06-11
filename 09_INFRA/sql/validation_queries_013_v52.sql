-- SP2I CAPEX - Validation 013 V5.2 Generative Engine
-- Requetes read-only post-migration.

-- 1. Inventaire objets V5.2.
SELECT
    relation_name,
    to_regclass(relation_name) IS NOT NULL AS exists_now
FROM (
    VALUES
        ('dim_network_type'),
        ('dim_equipment'),
        ('dim_route_rule'),
        ('dim_generation_formula'),
        ('fact_generation_bim'),
        ('fact_generation_network'),
        ('fact_generation_dqe'),
        ('fact_water'),
        ('fact_solar'),
        ('fact_energy'),
        ('fact_forage'),
        ('dim_facade_system'),
        ('vw_sp2i_generated_dqe'),
        ('vw_sp2i_generated_networks'),
        ('vw_sp2i_generated_capex'),
        ('vw_energy_dashboard'),
        ('vw_water_dashboard'),
        ('vw_autonomy_dashboard'),
        ('vw_facade_dashboard')
) AS expected(relation_name)
ORDER BY relation_name;

-- 2. Comptages.
SELECT 'dim_network_type' AS object_name, COUNT(*) AS rows_count FROM dim_network_type
UNION ALL SELECT 'dim_equipment', COUNT(*) FROM dim_equipment
UNION ALL SELECT 'dim_route_rule', COUNT(*) FROM dim_route_rule
UNION ALL SELECT 'dim_generation_formula', COUNT(*) FROM dim_generation_formula
UNION ALL SELECT 'fact_generation_bim', COUNT(*) FROM fact_generation_bim
UNION ALL SELECT 'fact_generation_network', COUNT(*) FROM fact_generation_network
UNION ALL SELECT 'fact_generation_dqe', COUNT(*) FROM fact_generation_dqe
UNION ALL SELECT 'fact_water', COUNT(*) FROM fact_water
UNION ALL SELECT 'fact_solar', COUNT(*) FROM fact_solar
UNION ALL SELECT 'fact_energy', COUNT(*) FROM fact_energy
UNION ALL SELECT 'fact_forage', COUNT(*) FROM fact_forage
UNION ALL SELECT 'dim_facade_system', COUNT(*) FROM dim_facade_system
ORDER BY object_name;

-- 3. Generation BAT_01.
SELECT
    generation_batch,
    COUNT(*) AS generated_rows,
    COUNT(DISTINCT appartement_id) AS appartements,
    COUNT(DISTINCT type_piece_id) AS type_pieces,
    COUNT(DISTINCT article_code) AS articles
FROM fact_generation_bim
GROUP BY generation_batch
ORDER BY generation_batch;

-- 4. Reseaux generes par type.
SELECT
    nt.network_code,
    nt.network_name,
    COUNT(*) AS network_rows,
    ROUND(COALESCE(SUM(fn.distance_ml), 0)::NUMERIC, 2) AS distance_ml
FROM fact_generation_network fn
JOIN dim_network_type nt
  ON nt.network_type_id = fn.network_type_id
GROUP BY nt.network_code, nt.network_name
ORDER BY nt.network_code;

-- 5. DQE genere.
SELECT
    generation_batch,
    COUNT(*) AS dqe_rows,
    ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 2) AS quantity_total,
    ROUND(COALESCE(SUM(capex_local), 0)::NUMERIC, 2) AS capex_local,
    ROUND(COALESCE(SUM(capex_import), 0)::NUMERIC, 2) AS capex_import
FROM fact_generation_dqe
GROUP BY generation_batch
ORDER BY generation_batch;

-- 6. Power BI V5.2.
SELECT * FROM vw_sp2i_generated_capex;
SELECT * FROM vw_energy_dashboard;
SELECT * FROM vw_water_dashboard;
SELECT * FROM vw_autonomy_dashboard;
SELECT * FROM vw_facade_dashboard;

-- 7. Compatibilite objets historiques.
SELECT *
FROM vw_sp2i_v52_migration_safety
ORDER BY object_type, object_name;

-- 8. Performance smoke test.
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    appartement,
    piece,
    article_code,
    quantity,
    capex_local
FROM vw_sp2i_generated_dqe
WHERE generation_batch = 'BAT_01_V52'
ORDER BY appartement, piece, article_code
LIMIT 100;
