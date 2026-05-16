from __future__ import annotations

ANALYTICS_VIEWS_SQL = """
CREATE OR REPLACE VIEW vw_capex_summary AS
SELECT
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette,
    ROUND(
        CASE WHEN COALESCE(SUM(capex_local), 0) = 0 THEN 0
             ELSE (SUM(economie)::numeric / NULLIF(SUM(capex_local), 0)::numeric) * 100
        END,
        2
    ) AS taux_economie,
    COUNT(*) AS nb_lignes,
    SUM(CASE WHEN decision_import = 'IMPORT' THEN 1 ELSE 0 END) AS nb_import
FROM fact_metre;

CREATE OR REPLACE VIEW vw_capex_by_lot AS
SELECT
    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette,
    COUNT(*) AS nb_lignes
FROM fact_metre
GROUP BY COALESCE(lot, 'NON_RENSEIGNE');

CREATE OR REPLACE VIEW vw_capex_by_building AS
SELECT
    COALESCE(batiment, 'NON_RENSEIGNE') AS batiment,
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette,
    COUNT(*) AS nb_lignes
FROM fact_metre
GROUP BY COALESCE(batiment, 'NON_RENSEIGNE');

CREATE OR REPLACE VIEW vw_import_analysis AS
SELECT
    COALESCE(decision_import, 'LOCAL') AS decision_import,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(capex_local), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette
FROM fact_metre
GROUP BY COALESCE(decision_import, 'LOCAL');

CREATE OR REPLACE VIEW vw_procurement_risk AS
SELECT
    COALESCE(decision_import, 'LOCAL') AS decision_import,
    COALESCE(famille, 'default') AS famille,
    COUNT(*) AS nb_lignes,
    ROUND(AVG(COALESCE(taux_economie, 0))::numeric, 4) AS taux_economie_moyen
FROM fact_metre
GROUP BY COALESCE(decision_import, 'LOCAL'), COALESCE(famille, 'default');

CREATE OR REPLACE VIEW vw_logistics_summary AS
SELECT
    COALESCE(decision_import, 'LOCAL') AS decision_import,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(capex_import), 0)::numeric, 2) AS cout_import_estime
FROM fact_metre
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
    COALESCE(lot, 'NON_RENSEIGNE') AS lot,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(capex_optimise), 0)::numeric, 2) AS capex_expose
FROM fact_metre
GROUP BY COALESCE(batiment, 'NON_RENSEIGNE'), COALESCE(niveau, 'GLOBAL'), COALESCE(lot, 'NON_RENSEIGNE');
"""
