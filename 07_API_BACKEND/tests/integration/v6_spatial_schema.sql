-- Schema V6 de test minimal et fidele (donnees 100% synthetiques).
-- Reproduit les colonnes de vw_fact_metre_financial_v6 utilisees par le backend
-- ainsi que les dimensions dim_projet / dim_batiment / dim_appartement.
-- Aucune donnee de production : uniquement des projets synthetiques.

DROP TABLE IF EXISTS dim_projet CASCADE;
DROP TABLE IF EXISTS dim_batiment CASCADE;
DROP TABLE IF EXISTS dim_appartement CASCADE;
DROP VIEW IF EXISTS vw_fact_metre_financial_v6 CASCADE;
DROP TABLE IF EXISTS fact_metre_financial_v6_test CASCADE;

CREATE TABLE dim_projet (
    projet_id   INTEGER PRIMARY KEY,
    projet_code TEXT UNIQUE NOT NULL,
    projet_nom  TEXT
);

CREATE TABLE dim_batiment (
    batiment_id      INTEGER PRIMARY KEY,
    batiment_code    TEXT,
    batiment         TEXT,
    surface_totale_m2 NUMERIC
);

CREATE TABLE dim_appartement (
    appartement_id INTEGER PRIMARY KEY,
    appartement_code TEXT,
    surface_m2     NUMERIC,
    surface        NUMERIC
);

-- Table de faits financiere V6 de test (contrat de colonnes identique a la vue).
CREATE TABLE fact_metre_financial_v6_test (
    project_code   TEXT,
    projet_id      INTEGER,
    batiment       TEXT,
    niveau         TEXT,
    appartement    TEXT,
    lot            TEXT,
    famille        TEXT,
    capex_local    NUMERIC,
    capex_import   NUMERIC,
    capex_optimise NUMERIC,
    economie       NUMERIC,
    decision_import TEXT,
    pricing_scope  TEXT
);

-- Vue financiere V6 de test : meme nom et contrat que la vue de production.
CREATE VIEW vw_fact_metre_financial_v6 AS
SELECT
    project_code,
    projet_id,
    batiment,
    niveau,
    appartement,
    lot,
    famille,
    capex_local,
    capex_import,
    capex_optimise,
    economie,
    decision_import,
    pricing_scope
FROM fact_metre_financial_v6_test;

-- ============================================================================
-- Donnees synthetiques
-- ============================================================================

-- Projet A : 2 niveaux a montants distincts (RDC = 1000, ETAGE1 = 2000).
INSERT INTO dim_projet (projet_id, projet_code, projet_nom) VALUES
    (1, 'PROJET_A', 'Projet A synthetique'),
    (2, 'PROJET_B', 'Projet B synthetique');

INSERT INTO dim_batiment (batiment_id, batiment_code, batiment, surface_totale_m2) VALUES
    (1, 'BAT_A', 'BAT_A', 500),
    (2, 'BAT_B', 'BAT_B', 300);

INSERT INTO dim_appartement (appartement_id, appartement_code, surface_m2, surface) VALUES
    (101, 'A-RDC-01', 50, 50),
    (102, 'A-RDC-02', 60, 60),
    (201, 'A-ET1-01', 70, 70),
    (301, 'B-RDC-01', 80, 80);

-- Projet A - niveau RDC : capex_local total = 1000
INSERT INTO fact_metre_financial_v6_test VALUES
    ('PROJET_A', 1, 'BAT_A', 'RDC', 'A-RDC-01', 'LOT_ELEC', 'Electricite', 400, 300, 360, 40, 'IMPORT', 'V6'),
    ('PROJET_A', 1, 'BAT_A', 'RDC', 'A-RDC-02', 'LOT_PNT', 'Peinture', 600, 0, 540, 60, 'LOCAL', 'V6');

-- Projet A - niveau ETAGE1 : capex_local total = 2000
INSERT INTO fact_metre_financial_v6_test VALUES
    ('PROJET_A', 1, 'BAT_A', 'ETAGE1', 'A-ET1-01', 'LOT_ELEC', 'Electricite', 800, 600, 720, 80, 'IMPORT', 'V6'),
    ('PROJET_A', 1, 'BAT_A', 'ETAGE1', 'A-ET1-01', 'LOT_CVC', 'Climatisation', 1200, 0, 1080, 120, 'LOCAL', 'V6');

-- Projet B - niveau RDC : capex_local total = 500 (doit rester isole de A)
INSERT INTO fact_metre_financial_v6_test VALUES
    ('PROJET_B', 2, 'BAT_B', 'RDC', 'B-RDC-01', 'LOT_ELEC', 'Electricite', 500, 0, 450, 50, 'LOCAL', 'V6');

-- Vue projet V6 de test : meme nom et taux que vw_project_cost_summary_v6.
-- Utilisee par le chemin "sans filtre spatial" (baseline projet entier).
CREATE OR REPLACE VIEW vw_project_cost_summary_v6 AS
SELECT
    project_code,
    projet_id,
    SUM(capex_local) AS capex_direct,
    SUM(capex_import) AS capex_import,
    SUM(capex_optimise) AS capex_optimise,
    SUM(economie) AS economie_nette,
    ROUND(SUM(capex_local) * 0.11, 2) AS indirect_costs,
    ROUND(SUM(capex_local) * 0.042, 2) AS site_installation,
    ROUND(SUM(capex_local) * 0.035, 2) AS import_logistics,
    ROUND((SUM(capex_local) + SUM(capex_local) * 0.11 + SUM(capex_local) * 0.042 + SUM(capex_local) * 0.035) * 0.12, 2) AS contingency,
    ROUND((SUM(capex_local) + SUM(capex_local) * 0.11 + SUM(capex_local) * 0.042 + SUM(capex_local) * 0.035) * 1.12, 2) AS total_project_cost,
    COALESCE(SUM(a.surface_m2), 0) AS surface_m2,
    COUNT(DISTINCT f.appartement) AS nb_appartements,
    COUNT(DISTINCT f.niveau) AS nb_niveaux,
    COALESCE(SUM(f.capex_local) FILTER (WHERE f.pricing_scope = 'LEGACY_LOT_FALLBACK'), 0) AS fallback_legacy_lot_capex
FROM fact_metre_financial_v6_test f
LEFT JOIN dim_appartement a
  ON CAST(a.appartement_id AS text) = CAST(f.appartement AS text)
GROUP BY project_code, projet_id;
