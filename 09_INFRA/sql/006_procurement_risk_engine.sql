/*
SP2I CAPEX - Phase 4 Procurement & Risk Engine

Objectif :
- enrichir les dimensions fournisseur et pays ;
- historiser les scores procurement dans fact_simulation ;
- exposer des vues Power BI dediees au risque, aux fournisseurs et a la
  complexite import Afrique <-> Chine.

Le script est idempotent.
*/

BEGIN;

ALTER TABLE dim_supplier
    ADD COLUMN IF NOT EXISTS supplier_type VARCHAR(100) NOT NULL DEFAULT 'IMPORT',
    ADD COLUMN IF NOT EXISTS incoterm VARCHAR(20) NOT NULL DEFAULT 'FOB',
    ADD COLUMN IF NOT EXISTS avg_delay_days DOUBLE PRECISION NOT NULL DEFAULT 45,
    ADD COLUMN IF NOT EXISTS defect_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS payment_terms VARCHAR(150) NOT NULL DEFAULT '30/70',
    ADD COLUMN IF NOT EXISTS reliability_score DOUBLE PRECISION NOT NULL DEFAULT 70,
    ADD COLUMN IF NOT EXISTS minimum_order_quantity DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS country_origin VARCHAR(150) NOT NULL DEFAULT 'NON_RENSEIGNE';

ALTER TABLE dim_country
    ADD COLUMN IF NOT EXISTS port_risk DOUBLE PRECISION NOT NULL DEFAULT 50,
    ADD COLUMN IF NOT EXISTS political_risk DOUBLE PRECISION NOT NULL DEFAULT 35,
    ADD COLUMN IF NOT EXISTS import_complexity DOUBLE PRECISION NOT NULL DEFAULT 45,
    ADD COLUMN IF NOT EXISTS average_customs_delay DOUBLE PRECISION NOT NULL DEFAULT 7;

UPDATE dim_country
SET
    port_risk = CASE
        WHEN country_name = 'Chine' THEN 55
        WHEN country_name = 'Congo' THEN 40
        WHEN country_name = 'France' THEN 20
        ELSE port_risk
    END,
    political_risk = CASE
        WHEN country_name = 'Chine' THEN 35
        WHEN country_name = 'Congo' THEN 35
        WHEN country_name = 'France' THEN 15
        ELSE political_risk
    END,
    import_complexity = CASE
        WHEN country_name = 'Chine' THEN 65
        WHEN country_name = 'Congo' THEN 25
        WHEN country_name = 'France' THEN 35
        ELSE import_complexity
    END,
    average_customs_delay = CASE
        WHEN country_name = 'Chine' THEN 7
        WHEN country_name = 'Congo' THEN 2
        WHEN country_name = 'France' THEN 4
        ELSE average_customs_delay
    END;

ALTER TABLE fact_simulation
    ADD COLUMN IF NOT EXISTS global_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS lead_time_days DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS cashflow_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS moq_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS complexity_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS procurement_reason JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS ix_fact_simulation_global_risk_score ON fact_simulation(global_risk_score);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_lead_time_days ON fact_simulation(lead_time_days);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_cashflow_score ON fact_simulation(cashflow_score);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_complexity_score ON fact_simulation(complexity_score);

DROP VIEW IF EXISTS
    v_procurement_summary,
    v_risk_analysis,
    v_supplier_ranking,
    v_country_risk,
    v_import_complexity;

