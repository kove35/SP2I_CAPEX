-- SP2I CAPEX - Validation 013 V5.2.2 Energy Resilience
-- Requetes read-only post-migration.

-- 1. Objets V5.2.2.
SELECT
    relation_name,
    to_regclass(relation_name) IS NOT NULL AS exists_now
FROM (
    VALUES
        ('dim_energy_system'),
        ('dim_generator_system'),
        ('dim_energy_equipment'),
        ('fact_generator'),
        ('fact_generator_consumption'),
        ('fact_energy_resilience'),
        ('vw_energy_resilience_dashboard'),
        ('vw_generator_dashboard'),
        ('vw_energy_sources_dashboard')
) AS expected(relation_name)
ORDER BY relation_name;

-- 2. Comptages principaux.
SELECT 'dim_energy_system' AS object_name, COUNT(*) AS rows_count FROM dim_energy_system
UNION ALL SELECT 'dim_generator_system', COUNT(*) FROM dim_generator_system
UNION ALL SELECT 'dim_energy_equipment', COUNT(*) FROM dim_energy_equipment
UNION ALL SELECT 'fact_generator', COUNT(*) FROM fact_generator
UNION ALL SELECT 'fact_generator_consumption', COUNT(*) FROM fact_generator_consumption
UNION ALL SELECT 'fact_energy_resilience', COUNT(*) FROM fact_energy_resilience
UNION ALL SELECT 'vw_energy_resilience_dashboard', COUNT(*) FROM vw_energy_resilience_dashboard
UNION ALL SELECT 'vw_generator_dashboard', COUNT(*) FROM vw_generator_dashboard
UNION ALL SELECT 'vw_energy_sources_dashboard', COUNT(*) FROM vw_energy_sources_dashboard
ORDER BY object_name;

-- 3. Volume DQE energie attendu: +120 a +250 lignes.
SELECT
    COUNT(*) AS nb_dqe_energy_lines,
    CASE
        WHEN COUNT(*) BETWEEN 120 AND 250 THEN 'OK'
        ELSE 'CHECK_VOLUME'
    END AS volume_status
FROM vw_energy_sources_dashboard;

-- 4. Couverture par systeme energie.
SELECT
    system_code,
    COUNT(*) AS nb_lignes_dqe,
    COUNT(DISTINCT equipment_code) AS nb_equipements,
    ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 2) AS quantite_reference
FROM vw_energy_sources_dashboard
GROUP BY system_code
ORDER BY nb_lignes_dqe DESC, system_code;

-- 5. Couverture par lot.
SELECT
    lot_code,
    COUNT(*) AS nb_lignes_dqe,
    COUNT(DISTINCT equipment_code) AS nb_equipements,
    ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 2) AS quantite_reference
FROM vw_energy_sources_dashboard
GROUP BY lot_code
ORDER BY nb_lignes_dqe DESC, lot_code;

-- 6. Verification configuration BAT_01.
SELECT
    project_code,
    batiment,
    surface_m2,
    apartment_count,
    solar_kwc,
    panel_count,
    battery_capacity_kwh,
    generator_code,
    fuel_tank_liters,
    autonomie_batteries_h,
    autonomie_carburant_h,
    autonomie_totale_h,
    taux_couverture_solaire
FROM vw_energy_resilience_dashboard
WHERE project_code = 'PROJET_MPEMBA'
  AND batiment = 'BAT_01';

-- 7. Groupe recommande BAT_01.
SELECT
    generator_code,
    generator_name,
    generator_power_kva,
    fuel_type,
    autonomy_hours,
    is_recommended_bat01
FROM dim_generator_system
WHERE is_recommended_bat01;

-- 8. Securite: aucune ecriture attendue dans fact_metre par V5.2.2.
SELECT
    'fact_metre' AS object_name,
    COUNT(*) AS current_rows
FROM fact_metre;

-- 9. Performance smoke test.
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    system_code,
    lot_code,
    equipment_code,
    generated_article_code,
    quantity,
    unit
FROM vw_energy_sources_dashboard
ORDER BY system_code, equipment_code, generated_article_code
LIMIT 250;
