-- SP2I CAPEX - V5.3 read cutover
-- Migration: 021_v53_read_cutover.sql
--
-- Objectif:
-- - basculer les lectures Analytics / Power BI / Reporting vers V5.3 ;
-- - creer la vue canonique vw_fact_metre_current ;
-- - recreer les vues Power BI principales sur vw_fact_metre_current ;
-- - ne pas supprimer, renommer ou modifier fact_metre ;
-- - ne pas modifier fact_simulation, fact_approvals ou procurement_decisions.
--
-- Les flux d'ecriture restent sur fact_metre:
-- - Pipeline
-- - Simulation
-- - Imports
-- - Synchronisations

BEGIN;

DO $$
DECLARE
    v_rows BIGINT;
    v_articles BIGINT;
    v_lots BIGINT;
    v_bad_rows BIGINT;
    v_capex_local NUMERIC;
    v_capex_import NUMERIC;
    v_capex_optimise NUMERIC;
    v_economie NUMERIC;
BEGIN
    IF to_regclass('vw_fact_metre_v53_financial') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: vw_fact_metre_v53_financial';
    END IF;

    SELECT
        COUNT(*),
        COUNT(DISTINCT article_code),
        COUNT(DISTINCT lot_code),
        COUNT(*) FILTER (
            WHERE NULLIF(TRIM(lot_code), '') IS NULL
               OR NULLIF(TRIM(article_code), '') IS NULL
               OR COALESCE(prix_local_fcfa, 0) <= 0
               OR COALESCE(prix_import_fcfa, 0) <= 0
               OR COALESCE(prix_optimise_fcfa, 0) <= 0
        ),
        COALESCE(SUM(capex_local), 0),
        COALESCE(SUM(capex_import), 0),
        COALESCE(SUM(capex_optimise), 0),
        COALESCE(SUM(economie), 0)
    INTO
        v_rows,
        v_articles,
        v_lots,
        v_bad_rows,
        v_capex_local,
        v_capex_import,
        v_capex_optimise,
        v_economie
    FROM vw_fact_metre_v53_financial;

    IF v_rows <> 4734 THEN
        RAISE EXCEPTION 'V5.3 read cutover blocked: expected 4734 rows, got %', v_rows;
    END IF;

    IF v_articles <> 2524 THEN
        RAISE EXCEPTION 'V5.3 read cutover blocked: expected 2524 articles, got %', v_articles;
    END IF;

    IF v_lots <> 18 THEN
        RAISE EXCEPTION 'V5.3 read cutover blocked: expected 18 lots, got %', v_lots;
    END IF;

    IF v_bad_rows <> 0 THEN
        RAISE EXCEPTION 'V5.3 read cutover blocked: % rows without lot, article or price', v_bad_rows;
    END IF;

    IF v_capex_local <= 0 OR v_capex_import <= 0 OR v_capex_optimise <= 0 OR v_economie <= 0 THEN
        RAISE EXCEPTION
            'V5.3 read cutover blocked: invalid totals local=%, import=%, optimise=%, economie=%',
            v_capex_local, v_capex_import, v_capex_optimise, v_economie;
    END IF;
END $$;

-- Source officielle de lecture.
CREATE OR REPLACE VIEW vw_fact_metre_current AS
SELECT *
FROM vw_fact_metre_v53_financial;

COMMENT ON VIEW vw_fact_metre_current IS
'Source officielle de lecture CAPEX. Phase 021: pointe vers vw_fact_metre_v53_financial. fact_metre reste la table historique et la cible des ecritures.';

-- Vues Power BI / Reporting basculees en lecture sur V5.3.
CREATE OR REPLACE VIEW vw_capex_summary AS
SELECT
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette,
    ROUND(
        CASE WHEN COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0) = 0 THEN 0
             ELSE (SUM(economie)::numeric / NULLIF(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric) * 100
        END,
        2
    ) AS taux_economie,
    COUNT(*) AS nb_lignes,
    SUM(CASE WHEN decision_import = 'IMPORT' THEN 1 ELSE 0 END) AS nb_import
