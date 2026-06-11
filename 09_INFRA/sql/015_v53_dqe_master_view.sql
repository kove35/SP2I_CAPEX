-- SP2I CAPEX - V5.3 DQE Master 18 lots
-- Migration: 015_v53_dqe_master_view.sql
--
-- Objectif:
-- - creer la vue canonique DQE_MPEMBA_V53_18_LOTS_MASTER ;
-- - federer les vues generatives V5.2.1 et V5.3 dans une vue unique ;
-- - conserver tous les doublons metier via UNION ALL ;
-- - ne pas modifier fact_metre, fact_simulation, fact_approvals ou procurement_decisions.
--
-- Aucune deduplication: pas de DISTINCT, pas de GROUP BY.

BEGIN;

CREATE OR REPLACE VIEW vw_sp2i_generated_dqe_master AS
SELECT
    'vw_sp2i_generated_quantities'::text AS source_view,
    generation_batch::text AS generation_batch,
    project_id::text AS project_id,
    batiment_id::text AS batiment_id,
    niveau_id::text AS niveau_id,
    appartement::text AS appartement,
    piece_id::text AS piece_id,
    type_piece::text AS type_piece,
    lot_code::text AS lot_code,
    equipment_code::text AS component_code,
    generated_article_code::text AS generated_article_code,
    generated_designation::text AS generated_designation,
    quantity::numeric AS quantity,
    unit::text AS unit,
    source_quantity::numeric AS source_quantity,
    source_surface_m2::numeric AS source_surface_m2,
    quantity_formula::text AS quantity_formula,
    NULL::text AS scope_note,
    created_at::timestamptz AS created_at
FROM vw_sp2i_generated_quantities

UNION ALL

SELECT
    'vw_sp2i_generated_building'::text AS source_view,
    generation_batch::text AS generation_batch,
    NULL::text AS project_id,
    NULL::text AS batiment_id,
    NULL::text AS niveau_id,
    NULL::text AS appartement,
    NULL::text AS piece_id,
    NULL::text AS type_piece,
    lot_code::text AS lot_code,
    component_code::text AS component_code,
    generated_article_code::text AS generated_article_code,
    generated_designation::text AS generated_designation,
    quantity::numeric AS quantity,
    unit::text AS unit,
    NULL::numeric AS source_quantity,
    NULL::numeric AS source_surface_m2,
    NULL::text AS quantity_formula,
    scope_note::text AS scope_note,
    created_at::timestamptz AS created_at
FROM vw_sp2i_generated_building

UNION ALL

SELECT
    'vw_sp2i_generated_envelope'::text AS source_view,
    generation_batch::text AS generation_batch,
    NULL::text AS project_id,
    NULL::text AS batiment_id,
    NULL::text AS niveau_id,
    NULL::text AS appartement,
    NULL::text AS piece_id,
    NULL::text AS type_piece,
    lot_code::text AS lot_code,
    component_code::text AS component_code,
    generated_article_code::text AS generated_article_code,
    generated_designation::text AS generated_designation,
    quantity::numeric AS quantity,
    unit::text AS unit,
    NULL::numeric AS source_quantity,
    NULL::numeric AS source_surface_m2,
    NULL::text AS quantity_formula,
    scope_note::text AS scope_note,
    created_at::timestamptz AS created_at
FROM vw_sp2i_generated_envelope

UNION ALL

SELECT
    'vw_sp2i_generated_special_systems'::text AS source_view,
    generation_batch::text AS generation_batch,
    NULL::text AS project_id,
    NULL::text AS batiment_id,
    NULL::text AS niveau_id,
    NULL::text AS appartement,
    NULL::text AS piece_id,
    NULL::text AS type_piece,
    lot_code::text AS lot_code,
    component_code::text AS component_code,
    generated_article_code::text AS generated_article_code,
    generated_designation::text AS generated_designation,
    quantity::numeric AS quantity,
    unit::text AS unit,
    NULL::numeric AS source_quantity,
    NULL::numeric AS source_surface_m2,
    NULL::text AS quantity_formula,
    scope_note::text AS scope_note,
    created_at::timestamptz AS created_at
FROM vw_sp2i_generated_special_systems;

COMMENT ON VIEW vw_sp2i_generated_dqe_master IS
'DQE_MPEMBA_V53_18_LOTS_MASTER - vue canonique additive issue de vw_sp2i_generated_quantities, vw_sp2i_generated_building, vw_sp2i_generated_envelope et vw_sp2i_generated_special_systems. UNION ALL conserve tous les doublons metier.';

COMMIT;
