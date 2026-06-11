-- SP2I CAPEX - Rollback non destructif V5.2.1 Quantity Expansion
-- Fichier: rollback_013_v52_1.sql
--
-- Strategie:
-- - ne pas DROP TABLE ;
-- - ne pas DROP VIEW ;
-- - ne pas toucher aux objets historiques ;
-- - desactiver les regles d expansion ;
-- - conserver les quantites generees pour audit.

BEGIN;

UPDATE dim_quantity_expansion_rule
SET is_active = FALSE
WHERE equipment_code IN (
    'SPOT_LED',
    'PRISE_16A',
    'PRISE_PLAN_TRAVAIL',
    'PRISE_FRIGO',
    'PRISE_MICRO_ONDES',
    'PRISE_HOTTE',
    'PRISE_RJ45',
    'PRISE_TV',
    'LAVABO',
    'WC',
    'DOUCHE',
    'EVIER',
    'SPLIT_12000',
    'SPLIT_18000',
    'EXTRACTEUR',
    'PANNEAU_550W',
    'POMPE_IMMERGEE'
);

CREATE OR REPLACE VIEW vw_sp2i_generated_quantities AS
SELECT
    NULL::VARCHAR(120) AS generation_batch,
    NULL::BIGINT AS project_id,
    NULL::BIGINT AS batiment_id,
    NULL::BIGINT AS niveau_id,
    NULL::VARCHAR(150) AS appartement,
    NULL::BIGINT AS piece_id,
    NULL::VARCHAR(80) AS type_piece,
    NULL::VARCHAR(120) AS equipment_code,
    NULL::VARCHAR(180) AS generated_article_code,
    NULL::VARCHAR(500) AS generated_designation,
    0::NUMERIC(16, 4) AS quantity,
    NULL::VARCHAR(40) AS unit,
    NULL::VARCHAR(120) AS lot_code,
    0::NUMERIC(14, 4) AS source_quantity,
    0::NUMERIC(12, 2) AS source_surface_m2,
    NULL::VARCHAR(120) AS quantity_formula,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

CREATE OR REPLACE VIEW vw_sp2i_generated_network_quantities AS
SELECT
    NULL::VARCHAR(120) AS generation_batch,
    NULL::VARCHAR(120) AS lot_code,
    NULL::VARCHAR(120) AS equipment_code,
    NULL::VARCHAR(180) AS generated_article_code,
    NULL::VARCHAR(500) AS generated_designation,
    NULL::VARCHAR(40) AS unit,
    0::BIGINT AS nb_lignes,
    0::NUMERIC(16, 4) AS quantite_totale,
    0::BIGINT AS network_rows_estimated
WHERE false;

COMMIT;