FROM vw_fact_metre_current;

CREATE OR REPLACE VIEW vw_project_kpis AS
SELECT * FROM vw_capex_summary;

CREATE OR REPLACE VIEW vw_dashboard_direction AS
SELECT * FROM vw_capex_summary;

CREATE OR REPLACE VIEW vw_dashboard_import AS
SELECT
    COALESCE(decision_import, 'LOCAL')::varchar AS decision_import,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(COALESCE(capex_import, montant_import, 0)), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette
FROM vw_fact_metre_current
GROUP BY COALESCE(decision_import, 'LOCAL')::varchar;

CREATE OR REPLACE VIEW vw_dashboard_chantier AS
SELECT
    COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE')::varchar AS batiment,
    COALESCE(NULLIF(niveau, ''), 'GLOBAL')::varchar AS niveau,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE')::varchar AS piece,
    COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE')::varchar AS lot,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_expose
FROM vw_fact_metre_current
GROUP BY
    COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE')::varchar,
    COALESCE(NULLIF(niveau, ''), 'GLOBAL')::varchar,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN'),
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE')::varchar,
    COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE')::varchar;

CREATE OR REPLACE VIEW vw_bim_dashboard AS
SELECT
    COALESCE(project_id, projet_id::text, 'PROJET_MPEMBA')::varchar AS projet,
    COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE')::varchar AS batiment,
    COALESCE(NULLIF(niveau, ''), 'GLOBAL')::varchar AS niveau,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE')::varchar AS piece,
    COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE')::varchar AS lot,
    'V53_GENERATED'::varchar AS famille,
    COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(COALESCE(capex_import, montant_import, 0)), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie,
    COUNT(*) AS nb_lignes
FROM vw_fact_metre_current
GROUP BY
    COALESCE(project_id, projet_id::text, 'PROJET_MPEMBA')::varchar,
    COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE')::varchar,
    COALESCE(NULLIF(niveau, ''), 'GLOBAL')::varchar,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN'),
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE')::varchar,
    COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE')::varchar,
    'V53_GENERATED'::varchar,
    COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE');

