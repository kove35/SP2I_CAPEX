-- SP2I CAPEX - V5.3 full cutover plan
-- Migration plan: 020_v53_cutover_plan.sql
--
-- Objectif:
-- - preparer la bascule logique fact_metre -> vw_fact_metre_v53_financial ;
-- - valider les prerequis V5.3: 4734 lignes, 2524 articles, 18 lots ;
-- - recreer les vues Power BI principales sur la source financiere V5.3 ;
-- - conserver un rollback simple vers fact_metre historique.
--
-- IMPORTANT:
-- - Ce script est un plan de cutover a executer uniquement en fenetre controlee.
-- - Il ne renomme pas fact_metre et ne cree pas de vue nommee fact_metre.
-- - Le remplacement physique de fact_metre par une vue casserait les flux d'ecriture
--   existants: upload/sync, ServicePipeline, RepositorySimulation.insert_fact_metre.
-- - La bascule backend doit donc etre faite dans le code ou via vues Power BI/API,
--   pas par shadowing direct de la table fact_metre.

BEGIN;

-- ============================================================================
-- 1. VALIDATIONS BLOQUANTES DES PREREQUIS V5.3
-- ============================================================================

DO $$
DECLARE
    v_master_rows BIGINT;
    v_financial_rows BIGINT;
    v_articles BIGINT;
    v_lots BIGINT;
    v_unpriced BIGINT;
BEGIN
    IF to_regclass('vw_sp2i_generated_dqe_master') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: vw_sp2i_generated_dqe_master';
    END IF;

    IF to_regclass('dim_bpu_v53') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: dim_bpu_v53';
    END IF;

    IF to_regclass('vw_bpu_v53_priced') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: vw_bpu_v53_priced';
    END IF;

    IF to_regclass('vw_fact_metre_v53_financial') IS NULL THEN
        RAISE EXCEPTION 'Missing prerequisite: vw_fact_metre_v53_financial';
    END IF;

    SELECT COUNT(*) INTO v_master_rows
    FROM vw_sp2i_generated_dqe_master;

    SELECT
        COUNT(*),
        COUNT(DISTINCT article_code),
        COUNT(DISTINCT lot_code),
        COUNT(*) FILTER (
            WHERE prix_local_fcfa <= 0
               OR prix_import_fcfa <= 0
               OR prix_optimise_fcfa <= 0
               OR capex_local <= 0
               OR capex_import <= 0
               OR capex_optimise <= 0
        )
    INTO v_financial_rows, v_articles, v_lots, v_unpriced
    FROM vw_fact_metre_v53_financial;

    IF v_master_rows <> 4734 THEN
        RAISE EXCEPTION 'Invalid V5.3 master row count: expected 4734, got %', v_master_rows;
    END IF;

    IF v_financial_rows <> 4734 THEN
        RAISE EXCEPTION 'Invalid V5.3 financial row count: expected 4734, got %', v_financial_rows;
    END IF;

    IF v_articles <> 2524 THEN
        RAISE EXCEPTION 'Invalid V5.3 article count: expected 2524, got %', v_articles;
    END IF;

    IF v_lots <> 18 THEN
        RAISE EXCEPTION 'Invalid V5.3 lot count: expected 18, got %', v_lots;
    END IF;

    IF v_unpriced <> 0 THEN
        RAISE EXCEPTION 'Invalid V5.3 financial coverage: % unpriced or zero-capex rows', v_unpriced;
    END IF;

    RAISE NOTICE 'V5.3 cutover prerequisites OK: rows=%, articles=%, lots=%',
        v_financial_rows, v_articles, v_lots;
END $$;

-- ============================================================================
-- 2. SOURCE CANONIQUE DE LECTURE
-- ============================================================================

CREATE OR REPLACE VIEW vw_fact_metre_current AS
SELECT *
FROM vw_fact_metre_v53_financial;

COMMENT ON VIEW vw_fact_metre_current IS
'Source canonique de lecture CAPEX. Cutover V5.3: pointe vers vw_fact_metre_v53_financial.';

-- ============================================================================
-- 3. VUES POWER BI BASCULEES SUR V5.3
-- ============================================================================

