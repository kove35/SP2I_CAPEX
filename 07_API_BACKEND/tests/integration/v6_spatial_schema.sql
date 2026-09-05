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
    appartement_id TEXT PRIMARY KEY,
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
    ('A-RDC-01', 'A-RDC-01', 50, 50),
    ('A-RDC-02', 'A-RDC-02', 60, 60),
    ('A-ET1-01', 'A-ET1-01', 70, 70),
    ('B-RDC-01', 'B-RDC-01', 80, 80);

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
-- Reproduit fidelement la definition SQL de production (033_v6_financial_reconciliation) :
-- la surface est dedoublonnee par appartement (MAX par appartement) avant sommation,
-- pour ne pas compter plusieurs fois la surface d'un appartement present sur plusieurs
-- lignes financieres. A-ET1-01 porte 2 lignes (LOT_ELEC + LOT_CVC) : sa surface (70)
-- ne doit etre comptee qu'une fois.
CREATE OR REPLACE VIEW vw_project_cost_summary_v6 AS
WITH direct_cost AS (
    SELECT
        project_code,
        projet_id,
        SUM(capex_local)::numeric AS capex_direct,
        SUM(capex_import)::numeric AS capex_import,
        SUM(capex_optimise)::numeric AS capex_optimise,
        SUM(economie)::numeric AS economie_nette,
        COUNT(*) FILTER (WHERE pricing_scope = 'LEGACY_LOT_FALLBACK') AS fallback_legacy_lot_lines,
        COALESCE(SUM(capex_local) FILTER (WHERE pricing_scope = 'LEGACY_LOT_FALLBACK'), 0)::numeric AS fallback_legacy_lot_capex
    FROM fact_metre_financial_v6_test
    GROUP BY project_code, projet_id
),
apartments AS (
    SELECT
        f.project_code,
        f.projet_id,
        f.appartement,
        MAX(COALESCE(a.surface_m2, a.surface, 0))::numeric AS surface_m2
    FROM fact_metre_financial_v6_test f
    LEFT JOIN dim_appartement a
      ON CAST(a.appartement_id AS text) = CAST(f.appartement AS text)
    WHERE NULLIF(TRIM(CAST(f.appartement AS text)), '') IS NOT NULL
    GROUP BY f.project_code, f.projet_id, f.appartement
),
apartment_summary AS (
    SELECT
        project_code,
        projet_id,
        SUM(surface_m2)::numeric AS surface_m2,
        COUNT(*)::numeric AS nb_appartements
    FROM apartments
    GROUP BY project_code, projet_id
),
spatial AS (
    SELECT
        p.project_code,
        p.projet_id,
        COALESCE(a.surface_m2, 0)::numeric AS surface_m2,
        COALESCE(a.nb_appartements, 0)::numeric AS nb_appartements,
        p.nb_niveaux
    FROM (
        SELECT
            project_code,
            projet_id,
            COUNT(DISTINCT niveau) FILTER (
                WHERE NULLIF(TRIM(CAST(niveau AS text)), '') IS NOT NULL
            )::numeric AS nb_niveaux
        FROM fact_metre_financial_v6_test
        GROUP BY project_code, projet_id
    ) p
    LEFT JOIN apartment_summary a USING (project_code, projet_id)
),
rates AS (
    SELECT 0.1100::numeric AS indirect_rate,
           0.0420::numeric AS site_installation_rate,
           0.0350::numeric AS import_logistics_rate,
           0.1200::numeric AS contingency_rate
),
base AS (
    SELECT
        d.*,
        s.surface_m2,
        s.nb_appartements,
        s.nb_niveaux,
        r.*,
        ROUND(d.capex_direct * r.indirect_rate, 2) AS indirect_costs,
        ROUND(d.capex_direct * r.site_installation_rate, 2) AS site_installation,
        ROUND(d.capex_direct * r.import_logistics_rate, 2) AS import_logistics
    FROM direct_cost d
    JOIN spatial s USING (project_code, projet_id)
    CROSS JOIN rates r
)
SELECT
    project_code,
    projet_id,
    capex_direct,
    capex_import,
    capex_optimise,
    economie_nette,
    indirect_costs,
    site_installation,
    import_logistics,
    ROUND((capex_direct + indirect_costs + site_installation + import_logistics) * contingency_rate, 2) AS contingency,
    ROUND((capex_direct + indirect_costs + site_installation + import_logistics) * (1 + contingency_rate), 2) AS total_project_cost,
    surface_m2,
    nb_appartements,
    nb_niveaux,
    ROUND(capex_direct / NULLIF(surface_m2, 0), 2) AS capex_direct_per_m2,
    ROUND((capex_direct + indirect_costs + site_installation + import_logistics) * (1 + contingency_rate) / NULLIF(surface_m2, 0), 2) AS total_project_cost_per_m2,
    ROUND((capex_direct + indirect_costs + site_installation + import_logistics) * (1 + contingency_rate) / NULLIF(nb_appartements, 0), 2) AS total_project_cost_per_appartement,
    ROUND((capex_direct + indirect_costs + site_installation + import_logistics) * (1 + contingency_rate) / NULLIF(nb_niveaux, 0), 2) AS total_project_cost_per_niveau,
    fallback_legacy_lot_lines,
    fallback_legacy_lot_capex,
    ROUND(100.0 * fallback_legacy_lot_capex / NULLIF(capex_direct, 0), 2) AS fallback_legacy_lot_pct
FROM base;