CREATE OR REPLACE VIEW vw_spatial_dashboard AS
WITH spatial_fact AS (
    SELECT
        COALESCE(project_id, projet_id::text, 'PROJET_MPEMBA')::varchar AS projet,
        COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE')::varchar AS batiment,
        COALESCE(NULLIF(niveau, ''), 'GLOBAL')::varchar AS niveau,
        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece,
        COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE')::varchar AS lot,
        'V53_GENERATED'::varchar AS famille,
        COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
        COALESCE(capex_local, prix_total_ht, 0) AS capex_local,
        COALESCE(capex_import, montant_import, 0) AS capex_import,
        COALESCE(capex_optimise, capex_local, prix_total_ht, 0) AS capex_optimise,
        COALESCE(economie, 0) AS economie
    FROM vw_fact_metre_current
)
SELECT
    f.projet,
    f.batiment,
    f.niveau,
    f.appartement,
    f.piece,
    COALESCE(NULLIF(dp.piece_type, ''), NULLIF(dp.type_piece, ''), 'TECHNIQUE') AS type_piece,
    COALESCE(dp.surface_m2, da.surface_m2) AS surface_m2,
    f.lot,
    f.famille,
    f.article,
    ROUND(COALESCE(SUM(f.capex_local), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(f.capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(f.economie), 0)::numeric, 2) AS economie,
    ROUND(
        CASE WHEN COALESCE(MAX(COALESCE(dp.surface_m2, da.surface_m2)), 0) = 0 THEN 0
             ELSE COALESCE(SUM(f.capex_optimise), 0)::numeric / NULLIF(MAX(COALESCE(dp.surface_m2, da.surface_m2)), 0)::numeric
        END,
        2
    ) AS capex_m2,
    COUNT(*) AS nb_lignes
FROM spatial_fact f
LEFT JOIN dim_appartement da ON da.appartement_id = f.appartement
LEFT JOIN dim_piece dp ON dp.appartement_id = f.appartement
    AND (dp.piece_nom = f.piece OR dp.piece = f.piece OR dp.piece_code = f.piece)
GROUP BY
    f.projet,
    f.batiment,
    f.niveau,
    f.appartement,
    f.piece,
    COALESCE(NULLIF(dp.piece_type, ''), NULLIF(dp.type_piece, ''), 'TECHNIQUE'),
    COALESCE(dp.surface_m2, da.surface_m2),
    f.lot,
    f.famille,
    f.article;

CREATE OR REPLACE VIEW vw_spatial_analytics AS
WITH typed AS (
    SELECT
        s.*,
        CASE s.type_piece
            WHEN 'JOUR' THEN 'ZONE_JOUR'
            WHEN 'NUIT' THEN 'ZONE_NUIT'
            WHEN 'SANITAIRE' THEN 'ZONE_SANITAIRE'
            WHEN 'EXTERIEUR' THEN 'ZONE_EXTERIEURE'
            ELSE 'ZONE_TECHNIQUE'
        END::varchar AS zone
    FROM vw_spatial_dashboard s
)
SELECT
    projet,
    batiment,
    niveau,
    appartement,
    zone,
    piece,
    type_piece,
    surface_m2,
    lot,
    'V53_GENERATED'::varchar AS sous_lot,
    famille,
    article,
    capex_local,
    capex_import,
    capex_optimise,
    economie,
    capex_m2,
    nb_lignes
FROM typed;

CREATE OR REPLACE VIEW vw_cost_intelligence AS
SELECT
    projet,
    batiment,
    niveau,
    appartement,
    zone,
    piece,
    type_piece,
    lot,
    sous_lot,
    famille,
    article,
    surface_m2,
    capex_local,
    capex_import,
    capex_optimise,
    economie,
    capex_m2,
    CASE WHEN COALESCE(capex_optimise, 0) = 0 THEN 0
         ELSE ROUND((economie / NULLIF(capex_optimise, 0))::numeric, 6)
    END AS roi,
    nb_lignes
FROM vw_spatial_analytics;

CREATE OR REPLACE VIEW vw_dim_lot_active AS
SELECT d.*
FROM dim_lot d
WHERE EXISTS (
    SELECT 1
    FROM vw_fact_metre_current f
    WHERE UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
       OR UPPER(TRIM(COALESCE(f.lot_code, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
);

CREATE OR REPLACE VIEW vw_dim_sous_lot_active AS
SELECT d.*
FROM dim_sous_lot_complet d
WHERE EXISTS (
    SELECT 1
    FROM vw_fact_metre_current f
    WHERE UPPER(TRIM(COALESCE(f.sous_lot_code, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
       OR UPPER(TRIM(COALESCE(f.sous_lot, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
);

CREATE OR REPLACE VIEW vw_dim_article_bpu_active AS
SELECT
    DENSE_RANK() OVER (ORDER BY d.article_code)::bigint AS article_bpu_id,
    d.article_code::varchar(150) AS code_article,
    d.lot_code::varchar(255) AS lot,
    d.sous_lot_code::varchar(255) AS sous_lot,
    d.designation::varchar(500) AS designation,
    d.unite::varchar(50) AS unite,
    true::boolean AS is_bim_compatible,
    d.created_at,
    d.updated_at,
    d.article_code::varchar(150) AS article_id,
    d.lot_code::varchar(150) AS lot_id,
    d.sous_lot_code::varchar(150) AS sous_lot_id,
    NULL::varchar(255) AS marque,
    d.is_active
FROM dim_bpu_v53 d
WHERE EXISTS (
    SELECT 1
    FROM vw_fact_metre_current f
    WHERE UPPER(TRIM(COALESCE(f.article_code, ''))) = UPPER(TRIM(COALESCE(d.article_code, '')))
       OR UPPER(TRIM(COALESCE(f.code_article, ''))) = UPPER(TRIM(COALESCE(d.article_code, '')))
);

COMMIT;