CREATE OR REPLACE VIEW v_procurement_summary AS
SELECT
    s.scenario_id,
    s.scenario_nom,
    COUNT(*) AS nombre_lignes,
    ROUND(AVG(f.global_risk_score)::NUMERIC, 2) AS global_risk_score_moyen,
    ROUND(AVG(f.lead_time_days)::NUMERIC, 2) AS lead_time_moyen,
    ROUND(AVG(f.cashflow_score)::NUMERIC, 2) AS cashflow_score_moyen,
    ROUND(AVG(f.moq_risk_score)::NUMERIC, 2) AS moq_risk_score_moyen,
    ROUND(AVG(f.complexity_score)::NUMERIC, 2) AS complexity_score_moyen,
    ROUND(COALESCE(SUM(f.economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total
FROM fact_simulation f
JOIN dim_scenario s ON s.scenario_id = f.scenario_id
GROUP BY s.scenario_id, s.scenario_nom;

CREATE OR REPLACE VIEW v_risk_analysis AS
SELECT
    s.scenario_id,
    s.scenario_nom,
    CASE
        WHEN f.global_risk_score < 30 THEN 'LOW'
        WHEN f.global_risk_score < 60 THEN 'MEDIUM'
        WHEN f.global_risk_score < 80 THEN 'HIGH'
        ELSE 'CRITICAL'
    END AS risk_level,
    COUNT(*) AS nombre_lignes,
    ROUND(AVG(f.global_risk_score)::NUMERIC, 2) AS global_risk_score_moyen,
    ROUND(AVG(f.risk_score)::NUMERIC, 2) AS decision_risk_score_moyen,
    ROUND(AVG(f.lead_time_days)::NUMERIC, 2) AS lead_time_moyen
FROM fact_simulation f
JOIN dim_scenario s ON s.scenario_id = f.scenario_id
GROUP BY s.scenario_id, s.scenario_nom, risk_level;

CREATE OR REPLACE VIEW v_supplier_ranking AS
SELECT
    sp.supplier_id,
    sp.supplier_name,
    sp.country_origin,
    sp.supplier_type,
    sp.incoterm,
    COUNT(f.simulation_line_id) AS nombre_lignes,
    ROUND(AVG(f.global_risk_score)::NUMERIC, 2) AS global_risk_score_moyen,
    ROUND(AVG(f.decision_score)::NUMERIC, 2) AS decision_score_moyen,
    ROUND(AVG(sp.reliability_score)::NUMERIC, 2) AS reliability_score,
    ROUND(AVG(sp.quality_score)::NUMERIC, 2) AS quality_score,
    ROUND(AVG(sp.defect_rate)::NUMERIC, 2) AS defect_rate
FROM dim_supplier sp
LEFT JOIN fact_simulation f ON f.supplier_id = sp.supplier_id
GROUP BY sp.supplier_id, sp.supplier_name, sp.country_origin, sp.supplier_type, sp.incoterm;

CREATE OR REPLACE VIEW v_country_risk AS
SELECT
    c.country_id,
    c.country_name,
    COUNT(f.simulation_line_id) AS nombre_lignes,
    ROUND(AVG(f.global_risk_score)::NUMERIC, 2) AS global_risk_score_moyen,
    ROUND(AVG(c.customs_risk)::NUMERIC, 2) AS customs_risk,
    ROUND(AVG(c.port_risk)::NUMERIC, 2) AS port_risk,
    ROUND(AVG(c.logistics_risk)::NUMERIC, 2) AS logistics_risk,
    ROUND(AVG(c.currency_risk)::NUMERIC, 2) AS currency_risk,
    ROUND(AVG(c.political_risk)::NUMERIC, 2) AS political_risk,
    ROUND(AVG(c.average_customs_delay)::NUMERIC, 2) AS average_customs_delay
FROM dim_country c
LEFT JOIN fact_simulation f ON f.country_id = c.country_id
GROUP BY c.country_id, c.country_name;

CREATE OR REPLACE VIEW v_import_complexity AS
SELECT
    s.scenario_id,
    s.scenario_nom,
    CASE
        WHEN f.complexity_score < 30 THEN 'LOW'
        WHEN f.complexity_score < 60 THEN 'MEDIUM'
        WHEN f.complexity_score < 80 THEN 'HIGH'
        ELSE 'CRITICAL'
    END AS complexity_level,
    COUNT(*) AS nombre_lignes,
    ROUND(AVG(f.complexity_score)::NUMERIC, 2) AS complexity_score_moyen,
    ROUND(AVG(f.moq_risk_score)::NUMERIC, 2) AS moq_risk_score_moyen,
    ROUND(AVG(f.lead_time_days)::NUMERIC, 2) AS lead_time_moyen
FROM fact_simulation f
JOIN dim_scenario s ON s.scenario_id = f.scenario_id
GROUP BY s.scenario_id, s.scenario_nom, complexity_level;

COMMIT;
