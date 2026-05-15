/*
SP2I CAPEX - Historisation des scenarios de simulation

Objectif :
- conserver le moteur temps reel existant ;
- ajouter une couche d'historisation PostgreSQL ;
- permettre Power BI de comparer plusieurs scenarios CAPEX.

Ce script est idempotent et ne modifie pas la table fact_metre existante.
*/

BEGIN;

CREATE TABLE IF NOT EXISTS dim_scenario (
    scenario_id UUID PRIMARY KEY,
    projet_id BIGINT NULL REFERENCES dim_projet(projet_id),
    scenario_nom VARCHAR(255) NOT NULL,
    scenario_type VARCHAR(100) NOT NULL DEFAULT 'BASELINE',
    description TEXT NOT NULL DEFAULT '',
    parameters_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_baseline BOOLEAN NOT NULL DEFAULT FALSE,
    created_by VARCHAR(150) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_dim_scenario_projet_id ON dim_scenario(projet_id);
CREATE INDEX IF NOT EXISTS ix_dim_scenario_type ON dim_scenario(scenario_type);
CREATE INDEX IF NOT EXISTS ix_dim_scenario_created_at ON dim_scenario(created_at);

CREATE TABLE IF NOT EXISTS simulation_run (
    run_id UUID PRIMARY KEY,
    scenario_id UUID NOT NULL REFERENCES dim_scenario(scenario_id) ON DELETE CASCADE,
    projet_id BIGINT NULL REFERENCES dim_projet(projet_id),
    source_file VARCHAR(500) NOT NULL DEFAULT '',
    source_type VARCHAR(100) NOT NULL DEFAULT 'API',
    rows_in INTEGER NOT NULL DEFAULT 0,
    rows_out INTEGER NOT NULL DEFAULT 0,
    rows_rejected INTEGER NOT NULL DEFAULT 0,
    warnings_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    errors_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'RUNNING'
);

CREATE INDEX IF NOT EXISTS ix_simulation_run_scenario_id ON simulation_run(scenario_id);
CREATE INDEX IF NOT EXISTS ix_simulation_run_status ON simulation_run(status);
CREATE INDEX IF NOT EXISTS ix_simulation_run_started_at ON simulation_run(started_at);

CREATE TABLE IF NOT EXISTS fact_simulation (
    simulation_line_id BIGSERIAL PRIMARY KEY,
    simulation_id UUID NOT NULL,
    scenario_id UUID NOT NULL REFERENCES dim_scenario(scenario_id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES simulation_run(run_id) ON DELETE CASCADE,
    projet_id BIGINT NULL REFERENCES dim_projet(projet_id),
    id_ligne VARCHAR(100) NOT NULL DEFAULT '',
    lot_id BIGINT NULL REFERENCES dim_lot(lot_id),
    famille_id BIGINT NULL REFERENCES dim_famille(famille_id),
    niveau_id BIGINT NULL REFERENCES dim_niveau(niveau_id),
    batiment_id BIGINT NULL REFERENCES dim_batiment(batiment_id),
    designation VARCHAR(500) NOT NULL DEFAULT '',
    quantite DOUBLE PRECISION NOT NULL DEFAULT 0,
    pu_local DOUBLE PRECISION NOT NULL DEFAULT 0,
    pu_import DOUBLE PRECISION NOT NULL DEFAULT 0,
    capex_local DOUBLE PRECISION NOT NULL DEFAULT 0,
    capex_import DOUBLE PRECISION NOT NULL DEFAULT 0,
    capex_optimise DOUBLE PRECISION NOT NULL DEFAULT 0,
    economie DOUBLE PRECISION NOT NULL DEFAULT 0,
    taux_economie DOUBLE PRECISION NOT NULL DEFAULT 0,
    decision_import VARCHAR(50) NOT NULL DEFAULT 'LOCAL',
    score_confiance DOUBLE PRECISION NOT NULL DEFAULT 0,
    statut_qualite VARCHAR(150) NOT NULL DEFAULT 'OK',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fact_simulation_simulation_id ON fact_simulation(simulation_id);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_scenario_id ON fact_simulation(scenario_id);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_run_id ON fact_simulation(run_id);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_projet_id ON fact_simulation(projet_id);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_lot_id ON fact_simulation(lot_id);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_famille_id ON fact_simulation(famille_id);
CREATE INDEX IF NOT EXISTS ix_fact_simulation_decision_import ON fact_simulation(decision_import);

DROP VIEW IF EXISTS
    v_kpi_scenario,
    v_compare_scenarios,
    v_scenario_evolution;

CREATE OR REPLACE VIEW v_kpi_scenario AS
SELECT
    s.scenario_id,
    s.scenario_nom,
    s.scenario_type,
    s.is_baseline,
    COUNT(f.simulation_line_id) AS nombre_lignes,
    ROUND(COALESCE(SUM(f.capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(f.capex_import), 0)::NUMERIC, 2) AS capex_import_total,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(f.economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(
        CASE
            WHEN COALESCE(SUM(f.capex_local), 0) = 0 THEN 0
            ELSE (COALESCE(SUM(f.economie), 0)::NUMERIC / NULLIF(SUM(f.capex_local), 0)::NUMERIC) * 100
        END,
        2
    ) AS taux_economie_global,
    COUNT(*) FILTER (WHERE f.decision_import = 'IMPORT') AS nb_import,
    COUNT(*) FILTER (WHERE f.decision_import = 'LOCAL') AS nb_local,
    MAX(f.created_at) AS derniere_simulation
FROM dim_scenario s
LEFT JOIN fact_simulation f ON f.scenario_id = s.scenario_id
GROUP BY s.scenario_id, s.scenario_nom, s.scenario_type, s.is_baseline;

CREATE OR REPLACE VIEW v_compare_scenarios AS
SELECT
    s.scenario_id,
    s.scenario_nom,
    s.scenario_type,
    l.lot,
    df.famille,
    COUNT(f.simulation_line_id) AS nombre_lignes,
    ROUND(COALESCE(SUM(f.capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(f.economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(
        CASE
            WHEN COALESCE(SUM(f.capex_local), 0) = 0 THEN 0
            ELSE (COALESCE(SUM(f.economie), 0)::NUMERIC / NULLIF(SUM(f.capex_local), 0)::NUMERIC) * 100
        END,
        2
    ) AS taux_economie
FROM fact_simulation f
JOIN dim_scenario s ON s.scenario_id = f.scenario_id
LEFT JOIN dim_lot l ON l.lot_id = f.lot_id
LEFT JOIN dim_famille df ON df.famille_id = f.famille_id
GROUP BY s.scenario_id, s.scenario_nom, s.scenario_type, l.lot, df.famille;

CREATE OR REPLACE VIEW v_scenario_evolution AS
SELECT
    s.scenario_id,
    s.scenario_nom,
    r.run_id,
    r.status,
    r.started_at,
    r.ended_at,
    r.duration_ms,
    r.rows_in,
    r.rows_out,
    r.rows_rejected,
    ROUND(COALESCE(SUM(f.capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(f.economie), 0)::NUMERIC, 2) AS economie_totale
FROM simulation_run r
JOIN dim_scenario s ON s.scenario_id = r.scenario_id
LEFT JOIN fact_simulation f ON f.run_id = r.run_id
GROUP BY
    s.scenario_id,
    s.scenario_nom,
    r.run_id,
    r.status,
    r.started_at,
    r.ended_at,
    r.duration_ms,
    r.rows_in,
    r.rows_out,
    r.rows_rejected;

COMMIT;
