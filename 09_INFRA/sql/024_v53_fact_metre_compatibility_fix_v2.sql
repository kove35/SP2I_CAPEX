-- SP2I CAPEX - V5.3 fact_metre compatibility fix v2
-- Migration: 024_v53_fact_metre_compatibility_fix_v2.sql
--
-- Objectif:
-- - ajouter sous_lot_id dans vw_fact_metre_v53_financial a partir de
--   sous_lot_code, deja renseigne sur 100 % des lignes V5.3 ;
-- - propager automatiquement la colonne vers vw_fact_metre_current ;
-- - conserver simultanement sous_lot_id, sous_lot_code et sous_lot ;
-- - ne pas modifier fact_metre, fact_simulation, fact_approvals,
--   procurement_decisions, imports DQE, pipeline, simulation ou procurement.
--
-- Interdictions respectees:
-- - aucun DROP TABLE ;
-- - aucun DELETE ;
-- - aucun UPDATE ;
-- - aucun TRUNCATE.
--
-- Dry-run:
--   remplacer le COMMIT final par ROLLBACK et executer avec ON_ERROR_STOP=1.

BEGIN;

DO $$
DECLARE
    v_rows BIGINT;
    v_articles BIGINT;
    v_lots BIGINT;
    v_sous_lot_code_rows BIGINT;
    v_distinct_sous_lot_codes BIGINT;
BEGIN
    IF to_regclass('vw_sp2i_generated_dqe_master') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: vw_sp2i_generated_dqe_master';
    END IF;

    IF to_regclass('vw_bpu_v53_priced') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: vw_bpu_v53_priced';
    END IF;

    SELECT
        COUNT(*),
        COUNT(DISTINCT generated_article_code),
        COUNT(DISTINCT lot_code)
    INTO v_rows, v_articles, v_lots
    FROM vw_sp2i_generated_dqe_master;

    IF v_rows <> 4734 THEN
        RAISE EXCEPTION 'V5.3 compatibility blocked: expected 4734 master rows, got %', v_rows;
    END IF;

    IF v_articles <> 2524 THEN
        RAISE EXCEPTION 'V5.3 compatibility blocked: expected 2524 articles, got %', v_articles;
    END IF;

    IF v_lots <> 18 THEN
        RAISE EXCEPTION 'V5.3 compatibility blocked: expected 18 lots, got %', v_lots;
    END IF;

    SELECT
        COUNT(sous_lot_code),
        COUNT(DISTINCT sous_lot_code)
    INTO v_sous_lot_code_rows, v_distinct_sous_lot_codes
    FROM vw_bpu_v53_priced;

    IF v_sous_lot_code_rows <> 2524 THEN
        RAISE EXCEPTION
            'V5.3 compatibility blocked: expected 2524 priced BPU rows with sous_lot_code, got %',
            v_sous_lot_code_rows;
    END IF;

    IF v_distinct_sous_lot_codes <> 79 THEN
        RAISE EXCEPTION
            'V5.3 compatibility blocked: expected 79 distinct sous_lot_code values, got %',
            v_distinct_sous_lot_codes;
    END IF;
END $$;

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
    created_at,

    -- Colonnes de compatibilite ajoutees en fin de vue pour Analytics.
    COALESCE(NULLIF(project_id, ''), 'PROJET_MPEMBA')::varchar(150) AS project_code,
    NULL::bigint AS lot_id,
    'V53_GENERATED'::varchar(100) AS famille,
    NULL::bigint AS famille_id,
    ''::varchar(255) AS marque,
    NULL::bigint AS zone_id,
    NULL::bigint AS appart_id,
    NULL::bigint AS objet_bim_id,
    ''::varchar(150) AS bim_object_id,
    ''::varchar(150) AS bim_object,
    ''::varchar(150) AS ifc_guid,
    ''::varchar(150) AS type_objet,
    'V53_GENERATED'::varchar(255) AS famille_bim,
    ''::varchar(150) AS systeme,
    ''::varchar(150) AS phase_chantier,
    NULL::double precision AS altitude,
    'READY'::varchar(50) AS execution_status,
    'V53_READY'::varchar(50) AS workflow_status,
    created_at::timestamptz AS eta,
    'LOW'::varchar(100) AS risque,
    'V53'::varchar(50) AS bim_maturity,
    ''::varchar(150) AS classification,
    ''::varchar(150) AS omniclass,
    ''::varchar(150) AS uniclass,
    ''::varchar(150) AS ifc_type,
    NULL::bigint AS scenario_id,
    created_at::timestamptz AS date_import,
    'FCFA'::varchar(10) AS devise_source,
    created_at::timestamptz AS updated_at,
    sous_lot_code::varchar(150) AS sous_lot_id
FROM financial_lines;

COMMENT ON VIEW vw_fact_metre_v53_financial IS
'Vue financiere V5.3 compatible fact_metre, enrichie de sous_lot_id depuis sous_lot_code. Aucun fait metier historique n est modifie.';

CREATE OR REPLACE VIEW vw_fact_metre_current AS
SELECT *
FROM vw_fact_metre_v53_financial;

COMMENT ON VIEW vw_fact_metre_current IS
'Source officielle de lecture CAPEX. Phase 024 v2: pointe vers vw_fact_metre_v53_financial avec sous_lot_id compatible fact_metre.';

DO $$
DECLARE
    v_column_count BIGINT;
    v_null_sous_lot_id BIGINT;
    v_distinct_sous_lot_id BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_column_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'vw_fact_metre_current'
      AND column_name = 'sous_lot_id';

    IF v_column_count <> 1 THEN
        RAISE EXCEPTION 'V5.3 compatibility blocked: expected 1 sous_lot_id column on vw_fact_metre_current, got %', v_column_count;
    END IF;

    SELECT COUNT(*)
    INTO v_null_sous_lot_id
    FROM vw_fact_metre_current
    WHERE sous_lot_id IS NULL;

    IF v_null_sous_lot_id <> 0 THEN
        RAISE EXCEPTION 'V5.3 compatibility blocked: expected 0 null sous_lot_id values, got %', v_null_sous_lot_id;
    END IF;

    SELECT COUNT(DISTINCT sous_lot_id)
    INTO v_distinct_sous_lot_id
    FROM vw_fact_metre_current;

    IF v_distinct_sous_lot_id <> 79 THEN
        RAISE EXCEPTION 'V5.3 compatibility blocked: expected 79 distinct sous_lot_id values, got %', v_distinct_sous_lot_id;
    END IF;
END $$;

COMMIT;
