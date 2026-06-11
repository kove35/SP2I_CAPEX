-- SP2I CAPEX - Rollback non destructif V5.3 Building Completion
-- Fichier: rollback_013_v53.sql
--
-- Strategie:
-- - ne pas DROP TABLE ;
-- - ne pas DROP VIEW ;
-- - ne pas toucher aux objets historiques ;
-- - desactiver les faits V5.3 disposant de is_active ;
-- - remplacer les vues V5.3 par des vues vides compatibles.

BEGIN;

UPDATE fact_generation_facade SET is_active = FALSE WHERE generation_batch = 'BAT_01_V53';
UPDATE fact_generation_menu_ext SET is_active = FALSE WHERE generation_batch = 'BAT_01_V53';
UPDATE fact_generation_menu_int SET is_active = FALSE WHERE generation_batch = 'BAT_01_V53';
UPDATE fact_generation_ascenseur SET is_active = FALSE WHERE generation_batch = 'BAT_01_V53';
UPDATE fact_generation_incendie SET is_active = FALSE WHERE generation_batch = 'BAT_01_V53';
UPDATE fact_generation_securite SET is_active = FALSE WHERE generation_batch = 'BAT_01_V53';
UPDATE fact_generation_vrd SET is_active = FALSE WHERE generation_batch = 'BAT_01_V53';

UPDATE dim_go_component SET is_active = FALSE;
UPDATE dim_maconnerie_component SET is_active = FALSE;
UPDATE dim_toiture_component SET is_active = FALSE;

CREATE OR REPLACE VIEW vw_sp2i_generated_building AS
SELECT
    NULL::TEXT AS source_table,
    NULL::VARCHAR(120) AS generation_batch,
    NULL::VARCHAR(120) AS lot_code,
    NULL::VARCHAR(120) AS component_code,
    NULL::VARCHAR(255) AS designation,
    0::NUMERIC(16, 4) AS quantity,
    NULL::VARCHAR(40) AS unit,
    0::INTEGER AS component_index,
    NULL::TEXT AS generated_article_code,
    NULL::TEXT AS generated_designation,
    NULL::VARCHAR(255) AS scope_note,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

CREATE OR REPLACE VIEW vw_sp2i_generated_envelope AS
SELECT
    NULL::TEXT AS source_table,
    NULL::VARCHAR(120) AS generation_batch,
    NULL::VARCHAR(120) AS lot_code,
    NULL::VARCHAR(120) AS component_code,
    NULL::VARCHAR(255) AS designation,
    0::NUMERIC(16, 4) AS quantity,
    NULL::VARCHAR(40) AS unit,
    0::INTEGER AS component_index,
    NULL::TEXT AS generated_article_code,
    NULL::TEXT AS generated_designation,
    NULL::VARCHAR(255) AS scope_note,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

CREATE OR REPLACE VIEW vw_sp2i_generated_special_systems AS
SELECT
    NULL::TEXT AS source_table,
    NULL::VARCHAR(120) AS generation_batch,
    NULL::VARCHAR(120) AS lot_code,
    NULL::VARCHAR(120) AS component_code,
    NULL::VARCHAR(255) AS designation,
    0::NUMERIC(16, 4) AS quantity,
    NULL::VARCHAR(40) AS unit,
    0::INTEGER AS component_index,
    NULL::TEXT AS generated_article_code,
    NULL::TEXT AS generated_designation,
    NULL::VARCHAR(255) AS scope_note,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

COMMIT;
