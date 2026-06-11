-- SP2I CAPEX - V5.3 dimensions rebuild
-- Migration: 022_v53_dimensions_rebuild_fixed.sql
--
-- Objectif:
-- - reconstruire les dimensions Power BI actives depuis le referentiel V5.3 ;
-- - supprimer les dependances de lecture active a dim_lot, dim_sous_lot_complet
--   et dim_article_bpu ;
-- - respecter strictement les contrats PostgreSQL existants des vues actives ;
-- - ne pas modifier fact_metre, fact_simulation, fact_approvals,
--   procurement_decisions ni les tables de dimensions historiques.

BEGIN;

DO $$
DECLARE
    v_fact_rows BIGINT;
    v_fact_lots BIGINT;
    v_bpu_articles BIGINT;
BEGIN
    IF to_regclass('vw_fact_metre_current') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: vw_fact_metre_current';
    END IF;

    IF to_regclass('dim_bpu_v53') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: dim_bpu_v53';
    END IF;

    SELECT COUNT(*), COUNT(DISTINCT lot_code)
    INTO v_fact_rows, v_fact_lots
    FROM vw_fact_metre_current;

    IF v_fact_rows <> 4734 THEN
        RAISE EXCEPTION 'V5.3 dimensions rebuild blocked: expected 4734 fact rows, got %', v_fact_rows;
    END IF;

    IF v_fact_lots <> 18 THEN
        RAISE EXCEPTION 'V5.3 dimensions rebuild blocked: expected 18 lots, got %', v_fact_lots;
    END IF;

    SELECT COUNT(DISTINCT article_code)
    INTO v_bpu_articles
    FROM dim_bpu_v53;

    IF v_bpu_articles <> 2524 THEN
        RAISE EXCEPTION 'V5.3 dimensions rebuild blocked: expected 2524 BPU articles, got %', v_bpu_articles;
    END IF;
END $$;

-- Contrat existant:
-- lot_id bigint
-- lot varchar(255)
-- ordre_lot integer
-- created_at timestamptz
-- updated_at timestamptz
-- lot_libelle varchar(100)
-- description varchar(255)
-- is_active boolean
CREATE OR REPLACE VIEW vw_dim_lot_active AS
WITH lots AS (
    SELECT DISTINCT
        NULLIF(TRIM(lot_code), '')::varchar(255) AS lot
    FROM vw_fact_metre_current
    WHERE NULLIF(TRIM(lot_code), '') IS NOT NULL
)
SELECT
    DENSE_RANK() OVER (ORDER BY lot)::bigint AS lot_id,
    lot::varchar(255) AS lot,
    DENSE_RANK() OVER (ORDER BY lot)::integer AS ordre_lot,
    now()::timestamptz AS created_at,
    now()::timestamptz AS updated_at,
    lot::varchar(100) AS lot_libelle,
    lot::varchar(255) AS description,
    true::boolean AS is_active
FROM lots;

COMMENT ON VIEW vw_dim_lot_active IS
'Dimension active des lots reconstruite depuis vw_fact_metre_current V5.3. Ne depend plus de dim_lot historique.';

-- Contrat existant strict:
-- sous_lot_id varchar(150)
-- lot_id varchar(150)
-- description varchar(255)
-- created_at timestamptz
-- updated_at timestamptz
-- sous_lot_libelle varchar(150)
-- sous_lot_ordre integer
-- sous_lot_famille varchar(100)
CREATE OR REPLACE VIEW vw_dim_sous_lot_active AS
WITH sous_lots AS (
    SELECT DISTINCT
        COALESCE(NULLIF(TRIM(sous_lot_code), ''), NULLIF(TRIM(sous_lot), ''), 'V53_GENERATED')::varchar(150) AS sous_lot_id,
        COALESCE(NULLIF(TRIM(lot_code), ''), NULLIF(TRIM(lot), ''), 'NON_RENSEIGNE')::varchar(150) AS lot_id,
        COALESCE(NULLIF(TRIM(sous_lot), ''), NULLIF(TRIM(sous_lot_code), ''), 'V53_GENERATED')::varchar(255) AS description
    FROM vw_fact_metre_current
    WHERE NULLIF(TRIM(lot_code), '') IS NOT NULL
)
SELECT
    sous_lot_id::varchar(150) AS sous_lot_id,
    lot_id::varchar(150) AS lot_id,
    description::varchar(255) AS description,
    now()::timestamptz AS created_at,
    now()::timestamptz AS updated_at,
    LEFT(description, 150)::varchar(150) AS sous_lot_libelle,
    DENSE_RANK() OVER (ORDER BY lot_id, sous_lot_id)::integer AS sous_lot_ordre,
    lot_id::varchar(100) AS sous_lot_famille
