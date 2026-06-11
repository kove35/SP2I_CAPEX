from __future__ import annotations

from app.config.fact_source import get_fact_source


def build_analytics_views_sql() -> str:
    fact_source = get_fact_source()
    return f"""
DROP VIEW IF EXISTS vw_cost_intelligence CASCADE;
DROP VIEW IF EXISTS vw_dim_article_bpu_active CASCADE;
DROP VIEW IF EXISTS vw_dim_sous_lot_active CASCADE;
DROP VIEW IF EXISTS vw_dim_lot_active CASCADE;
DROP VIEW IF EXISTS vw_spatial_analytics CASCADE;
DROP VIEW IF EXISTS vw_spatial_dashboard CASCADE;
DROP VIEW IF EXISTS vw_bim_dashboard CASCADE;
DROP VIEW IF EXISTS vw_dashboard_chantier CASCADE;
DROP VIEW IF EXISTS vw_dashboard_import CASCADE;
DROP VIEW IF EXISTS vw_dashboard_direction CASCADE;
DROP VIEW IF EXISTS vw_project_kpis CASCADE;
DROP VIEW IF EXISTS vw_logistics_summary CASCADE;
DROP VIEW IF EXISTS vw_procurement_risk CASCADE;
DROP VIEW IF EXISTS vw_import_analysis CASCADE;
DROP VIEW IF EXISTS vw_capex_by_building CASCADE;
DROP VIEW IF EXISTS vw_capex_by_lot CASCADE;
DROP VIEW IF EXISTS vw_capex_summary CASCADE;

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
FROM {fact_source};

CREATE OR REPLACE VIEW vw_capex_by_lot AS
SELECT
    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette,
    COUNT(*) AS nb_lignes
FROM {fact_source}
GROUP BY COALESCE(lot, 'NON_RENSEIGNE');

CREATE OR REPLACE VIEW vw_capex_by_building AS
SELECT
    COALESCE(batiment, 'NON_RENSEIGNE') AS batiment,
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette,
    COUNT(*) AS nb_lignes
FROM {fact_source}
GROUP BY COALESCE(batiment, 'NON_RENSEIGNE');

CREATE OR REPLACE VIEW vw_import_analysis AS
SELECT
    COALESCE(decision_import, 'LOCAL') AS decision_import,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(COALESCE(capex_import, montant_import, 0)), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette
FROM {fact_source}
GROUP BY COALESCE(decision_import, 'LOCAL');

CREATE OR REPLACE VIEW vw_procurement_risk AS
SELECT
    COALESCE(decision_import, 'LOCAL') AS decision_import,
    COALESCE(famille, 'default') AS famille,
    COUNT(*) AS nb_lignes,
    ROUND(AVG(COALESCE(taux_economie, 0))::numeric, 4) AS taux_economie_moyen
FROM {fact_source}
GROUP BY COALESCE(decision_import, 'LOCAL'), COALESCE(famille, 'default');

CREATE OR REPLACE VIEW vw_logistics_summary AS
SELECT
    COALESCE(decision_import, 'LOCAL') AS decision_import,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(COALESCE(capex_import, montant_import, 0)), 0)::numeric, 2) AS cout_import_estime
FROM {fact_source}
GROUP BY COALESCE(decision_import, 'LOCAL');

CREATE OR REPLACE VIEW vw_project_kpis AS
SELECT * FROM vw_capex_summary;

CREATE OR REPLACE VIEW vw_dashboard_direction AS
SELECT * FROM vw_capex_summary;

CREATE OR REPLACE VIEW vw_dashboard_import AS
SELECT * FROM vw_import_analysis;

CREATE OR REPLACE VIEW vw_dashboard_chantier AS
SELECT
    COALESCE(batiment, 'NON_RENSEIGNE') AS batiment,
    COALESCE(niveau, 'GLOBAL') AS niveau,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
    COALESCE(piece, 'NON_RENSEIGNE') AS piece,
    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_expose
FROM {fact_source}
GROUP BY
    COALESCE(batiment, 'NON_RENSEIGNE'),
    COALESCE(niveau, 'GLOBAL'),
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN'),
    COALESCE(piece, 'NON_RENSEIGNE'),
    COALESCE(lot, 'NON_RENSEIGNE');

CREATE OR REPLACE VIEW vw_bim_dashboard AS
SELECT
    COALESCE(project_code, projet_id::text, 'PROJET_MPEMBA') AS projet,
    COALESCE(batiment, 'NON_RENSEIGNE') AS batiment,
    COALESCE(niveau, 'GLOBAL') AS niveau,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
    COALESCE(piece, 'NON_RENSEIGNE') AS piece,
    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
    COALESCE(famille, 'default') AS famille,
    COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(COALESCE(capex_import, montant_import, 0)), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie,
    COUNT(*) AS nb_lignes
FROM {fact_source}
GROUP BY
    COALESCE(project_code, projet_id::text, 'PROJET_MPEMBA'),
    COALESCE(batiment, 'NON_RENSEIGNE'),
    COALESCE(niveau, 'GLOBAL'),
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN'),
    COALESCE(piece, 'NON_RENSEIGNE'),
    COALESCE(lot, 'NON_RENSEIGNE'),
    COALESCE(famille, 'default'),
    COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE');

CREATE OR REPLACE VIEW vw_spatial_dashboard AS
WITH spatial_fact AS (
    SELECT
        COALESCE(project_code, projet_id::text, 'PROJET_MPEMBA') AS projet,
        COALESCE(batiment, 'NON_RENSEIGNE') AS batiment,
        COALESCE(niveau, 'GLOBAL') AS niveau,
        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece,
        COALESCE(lot, 'NON_RENSEIGNE') AS lot,
        COALESCE(famille, 'default') AS famille,
        COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
        COALESCE(capex_local, prix_total_ht, 0) AS capex_local,
        COALESCE(capex_import, montant_import, 0) AS capex_import,
        COALESCE(capex_optimise, capex_local, prix_total_ht, 0) AS capex_optimise,
        COALESCE(economie, 0) AS economie
    FROM {fact_source}
)
SELECT
    f.projet,
    f.batiment,
    f.niveau,
    f.appartement,
    f.piece,
    COALESCE(NULLIF(dp.piece_type, ''), NULLIF(dp.type_piece, ''),
        CASE
            WHEN UPPER(f.piece) LIKE '%%SEJOUR%%' OR UPPER(f.piece) LIKE '%%SALON%%' OR UPPER(f.piece) LIKE '%%CUISINE%%' THEN 'JOUR'
            WHEN UPPER(f.piece) LIKE '%%CHAMBRE%%' OR UPPER(f.piece) LIKE '%%DRESSING%%' THEN 'NUIT'
            WHEN UPPER(f.piece) LIKE '%%SDE%%' OR UPPER(f.piece) LIKE '%%SDB%%' OR UPPER(f.piece) LIKE '%%WC%%' THEN 'SANITAIRE'
            WHEN UPPER(f.piece) LIKE '%%COULOIR%%' OR UPPER(f.piece) LIKE '%%ESCALIER%%' THEN 'CIRCULATION'
            WHEN UPPER(f.piece) LIKE '%%BALCON%%' OR UPPER(f.piece) LIKE '%%TERRASSE%%' THEN 'EXTERIEUR'
            ELSE 'AUTRE'
        END
    ) AS type_piece,
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
LEFT JOIN dim_piece dp ON dp.appartement_id = f.appartement AND (dp.piece_nom = f.piece OR dp.piece = f.piece OR dp.piece_code = f.piece)
GROUP BY
    f.projet,
    f.batiment,
    f.niveau,
    f.appartement,
    f.piece,
    COALESCE(NULLIF(dp.piece_type, ''), NULLIF(dp.type_piece, ''),
        CASE
            WHEN UPPER(f.piece) LIKE '%%SEJOUR%%' OR UPPER(f.piece) LIKE '%%SALON%%' OR UPPER(f.piece) LIKE '%%CUISINE%%' THEN 'JOUR'
            WHEN UPPER(f.piece) LIKE '%%CHAMBRE%%' OR UPPER(f.piece) LIKE '%%DRESSING%%' THEN 'NUIT'
            WHEN UPPER(f.piece) LIKE '%%SDE%%' OR UPPER(f.piece) LIKE '%%SDB%%' OR UPPER(f.piece) LIKE '%%WC%%' THEN 'SANITAIRE'
            WHEN UPPER(f.piece) LIKE '%%COULOIR%%' OR UPPER(f.piece) LIKE '%%ESCALIER%%' THEN 'CIRCULATION'
            WHEN UPPER(f.piece) LIKE '%%BALCON%%' OR UPPER(f.piece) LIKE '%%TERRASSE%%' THEN 'EXTERIEUR'
            ELSE 'AUTRE'
        END
    ),
    COALESCE(dp.surface_m2, da.surface_m2),
    f.lot,
    f.famille,
    f.article;

CREATE OR REPLACE VIEW vw_spatial_analytics AS
WITH spatial_fact AS (
    SELECT
        COALESCE(project_code, projet_id::text, 'PROJET_MPEMBA') AS projet,
        COALESCE(batiment, 'NON_RENSEIGNE') AS batiment,
        COALESCE(niveau, 'GLOBAL') AS niveau,
        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece,
        COALESCE(lot, 'NON_RENSEIGNE') AS lot,
        COALESCE(sous_lot, 'NON_RENSEIGNE') AS sous_lot,
        COALESCE(famille, 'default') AS famille,
        COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
        COALESCE(capex_local, prix_total_ht, 0) AS capex_local,
        COALESCE(capex_import, montant_import, 0) AS capex_import,
        COALESCE(capex_optimise, capex_local, prix_total_ht, 0) AS capex_optimise,
        COALESCE(economie, 0) AS economie
    FROM {fact_source}
),
typed AS (
    SELECT
        f.*,
        COALESCE(NULLIF(dp.piece_type, ''), NULLIF(dp.type_piece, ''),
            CASE
                WHEN UPPER(f.piece) LIKE '%%SEJOUR%%' OR UPPER(f.piece) LIKE '%%SALON%%' OR UPPER(f.piece) LIKE '%%CUISINE%%' THEN 'JOUR'
                WHEN UPPER(f.piece) LIKE '%%CHAMBRE%%' OR UPPER(f.piece) LIKE '%%DRESSING%%' THEN 'NUIT'
                WHEN UPPER(f.piece) LIKE '%%SDE%%' OR UPPER(f.piece) LIKE '%%SDB%%' OR UPPER(f.piece) LIKE '%%WC%%' THEN 'SANITAIRE'
                WHEN UPPER(f.piece) LIKE '%%COULOIR%%' OR UPPER(f.piece) LIKE '%%ESCALIER%%' THEN 'CIRCULATION'
                WHEN UPPER(f.piece) LIKE '%%BALCON%%' OR UPPER(f.piece) LIKE '%%TERRASSE%%' THEN 'EXTERIEUR'
                ELSE 'TECHNIQUE'
            END
        ) AS type_piece,
        COALESCE(dp.surface_m2, da.surface_m2, db.surface_totale_m2) AS surface_m2
    FROM spatial_fact f
    LEFT JOIN dim_batiment db ON db.batiment = f.batiment OR db.batiment_code = f.batiment
    LEFT JOIN dim_appartement da ON da.appartement_id = f.appartement
    LEFT JOIN dim_piece dp ON dp.appartement_id = f.appartement AND (dp.piece_nom = f.piece OR dp.piece = f.piece OR dp.piece_code = f.piece)
)
SELECT
    t.projet,
    t.batiment,
    t.niveau,
    t.appartement,
    COALESCE(dz.zone_code,
        CASE t.type_piece
            WHEN 'JOUR' THEN 'ZONE_JOUR'
            WHEN 'NUIT' THEN 'ZONE_NUIT'
            WHEN 'SANITAIRE' THEN 'ZONE_SANITAIRE'
            WHEN 'CIRCULATION' THEN 'ZONE_CIRCULATION'
            WHEN 'EXTERIEUR' THEN 'ZONE_EXTERIEURE'
            ELSE 'ZONE_TECHNIQUE'
        END
    ) AS zone,
    t.piece,
    t.type_piece,
    t.surface_m2,
    t.lot,
    t.sous_lot,
    t.famille,
    t.article,
    ROUND(COALESCE(SUM(t.capex_local), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(t.capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(t.capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(t.economie), 0)::numeric, 2) AS economie,
    ROUND(
        CASE WHEN COALESCE(MAX(t.surface_m2), 0) = 0 THEN 0
             ELSE COALESCE(SUM(t.capex_optimise), 0)::numeric / NULLIF(MAX(t.surface_m2), 0)::numeric
        END,
        2
    ) AS capex_m2,
    COUNT(*) AS nb_lignes
FROM typed t
LEFT JOIN dim_zone dz ON dz.type_zone = t.type_piece OR dz.zone_code = t.type_piece
GROUP BY
    t.projet,
    t.batiment,
    t.niveau,
    t.appartement,
    COALESCE(dz.zone_code,
        CASE t.type_piece
            WHEN 'JOUR' THEN 'ZONE_JOUR'
            WHEN 'NUIT' THEN 'ZONE_NUIT'
            WHEN 'SANITAIRE' THEN 'ZONE_SANITAIRE'
            WHEN 'CIRCULATION' THEN 'ZONE_CIRCULATION'
            WHEN 'EXTERIEUR' THEN 'ZONE_EXTERIEURE'
            ELSE 'ZONE_TECHNIQUE'
        END
    ),
    t.piece,
    t.type_piece,
    t.surface_m2,
    t.lot,
    t.sous_lot,
    t.famille,
    t.article;

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
    FROM {fact_source} f
    WHERE UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
       OR UPPER(TRIM(COALESCE(CAST(f.lot_id AS text), ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
);

CREATE OR REPLACE VIEW vw_dim_sous_lot_active AS
SELECT d.*
FROM dim_sous_lot_complet d
WHERE EXISTS (
    SELECT 1
    FROM {fact_source} f
    WHERE UPPER(TRIM(COALESCE(f.sous_lot_id, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
       OR UPPER(TRIM(COALESCE(f.sous_lot, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
);

CREATE OR REPLACE VIEW vw_dim_article_bpu_active AS
SELECT d.*
FROM dim_article_bpu d
WHERE EXISTS (
    SELECT 1
    FROM {fact_source} f
    WHERE UPPER(TRIM(COALESCE(f.code_article, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
       OR UPPER(TRIM(COALESCE(f.article_id, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
       OR UPPER(TRIM(COALESCE(f.article_id, ''))) = UPPER(TRIM(COALESCE(d.article_id, '')))
);
"""


ANALYTICS_VIEWS_SQL = build_analytics_views_sql()
