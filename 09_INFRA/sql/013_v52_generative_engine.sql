-- SP2I CAPEX - V5.2 Generative Engine
-- Migration: 013_v52_generative_engine.sql
--
-- Objectif:
-- PLAN -> BIM -> Reseaux -> DQE -> CAPEX -> Procurement -> Analytics -> Power BI
--
-- Contraintes respectees:
-- - aucune suppression ;
-- - aucun renommage ;
-- - aucune modification destructive ;
-- - aucune vue Power BI existante modifiee ;
-- - aucun endpoint modifie ;
-- - couche strictement additive.

BEGIN;

-- ============================================================================
-- PHASE 1 - AUDIT AUTOMATIQUE ADDITIF
-- ============================================================================

CREATE TABLE IF NOT EXISTS sp2i_v52_migration_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    audit_code VARCHAR(120) NOT NULL,
    audit_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW vw_sp2i_v52_compatibility_report AS
SELECT
    'TABLE' AS object_type,
    t.table_name AS object_name,
    NULL::TEXT AS detail,
    now() AS checked_at
FROM information_schema.tables t
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
UNION ALL
SELECT
    'VIEW' AS object_type,
    v.table_name AS object_name,
    NULL::TEXT AS detail,
    now() AS checked_at
FROM information_schema.views v
WHERE v.table_schema = 'public'
UNION ALL
SELECT
    'INDEX' AS object_type,
    i.indexname AS object_name,
    i.tablename AS detail,
    now() AS checked_at
FROM pg_indexes i
WHERE i.schemaname = 'public';

CREATE OR REPLACE VIEW vw_sp2i_v52_migration_safety AS
SELECT
    expected.object_name,
    expected.object_type,
    to_regclass(expected.object_name) IS NOT NULL AS exists_now,
    CASE
        WHEN to_regclass(expected.object_name) IS NOT NULL THEN 'OK'
        ELSE 'MISSING'
    END AS status
FROM (
    VALUES
        ('fact_metre', 'LEGACY_TABLE'),
        ('fact_simulation', 'LEGACY_TABLE'),
        ('fact_shipment', 'LEGACY_TABLE'),
        ('fact_logistics_cost', 'LEGACY_TABLE'),
        ('fact_approvals', 'LEGACY_TABLE'),
        ('procurement_decisions', 'LEGACY_TABLE'),
        ('dim_batiment', 'LEGACY_DIMENSION'),
        ('dim_niveau', 'LEGACY_DIMENSION'),
        ('dim_appartement', 'LEGACY_DIMENSION'),
        ('dim_piece', 'LEGACY_DIMENSION'),
        ('dim_lot', 'LEGACY_DIMENSION'),
        ('dim_sous_lot', 'LEGACY_DIMENSION'),
        ('dim_famille', 'LEGACY_DIMENSION'),
        ('dim_article_bpu', 'LEGACY_DIMENSION'),
        ('vw_capex_summary', 'LEGACY_VIEW'),
        ('vw_bim_dashboard', 'LEGACY_VIEW'),
        ('vw_dim_lot_active', 'LEGACY_VIEW'),
        ('vw_dim_sous_lot_active', 'LEGACY_VIEW'),
        ('vw_dim_article_bpu_active', 'LEGACY_VIEW')
) AS expected(object_name, object_type);

INSERT INTO sp2i_v52_migration_audit (audit_code, audit_payload)
SELECT
    'PRE_MIGRATION_COMPATIBILITY',
    jsonb_build_object(
        'legacy_objects_ok',
        bool_and(status = 'OK'),
        'checked_objects',
        jsonb_agg(jsonb_build_object('object', object_name, 'status', status))
    )
FROM vw_sp2i_v52_migration_safety
ON CONFLICT DO NOTHING;

