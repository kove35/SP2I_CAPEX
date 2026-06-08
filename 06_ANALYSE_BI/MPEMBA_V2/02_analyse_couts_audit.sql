-- SP2I CAPEX MPEMBA V2 - Audit page Power BI 02_ANALYSE_COUTS
-- Objectif : detecter les slicers dimensionnels qui filtrent fact_metre a vide.

-- PHASE 1.1 - Tous les lots presents dans fact_metre.
SELECT DISTINCT
    lot
FROM fact_metre
ORDER BY lot;

-- PHASE 1.2 - Tous les lots presents dans dim_lot.
SELECT
    lot,
    COALESCE(description, lot) AS lot_libelle
FROM dim_lot
ORDER BY lot;

-- PHASE 1.3 - Lots presents dans dim_lot mais jamais utilises dans fact_metre.
-- Ces valeurs ne doivent pas alimenter les segments Power BI de 02_ANALYSE_COUTS.
SELECT
    d.lot,
    COALESCE(d.description, d.lot) AS lot_libelle
FROM dim_lot d
LEFT JOIN fact_metre f
    ON UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
    OR UPPER(TRIM(COALESCE(CAST(f.lot_id AS text), ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
WHERE f.id_ligne IS NULL
ORDER BY d.lot;

-- PHASE 1.4 - Lots presents dans fact_metre mais absents de dim_lot.
-- Ces lignes existent mais les visuels peuvent devenir incoherents si le modele filtre via dim_lot.
SELECT DISTINCT
    f.lot
FROM fact_metre f
LEFT JOIN dim_lot d
    ON UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
    OR UPPER(TRIM(COALESCE(CAST(f.lot_id AS text), ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
WHERE f.lot IS NOT NULL
  AND d.lot IS NULL
ORDER BY f.lot;

-- PHASE 1.5 - Test du cas observe : ancien libelle vs nouveau code BIM.
SELECT
    f.batiment,
    f.niveau,
    COALESCE(NULLIF(f.appartement_id, ''), NULLIF(f.appartement_code, ''), NULLIF(f.appart, '')) AS appartement,
    COALESCE(NULLIF(f.piece, ''), NULLIF(f.piece_code, '')) AS piece,
    f.lot,
    COUNT(*) AS nb_lignes,
    COALESCE(SUM(f.capex_local), 0) AS capex_local,
    COALESCE(SUM(f.capex_optimise), 0) AS capex_optimise,
    COALESCE(SUM(f.economie), 0) AS economie
FROM fact_metre f
WHERE f.batiment = 'BAT_01'
  AND f.niveau = 'N2'
  AND COALESCE(NULLIF(f.appartement_id, ''), NULLIF(f.appartement_code, ''), NULLIF(f.appart, '')) = 'A201'
  AND COALESCE(NULLIF(f.piece, ''), NULLIF(f.piece_code, '')) = 'SEJOUR'
GROUP BY
    f.batiment,
    f.niveau,
    COALESCE(NULLIF(f.appartement_id, ''), NULLIF(f.appartement_code, ''), NULLIF(f.appart, '')),
    COALESCE(NULLIF(f.piece, ''), NULLIF(f.piece_code, '')),
    f.lot
ORDER BY f.lot;

-- PHASE 1.6 - Coherence sous-lots : sous-lots de fact_metre absents du referentiel.
SELECT DISTINCT
    f.lot,
    f.sous_lot_id,
    f.sous_lot
FROM fact_metre f
LEFT JOIN dim_sous_lot_complet d
    ON UPPER(TRIM(COALESCE(f.sous_lot_id, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
    OR UPPER(TRIM(COALESCE(f.sous_lot, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
WHERE COALESCE(NULLIF(f.sous_lot_id, ''), NULLIF(f.sous_lot, '')) IS NOT NULL
  AND d.sous_lot_id IS NULL
ORDER BY f.lot, f.sous_lot_id, f.sous_lot;

-- PHASE 1.7 - Sous-lots du referentiel jamais utilises dans fact_metre.
SELECT
    d.sous_lot_id,
    d.lot_id,
    d.description
FROM dim_sous_lot_complet d
LEFT JOIN fact_metre f
    ON UPPER(TRIM(COALESCE(f.sous_lot_id, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
    OR UPPER(TRIM(COALESCE(f.sous_lot, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
WHERE f.id_ligne IS NULL
ORDER BY d.lot_id, d.sous_lot_id;

-- PHASE 1.8 - Coherence articles : articles de fact_metre absents de dim_article_bpu.
SELECT DISTINCT
    f.lot,
    f.sous_lot_id,
    f.article_id,
    f.code_article,
    f.designation
FROM fact_metre f
LEFT JOIN dim_article_bpu d
    ON UPPER(TRIM(COALESCE(f.code_article, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
    OR UPPER(TRIM(COALESCE(f.article_id, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
WHERE COALESCE(NULLIF(f.code_article, ''), NULLIF(f.article_id, '')) IS NOT NULL
  AND d.code_article IS NULL
ORDER BY f.lot, f.sous_lot_id, f.code_article, f.article_id;

-- PHASE 1.9 - Articles du referentiel jamais utilises dans fact_metre.
SELECT
    d.code_article,
    d.designation,
    d.unite
FROM dim_article_bpu d
LEFT JOIN fact_metre f
    ON UPPER(TRIM(COALESCE(f.code_article, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
    OR UPPER(TRIM(COALESCE(f.article_id, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
WHERE f.id_ligne IS NULL
ORDER BY d.code_article;

-- PHASE 1.10 - Controle rapide des vues actives recommandees pour Power BI.
SELECT 'vw_dim_lot_active' AS view_name, COUNT(*) AS rows_count FROM vw_dim_lot_active
UNION ALL SELECT 'vw_dim_sous_lot_active', COUNT(*) FROM vw_dim_sous_lot_active
UNION ALL SELECT 'vw_dim_article_bpu_active', COUNT(*) FROM vw_dim_article_bpu_active;

