-- SP2I CAPEX - Recette locale isolee : schema V6 synthetique.
-- AUCUNE donnee reelle. Deux projets chiffres (A, B), un projet vide (C) et un
-- projet a geometrie non resolvable (D) pour tester le ratio indisponible.
-- vw_fact_metre_financial_v6 est definie sur une table synthetique exposant le
-- contrat de la vue de production (033), sans rejouer la chaine canonique.

BEGIN;

DROP TABLE IF EXISTS dim_projet CASCADE;
DROP TABLE IF EXISTS dim_batiment CASCADE;
DROP TABLE IF EXISTS dim_appartement CASCADE;
DROP TABLE IF EXISTS recipe_fact_v6 CASCADE;
DROP VIEW IF EXISTS vw_fact_metre_financial_v6 CASCADE;

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

CREATE TABLE recipe_fact_v6 (
    id_ligne                 TEXT PRIMARY KEY,
    canonical_id_ligne       TEXT,
    projet_id                INTEGER,
    project_code             TEXT,
    designation              TEXT,
    quantite                 NUMERIC,
    unite                    TEXT,
    lot                      TEXT,
    lot_code                 TEXT,
    article_code             TEXT,
    sous_lot                 TEXT,
    batiment                 TEXT,
    niveau                   TEXT,
    appartement              TEXT,
    piece                    TEXT,
    famille                  TEXT,
    prix_local_fcfa          NUMERIC,
    prix_import_fcfa         NUMERIC,
    prix_optimise_fcfa       NUMERIC,
    capex_local              NUMERIC,
    capex_import             NUMERIC,
    capex_optimise           NUMERIC,
    economie                 NUMERIC,
    taux_economie            NUMERIC,
    decision_import          TEXT,
    pricing_scope            TEXT,
    pricing_confidence       TEXT,
    price_reference_code     TEXT,
    source_prix              TEXT,
    created_at               TIMESTAMPTZ DEFAULT now(),
    date_import              TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE VIEW vw_fact_metre_financial_v6 AS
SELECT
    id_ligne, canonical_id_ligne, projet_id, project_code, designation,
    quantite, unite, lot, lot_code, article_code, sous_lot, batiment, niveau,
    appartement, piece, famille, prix_local_fcfa, prix_import_fcfa,
    prix_optimise_fcfa, capex_local, capex_import, capex_optimise, economie,
    taux_economie, decision_import, pricing_scope, pricing_confidence,
    price_reference_code, source_prix, created_at, date_import
FROM recipe_fact_v6;

CREATE OR REPLACE VIEW vw_project_cost_summary_v6 AS
WITH direct_cost AS (
    SELECT
        projet_id,
        project_code,
        SUM(capex_local)::numeric AS capex_direct,
        SUM(capex_import)::numeric AS capex_import,
        SUM(capex_optimise)::numeric AS capex_optimise,
        SUM(economie)::numeric AS economie_nette,
        COUNT(*) FILTER (WHERE pricing_scope = 'LEGACY_LOT_FALLBACK') AS fallback_legacy_lot_lines,
        COALESCE(SUM(capex_local) FILTER (WHERE pricing_scope = 'LEGACY_LOT_FALLBACK'), 0)::numeric AS fallback_legacy_lot_capex
    FROM vw_fact_metre_financial_v6
    GROUP BY projet_id, project_code
),
apartments AS (
    SELECT
        f.projet_id,
        f.project_code,
        f.appartement,
        MAX(COALESCE(a.surface_m2, a.surface, 0))::numeric AS surface_m2
    FROM vw_fact_metre_financial_v6 f
    LEFT JOIN dim_appartement a
      ON CAST(a.appartement_id AS text) = CAST(f.appartement AS text)
    WHERE NULLIF(TRIM(CAST(f.appartement AS text)), '') IS NOT NULL
    GROUP BY f.projet_id, f.project_code, f.appartement
),
building_surface AS (
    SELECT
        x.projet_id,
        x.project_code,
        SUM(x.surface_m2)::numeric AS surface_m2
    FROM (
        SELECT
            f.projet_id,
            f.project_code,
            f.batiment,
            MAX(COALESCE(b.surface_totale_m2, 0))::numeric AS surface_m2
        FROM vw_fact_metre_financial_v6 f
        LEFT JOIN dim_batiment b
          ON LOWER(COALESCE(NULLIF(b.batiment_code, ''), b.batiment)) = LOWER(f.batiment)
        GROUP BY f.projet_id, f.project_code, f.batiment
    ) x
    GROUP BY x.projet_id, x.project_code
),
apartment_summary AS (
    SELECT
        projet_id,
        project_code,
        SUM(surface_m2)::numeric AS surface_m2,
        COUNT(*)::numeric AS nb_appartements
    FROM apartments
    GROUP BY projet_id, project_code
),
spatial AS (
    SELECT
        p.projet_id,
        p.project_code,
        COALESCE(NULLIF(a.surface_m2, 0), bs.surface_m2, 0)::numeric AS surface_m2,
        COALESCE(a.nb_appartements, 0)::numeric AS nb_appartements,
        p.nb_niveaux
    FROM (
        SELECT
            projet_id,
            project_code,
            COUNT(DISTINCT niveau) FILTER (
                WHERE NULLIF(TRIM(CAST(niveau AS text)), '') IS NOT NULL
            )::numeric AS nb_niveaux
        FROM vw_fact_metre_financial_v6
        GROUP BY projet_id, project_code
    ) p
    LEFT JOIN apartment_summary a USING (projet_id, project_code)
    LEFT JOIN building_surface bs USING (projet_id, project_code)
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
    JOIN spatial s USING (projet_id, project_code)
    CROSS JOIN rates r
)
SELECT
    projet_id,
    project_code,
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
    indirect_rate,
    site_installation_rate,
    import_logistics_rate,
    contingency_rate,
    ROUND(capex_direct / NULLIF(surface_m2, 0), 2) AS capex_direct_per_m2,
    ROUND((capex_direct + indirect_costs + site_installation + import_logistics) * (1 + contingency_rate) / NULLIF(surface_m2, 0), 2) AS total_project_cost_per_m2,
    ROUND((capex_direct + indirect_costs + site_installation + import_logistics) * (1 + contingency_rate) / NULLIF(nb_appartements, 0), 2) AS total_project_cost_per_appartement,
    ROUND((capex_direct + indirect_costs + site_installation + import_logistics) * (1 + contingency_rate) / NULLIF(nb_niveaux, 0), 2) AS total_project_cost_per_niveau,
    fallback_legacy_lot_lines,
    fallback_legacy_lot_capex,
    ROUND(100.0 * fallback_legacy_lot_capex / NULLIF(capex_direct, 0), 2) AS fallback_legacy_lot_pct
FROM base;

CREATE OR REPLACE VIEW vw_dashboard_direction_v6_scoped AS
WITH by_lot AS (
    SELECT
        projet_id,
        project_code,
        lot,
        SUM(capex_local)::numeric AS capex_direct,
        COUNT(*) AS nb_lignes,
        COUNT(DISTINCT article_code) AS nb_articles,
        COUNT(*) FILTER (WHERE pricing_scope = 'LEGACY_LOT_FALLBACK') AS fallback_legacy_lot_lines,
        COALESCE(SUM(capex_local) FILTER (WHERE pricing_scope = 'LEGACY_LOT_FALLBACK'), 0)::numeric AS fallback_legacy_lot_capex
    FROM vw_fact_metre_financial_v6
    GROUP BY projet_id, project_code, lot
),
total AS (
    SELECT projet_id, SUM(capex_direct) AS total_capex_direct
    FROM by_lot GROUP BY projet_id
)
SELECT
    b.projet_id,
    b.project_code,
    b.lot,
    b.capex_direct,
    ROUND(100.0 * b.capex_direct / NULLIF(t.total_capex_direct, 0), 2) AS pct_capex_direct,
    b.nb_lignes,
    b.nb_articles,
    b.fallback_legacy_lot_lines,
    b.fallback_legacy_lot_capex,
    p.capex_direct AS project_capex_direct,
    p.indirect_costs,
    p.site_installation,
    p.import_logistics,
    p.contingency,
    p.total_project_cost,
    p.total_project_cost_per_m2,
    p.total_project_cost_per_appartement,
    p.total_project_cost_per_niveau
FROM by_lot b
JOIN total t USING (projet_id)
JOIN vw_project_cost_summary_v6 p USING (projet_id, project_code);

CREATE OR REPLACE VIEW vw_cost_intelligence_v6_scoped AS
SELECT
    projet_id,
    project_code,
    lot,
    sous_lot,
    article_code,
    designation,
    unite,
    SUM(quantite)::numeric AS quantite,
    MIN(prix_local_fcfa)::numeric AS prix_local_fcfa,
    MIN(prix_import_fcfa)::numeric AS prix_import_fcfa,
    MIN(prix_optimise_fcfa)::numeric AS prix_optimise_fcfa,
    SUM(capex_local)::numeric AS capex_local,
    SUM(capex_import)::numeric AS capex_import,
    SUM(capex_optimise)::numeric AS capex_optimise,
    SUM(economie)::numeric AS economie,
    MIN(decision_import)::text AS decision_import,
    MIN(pricing_scope)::text AS pricing_scope,
    MIN(pricing_confidence)::text AS pricing_confidence,
    MIN(price_reference_code)::text AS price_reference_code
FROM vw_fact_metre_financial_v6
GROUP BY projet_id, project_code, lot, sous_lot, article_code, designation, unite;

-- ---------------------------------------------------------------------------
-- Dimensions synthetiques
-- ---------------------------------------------------------------------------
INSERT INTO dim_projet (projet_id, projet_code, projet_nom) VALUES
    (1, 'PROJET_A', 'Projet A synthetique'),
    (2, 'PROJET_B', 'Projet B synthetique'),
    (3, 'PROJET_C', 'Projet C vide'),
    (4, 'PROJET_D', 'Projet D geometrie non resolvable'),
    (5, 'PROJET_E', 'Projet E montants nuls')
ON CONFLICT (projet_code) DO NOTHING;

INSERT INTO dim_batiment (batiment_id, batiment_code, batiment, surface_totale_m2) VALUES
    (1, 'BAT_A', 'BAT_A', 500),
    (2, 'BAT_B', 'BAT_B', 300)
ON CONFLICT DO NOTHING;

INSERT INTO dim_appartement (appartement_id, appartement_code, surface_m2, surface) VALUES
    ('A-RDC-01', 'A-RDC-01', 50, 50),
    ('A-RDC-02', 'A-RDC-02', 60, 60),
    ('A-ET1-01', 'A-ET1-01', 70, 70),
    ('B-RDC-01', 'B-RDC-01', 80, 80)
ON CONFLICT (appartement_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Faits financiers synthetiques
-- ---------------------------------------------------------------------------
-- Projet A : RDC = 1000 (2 apparts), ETAGE1 = 2000 (A-ET1-01 sur 2 lots).
INSERT INTO recipe_fact_v6 (id_ligne, projet_id, project_code, designation, quantite, unite,
    lot, article_code, batiment, niveau, appartement, famille,
    prix_local_fcfa, prix_import_fcfa, prix_optimise_fcfa,
    capex_local, capex_import, capex_optimise, economie,
    decision_import, pricing_scope) VALUES
 ('A-RDC-01-L1', 1, 'PROJET_A', 'Cable electrique', 10, 'ml', 'LOT_ELEC', 'ELEC-01', 'BAT_A', 'RDC', 'A-RDC-01', 'Electricite',
  40, 30, 36, 400, 300, 360, 40, 'IMPORT', 'V6'),
 ('A-RDC-02-L2', 1, 'PROJET_A', 'Peinture interieure', 100, 'm2', 'LOT_PNT', 'PNT-01', 'BAT_A', 'RDC', 'A-RDC-02', 'Peinture',
  6, 0, 5.4, 600, 0, 540, 60, 'LOCAL', 'V6'),
 ('A-ET1-01-L3', 1, 'PROJET_A', 'Climatiseur', 2, 'u', 'LOT_CVC', 'CVC-01', 'BAT_A', 'ETAGE1', 'A-ET1-01', 'Climatisation',
  600, 300, 540, 1200, 600, 1080, 120, 'IMPORT', 'V6'),
 ('A-ET1-01-L4', 1, 'PROJET_A', 'Gaine ventilation', 20, 'ml', 'LOT_CVC', 'CVC-02', 'BAT_A', 'ETAGE1', 'A-ET1-01', 'Climatisation',
  40, 0, 36, 800, 0, 720, 80, 'LOCAL', 'V6');

-- Projet B : 1 ligne RDC = 500 (doit rester isole de A).
INSERT INTO recipe_fact_v6 (id_ligne, projet_id, project_code, designation, quantite, unite,
    lot, article_code, batiment, niveau, appartement, famille,
    prix_local_fcfa, prix_import_fcfa, prix_optimise_fcfa,
    capex_local, capex_import, capex_optimise, economie,
    decision_import, pricing_scope) VALUES
 ('B-RDC-01-L1', 2, 'PROJET_B', 'Tableau electrique', 1, 'u', 'LOT_ELEC', 'ELEC-B1', 'BAT_B', 'RDC', 'B-RDC-01', 'Electricite',
  500, 0, 450, 500, 0, 450, 50, 'LOCAL', 'V6');

-- Projet D : 1 ligne sans appartement ni batiment reference -> surface non
-- resolvable (les ratios /m2 deviennent indisponibles une fois filtres).
INSERT INTO recipe_fact_v6 (id_ligne, projet_id, project_code, designation, quantite, unite,
    lot, article_code, batiment, niveau, appartement, famille,
    prix_local_fcfa, prix_import_fcfa, prix_optimise_fcfa,
    capex_local, capex_import, capex_optimise, economie,
    decision_import, pricing_scope) VALUES
 ('D-S1-L1', 4, 'PROJET_D', 'Gros oeuvre', 1, 'ens', 'LOT_FOND', 'GO-D1', 'BAT_D', 'S1', NULL, 'Gros oeuvre',
  1000, 0, 900, 1000, 0, 900, 100, 'LOCAL', 'V6');

-- Projet E : des LIGNES REELLES mais toutes a montant nul (test vrai zero).
INSERT INTO recipe_fact_v6 (id_ligne, projet_id, project_code, designation, quantite, unite,
    lot, article_code, batiment, niveau, appartement, famille,
    prix_local_fcfa, prix_import_fcfa, prix_optimise_fcfa,
    capex_local, capex_import, capex_optimise, economie,
    decision_import, pricing_scope) VALUES
 ('E-01', 5, 'PROJET_E', 'Reservation option', 0, 'u', 'LOT_ELEC', 'ELEC-E1', 'BAT_A', 'RDC', 'A-RDC-01', 'Electricite',
  0, 0, 0, 0, 0, 0, 0, 'LOCAL', 'V6'),
 ('E-02', 5, 'PROJET_E', 'Peinture offerte', 0, 'u', 'LOT_PNT', 'PNT-E1', 'BAT_A', 'RDC', 'A-RDC-01', 'Peinture',
  0, 0, 0, 0, 0, 0, 0, 'LOCAL', 'V6');

-- ---------------------------------------------------------------------------
-- Source de faits "courante" utilisee par /analytics/filters (dropdowns BI).
-- En production cette relation est construite par la chaine de migrations
-- (analytics views) ; dans ce schema minimal de recette elle expose le meme
-- contrat de colonnes (project_code/projet_id + dimensions + montants) sur le
-- grain financier synthetique recipe_fact_v6. Sans elle, le endpoint renvoie
-- HTTP 500 "relation vw_fact_metre_current does not exist".
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_fact_metre_current AS
SELECT
    project_code, projet_id, designation, quantite, unite,
    lot, lot_code, article_code, sous_lot, batiment, niveau,
    appartement, piece, famille,
    prix_local_fcfa, prix_import_fcfa, prix_optimise_fcfa,
    capex_local, capex_import, capex_optimise, economie,
    decision_import, pricing_scope
FROM recipe_fact_v6;

COMMIT;

