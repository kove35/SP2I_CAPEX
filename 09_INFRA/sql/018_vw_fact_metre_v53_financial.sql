-- SP2I CAPEX - Fact metre V5.3 financial view
-- Migration: 018_vw_fact_metre_v53_financial.sql
--
-- Objectif:
-- - creer une vue financiere compatible fact_metre a partir du master DQE V5.3 ;
-- - joindre les quantites generees aux prix de vw_bpu_v53_priced ;
-- - calculer CAPEX local, import, optimise, economie et taux economie ;
-- - ne pas modifier fact_metre, fact_simulation, fact_approvals ou procurement_decisions.
--
-- Preconditions:
-- - 015_v53_dqe_master_view.sql appliquee ;
-- - 016_dim_bpu_v53.sql appliquee ;
-- - 017_bpu_v53_pricing_strategy.sql appliquee.

BEGIN;

CREATE OR REPLACE VIEW vw_fact_metre_v53_financial AS
WITH financial_lines AS (
    SELECT
        m.source_view,
        m.generation_batch,
        m.project_id,
        m.batiment_id,
        m.niveau_id,
        m.appartement,
        m.piece_id,
        m.type_piece,
        m.lot_code,
        m.component_code,
        m.generated_article_code,
        m.generated_designation,
        m.quantity,
        m.unit,
        m.source_quantity,
        m.source_surface_m2,
        m.quantity_formula,
        m.scope_note,
        m.created_at,
        p.article_code,
        p.designation AS bpu_designation,
        p.sous_lot_code,
        p.unite AS bpu_unite,
        p.prix_local_fcfa,
        p.prix_import_fcfa,
        p.prix_optimise_fcfa,
        p.decision_import,
        p.niveau_confiance,
        p.source_prix,
        p.fournisseur_local,
        p.fournisseur_import,
        p.pays_import
    FROM vw_sp2i_generated_dqe_master m
    JOIN vw_bpu_v53_priced p
      ON p.article_code = m.generated_article_code
)
SELECT
    md5(CONCAT_WS(
        '|',
        source_view,
        generation_batch,
        project_id,
        batiment_id,
        niveau_id,
        appartement,
        piece_id,
        type_piece,
        lot_code,
        component_code,
        generated_article_code,
        generated_designation,
        quantity::text
    )) AS id_ligne,
    COALESCE(NULLIF(generated_designation, ''), NULLIF(bpu_designation, ''), article_code) AS designation,
    quantity::numeric AS quantite,
    COALESCE(NULLIF(unit, ''), NULLIF(bpu_unite, '')) AS unite,
    lot_code AS lot,
    lot_code,
    article_code,
    article_code AS code_article,
    article_code AS article_id,
    sous_lot_code,
    component_code AS sous_lot,
    prix_local_fcfa::numeric AS prix_local_fcfa,
    prix_import_fcfa::numeric AS prix_import_fcfa,
    prix_optimise_fcfa::numeric AS prix_optimise_fcfa,
    prix_local_fcfa::numeric AS pu_local,
    prix_import_fcfa::numeric AS pu_import,
    (quantity * prix_local_fcfa)::numeric AS prix_total_ht,
    (quantity * prix_local_fcfa)::numeric AS capex_local,
    (quantity * prix_import_fcfa)::numeric AS capex_import,
    (quantity * prix_optimise_fcfa)::numeric AS capex_optimise,
    ((quantity * prix_local_fcfa) - (quantity * prix_optimise_fcfa))::numeric AS economie,
    ((quantity * prix_local_fcfa) - (quantity * prix_optimise_fcfa))::numeric AS economie_nette,
    CASE
        WHEN COALESCE(quantity * prix_local_fcfa, 0) = 0 THEN 0::numeric
        ELSE ((quantity * prix_local_fcfa) - (quantity * prix_optimise_fcfa))
             / NULLIF(quantity * prix_local_fcfa, 0)
    END AS taux_economie,
    decision_import,
    project_id,
    NULLIF(project_id, '')::bigint AS projet_id,
    batiment_id,
    NULLIF(batiment_id, '')::bigint AS batiment_id_num,
    batiment_id AS batiment,
    batiment_id AS batiment_code,
    niveau_id,
    NULLIF(niveau_id, '')::bigint AS niveau_id_num,
    niveau_id AS niveau,
    niveau_id AS niveau_code,
    appartement,
    appartement AS appartement_id,
    appartement AS appartement_code,
    appartement AS appart,
    piece_id,
    NULLIF(piece_id, '')::bigint AS piece_id_num,
    piece_id AS piece_code,
    piece_id AS piece,
    type_piece,
    type_piece AS type_zone,
    component_code,
    quantity_formula AS formule,
    scope_note,
    niveau_confiance,
    source_prix,
    fournisseur_local,
    fournisseur_import,
    pays_import,
    CASE
        WHEN decision_import = 'IMPORT' THEN fournisseur_import
        ELSE fournisseur_local
    END AS fournisseur,
    decision_import AS import_local,
    (quantity * prix_import_fcfa)::numeric AS montant_import,
    decision_import AS decision,
    'GENERATED_V53'::text AS source_file_type,
    'OK'::text AS statut_ligne,
    created_at
FROM financial_lines;

COMMENT ON VIEW vw_fact_metre_v53_financial IS
'Vue financiere V5.3 compatible fact_metre, calculee depuis vw_sp2i_generated_dqe_master et vw_bpu_v53_priced. Aucun fait metier historique n est modifie.';

COMMIT;