CREATE OR REPLACE VIEW vw_capex_summary AS
SELECT
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette,
    ROUND(
        CASE WHEN COALESCE(SUM(capex_local), 0) = 0 THEN 0
             ELSE SUM(economie)::numeric / NULLIF(SUM(capex_local), 0)::numeric * 100
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
    COALESCE(decision_import, 'LOCAL') AS decision_import,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette
FROM vw_fact_metre_current
GROUP BY COALESCE(decision_import, 'LOCAL');

CREATE OR REPLACE VIEW vw_dashboard_chantier AS
SELECT
    COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE') AS batiment,
    COALESCE(NULLIF(niveau, ''), 'GLOBAL') AS niveau,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece,
    COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE') AS lot,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_expose
FROM vw_fact_metre_current
GROUP BY
    COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE'),
    COALESCE(NULLIF(niveau, ''), 'GLOBAL'),
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN'),
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE'),
    COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE');

CREATE OR REPLACE VIEW vw_bim_dashboard AS
SELECT
    COALESCE(project_id, projet_id::text, 'PROJET_MPEMBA') AS projet,
    COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE') AS batiment,
    COALESCE(NULLIF(niveau, ''), 'GLOBAL') AS niveau,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece,
    COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE') AS lot,
    COALESCE(NULLIF(famille, ''), 'V53_GENERATED') AS famille,
    COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie,
    COUNT(*) AS nb_lignes
FROM vw_fact_metre_current
GROUP BY
    COALESCE(project_id, projet_id::text, 'PROJET_MPEMBA'),
    COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE'),
    COALESCE(NULLIF(niveau, ''), 'GLOBAL'),
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN'),
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE'),
    COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE'),
    COALESCE(NULLIF(famille, ''), 'V53_GENERATED'),
    COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE');

-- Spatial and cost intelligence views keep their dimensional joins but switch
-- their financial source to vw_fact_metre_current.
CREATE OR REPLACE VIEW vw_spatial_dashboard AS
WITH spatial_fact AS (
    SELECT
        COALESCE(project_id, projet_id::text, 'PROJET_MPEMBA') AS projet,
        COALESCE(NULLIF(batiment, ''), 'NON_RENSEIGNE') AS batiment,
        COALESCE(NULLIF(niveau, ''), 'GLOBAL') AS niveau,
        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece,
        COALESCE(NULLIF(lot, ''), NULLIF(lot_code, ''), 'NON_RENSEIGNE') AS lot,
        COALESCE(NULLIF(famille, ''), 'V53_GENERATED') AS famille,
        COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
        capex_local,
        capex_import,
        capex_optimise,
        economie
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
             ELSE COALESCE(SUM(f.capex_optimise), 0)::numeric
                  / NULLIF(MAX(COALESCE(dp.surface_m2, da.surface_m2)), 0)::numeric
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
SELECT
    projet,
    batiment,
    niveau,
    appartement,
    CASE type_piece
        WHEN 'JOUR' THEN 'ZONE_JOUR'
        WHEN 'NUIT' THEN 'ZONE_NUIT'
        WHEN 'SANITAIRE' THEN 'ZONE_SANITAIRE'
        WHEN 'EXTERIEUR' THEN 'ZONE_EXTERIEURE'
        ELSE 'ZONE_TECHNIQUE'
    END AS zone,
    piece,
    type_piece,
    surface_m2,
    lot,
    'V53_GENERATED'::text AS sous_lot,
    famille,
    article,
    capex_local,
    capex_import,
    capex_optimise,
    economie,
    capex_m2,
    nb_lignes
FROM vw_spatial_dashboard;

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

-- Active dimensions switched to V5.3 financial source.
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
SELECT d.*
FROM dim_bpu_v53 d
WHERE EXISTS (
    SELECT 1
    FROM vw_fact_metre_current f
    WHERE UPPER(TRIM(COALESCE(f.article_code, ''))) = UPPER(TRIM(COALESCE(d.article_code, '')))
);

-- ============================================================================
-- 4. VALIDATIONS POST-CUTOVER
-- ============================================================================

DO $$
DECLARE
    v_rows BIGINT;
    v_articles BIGINT;
    v_lots BIGINT;
    v_capex NUMERIC;
BEGIN
    SELECT
        COUNT(*),
        COUNT(DISTINCT article_code),
        COUNT(DISTINCT lot_code),
        COALESCE(SUM(capex_local), 0)
    INTO v_rows, v_articles, v_lots, v_capex
    FROM vw_fact_metre_current;

    IF v_rows <> 4734 OR v_articles <> 2524 OR v_lots <> 18 OR v_capex <= 0 THEN
        RAISE EXCEPTION 'V5.3 cutover validation failed: rows=%, articles=%, lots=%, capex=%',
            v_rows, v_articles, v_lots, v_capex;
    END IF;

    RAISE NOTICE 'V5.3 cutover validation OK: rows=%, articles=%, lots=%, capex_local=%',
        v_rows, v_articles, v_lots, v_capex;
END $$;

COMMIT;

-- ============================================================================
-- 5. ROLLBACK COMPLET
-- ============================================================================
--
-- Le rollback de ce plan consiste a reexecuter la migration Power BI historique
-- sql/powerbi/001_powerbi_views.sql, qui recree:
-- - vw_capex_summary
-- - vw_project_kpis
-- - vw_dashboard_direction
-- - vw_dashboard_import
-- - vw_dashboard_chantier
-- - vw_bim_dashboard
-- - vw_spatial_dashboard
-- - vw_spatial_analytics
-- - vw_cost_intelligence
-- - vw_dim_lot_active
-- - vw_dim_sous_lot_active
-- - vw_dim_article_bpu_active
--
-- Puis executer:
--
-- BEGIN;
-- DROP VIEW IF EXISTS vw_fact_metre_current;
-- COMMIT;
