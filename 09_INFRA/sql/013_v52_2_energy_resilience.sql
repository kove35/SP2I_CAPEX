-- SP2I CAPEX - V5.2.2 Energy Resilience
-- Migration: 013_v52_2_energy_resilience.sql
--
-- Objectif:
-- - ajouter le systeme energetique complet BAT_01 ;
-- - preparer solaire, batteries, groupe, ATS, EMS, terre, foudre et telegestion ;
-- - exposer des vues Power BI additives ;
-- - ne modifier aucun objet historique SP2I.
--
-- Compatibilite:
-- - PostgreSQL 18
-- - Neon PostgreSQL
-- - Power BI DirectQuery
--
-- Garanties:
-- - aucune ecriture dans fact_metre, fact_simulation, fact_approvals ou procurement_decisions ;
-- - aucun endpoint backend/frontend modifie ;
-- - aucun rapport Power BI existant modifie ;
-- - migration additive et idempotente.

BEGIN;

-- ============================================================================
-- 1. DIM_ENERGY_SYSTEM
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_energy_system (
    energy_system_id BIGSERIAL PRIMARY KEY,
    system_code VARCHAR(80) NOT NULL UNIQUE,
    system_name VARCHAR(255) NOT NULL,
    system_category VARCHAR(120) NOT NULL DEFAULT 'ENERGIE',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE dim_energy_system IS
    'V5.2.2 - Referentiel des systemes energie BAT_01.';

INSERT INTO dim_energy_system (system_code, system_name, system_category, is_active)
VALUES
    ('RESEAU_PUBLIC', 'Reseau public E2C', 'SOURCE', TRUE),
    ('SOLAIRE', 'Solaire photovoltaique', 'SOURCE', TRUE),
    ('BATTERIE', 'Stockage batteries', 'STOCKAGE', TRUE),
    ('GROUPE', 'Groupe electrogene', 'SECOURS', TRUE),
    ('ATS', 'Inverseur automatique de source', 'SECOURS', TRUE),
    ('EMS', 'Energy Management System', 'PILOTAGE', TRUE),
    ('FOUDRE', 'Protection foudre', 'PROTECTION', TRUE),
    ('TERRE', 'Mise a la terre', 'PROTECTION', TRUE),
    ('TELEGESTION', 'Telegestion energie', 'PILOTAGE', TRUE)
ON CONFLICT (system_code) DO NOTHING;

-- ============================================================================
-- 2. DIM_GENERATOR_SYSTEM
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_generator_system (
    generator_id BIGSERIAL PRIMARY KEY,
    generator_code VARCHAR(80) NOT NULL UNIQUE,
    generator_name VARCHAR(255) NOT NULL,
    generator_power_kva NUMERIC(12, 2) NOT NULL,
    fuel_type VARCHAR(80) NOT NULL,
    autonomy_hours NUMERIC(12, 2) NOT NULL DEFAULT 0,
    is_recommended_bat01 BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE dim_generator_system IS
    'V5.2.2 - Configurations groupe electrogene pour resilience energetique.';

INSERT INTO dim_generator_system (
    generator_code,
    generator_name,
    generator_power_kva,
    fuel_type,
    autonomy_hours,
    is_recommended_bat01,
    is_active
)
VALUES
    ('GEN_080KVA', 'Groupe electrogene 80 kVA', '80', 'DIESEL', 18, FALSE, TRUE),
    ('GEN_150KVA', 'Groupe electrogene 150 kVA', '150', 'DIESEL', 48, TRUE, TRUE),
    ('GEN_250KVA', 'Groupe electrogene 250 kVA', '250', 'DIESEL', 72, FALSE, TRUE)
ON CONFLICT (generator_code) DO NOTHING;

-- ============================================================================
-- 3. DIM_ENERGY_EQUIPMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_energy_equipment (
    energy_equipment_id BIGSERIAL PRIMARY KEY,
    equipment_code VARCHAR(120) NOT NULL UNIQUE,
    equipment_name VARCHAR(255) NOT NULL,
    energy_system_id BIGINT NOT NULL REFERENCES dim_energy_system(energy_system_id),
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_ELEC',
    unit VARCHAR(40) NOT NULL DEFAULT 'U',
    quantity_reference NUMERIC(14, 4) NOT NULL DEFAULT 1,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_dim_energy_equipment_line_count CHECK (dqe_line_count >= 1)
);

COMMENT ON TABLE dim_energy_equipment IS
    'V5.2.2 - Equipements energie et coefficients de lignes DQE BAT_01.';

INSERT INTO dim_energy_equipment (
    equipment_code,
    equipment_name,
    energy_system_id,
    lot_code,
    unit,
    quantity_reference,
    dqe_line_count
)
SELECT seed.equipment_code, seed.equipment_name, es.energy_system_id, seed.lot_code, seed.unit, seed.quantity_reference, seed.dqe_line_count
FROM (
    VALUES
        ('CELLULE_BT', 'Cellule basse tension arrivee E2C', 'RESEAU_PUBLIC', 'LOT_ELEC', 'U', 1::NUMERIC, 4),
        ('COMPTEUR_GENERAL', 'Compteur general communicant', 'RESEAU_PUBLIC', 'LOT_ELEC', 'U', 1::NUMERIC, 3),
        ('ANALYSEUR_RESEAU', 'Analyseur reseau triphase', 'RESEAU_PUBLIC', 'LOT_ELEC', 'U', 1::NUMERIC, 3),
        ('SECTIONNEUR', 'Sectionneur general', 'RESEAU_PUBLIC', 'LOT_ELEC', 'U', 1::NUMERIC, 3),
        ('DISJONCTEUR_GENERAL', 'Disjoncteur general 400A', 'RESEAU_PUBLIC', 'LOT_ELEC', 'U', 1::NUMERIC, 4),
        ('TGBT', 'Tableau general basse tension', 'RESEAU_PUBLIC', 'LOT_ELEC', 'U', 1::NUMERIC, 6),
        ('JEU_BARRES', 'Jeu de barres TGBT', 'RESEAU_PUBLIC', 'LOT_ELEC', 'ENS', 1::NUMERIC, 4),
        ('DISJONCTEUR_DEPART', 'Disjoncteurs depart TGBT', 'RESEAU_PUBLIC', 'LOT_ELEC', 'U', 14::NUMERIC, 5),
        ('PANNEAU_550W', 'Panneau photovoltaique 550 Wc', 'SOLAIRE', 'LOT_SOLAIRE', 'U', 110::NUMERIC, 6),
        ('STRUCTURE_PV', 'Structure toiture terrasse PV', 'SOLAIRE', 'LOT_SOLAIRE', 'ENS', 1::NUMERIC, 5),
        ('CONNECTEUR_MC4', 'Connecteurs MC4', 'SOLAIRE', 'LOT_SOLAIRE', 'U', 240::NUMERIC, 3),
        ('COFFRET_DC', 'Coffret courant continu PV', 'SOLAIRE', 'LOT_SOLAIRE', 'U', 4::NUMERIC, 4),
        ('PARAFOUDRE_DC', 'Parafoudre DC photovoltaique', 'SOLAIRE', 'LOT_SOLAIRE', 'U', 4::NUMERIC, 3),
        ('ONDULEUR_30KW', 'Onduleur solaire 30 kW', 'SOLAIRE', 'LOT_SOLAIRE', 'U', 2::NUMERIC, 5),
        ('BATTERIE_LIFEPO4', 'Batteries LiFePO4 200 kWh', 'BATTERIE', 'LOT_SOLAIRE', 'KWH', 200::NUMERIC, 5),
        ('BMS', 'Battery Management System', 'BATTERIE', 'LOT_SOLAIRE', 'U', 1::NUMERIC, 4),
        ('RACK_BATTERIE', 'Racks batteries', 'BATTERIE', 'LOT_SOLAIRE', 'U', 4::NUMERIC, 4),
        ('GEN_150KVA', 'Groupe electrogene 150 kVA', 'GROUPE', 'LOT_ELEC', 'U', 1::NUMERIC, 7),
        ('CUVE_3000L', 'Cuve gasoil 3000 litres', 'GROUPE', 'LOT_ELEC', 'U', 0::NUMERIC, 3),
        ('CUVE_5000L', 'Cuve gasoil 5000 litres', 'GROUPE', 'LOT_ELEC', 'U', 1::NUMERIC, 5),
        ('ATS_400A', 'ATS 400A', 'ATS', 'LOT_ELEC', 'U', 1::NUMERIC, 5),
        ('TABLEAU_SECOURS', 'Tableau secours', 'ATS', 'LOT_ELEC', 'U', 1::NUMERIC, 5),
        ('CONTROLEUR_ENERGIE', 'Controleur energie central', 'EMS', 'LOT_CFA', 'U', 1::NUMERIC, 4),
        ('PASSERELLE_MODBUS', 'Passerelle Modbus TCP', 'EMS', 'LOT_CFA', 'U', 2::NUMERIC, 3),
        ('SERVEUR_MONITORING', 'Serveur monitoring energie', 'EMS', 'LOT_CFA', 'U', 1::NUMERIC, 4),
        ('PIQUET_TERRE', 'Piquets de terre cuivre', 'TERRE', 'LOT_ELEC', 'U', 18::NUMERIC, 4),
        ('BARRETTE_COUPURE', 'Barrettes de coupure terre', 'TERRE', 'LOT_ELEC', 'U', 6::NUMERIC, 3),
        ('CUIVRE_NU', 'Cable cuivre nu terre', 'TERRE', 'LOT_ELEC', 'ML', 420::NUMERIC, 5),
        ('PARATONNERRE', 'Paratonnerre toiture terrasse', 'FOUDRE', 'LOT_ELEC', 'U', 1::NUMERIC, 5),
        ('DESCENTE_FOUDRE', 'Descente foudre cuivre', 'FOUDRE', 'LOT_ELEC', 'ML', 90::NUMERIC, 4),
        ('PARAFOUDRE_T1', 'Parafoudre type 1', 'FOUDRE', 'LOT_ELEC', 'U', 1::NUMERIC, 4),
        ('PARAFOUDRE_T2', 'Parafoudre type 2 divisionnaire', 'FOUDRE', 'LOT_ELEC', 'U', 8::NUMERIC, 4),
        ('COMPTEUR_COMMUNICANT', 'Compteurs communicants depart', 'TELEGESTION', 'LOT_CFA', 'U', 12::NUMERIC, 4),
        ('PASSERELLE_IOT', 'Passerelle IoT energie', 'TELEGESTION', 'LOT_CFA', 'U', 1::NUMERIC, 4),
        ('DATA_LOGGER', 'Data logger energie', 'TELEGESTION', 'LOT_CFA', 'U', 1::NUMERIC, 4)
) AS seed(equipment_code, equipment_name, system_code, lot_code, unit, quantity_reference, dqe_line_count)
JOIN dim_energy_system es
  ON es.system_code = seed.system_code
ON CONFLICT (equipment_code) DO NOTHING;

-- ============================================================================
-- 4. FACT_GENERATOR
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_generator (
    generator_fact_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(120) NOT NULL DEFAULT 'PROJET_MPEMBA',
    batiment VARCHAR(120) NOT NULL DEFAULT 'BAT_01',
    generator_code VARCHAR(80) NOT NULL REFERENCES dim_generator_system(generator_code),
    puissance_kva NUMERIC(12, 2) NOT NULL,
    temps_fonctionnement_h NUMERIC(12, 2) NOT NULL DEFAULT 0,
    consommation_l_h NUMERIC(12, 2) NOT NULL DEFAULT 0,
    consommation_jour_l NUMERIC(12, 2) NOT NULL DEFAULT 0,
    fuel_type VARCHAR(80) NOT NULL DEFAULT 'DIESEL',
    is_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generator_scope UNIQUE (project_code, batiment, generator_code)
);

INSERT INTO fact_generator (
    project_code,
    batiment,
    generator_code,
    puissance_kva,
    temps_fonctionnement_h,
    consommation_l_h,
    consommation_jour_l,
    fuel_type,
    is_recommended
)
VALUES
    ('PROJET_MPEMBA', 'BAT_01', 'GEN_150KVA', 150, 10, 28, 280, 'DIESEL', TRUE)
ON CONFLICT (project_code, batiment, generator_code) DO NOTHING;

-- ============================================================================
-- 5. FACT_GENERATOR_CONSUMPTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_generator_consumption (
    generator_consumption_id BIGSERIAL PRIMARY KEY,
    generator_fact_id BIGINT NOT NULL REFERENCES fact_generator(generator_fact_id),
    consumption_date DATE NOT NULL,
    heures NUMERIC(12, 2) NOT NULL DEFAULT 0,
    litres NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cout NUMERIC(16, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generator_consumption_day UNIQUE (generator_fact_id, consumption_date)
);

INSERT INTO fact_generator_consumption (
    generator_fact_id,
    consumption_date,
    heures,
    litres,
    cout
)
SELECT fg.generator_fact_id, seed.consumption_date, seed.heures, seed.litres, seed.cout
FROM (
    VALUES
        (DATE '2026-05-29', 10::NUMERIC, 280::NUMERIC, 252000::NUMERIC),
        (DATE '2026-05-30', 8::NUMERIC, 224::NUMERIC, 201600::NUMERIC),
        (DATE '2026-05-31', 6::NUMERIC, 168::NUMERIC, 151200::NUMERIC)
) AS seed(consumption_date, heures, litres, cout)
JOIN fact_generator fg
  ON fg.project_code = 'PROJET_MPEMBA'
 AND fg.batiment = 'BAT_01'
 AND fg.generator_code = 'GEN_150KVA'
ON CONFLICT (generator_fact_id, consumption_date) DO NOTHING;

-- ============================================================================
-- 6. FACT_ENERGY_RESILIENCE
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_energy_resilience (
    energy_resilience_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(120) NOT NULL DEFAULT 'PROJET_MPEMBA',
    batiment VARCHAR(120) NOT NULL DEFAULT 'BAT_01',
    surface_m2 NUMERIC(14, 2) NOT NULL DEFAULT 1263.90,
    apartment_count INTEGER NOT NULL DEFAULT 6,
    solar_kwc NUMERIC(12, 2) NOT NULL DEFAULT 60,
    panel_count INTEGER NOT NULL DEFAULT 110,
    battery_capacity_kwh NUMERIC(12, 2) NOT NULL DEFAULT 200,
    generator_code VARCHAR(80) NOT NULL DEFAULT 'GEN_150KVA',
    fuel_tank_liters NUMERIC(12, 2) NOT NULL DEFAULT 5000,
    estimated_daily_consumption_kwh NUMERIC(12, 2) NOT NULL DEFAULT 420,
    estimated_daily_solar_kwh NUMERIC(12, 2) NOT NULL DEFAULT 270,
    autonomie_batteries_h NUMERIC(12, 2) NOT NULL DEFAULT 0,
    autonomie_carburant_h NUMERIC(12, 2) NOT NULL DEFAULT 0,
    autonomie_totale_h NUMERIC(12, 2) NOT NULL DEFAULT 0,
    taux_couverture_solaire NUMERIC(12, 4) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_energy_resilience_scope UNIQUE (project_code, batiment)
);

INSERT INTO fact_energy_resilience (
    project_code,
    batiment,
    surface_m2,
    apartment_count,
    solar_kwc,
    panel_count,
    battery_capacity_kwh,
    generator_code,
    fuel_tank_liters,
    estimated_daily_consumption_kwh,
    estimated_daily_solar_kwh,
    autonomie_batteries_h,
    autonomie_carburant_h,
    autonomie_totale_h,
    taux_couverture_solaire
)
VALUES (
    'PROJET_MPEMBA',
    'BAT_01',
    1263.90,
    6,
    60,
    110,
    200,
    'GEN_150KVA',
    5000,
    420,
    270,
    ROUND((200 / NULLIF(420 / 24, 0))::NUMERIC, 2),
    ROUND((5000 / NULLIF(28, 0))::NUMERIC, 2),
    ROUND(((200 / NULLIF(420 / 24, 0)) + (5000 / NULLIF(28, 0)))::NUMERIC, 2),
    ROUND((270 / NULLIF(420, 0))::NUMERIC, 4)
)
ON CONFLICT (project_code, batiment) DO NOTHING;

-- ============================================================================
-- 7. VUES POWER BI ADDITIVES
-- ============================================================================

CREATE OR REPLACE VIEW vw_energy_resilience_dashboard AS
SELECT
    er.project_code,
    er.batiment,
    er.surface_m2,
    er.apartment_count,
    er.solar_kwc,
    er.panel_count,
    er.battery_capacity_kwh,
    er.generator_code,
    gs.generator_name,
    gs.generator_power_kva,
    er.fuel_tank_liters,
    er.estimated_daily_consumption_kwh,
    er.estimated_daily_solar_kwh,
    er.autonomie_batteries_h,
    er.autonomie_carburant_h,
    er.autonomie_totale_h,
    er.taux_couverture_solaire,
    ROUND((er.solar_kwc / NULLIF(er.surface_m2, 0))::NUMERIC, 4) AS kwc_m2,
    er.created_at
FROM fact_energy_resilience er
LEFT JOIN dim_generator_system gs
  ON gs.generator_code = er.generator_code;

CREATE OR REPLACE VIEW vw_generator_dashboard AS
SELECT
    fg.project_code,
    fg.batiment,
    fg.generator_code,
    gs.generator_name,
    fg.puissance_kva,
    fg.temps_fonctionnement_h,
    fg.consommation_l_h,
    fg.consommation_jour_l,
    fg.fuel_type,
    fg.is_recommended,
    ROUND(COALESCE(SUM(gc.heures), 0)::NUMERIC, 2) AS heures_historique,
    ROUND(COALESCE(SUM(gc.litres), 0)::NUMERIC, 2) AS litres_historique,
    ROUND(COALESCE(SUM(gc.cout), 0)::NUMERIC, 2) AS cout_historique
FROM fact_generator fg
LEFT JOIN dim_generator_system gs
  ON gs.generator_code = fg.generator_code
LEFT JOIN fact_generator_consumption gc
  ON gc.generator_fact_id = fg.generator_fact_id
GROUP BY
    fg.project_code,
    fg.batiment,
    fg.generator_code,
    gs.generator_name,
    fg.puissance_kva,
    fg.temps_fonctionnement_h,
    fg.consommation_l_h,
    fg.consommation_jour_l,
    fg.fuel_type,
    fg.is_recommended;

CREATE OR REPLACE VIEW vw_energy_sources_dashboard AS
WITH expanded_dqe AS (
    SELECT
        'BAT_01_V52_2'::VARCHAR(120) AS generation_batch,
        ee.equipment_code,
        ee.equipment_name,
        es.system_code,
        es.system_name,
        ee.lot_code,
        ee.unit,
        ee.quantity_reference,
        gs.component_index,
        ee.equipment_code || '_DQE_' || LPAD(gs.component_index::TEXT, 3, '0') AS generated_article_code,
        ee.equipment_name || ' - composant DQE ' || gs.component_index::TEXT AS generated_designation,
        CASE
            WHEN ee.dqe_line_count <= 0 THEN ee.quantity_reference
            ELSE ROUND((ee.quantity_reference / ee.dqe_line_count)::NUMERIC, 4)
        END AS quantity
    FROM dim_energy_equipment ee
    JOIN dim_energy_system es
      ON es.energy_system_id = ee.energy_system_id
    CROSS JOIN LATERAL generate_series(1, ee.dqe_line_count) AS gs(component_index)
    WHERE ee.is_active
      AND es.is_active
)
SELECT
    generation_batch,
    system_code,
    system_name,
    lot_code,
    equipment_code,
    equipment_name,
    generated_article_code,
    generated_designation,
    quantity,
    unit,
    component_index,
    COUNT(*) OVER () AS total_generated_dqe_lines,
    SUM(quantity) OVER (PARTITION BY system_code) AS system_quantity_total
FROM expanded_dqe;

-- ============================================================================
-- 8. INDEX
-- ============================================================================

CREATE INDEX IF NOT EXISTS ix_dim_energy_system_code
    ON dim_energy_system (system_code);

CREATE INDEX IF NOT EXISTS ix_dim_generator_system_code
    ON dim_generator_system (generator_code);

CREATE INDEX IF NOT EXISTS ix_dim_generator_system_recommended
    ON dim_generator_system (is_recommended_bat01)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_dim_energy_equipment_system
    ON dim_energy_equipment (energy_system_id, equipment_code)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_dim_energy_equipment_lot
    ON dim_energy_equipment (lot_code);

CREATE INDEX IF NOT EXISTS ix_fact_generator_scope
    ON fact_generator (project_code, batiment, generator_code);

CREATE INDEX IF NOT EXISTS ix_fact_generator_consumption_fact_date
    ON fact_generator_consumption (generator_fact_id, consumption_date);

CREATE INDEX IF NOT EXISTS ix_fact_energy_resilience_scope
    ON fact_energy_resilience (project_code, batiment);

COMMIT;

-- ============================================================================
-- 9. VALIDATION POST-MIGRATION
-- ============================================================================
-- Ces requetes sont read-only et peuvent etre executees apres la migration.

SELECT relation_name, rows_count
FROM (
    VALUES
        ('dim_energy_system', (SELECT COUNT(*) FROM dim_energy_system)),
        ('dim_generator_system', (SELECT COUNT(*) FROM dim_generator_system)),
        ('dim_energy_equipment', (SELECT COUNT(*) FROM dim_energy_equipment)),
        ('fact_generator', (SELECT COUNT(*) FROM fact_generator)),
        ('fact_generator_consumption', (SELECT COUNT(*) FROM fact_generator_consumption)),
        ('fact_energy_resilience', (SELECT COUNT(*) FROM fact_energy_resilience)),
        ('vw_energy_resilience_dashboard', (SELECT COUNT(*) FROM vw_energy_resilience_dashboard)),
        ('vw_generator_dashboard', (SELECT COUNT(*) FROM vw_generator_dashboard)),
        ('vw_energy_sources_dashboard', (SELECT COUNT(*) FROM vw_energy_sources_dashboard))
) AS counts(relation_name, rows_count)
ORDER BY relation_name;

SELECT
    system_code,
    COUNT(*) AS nb_lignes_dqe,
    ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 2) AS quantite_reference
FROM vw_energy_sources_dashboard
GROUP BY system_code
ORDER BY nb_lignes_dqe DESC, system_code;

SELECT
    COUNT(*) AS nb_lignes_dqe_energie,
    CASE
        WHEN COUNT(*) BETWEEN 120 AND 250 THEN 'OK'
        ELSE 'CHECK_VOLUME'
    END AS volume_status
FROM vw_energy_sources_dashboard;
