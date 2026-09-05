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
