-- SP2I CAPEX - Rollback non destructif V5.2 Generative Engine
-- Fichier: rollback_013_v52.sql
--
-- Contrainte projet:
-- - ne jamais DROP TABLE ;
-- - ne jamais DROP VIEW ;
-- - ne pas toucher aux objets historiques ;
-- - neutraliser uniquement la couche V5.2 ajoutee par 013.
--
-- Strategie:
-- - desactiver les dimensions/rules V5.2 ;
-- - vider fonctionnellement les vues V5.2 via CREATE OR REPLACE VIEW ... WHERE false ;
-- - conserver les donnees pour audit et restauration ulterieure.

BEGIN;

UPDATE dim_network_type
SET is_active = FALSE
WHERE network_code IN ('ELEC', 'CFA', 'PLOMB', 'SAN', 'CVC', 'INCENDIE', 'SECURITE', 'SOLAIRE', 'FORAGE', 'VRD');

UPDATE dim_equipment
SET is_active = FALSE
WHERE equipment_code IN (
    'PRISE_16A',
    'PRISE_RJ45',
    'SPOT_LED',
    'WC',
    'LAVABO',
    'DOUCHE',
    'SPLIT_12000',
    'SPLIT_18000',
    'CAMERA_IP',
    'PANNEAU_550W',
    'POMPE_IMMERGEE'
);

UPDATE dim_route_rule
SET is_active = FALSE
WHERE equipment_code IN (
    'PRISE_16A',
    'PRISE_RJ45',
    'SPOT_LED',
    'SPLIT_12000',
    'SPLIT_18000',
    'EF',
    'EC',
    'EU',
    'EV',
    'DETECTEUR',
    'CAMERA_IP',
    'PANNEAU_550W',
    'POMPE_IMMERGEE',
    'VRD_FOURREAU'
);

UPDATE dim_generation_formula
SET is_active = FALSE
WHERE equipment_code IN (
    'SPOT_LED',
    'PRISE_16A',
    'PRISE_RJ45',
    'PRISE_TV',
    'SPLIT_18000',
    'SPLIT_12000',
    'PRISE_PLAN_TRAVAIL',
    'PRISE_FRIGO',
    'PRISE_MICRO_ONDES',
    'PRISE_HOTTE',
    'EVIER',
    'WC',
    'LAVABO',
    'DOUCHE',
    'MIROIR',
    'EXTRACTEUR'
);

UPDATE dim_facade_system
SET is_active = FALSE
WHERE cladding_type IN ('ENDUIT', 'ALUCOBOND Beige Sable', 'ALUCOBOND Bois')
   OR insulation_type IN ('ITE laine roche', 'LAINE_ROCHE');

CREATE OR REPLACE VIEW vw_sp2i_generated_dqe AS
SELECT
    NULL::VARCHAR(120) AS generation_batch,
    NULL::VARCHAR(100) AS projet,
    NULL::VARCHAR(150) AS batiment,
    NULL::VARCHAR(100) AS niveau,
    NULL::VARCHAR(150) AS appartement,
    NULL::TEXT AS piece,
    NULL::VARCHAR(80) AS type_piece,
    NULL::VARCHAR(180) AS article_code,
    NULL::VARCHAR(500) AS designation,
    NULL::VARCHAR(40) AS unit,
    NULL::NUMERIC(14, 4) AS quantity,
    NULL::VARCHAR(255) AS source_formula,
    NULL::NUMERIC(16, 2) AS capex_local,
    NULL::NUMERIC(16, 2) AS capex_import,
    NULL::NUMERIC(16, 2) AS economie_potentielle,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

CREATE OR REPLACE VIEW vw_sp2i_generated_networks AS
SELECT
    NULL::VARCHAR(120) AS generation_batch,
    NULL::VARCHAR(60) AS network_code,
    NULL::VARCHAR(255) AS network_name,
    NULL::VARCHAR(120) AS equipment_code,
    NULL::VARCHAR(255) AS equipment_name,
    NULL::VARCHAR(180) AS source_node,
    NULL::VARCHAR(180) AS destination_node,
    NULL::NUMERIC(14, 4) AS distance_ml,
    NULL::VARCHAR(40) AS unit,
    NULL::VARCHAR(150) AS appartement,
    NULL::TEXT AS piece,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

CREATE OR REPLACE VIEW vw_sp2i_generated_capex AS
SELECT
    NULL::VARCHAR(120) AS generation_batch,
    0::BIGINT AS nb_lignes_dqe,
    0::NUMERIC(16, 2) AS capex_local,
    0::NUMERIC(16, 2) AS capex_import,
    0::NUMERIC(16, 2) AS economie_potentielle
WHERE false;

CREATE OR REPLACE VIEW vw_energy_dashboard AS
SELECT
    NULL::VARCHAR(120) AS project_code,
    NULL::VARCHAR(120) AS batiment,
    0::NUMERIC(14, 2) AS consumption,
    0::NUMERIC(14, 2) AS production,
    0::NUMERIC(14, 2) AS balance,
    0::NUMERIC(14, 4) AS coverage_ratio,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

CREATE OR REPLACE VIEW vw_water_dashboard AS
SELECT
    NULL::VARCHAR(120) AS project_code,
    NULL::VARCHAR(120) AS batiment,
    0::NUMERIC(12, 2) AS forage_depth,
    0::NUMERIC(12, 2) AS pump_power,
    0::NUMERIC(12, 2) AS tank_volume,
    0::NUMERIC(12, 2) AS daily_consumption,
    0::NUMERIC(12, 2) AS autonomy_days,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

CREATE OR REPLACE VIEW vw_autonomy_dashboard AS
SELECT
    NULL::VARCHAR(120) AS project_code,
    NULL::VARCHAR(120) AS batiment,
    0::NUMERIC(14, 2) AS consumption,
    0::NUMERIC(14, 2) AS production,
    0::NUMERIC(14, 2) AS balance,
    0::NUMERIC(12, 2) AS water_autonomy_days,
    0::NUMERIC(12, 2) AS installed_kwc,
    0::INTEGER AS panel_count,
    0::NUMERIC(12, 2) AS battery_capacity,
    0::NUMERIC(12, 2) AS solar_autonomy_hours,
    0::NUMERIC(12, 2) AS flow_rate,
    0::NUMERIC(12, 2) AS storage_volume
WHERE false;

CREATE OR REPLACE VIEW vw_facade_dashboard AS
SELECT
    NULL::BIGINT AS facade_system_id,
    NULL::VARCHAR(180) AS support_wall,
    NULL::VARCHAR(180) AS insulation_type,
    0::NUMERIC(12, 2) AS insulation_thickness,
    NULL::VARCHAR(180) AS cladding_type,
    0::NUMERIC(12, 2) AS ventilation_gap,
    NULL::VARCHAR(180) AS fixation_system,
    FALSE AS is_active,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

INSERT INTO sp2i_v52_migration_audit (audit_code, audit_payload)
VALUES (
    'ROLLBACK_013_V52_NON_DESTRUCTIVE',
    jsonb_build_object(
        'strategy', 'disable_only_no_drop',
        'legacy_objects_preserved', true,
        'executed_at', now()
    )
);

COMMIT;