-- ============================================================================
-- PHASE 2 - NOUVELLES DIMENSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_network_type (
    network_type_id BIGSERIAL PRIMARY KEY,
    network_code VARCHAR(60) NOT NULL UNIQUE,
    network_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO dim_network_type (network_code, network_name, is_active)
VALUES
    ('ELEC', 'Electricite courant fort', TRUE),
    ('CFA', 'Courants faibles', TRUE),
    ('PLOMB', 'Plomberie', TRUE),
    ('SAN', 'Sanitaire', TRUE),
    ('CVC', 'Climatisation ventilation', TRUE),
    ('INCENDIE', 'Securite incendie', TRUE),
    ('SECURITE', 'Surete et controle acces', TRUE),
    ('SOLAIRE', 'Solaire photovoltaique', TRUE),
    ('FORAGE', 'Forage et eau autonome', TRUE),
    ('VRD', 'Voiries et reseaux divers', TRUE)
ON CONFLICT (network_code) DO NOTHING;

CREATE TABLE IF NOT EXISTS dim_equipment (
    equipment_id BIGSERIAL PRIMARY KEY,
    equipment_code VARCHAR(120) NOT NULL UNIQUE,
    equipment_name VARCHAR(255) NOT NULL,
    network_type_id BIGINT NOT NULL REFERENCES dim_network_type(network_type_id),
    article_code VARCHAR(180) NOT NULL,
    unit VARCHAR(40) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO dim_equipment (
    equipment_code,
    equipment_name,
    network_type_id,
    article_code,
    unit,
    is_active
)
SELECT seed.equipment_code, seed.equipment_name, nt.network_type_id, seed.article_code, seed.unit, TRUE
FROM (
    VALUES
        ('PRISE_16A', 'Prise 16A 2P+T', 'ELEC', 'ELEC_PRISE_16A', 'U'),
        ('PRISE_PLAN_TRAVAIL', 'Prise plan de travail', 'ELEC', 'ELEC_PRISE_PLAN_TRAVAIL', 'U'),
        ('PRISE_FRIGO', 'Prise frigo', 'ELEC', 'ELEC_PRISE_FRIGO', 'U'),
        ('PRISE_MICRO_ONDES', 'Prise micro-ondes', 'ELEC', 'ELEC_PRISE_MICRO_ONDES', 'U'),
        ('PRISE_HOTTE', 'Prise hotte', 'ELEC', 'ELEC_PRISE_HOTTE', 'U'),
        ('SPOT_LED', 'Spot LED encastre', 'ELEC', 'ELEC_SPOT_LED', 'U'),
        ('TABLEAU_DIVISIONNAIRE', 'Tableau divisionnaire', 'ELEC', 'ELEC_TABLEAU_DIV', 'U'),
        ('PROTECTION_10A', 'Protection 10A', 'ELEC', 'ELEC_PROTECTION_10A', 'U'),
        ('PROTECTION_16A', 'Protection 16A', 'ELEC', 'ELEC_PROTECTION_16A', 'U'),
        ('PRISE_RJ45', 'Prise RJ45', 'CFA', 'CFA_RJ45', 'U'),
        ('PRISE_TV', 'Prise TV', 'CFA', 'CFA_TV', 'U'),
        ('WIFI_AP', 'Point acces Wifi', 'CFA', 'CFA_WIFI_AP', 'U'),
        ('CAMERA_IP', 'Camera IP', 'SECURITE', 'SEC_CAMERA_IP', 'U'),
        ('WC', 'Cuvette WC', 'SAN', 'SAN_WC', 'U'),
        ('LAVABO', 'Lavabo', 'SAN', 'SAN_LAVABO', 'U'),
        ('DOUCHE', 'Douche', 'SAN', 'SAN_DOUCHE', 'U'),
        ('MIROIR', 'Miroir sanitaire', 'SAN', 'SAN_MIROIR', 'U'),
        ('EVIER', 'Evier cuisine', 'PLOMB', 'PLOMB_EVIER', 'U'),
        ('EF', 'Alimentation eau froide', 'PLOMB', 'PLOMB_EF', 'ML'),
        ('EC', 'Alimentation eau chaude', 'PLOMB', 'PLOMB_EC', 'ML'),
        ('EU', 'Evacuation eaux usees', 'PLOMB', 'PLOMB_EU', 'ML'),
        ('EV', 'Evacuation eaux vannes', 'PLOMB', 'PLOMB_EV', 'ML'),
        ('SPLIT_12000', 'Split 12000 BTU', 'CVC', 'CVC_SPLIT_12000', 'U'),
        ('SPLIT_18000', 'Split 18000 BTU', 'CVC', 'CVC_SPLIT_18000', 'U'),
        ('EXTRACTEUR', 'Extracteur air', 'CVC', 'CVC_EXTRACTEUR', 'U'),
        ('LIAISON_CUIVRE', 'Liaison cuivre climatiseur', 'CVC', 'CVC_LIAISON_CUIVRE', 'ML'),
        ('CONDENSATS', 'Evacuation condensats', 'CVC', 'CVC_CONDENSATS', 'ML'),
        ('DETECTEUR', 'Detecteur incendie', 'INCENDIE', 'INC_DETECTEUR', 'U'),
        ('BAES', 'Bloc autonome eclairage securite', 'INCENDIE', 'INC_BAES', 'U'),
        ('RIA', 'Robinet incendie arme', 'INCENDIE', 'INC_RIA', 'U'),
        ('EXTINCTEUR', 'Extincteur', 'INCENDIE', 'INC_EXTINCTEUR', 'U'),
        ('PANNEAU_550W', 'Panneau solaire 550W', 'SOLAIRE', 'SOL_PANNEAU_550W', 'U'),
        ('ONDULEUR', 'Onduleur solaire', 'SOLAIRE', 'SOL_ONDULEUR', 'U'),
        ('BATTERIE', 'Batterie solaire', 'SOLAIRE', 'SOL_BATTERIE', 'U'),
        ('POMPE_IMMERGEE', 'Pompe immergee', 'FORAGE', 'FOR_POMPE_IMMERGEE', 'U'),
        ('FORAGE_150M', 'Forage 150 m', 'FORAGE', 'FOR_FORAGE_150M', 'FORFAIT'),
        ('VRD_FOURREAU', 'Fourreau VRD', 'VRD', 'VRD_FOURREAU', 'ML')
) AS seed(equipment_code, equipment_name, network_code, article_code, unit)
JOIN dim_network_type nt
  ON nt.network_code = seed.network_code
ON CONFLICT (equipment_code) DO NOTHING;

CREATE TABLE IF NOT EXISTS dim_route_rule (
    rule_id BIGSERIAL PRIMARY KEY,
    network_type_id BIGINT NOT NULL REFERENCES dim_network_type(network_type_id),
    equipment_code VARCHAR(120) NOT NULL,
    routing_method VARCHAR(120) NOT NULL,
    default_distance NUMERIC(12, 2) NOT NULL DEFAULT 0,
    coefficient NUMERIC(12, 4) NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dim_route_rule UNIQUE (network_type_id, equipment_code, routing_method)
);

INSERT INTO dim_route_rule (
    network_type_id,
    equipment_code,
    routing_method,
    default_distance,
    coefficient,
    is_active
)
SELECT nt.network_type_id, seed.equipment_code, seed.routing_method, seed.default_distance, seed.coefficient, TRUE
FROM (
    VALUES
        ('ELEC', 'PRISE_16A', 'AVERAGE_DISTANCE', 14.00::NUMERIC, 1.15::NUMERIC),
        ('CFA', 'PRISE_RJ45', 'AVERAGE_DISTANCE', 18.00::NUMERIC, 1.15::NUMERIC),
        ('ELEC', 'SPOT_LED', 'AVERAGE_DISTANCE', 12.00::NUMERIC, 1.10::NUMERIC),
        ('CFA', 'PRISE_TV', 'AVERAGE_DISTANCE', 18.00::NUMERIC, 1.10::NUMERIC),
        ('CVC', 'SPLIT_12000', 'AVERAGE_DISTANCE', 10.00::NUMERIC, 1.20::NUMERIC),
        ('CVC', 'SPLIT_18000', 'AVERAGE_DISTANCE', 12.00::NUMERIC, 1.20::NUMERIC),
        ('PLOMB', 'EF', 'PIECE_WET_ZONE', 8.00::NUMERIC, 1.15::NUMERIC),
        ('PLOMB', 'EC', 'PIECE_WET_ZONE', 8.00::NUMERIC, 1.15::NUMERIC),
        ('PLOMB', 'EU', 'PIECE_WET_ZONE', 7.00::NUMERIC, 1.10::NUMERIC),
        ('PLOMB', 'EV', 'PIECE_WET_ZONE', 7.00::NUMERIC, 1.10::NUMERIC),
        ('INCENDIE', 'DETECTEUR', 'AVERAGE_DISTANCE', 10.00::NUMERIC, 1.10::NUMERIC),
        ('SECURITE', 'CAMERA_IP', 'AVERAGE_DISTANCE', 22.00::NUMERIC, 1.10::NUMERIC),
        ('SOLAIRE', 'PANNEAU_550W', 'ROOF_ARRAY', 4.00::NUMERIC, 1.05::NUMERIC),
        ('FORAGE', 'POMPE_IMMERGEE', 'TECHNICAL_SHAFT', 35.00::NUMERIC, 1.10::NUMERIC),
        ('VRD', 'VRD_FOURREAU', 'SITE_MAIN_ROUTE', 60.00::NUMERIC, 1.20::NUMERIC)
) AS seed(network_code, equipment_code, routing_method, default_distance, coefficient)
JOIN dim_network_type nt
  ON nt.network_code = seed.network_code
ON CONFLICT (network_type_id, equipment_code, routing_method) DO NOTHING;

CREATE TABLE IF NOT EXISTS dim_generation_formula (
    formula_id BIGSERIAL PRIMARY KEY,
    type_piece_id BIGINT NOT NULL REFERENCES dim_type_piece(id),
    equipment_code VARCHAR(120) NOT NULL,
    formula_type VARCHAR(80) NOT NULL,
    formula_expression VARCHAR(255) NOT NULL,
    quantity_min NUMERIC(12, 2) NOT NULL DEFAULT 0,
    quantity_max NUMERIC(12, 2) NOT NULL DEFAULT 999999,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dim_generation_formula UNIQUE (type_piece_id, equipment_code, formula_expression)
);

INSERT INTO dim_generation_formula (
    type_piece_id,
    equipment_code,
    formula_type,
    formula_expression,
    quantity_min,
    quantity_max,
    is_active
)
SELECT tp.id, seed.equipment_code, seed.formula_type, seed.formula_expression, seed.quantity_min, seed.quantity_max, TRUE
FROM (
    VALUES
        ('SEJOUR', 'SPOT_LED', 'SURFACE_RATIO', 'surface / 7', 10::NUMERIC, 10::NUMERIC),
        ('SEJOUR', 'PRISE_16A', 'SURFACE_RATIO', 'surface / 10', 8::NUMERIC, 8::NUMERIC),
        ('SEJOUR', 'PRISE_RJ45', 'FIXED', '2', 2::NUMERIC, 2::NUMERIC),
        ('SEJOUR', 'PRISE_TV', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SEJOUR', 'SPLIT_18000', 'FIXED', '2', 2::NUMERIC, 2::NUMERIC),
        ('CH1', 'SPOT_LED', 'FIXED', '4', 4::NUMERIC, 4::NUMERIC),
        ('CH1', 'PRISE_16A', 'FIXED', '6', 6::NUMERIC, 6::NUMERIC),
        ('CH1', 'PRISE_RJ45', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CH1', 'PRISE_TV', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CH1', 'SPLIT_12000', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CH2', 'SPOT_LED', 'FIXED', '4', 4::NUMERIC, 4::NUMERIC),
        ('CH2', 'PRISE_16A', 'FIXED', '6', 6::NUMERIC, 6::NUMERIC),
        ('CH2', 'PRISE_RJ45', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CH2', 'PRISE_TV', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CH2', 'SPLIT_12000', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CH3', 'SPOT_LED', 'FIXED', '4', 4::NUMERIC, 4::NUMERIC),
        ('CH3', 'PRISE_16A', 'FIXED', '6', 6::NUMERIC, 6::NUMERIC),
        ('CH3', 'PRISE_RJ45', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CH3', 'PRISE_TV', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CH3', 'SPLIT_12000', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CUISINE', 'PRISE_PLAN_TRAVAIL', 'FIXED', '4', 4::NUMERIC, 4::NUMERIC),
        ('CUISINE', 'PRISE_FRIGO', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CUISINE', 'PRISE_MICRO_ONDES', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CUISINE', 'PRISE_HOTTE', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CUISINE', 'EVIER', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('CUISINE', 'SPLIT_12000', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB1', 'WC', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB1', 'LAVABO', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB1', 'DOUCHE', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB1', 'MIROIR', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB1', 'EXTRACTEUR', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB2', 'WC', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB2', 'LAVABO', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB2', 'DOUCHE', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB2', 'MIROIR', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC),
        ('SDB2', 'EXTRACTEUR', 'FIXED', '1', 1::NUMERIC, 1::NUMERIC)
) AS seed(type_piece_code, equipment_code, formula_type, formula_expression, quantity_min, quantity_max)
JOIN dim_type_piece tp
  ON tp.code = seed.type_piece_code
ON CONFLICT (type_piece_id, equipment_code, formula_expression) DO NOTHING;

-- ============================================================================
-- PHASE 3 - TABLES DE GENERATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_generation_bim (
    generation_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT,
    batiment_id BIGINT,
    niveau_id BIGINT,
    appartement_id VARCHAR(150),
    piece_id BIGINT,
    type_piece_id BIGINT REFERENCES dim_type_piece(id),
    surface_m2 NUMERIC(12, 2) NOT NULL DEFAULT 0,
    article_code VARCHAR(180) NOT NULL,
    quantity_generated NUMERIC(14, 4) NOT NULL DEFAULT 0,
    formula_id BIGINT REFERENCES dim_generation_formula(formula_id),
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V52',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_bim UNIQUE (generation_batch, appartement_id, type_piece_id, article_code, formula_id)
);

CREATE TABLE IF NOT EXISTS fact_generation_network (
    network_generation_id BIGSERIAL PRIMARY KEY,
    generation_id BIGINT NOT NULL REFERENCES fact_generation_bim(generation_id),
    network_type_id BIGINT NOT NULL REFERENCES dim_network_type(network_type_id),
    equipment_code VARCHAR(120) NOT NULL,
    source_node VARCHAR(180) NOT NULL,
    destination_node VARCHAR(180) NOT NULL,
    distance_ml NUMERIC(14, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL DEFAULT 'ML',
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V52',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_network UNIQUE (generation_id, network_type_id, equipment_code, source_node, destination_node)
);

CREATE TABLE IF NOT EXISTS fact_generation_dqe (
    generated_dqe_id BIGSERIAL PRIMARY KEY,
    generation_id BIGINT NOT NULL REFERENCES fact_generation_bim(generation_id),
    article_code VARCHAR(180) NOT NULL,
    designation VARCHAR(500) NOT NULL,
    unit VARCHAR(40) NOT NULL,
    quantity NUMERIC(14, 4) NOT NULL DEFAULT 0,
    source_formula VARCHAR(255) NOT NULL,
    capex_local NUMERIC(16, 2) NOT NULL DEFAULT 0,
    capex_import NUMERIC(16, 2) NOT NULL DEFAULT 0,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V52',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_dqe UNIQUE (generation_id, article_code)
);

-- ============================================================================
-- PHASE 6 - AUTONOMIE
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_water (
    water_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(120) NOT NULL DEFAULT 'PROJET_MPEMBA',
    batiment VARCHAR(120) NOT NULL DEFAULT 'BAT_01',
    forage_depth NUMERIC(12, 2) NOT NULL DEFAULT 0,
    pump_power NUMERIC(12, 2) NOT NULL DEFAULT 0,
    tank_volume NUMERIC(12, 2) NOT NULL DEFAULT 0,
    daily_consumption NUMERIC(12, 2) NOT NULL DEFAULT 0,
    autonomy_days NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fact_solar (
    solar_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(120) NOT NULL DEFAULT 'PROJET_MPEMBA',
    batiment VARCHAR(120) NOT NULL DEFAULT 'BAT_01',
    installed_kwc NUMERIC(12, 2) NOT NULL DEFAULT 0,
    panel_count INTEGER NOT NULL DEFAULT 0,
    battery_capacity NUMERIC(12, 2) NOT NULL DEFAULT 0,
    daily_production NUMERIC(12, 2) NOT NULL DEFAULT 0,
    autonomy_hours NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fact_energy (
    energy_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(120) NOT NULL DEFAULT 'PROJET_MPEMBA',
    batiment VARCHAR(120) NOT NULL DEFAULT 'BAT_01',
    consumption NUMERIC(14, 2) NOT NULL DEFAULT 0,
    production NUMERIC(14, 2) NOT NULL DEFAULT 0,
    balance NUMERIC(14, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fact_forage (
    forage_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(120) NOT NULL DEFAULT 'PROJET_MPEMBA',
    batiment VARCHAR(120) NOT NULL DEFAULT 'BAT_01',
    flow_rate NUMERIC(12, 2) NOT NULL DEFAULT 0,
    storage_volume NUMERIC(12, 2) NOT NULL DEFAULT 0,
    daily_usage NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO fact_water (project_code, batiment, forage_depth, pump_power, tank_volume, daily_consumption, autonomy_days)
SELECT 'PROJET_MPEMBA', 'BAT_01', 150, 3.00, 20000, 7200, 2.78
WHERE NOT EXISTS (SELECT 1 FROM fact_water WHERE project_code = 'PROJET_MPEMBA' AND batiment = 'BAT_01');

INSERT INTO fact_solar (project_code, batiment, installed_kwc, panel_count, battery_capacity, daily_production, autonomy_hours)
SELECT 'PROJET_MPEMBA', 'BAT_01', 33.00, 60, 80.00, 145.00, 18.00
WHERE NOT EXISTS (SELECT 1 FROM fact_solar WHERE project_code = 'PROJET_MPEMBA' AND batiment = 'BAT_01');

INSERT INTO fact_energy (project_code, batiment, consumption, production, balance)
SELECT 'PROJET_MPEMBA', 'BAT_01', 120.00, 145.00, 25.00
WHERE NOT EXISTS (SELECT 1 FROM fact_energy WHERE project_code = 'PROJET_MPEMBA' AND batiment = 'BAT_01');

INSERT INTO fact_forage (project_code, batiment, flow_rate, storage_volume, daily_usage)
SELECT 'PROJET_MPEMBA', 'BAT_01', 4.50, 20000, 7200
WHERE NOT EXISTS (SELECT 1 FROM fact_forage WHERE project_code = 'PROJET_MPEMBA' AND batiment = 'BAT_01');

-- ============================================================================
-- PHASE 7 - FACADE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_facade_system (
    facade_system_id BIGSERIAL PRIMARY KEY,
    support_wall VARCHAR(180) NOT NULL,
    insulation_type VARCHAR(180) NOT NULL,
    insulation_thickness NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cladding_type VARCHAR(180) NOT NULL,
    ventilation_gap NUMERIC(12, 2) NOT NULL DEFAULT 0,
    fixation_system VARCHAR(180) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dim_facade_system UNIQUE (support_wall, insulation_type, insulation_thickness, cladding_type)
);

INSERT INTO dim_facade_system (
    support_wall,
    insulation_type,
    insulation_thickness,
    cladding_type,
    ventilation_gap,
    fixation_system,
    is_active
)
VALUES
    ('BETON', 'ITE laine roche', 100, 'ENDUIT', 20, 'Chevilles rosaces', TRUE),
    ('BETON', 'ITE laine roche', 120, 'ENDUIT', 20, 'Chevilles rosaces', TRUE),
    ('BETON', 'LAINE_ROCHE', 100, 'ALUCOBOND Beige Sable', 40, 'Ossature aluminium', TRUE),
    ('BETON', 'LAINE_ROCHE', 100, 'ALUCOBOND Bois', 40, 'Ossature aluminium', TRUE)
ON CONFLICT (support_wall, insulation_type, insulation_thickness, cladding_type) DO NOTHING;

-- ============================================================================
-- PHASE 4/5 - PROCEDURE DE GENERATION BAT_01
-- ============================================================================

CREATE OR REPLACE FUNCTION sp2i_v52_generate_bat01()
RETURNS TABLE (
    generated_bim_rows BIGINT,
    generated_network_rows BIGINT,
    generated_dqe_rows BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    before_bim BIGINT;
    before_network BIGINT;
    before_dqe BIGINT;
    after_bim BIGINT;
    after_network BIGINT;
    after_dqe BIGINT;
BEGIN
    SELECT COUNT(*) INTO before_bim FROM fact_generation_bim WHERE generation_batch = 'BAT_01_V52';
    SELECT COUNT(*) INTO before_network FROM fact_generation_network WHERE generation_batch = 'BAT_01_V52';
    SELECT COUNT(*) INTO before_dqe FROM fact_generation_dqe WHERE generation_batch = 'BAT_01_V52';

    WITH apartments(appartement_code, niveau_code) AS (
        VALUES
            ('A101', 'N1'),
            ('B101', 'N1'),
            ('A201', 'N2'),
            ('B201', 'N2'),
            ('A301', 'N3'),
            ('B301', 'N3')
    ),
    pieces(piece_code, type_piece_code, surface_m2) AS (
        VALUES
            ('SEJOUR', 'SEJOUR', 70.00::NUMERIC),
            ('CUISINE', 'CUISINE', 12.00::NUMERIC),
            ('CHAMBRE_1', 'CH1', 29.00::NUMERIC),
            ('CHAMBRE_2', 'CH2', 19.00::NUMERIC),
            ('CHAMBRE_3', 'CH3', 18.00::NUMERIC),
            ('DRESSING', 'DRESSING', 7.60::NUMERIC),
            ('SDB_1', 'SDB1', 9.13::NUMERIC),
            ('SDB_2', 'SDB2', 9.13::NUMERIC),
            ('WC_VISITEUR', 'WC', 2.50::NUMERIC),
            ('DEGAGEMENT', 'DEGAGEMENT', 25.00::NUMERIC),
            ('BALCON', 'BALCON', 18.00::NUMERIC)
    ),
    scope_rows AS (
        SELECT
            p.appartement_code,
            p.niveau_code,
            pc.piece_code,
            pc.type_piece_code,
            pc.surface_m2,
            tp.id AS type_piece_id,
            COALESCE(dp.piece_id, 0) AS piece_id,
            gf.formula_id,
            gf.equipment_code AS article_code,
            CASE
                WHEN gf.formula_type = 'FIXED' THEN gf.formula_expression::NUMERIC
                WHEN gf.formula_type = 'SURFACE_RATIO' THEN CEIL(pc.surface_m2 / NULLIF(regexp_replace(gf.formula_expression, '[^0-9.]', '', 'g')::NUMERIC, 0))
                ELSE 0
            END AS raw_quantity,
            gf.quantity_min,
            gf.quantity_max
        FROM apartments p
        CROSS JOIN pieces pc
        JOIN dim_type_piece tp
          ON tp.code = pc.type_piece_code
        JOIN dim_generation_formula gf
          ON gf.type_piece_id = tp.id
         AND gf.is_active
        LEFT JOIN dim_piece dp
          ON UPPER(COALESCE(dp.appart, '')) = UPPER(p.appartement_code)
         AND UPPER(COALESCE(dp.piece_code, dp.piece, '')) IN (UPPER(pc.piece_code), UPPER(pc.type_piece_code))
    ),
    inserted AS (
        INSERT INTO fact_generation_bim (
            project_id,
            batiment_id,
            niveau_id,
            appartement_id,
            piece_id,
            type_piece_id,
            surface_m2,
            article_code,
            quantity_generated,
            formula_id,
            generation_batch
        )
        SELECT
            (SELECT projet_id FROM dim_projet WHERE projet_code = 'PROJET_MPEMBA' LIMIT 1),
            (SELECT batiment_id FROM dim_batiment WHERE batiment IN ('BAT_01', 'BATIMENT_01') ORDER BY batiment_id LIMIT 1),
            (SELECT niveau_id FROM dim_niveau WHERE niveau = scope_rows.niveau_code OR niveau = replace(scope_rows.niveau_code, 'N', 'ETAGE ') ORDER BY niveau_id LIMIT 1),
            scope_rows.appartement_code,
            NULLIF(scope_rows.piece_id, 0),
            scope_rows.type_piece_id,
            scope_rows.surface_m2,
            scope_rows.article_code,
            LEAST(GREATEST(scope_rows.raw_quantity, scope_rows.quantity_min), scope_rows.quantity_max),
            scope_rows.formula_id,
            'BAT_01_V52'
        FROM scope_rows
        ON CONFLICT (generation_batch, appartement_id, type_piece_id, article_code, formula_id) DO NOTHING
        RETURNING generation_id
    )
    SELECT COUNT(*) FROM inserted INTO after_bim;

    WITH generation_scope AS (
        SELECT
            gb.generation_id,
            gb.appartement_id,
            gb.article_code AS equipment_code,
            gb.quantity_generated,
            nt.network_type_id,
            rr.default_distance,
            rr.coefficient,
            COALESCE(e.unit, 'ML') AS unit
        FROM fact_generation_bim gb
        JOIN dim_equipment e
          ON e.equipment_code = gb.article_code
        JOIN dim_network_type nt
          ON nt.network_type_id = e.network_type_id
        LEFT JOIN dim_route_rule rr
          ON rr.network_type_id = nt.network_type_id
         AND rr.equipment_code = e.equipment_code
         AND rr.is_active
        WHERE gb.generation_batch = 'BAT_01_V52'
    ),
    inserted AS (
        INSERT INTO fact_generation_network (
            generation_id,
            network_type_id,
            equipment_code,
            source_node,
            destination_node,
            distance_ml,
            unit,
            generation_batch
        )
        SELECT
            generation_id,
            network_type_id,
            equipment_code,
            'GAINE_TECHNIQUE_' || appartement_id AS source_node,
            appartement_id || '_' || equipment_code AS destination_node,
            ROUND((COALESCE(default_distance, 0) * COALESCE(coefficient, 1) * GREATEST(quantity_generated, 1))::NUMERIC, 4),
            CASE WHEN unit = 'ML' THEN 'ML' ELSE 'ML' END,
            'BAT_01_V52'
        FROM generation_scope
        WHERE COALESCE(default_distance, 0) > 0
        ON CONFLICT (generation_id, network_type_id, equipment_code, source_node, destination_node) DO NOTHING
        RETURNING network_generation_id
    )
    SELECT COUNT(*) FROM inserted INTO after_network;

    WITH generated AS (
        SELECT
            gb.generation_id,
            gb.article_code,
            e.equipment_name,
            e.unit,
            gb.quantity_generated,
            gf.formula_expression,
            CASE
                WHEN e.unit = 'ML' THEN 2500
                WHEN gb.article_code LIKE 'SPLIT%' THEN 450000
                WHEN gb.article_code IN ('WC', 'LAVABO', 'DOUCHE') THEN 120000
                WHEN gb.article_code LIKE 'PANNEAU%' THEN 180000
                ELSE 15000
            END::NUMERIC AS unit_price_local,
            CASE
                WHEN e.unit = 'ML' THEN 2150
                WHEN gb.article_code LIKE 'SPLIT%' THEN 375000
                WHEN gb.article_code IN ('WC', 'LAVABO', 'DOUCHE') THEN 102000
                WHEN gb.article_code LIKE 'PANNEAU%' THEN 150000
                ELSE 12600
            END::NUMERIC AS unit_price_import
        FROM fact_generation_bim gb
        JOIN dim_equipment e
          ON e.equipment_code = gb.article_code
        LEFT JOIN dim_generation_formula gf
          ON gf.formula_id = gb.formula_id
        WHERE gb.generation_batch = 'BAT_01_V52'
    ),
    inserted AS (
        INSERT INTO fact_generation_dqe (
            generation_id,
            article_code,
            designation,
            unit,
            quantity,
            source_formula,
            capex_local,
            capex_import,
            generation_batch
        )
        SELECT
            generation_id,
            article_code,
            equipment_name,
            unit,
            quantity_generated,
            COALESCE(formula_expression, ''),
            ROUND((quantity_generated * unit_price_local)::NUMERIC, 2),
            ROUND((quantity_generated * unit_price_import)::NUMERIC, 2),
            'BAT_01_V52'
        FROM generated
        ON CONFLICT (generation_id, article_code) DO NOTHING
        RETURNING generated_dqe_id
    )
    SELECT COUNT(*) FROM inserted INTO after_dqe;

    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM fact_generation_bim WHERE generation_batch = 'BAT_01_V52') - before_bim,
        (SELECT COUNT(*) FROM fact_generation_network WHERE generation_batch = 'BAT_01_V52') - before_network,
        (SELECT COUNT(*) FROM fact_generation_dqe WHERE generation_batch = 'BAT_01_V52') - before_dqe;
END;
$$;

-- Generation initiale idempotente BAT_01.
SELECT * FROM sp2i_v52_generate_bat01();

-- ============================================================================
-- PHASE 8 - VUES POWER BI NOUVELLES
-- ============================================================================

CREATE OR REPLACE VIEW vw_sp2i_generated_dqe AS
SELECT
    gb.generation_batch,
    COALESCE(dp.projet_code, 'PROJET_MPEMBA') AS projet,
    COALESCE(db.batiment, 'BAT_01') AS batiment,
    COALESCE(dn.niveau, 'NON_RENSEIGNE') AS niveau,
    gb.appartement_id AS appartement,
    COALESCE(dpi.piece_code, dpi.piece, gb.piece_id::TEXT, 'NON_RENSEIGNE') AS piece,
    tp.code AS type_piece,
    gd.article_code,
    gd.designation,
    gd.unit,
    gd.quantity,
    gd.source_formula,
    gd.capex_local,
    gd.capex_import,
    ROUND((gd.capex_local - gd.capex_import)::NUMERIC, 2) AS economie_potentielle,
    gd.created_at
FROM fact_generation_dqe gd
JOIN fact_generation_bim gb
  ON gb.generation_id = gd.generation_id
LEFT JOIN dim_projet dp
  ON dp.projet_id = gb.project_id
LEFT JOIN dim_batiment db
  ON db.batiment_id = gb.batiment_id
LEFT JOIN dim_niveau dn
  ON dn.niveau_id = gb.niveau_id
LEFT JOIN dim_piece dpi
  ON dpi.piece_id = gb.piece_id
LEFT JOIN dim_type_piece tp
  ON tp.id = gb.type_piece_id;

CREATE OR REPLACE VIEW vw_sp2i_generated_networks AS
SELECT
    fn.generation_batch,
    nt.network_code,
    nt.network_name,
    fn.equipment_code,
    e.equipment_name,
    fn.source_node,
    fn.destination_node,
    fn.distance_ml,
    fn.unit,
    gb.appartement_id AS appartement,
    COALESCE(dp.piece_code, dp.piece, gb.piece_id::TEXT, 'NON_RENSEIGNE') AS piece,
    fn.created_at
FROM fact_generation_network fn
JOIN fact_generation_bim gb
  ON gb.generation_id = fn.generation_id
JOIN dim_network_type nt
  ON nt.network_type_id = fn.network_type_id
LEFT JOIN dim_equipment e
  ON e.equipment_code = fn.equipment_code
LEFT JOIN dim_piece dp
  ON dp.piece_id = gb.piece_id;

CREATE OR REPLACE VIEW vw_sp2i_generated_capex AS
SELECT
    generation_batch,
    COUNT(*) AS nb_lignes_dqe,
    ROUND(COALESCE(SUM(capex_local), 0)::NUMERIC, 2) AS capex_local,
    ROUND(COALESCE(SUM(capex_import), 0)::NUMERIC, 2) AS capex_import,
    ROUND(COALESCE(SUM(capex_local - capex_import), 0)::NUMERIC, 2) AS economie_potentielle
FROM fact_generation_dqe
GROUP BY generation_batch;

CREATE OR REPLACE VIEW vw_energy_dashboard AS
SELECT
    project_code,
    batiment,
    consumption,
    production,
    balance,
    CASE WHEN consumption = 0 THEN 0 ELSE ROUND((production / NULLIF(consumption, 0))::NUMERIC, 4) END AS coverage_ratio,
    created_at
FROM fact_energy;

CREATE OR REPLACE VIEW vw_water_dashboard AS
SELECT
    project_code,
    batiment,
    forage_depth,
    pump_power,
    tank_volume,
    daily_consumption,
    autonomy_days,
    created_at
FROM fact_water;

CREATE OR REPLACE VIEW vw_autonomy_dashboard AS
SELECT
    COALESCE(e.project_code, w.project_code, s.project_code, f.project_code) AS project_code,
    COALESCE(e.batiment, w.batiment, s.batiment, f.batiment) AS batiment,
    e.consumption,
    e.production,
    e.balance,
    w.autonomy_days AS water_autonomy_days,
    s.installed_kwc,
    s.panel_count,
    s.battery_capacity,
    s.autonomy_hours AS solar_autonomy_hours,
    f.flow_rate,
    f.storage_volume
FROM fact_energy e
FULL OUTER JOIN fact_water w
  ON w.project_code = e.project_code AND w.batiment = e.batiment
FULL OUTER JOIN fact_solar s
  ON s.project_code = COALESCE(e.project_code, w.project_code)
 AND s.batiment = COALESCE(e.batiment, w.batiment)
FULL OUTER JOIN fact_forage f
  ON f.project_code = COALESCE(e.project_code, w.project_code, s.project_code)
 AND f.batiment = COALESCE(e.batiment, w.batiment, s.batiment);

CREATE OR REPLACE VIEW vw_facade_dashboard AS
SELECT
    facade_system_id,
    support_wall,
    insulation_type,
    insulation_thickness,
    cladding_type,
    ventilation_gap,
    fixation_system,
    is_active,
    created_at
FROM dim_facade_system;

-- ============================================================================
-- PHASE 9 - PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS ix_dim_network_type_code
    ON dim_network_type (network_code);

CREATE INDEX IF NOT EXISTS ix_dim_equipment_network
    ON dim_equipment (network_type_id, equipment_code);

CREATE INDEX IF NOT EXISTS ix_dim_route_rule_network_equipment
    ON dim_route_rule (network_type_id, equipment_code);

CREATE INDEX IF NOT EXISTS ix_dim_generation_formula_type_piece
    ON dim_generation_formula (type_piece_id, equipment_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_bim_scope
    ON fact_generation_bim (generation_batch, appartement_id, piece_id, article_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_bim_type_piece
    ON fact_generation_bim (type_piece_id);

CREATE INDEX IF NOT EXISTS ix_fact_generation_network_scope
    ON fact_generation_network (generation_batch, network_type_id, equipment_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_network_generation_id
    ON fact_generation_network (generation_id);

CREATE INDEX IF NOT EXISTS ix_fact_generation_dqe_batch_article
    ON fact_generation_dqe (generation_batch, article_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_dqe_generation_id
    ON fact_generation_dqe (generation_id);

CREATE INDEX IF NOT EXISTS ix_fact_water_project
    ON fact_water (project_code, batiment);

CREATE INDEX IF NOT EXISTS ix_fact_solar_project
    ON fact_solar (project_code, batiment);

CREATE INDEX IF NOT EXISTS ix_fact_energy_project
    ON fact_energy (project_code, batiment);

CREATE INDEX IF NOT EXISTS ix_fact_forage_project
    ON fact_forage (project_code, batiment);

CREATE INDEX IF NOT EXISTS ix_dim_facade_system_active
    ON dim_facade_system (is_active, cladding_type);

INSERT INTO sp2i_v52_migration_audit (audit_code, audit_payload)
VALUES (
    'POST_MIGRATION_V52',
    jsonb_build_object(
        'dim_network_type', (SELECT COUNT(*) FROM dim_network_type),
        'dim_equipment', (SELECT COUNT(*) FROM dim_equipment),
        'dim_route_rule', (SELECT COUNT(*) FROM dim_route_rule),
        'dim_generation_formula', (SELECT COUNT(*) FROM dim_generation_formula),
        'fact_generation_bim', (SELECT COUNT(*) FROM fact_generation_bim),
        'fact_generation_network', (SELECT COUNT(*) FROM fact_generation_network),
        'fact_generation_dqe', (SELECT COUNT(*) FROM fact_generation_dqe)
    )
);

COMMIT;

-- ============================================================================
-- VALIDATION RAPIDE
-- ============================================================================

SELECT relation_name, rows_count
FROM (
    VALUES
        ('dim_network_type', (SELECT COUNT(*) FROM dim_network_type)),
        ('dim_equipment', (SELECT COUNT(*) FROM dim_equipment)),
        ('dim_route_rule', (SELECT COUNT(*) FROM dim_route_rule)),
        ('dim_generation_formula', (SELECT COUNT(*) FROM dim_generation_formula)),
        ('fact_generation_bim', (SELECT COUNT(*) FROM fact_generation_bim)),
        ('fact_generation_network', (SELECT COUNT(*) FROM fact_generation_network)),
        ('fact_generation_dqe', (SELECT COUNT(*) FROM fact_generation_dqe)),
        ('fact_water', (SELECT COUNT(*) FROM fact_water)),
        ('fact_solar', (SELECT COUNT(*) FROM fact_solar)),
        ('fact_energy', (SELECT COUNT(*) FROM fact_energy)),
        ('fact_forage', (SELECT COUNT(*) FROM fact_forage)),
        ('dim_facade_system', (SELECT COUNT(*) FROM dim_facade_system))
) AS validation(relation_name, rows_count)
ORDER BY relation_name;
