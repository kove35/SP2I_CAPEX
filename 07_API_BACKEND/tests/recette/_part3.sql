
-- ---------------------------------------------------------------------------
-- Dimensions synthetiques
-- ---------------------------------------------------------------------------
INSERT INTO dim_projet (projet_id, projet_code, projet_nom) VALUES
    (1, 'PROJET_A', 'Projet A synthetique'),
    (2, 'PROJET_B', 'Projet B synthetique'),
    (3, 'PROJET_C', 'Projet C vide'),
    (4, 'PROJET_D', 'Projet D geometrie non resolvable')
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