FROM sous_lots;

COMMENT ON VIEW vw_dim_sous_lot_active IS
'Dimension active des sous-lots reconstruite depuis vw_fact_metre_current V5.3. Ne depend plus de dim_sous_lot_complet historique.';

-- Contrat existant strict:
-- article_bpu_id bigint
-- code_article varchar(150)
-- lot varchar(255)
-- sous_lot varchar(255)
-- designation varchar(500)
-- unite varchar(50)
-- is_bim_compatible boolean
-- created_at timestamptz
-- updated_at timestamptz
-- article_id varchar(150)
-- lot_id varchar(150)
-- sous_lot_id varchar(150)
-- marque varchar(255)
-- is_active boolean
CREATE OR REPLACE VIEW vw_dim_article_bpu_active AS
SELECT
    DENSE_RANK() OVER (ORDER BY d.article_code)::bigint AS article_bpu_id,
    d.article_code::varchar(150) AS code_article,
    d.lot_code::varchar(255) AS lot,
    d.sous_lot_code::varchar(255) AS sous_lot,
    d.designation::varchar(500) AS designation,
    d.unite::varchar(50) AS unite,
    true::boolean AS is_bim_compatible,
    d.created_at::timestamptz AS created_at,
    d.updated_at::timestamptz AS updated_at,
    d.article_code::varchar(150) AS article_id,
    d.lot_code::varchar(150) AS lot_id,
    d.sous_lot_code::varchar(150) AS sous_lot_id,
    NULL::varchar(255) AS marque,
    d.is_active::boolean AS is_active
FROM dim_bpu_v53 d
WHERE d.is_active IS TRUE;

COMMENT ON VIEW vw_dim_article_bpu_active IS
'Dimension active des articles BPU reconstruite depuis dim_bpu_v53. Ne depend plus de dim_article_bpu historique.';

DO $$
DECLARE
    v_lots BIGINT;
    v_distinct_lots BIGINT;
    v_articles BIGINT;
    v_missing_lots BIGINT;
BEGIN
    SELECT COUNT(*), COUNT(DISTINCT lot)
    INTO v_lots, v_distinct_lots
    FROM vw_dim_lot_active;

    IF v_lots <> 18 OR v_distinct_lots <> 18 THEN
        RAISE EXCEPTION
            'V5.3 dimensions rebuild blocked: expected 18 active lots / 18 distinct lots, got % / %',
            v_lots, v_distinct_lots;
    END IF;

    SELECT COUNT(*)
    INTO v_articles
    FROM vw_dim_article_bpu_active;

    IF v_articles <> 2524 THEN
        RAISE EXCEPTION 'V5.3 dimensions rebuild blocked: expected 2524 active BPU articles, got %', v_articles;
    END IF;

    WITH expected_lots(lot) AS (
        VALUES
            ('LOT_ASC'),
            ('LOT_CAR'),
            ('LOT_CFA'),
            ('LOT_CVC'),
            ('LOT_ELEC'),
            ('LOT_FACADE'),
            ('LOT_FP'),
            ('LOT_GO'),
            ('LOT_INCENDIE'),
            ('LOT_MAC'),
            ('LOT_MENU_EXT'),
            ('LOT_MENU_INT'),
            ('LOT_PLOMB'),
            ('LOT_PNT'),
            ('LOT_SAN'),
            ('LOT_SECURITE'),
            ('LOT_TOIT'),
            ('LOT_VRD')
    )
    SELECT COUNT(*)
    INTO v_missing_lots
    FROM expected_lots e
    LEFT JOIN vw_dim_lot_active a ON a.lot = e.lot
    WHERE a.lot IS NULL;

    IF v_missing_lots <> 0 THEN
        RAISE EXCEPTION 'V5.3 dimensions rebuild blocked: % expected lots are missing', v_missing_lots;
    END IF;
END $$;

COMMIT;
