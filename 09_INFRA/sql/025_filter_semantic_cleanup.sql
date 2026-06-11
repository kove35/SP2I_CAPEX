-- SP2I CAPEX - V5.3 filter semantic cleanup
-- Migration: 025_filter_semantic_cleanup.sql
--
-- Objectif:
-- - corriger l'exposition des IDs techniques dans les filtres Analytics V5.3 ;
-- - reconstruire batiment, batiment_code, niveau et niveau_code depuis
--   dim_batiment et dim_niveau ;
-- - conserver batiment_id, batiment_id_num, niveau_id et niveau_id_num
--   sans modification ;
-- - ne modifier aucune table physique ni aucune donnee metier.
--
-- Interdictions respectees:
-- - aucun DROP TABLE ;
-- - aucun DELETE ;
-- - aucun UPDATE ;
-- - aucun TRUNCATE ;
-- - aucun changement frontend/backend.

BEGIN;

DO $$
BEGIN
    IF to_regclass('vw_sp2i_generated_dqe_master') IS NULL THEN
        RAISE EXCEPTION '025 blocked: missing prerequisite vw_sp2i_generated_dqe_master';
    END IF;

    IF to_regclass('vw_bpu_v53_priced') IS NULL THEN
        RAISE EXCEPTION '025 blocked: missing prerequisite vw_bpu_v53_priced';
    END IF;

    IF to_regclass('dim_batiment') IS NULL THEN
        RAISE EXCEPTION '025 blocked: missing prerequisite dim_batiment';
    END IF;

    IF to_regclass('dim_niveau') IS NULL THEN
        RAISE EXCEPTION '025 blocked: missing prerequisite dim_niveau';
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
),
semantic_lines AS (
    SELECT
        fl.*,
        CASE
            WHEN COALESCE(NULLIF(db.batiment_code, ''), NULLIF(db.batiment, ''), 'BAT_01')
                 IN ('BATIMENT_01', 'BATIMENT PRINCIPAL')
                THEN 'BAT_01'
            ELSE COALESCE(NULLIF(db.batiment_code, ''), NULLIF(db.batiment, ''), 'BAT_01')
        END::text AS semantic_batiment,
        CASE
            WHEN COALESCE(NULLIF(db.batiment_code, ''), NULLIF(db.batiment, ''), 'BAT_01')
                 IN ('BATIMENT_01', 'BATIMENT PRINCIPAL')
                THEN 'BAT_01'
            ELSE COALESCE(NULLIF(db.batiment_code, ''), NULLIF(db.batiment, ''), 'BAT_01')
        END::text AS semantic_batiment_code,
        CASE
            WHEN NULLIF(fl.niveau_id, '') IS NULL THEN NULL
            ELSE COALESCE(NULLIF(dn.niveau, ''), 'GLOBAL')
        END::text AS semantic_niveau,
        CASE
            WHEN NULLIF(fl.niveau_id, '') IS NULL THEN NULL
            ELSE COALESCE(NULLIF(dn.niveau, ''), 'GLOBAL')
        END::text AS semantic_niveau_code
    FROM financial_lines fl
    LEFT JOIN dim_batiment db
      ON db.batiment_id = NULLIF(fl.batiment_id, '')::bigint
    LEFT JOIN dim_niveau dn
      ON dn.niveau_id = NULLIF(fl.niveau_id, '')::bigint
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
    semantic_batiment AS batiment,
    semantic_batiment_code AS batiment_code,
    niveau_id,
    NULLIF(niveau_id, '')::bigint AS niveau_id_num,
    semantic_niveau AS niveau,
    semantic_niveau_code AS niveau_code,
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
FROM semantic_lines;

COMMENT ON VIEW vw_fact_metre_v53_financial IS
'Vue financiere V5.3 compatible fact_metre. Phase 025: batiment/niveau exposes en codes metier via dim_batiment/dim_niveau, IDs techniques conserves.';

CREATE OR REPLACE VIEW vw_fact_metre_current AS
SELECT *
FROM vw_fact_metre_v53_financial;

COMMENT ON VIEW vw_fact_metre_current IS
'Source officielle de lecture CAPEX. Phase 025: pointe vers vw_fact_metre_v53_financial avec filtres batiment/niveau semantiques.';

DO $$
DECLARE
    v_bad_batiment BIGINT;
    v_bad_niveau BIGINT;
    v_unexpected_batiment BIGINT;
    v_unexpected_niveau BIGINT;
    v_null_sous_lot_id BIGINT;
    v_distinct_sous_lot_id BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_bad_batiment
    FROM (
        SELECT DISTINCT batiment
        FROM vw_fact_metre_current
        WHERE batiment IS NOT NULL
          AND batiment ~ '^[0-9]+$'
    ) bad;

    IF v_bad_batiment <> 0 THEN
        RAISE EXCEPTION '025 blocked: numeric technical IDs still exposed in batiment';
    END IF;

    SELECT COUNT(*)
    INTO v_unexpected_batiment
    FROM (
        SELECT DISTINCT batiment
        FROM vw_fact_metre_current
        WHERE batiment IS NOT NULL
          AND batiment <> 'BAT_01'
    ) bad;

    IF v_unexpected_batiment <> 0 THEN
        RAISE EXCEPTION '025 blocked: unexpected batiment labels detected; expected BAT_01 only';
    END IF;

    SELECT COUNT(*)
    INTO v_bad_niveau
    FROM (
        SELECT DISTINCT niveau
        FROM vw_fact_metre_current
        WHERE niveau IS NOT NULL
          AND niveau ~ '^[0-9]+$'
    ) bad;

    IF v_bad_niveau <> 0 THEN
        RAISE EXCEPTION '025 blocked: numeric technical IDs still exposed in niveau';
    END IF;

    SELECT COUNT(*)
    INTO v_unexpected_niveau
    FROM (
        SELECT DISTINCT niveau
        FROM vw_fact_metre_current
        WHERE niveau IS NOT NULL
          AND niveau NOT IN ('N1', 'N2', 'N3')
    ) bad;

    IF v_unexpected_niveau <> 0 THEN
        RAISE EXCEPTION '025 blocked: unexpected niveau labels detected; expected N1, N2, N3 only';
    END IF;

    SELECT COUNT(*)
    INTO v_null_sous_lot_id
    FROM vw_fact_metre_current
    WHERE sous_lot_id IS NULL;

    IF v_null_sous_lot_id <> 0 THEN
        RAISE EXCEPTION '025 blocked: expected 0 null sous_lot_id values, got %', v_null_sous_lot_id;
    END IF;

    SELECT COUNT(DISTINCT sous_lot_id)
    INTO v_distinct_sous_lot_id
    FROM vw_fact_metre_current;

    IF v_distinct_sous_lot_id <> 79 THEN
        RAISE EXCEPTION '025 blocked: expected 79 distinct sous_lot_id values, got %', v_distinct_sous_lot_id;
    END IF;
END $$;

-- Validations SQL a executer apres migration:
--
-- SELECT DISTINCT batiment
-- FROM vw_fact_metre_current
-- ORDER BY 1;
--
-- SELECT DISTINCT batiment_code
-- FROM vw_fact_metre_current
-- ORDER BY 1;
--
-- SELECT DISTINCT niveau
-- FROM vw_fact_metre_current
-- ORDER BY 1;
--
-- SELECT DISTINCT niveau_code
-- FROM vw_fact_metre_current
-- ORDER BY 1;
--
-- SELECT DISTINCT
--     batiment_id,
--     batiment
-- FROM vw_fact_metre_current
-- ORDER BY 1;
--
-- SELECT DISTINCT
--     niveau_id,
--     niveau
-- FROM vw_fact_metre_current
-- ORDER BY 1;

COMMIT;
