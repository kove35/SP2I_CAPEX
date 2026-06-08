-- SP2I CAPEX MPEMBA V2 - Audit complet Neon / Power BI Ready
-- Base cible : Neon PostgreSQL / neondb
-- Objectif : verifier que les filtres Power BI ne peuvent pas produire
-- d'incoherences dues au referentiel, aux dimensions ou aux relations.

-- PHASE 1 - Inventaire tables et vues.
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_type, table_name;

-- Cles primaires.
SELECT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON kcu.constraint_name = tc.constraint_name
   AND kcu.table_schema = tc.table_schema
WHERE tc.table_schema = 'public'
  AND tc.constraint_type = 'PRIMARY KEY'
ORDER BY tc.table_name, kcu.ordinal_position;

-- Cles etrangeres.
SELECT
    tc.table_name AS source_table,
    kcu.column_name AS source_column,
    ccu.table_name AS target_table,
    ccu.column_name AS target_column,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON kcu.constraint_name = tc.constraint_name
   AND kcu.table_schema = tc.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
   AND ccu.table_schema = tc.table_schema
WHERE tc.table_schema = 'public'
  AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;

-- PHASE 2 - Audit fact_metre.
SELECT COUNT(*) AS fact_metre_rows FROM fact_metre;

SELECT
    COALESCE(SUM(capex_local), 0) AS capex_local,
    COALESCE(SUM(capex_import), 0) AS capex_import,
    COALESCE(SUM(capex_optimise), 0) AS capex_optimise,
    COALESCE(SUM(economie), 0) AS economie
FROM fact_metre;

SELECT
    COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(lot), ''), NULL) IS NULL) AS sans_lot,
    COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(sous_lot), ''), NULLIF(TRIM(sous_lot_id), ''), NULL) IS NULL) AS sans_sous_lot,
    COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(code_article), ''), NULLIF(TRIM(article_id), ''), NULL) IS NULL) AS sans_article,
    COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(batiment), ''), NULL) IS NULL) AS sans_batiment,
    COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(niveau), ''), NULL) IS NULL) AS sans_niveau,
    COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(appartement_id), ''), NULLIF(TRIM(appartement_code), ''), NULLIF(TRIM(appart), ''), NULL) IS NULL) AS sans_appartement,
    COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(piece), ''), NULLIF(TRIM(piece_code), ''), NULL) IS NULL) AS sans_piece
FROM fact_metre;

SELECT
    batiment,
    niveau,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, '')) AS appartement,
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, '')) AS piece,
    lot,
    COALESCE(NULLIF(sous_lot_id, ''), NULLIF(sous_lot, '')) AS sous_lot_key,
    COALESCE(NULLIF(code_article, ''), NULLIF(article_id, '')) AS article_key,
    designation,
    COUNT(*) AS duplicate_count
FROM fact_metre
GROUP BY
    batiment,
    niveau,
    COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, '')),
    COALESCE(NULLIF(piece, ''), NULLIF(piece_code, '')),
    lot,
    COALESCE(NULLIF(sous_lot_id, ''), NULLIF(sous_lot, '')),
    COALESCE(NULLIF(code_article, ''), NULLIF(article_id, '')),
    designation
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 100;

-- PHASE 3 - Audit dim_lot.
SELECT DISTINCT lot FROM fact_metre ORDER BY lot;

SELECT lot, COALESCE(description, lot) AS lot_libelle
FROM dim_lot
ORDER BY lot;

SELECT DISTINCT f.lot
FROM fact_metre f
LEFT JOIN dim_lot d
    ON UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
WHERE f.lot IS NOT NULL
  AND d.lot IS NULL
ORDER BY f.lot;

SELECT d.lot, COALESCE(d.description, d.lot) AS lot_libelle
FROM dim_lot d
LEFT JOIN fact_metre f
    ON UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
WHERE f.id_ligne IS NULL
ORDER BY d.lot;

SELECT * FROM vw_dim_lot_active ORDER BY lot;

-- PHASE 4 - Audit dim_sous_lot_complet.
SELECT DISTINCT COALESCE(NULLIF(sous_lot_id, ''), NULLIF(sous_lot, '')) AS sous_lot_key
FROM fact_metre
WHERE COALESCE(NULLIF(sous_lot_id, ''), NULLIF(sous_lot, '')) IS NOT NULL
ORDER BY sous_lot_key;

SELECT DISTINCT
    f.lot,
    COALESCE(NULLIF(f.sous_lot_id, ''), NULLIF(f.sous_lot, '')) AS sous_lot_key
FROM fact_metre f
LEFT JOIN dim_sous_lot_complet d
    ON UPPER(TRIM(COALESCE(f.sous_lot_id, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
    OR UPPER(TRIM(COALESCE(f.sous_lot, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
WHERE COALESCE(NULLIF(f.sous_lot_id, ''), NULLIF(f.sous_lot, '')) IS NOT NULL
  AND d.sous_lot_id IS NULL
ORDER BY f.lot, sous_lot_key;

SELECT d.sous_lot_id, d.lot_id, COUNT(*) AS duplicates
FROM dim_sous_lot_complet d
GROUP BY d.sous_lot_id, d.lot_id
HAVING COUNT(*) > 1
ORDER BY duplicates DESC;

SELECT * FROM vw_dim_sous_lot_active ORDER BY lot_id, sous_lot_id;

-- PHASE 5 - Audit dim_article_bpu.
SELECT DISTINCT COALESCE(NULLIF(code_article, ''), NULLIF(article_id, '')) AS article_key
FROM fact_metre
WHERE COALESCE(NULLIF(code_article, ''), NULLIF(article_id, '')) IS NOT NULL
ORDER BY article_key;

SELECT DISTINCT
    f.lot,
    f.sous_lot_id,
    f.code_article,
    f.article_id,
    f.designation
FROM fact_metre f
LEFT JOIN dim_article_bpu d
    ON UPPER(TRIM(COALESCE(f.code_article, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
    OR UPPER(TRIM(COALESCE(f.article_id, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
WHERE COALESCE(NULLIF(f.code_article, ''), NULLIF(f.article_id, '')) IS NOT NULL
  AND d.code_article IS NULL
ORDER BY f.lot, f.sous_lot_id, f.code_article, f.article_id;

SELECT
    code_article,
    REGEXP_REPLACE(UPPER(code_article), '[^A-Z0-9]', '', 'g') AS normalized_code,
    COUNT(*) AS variants
FROM dim_article_bpu
GROUP BY code_article, REGEXP_REPLACE(UPPER(code_article), '[^A-Z0-9]', '', 'g')
ORDER BY normalized_code, code_article;

SELECT * FROM vw_dim_article_bpu_active ORDER BY code_article;

-- PHASE 6 - Audit BIM spatial.
SELECT
    COUNT(DISTINCT batiment) AS nb_batiments,
    COUNT(DISTINCT niveau) AS nb_niveaux,
    COUNT(DISTINCT COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''))) AS nb_appartements,
    COUNT(DISTINCT COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''))) AS nb_pieces
FROM fact_metre;

SELECT da.appartement_id
FROM dim_appartement da
LEFT JOIN dim_piece dp ON dp.appartement_id = da.appartement_id
WHERE dp.piece_id IS NULL
ORDER BY da.appartement_id;

SELECT dp.piece_id, dp.piece_nom
FROM dim_piece dp
LEFT JOIN dim_appartement da ON da.appartement_id = dp.appartement_id
WHERE dp.appartement_id IS NOT NULL
  AND da.appartement_id IS NULL
ORDER BY dp.piece_id;

-- PHASE 7/8 - Relations analytiques et Power BI ready.
SELECT 'vw_dim_lot_active' AS view_name, COUNT(*) AS rows_count, COUNT(DISTINCT lot) AS distinct_count FROM vw_dim_lot_active
UNION ALL
SELECT 'vw_dim_sous_lot_active', COUNT(*), COUNT(DISTINCT sous_lot_id) FROM vw_dim_sous_lot_active
UNION ALL
SELECT 'vw_dim_article_bpu_active', COUNT(*), COUNT(DISTINCT code_article) FROM vw_dim_article_bpu_active;

-- PHASE 9 - KPI SQL.
SELECT
    COALESCE(SUM(f.capex_local), 0) AS capex_local,
    COALESCE(SUM(f.capex_import), 0) AS capex_import,
    COALESCE(SUM(f.capex_optimise), 0) AS capex_optimise,
    COALESCE(SUM(f.economie), 0) AS economie,
    CASE WHEN COALESCE(SUM(f.capex_local), 0) = 0 THEN 0
         ELSE COALESCE(SUM(f.economie), 0) / NULLIF(SUM(f.capex_local), 0)
    END AS taux_economie,
    COALESCE(SUM(DISTINCT dp.surface_m2), 0) AS surface_totale,
    COALESCE(AVG(DISTINCT da.surface_m2), 0) AS surface_moyenne_appartement,
    CASE WHEN COALESCE(SUM(DISTINCT dp.surface_m2), 0) = 0 THEN 0
         ELSE COALESCE(SUM(f.capex_optimise), 0) / NULLIF(SUM(DISTINCT dp.surface_m2), 0)
    END AS capex_m2
FROM fact_metre f
LEFT JOIN dim_piece dp ON dp.piece_id = f.piece_id
LEFT JOIN dim_appartement da ON da.appartement_id = f.appartement_id;

-- PHASE 10 - Tests de robustesse.
WITH test_filters AS (
    SELECT 'BAT_01'::text AS batiment, NULL::text AS niveau, NULL::text AS appartement, NULL::text AS piece
    UNION ALL SELECT 'BAT_01', 'N1', 'A101', 'CHAMBRE_1'
    UNION ALL SELECT 'BAT_01', 'N2', 'A201', 'SEJOUR'
    UNION ALL SELECT 'BAT_01', 'N3', 'B301', 'SDB_1'
)
SELECT
    t.batiment,
    t.niveau,
    t.appartement,
    t.piece,
    COUNT(f.*) AS nb_lignes,
    COALESCE(SUM(f.capex_local), 0) AS capex_local,
    COALESCE(SUM(f.capex_optimise), 0) AS capex_optimise,
    COALESCE(SUM(f.economie), 0) AS economie
FROM test_filters t
LEFT JOIN fact_metre f
    ON f.batiment = t.batiment
   AND (t.niveau IS NULL OR f.niveau = t.niveau)
   AND (
        t.appartement IS NULL
        OR COALESCE(NULLIF(f.appartement_id, ''), NULLIF(f.appartement_code, ''), NULLIF(f.appart, '')) = t.appartement
   )
   AND (
        t.piece IS NULL
        OR COALESCE(NULLIF(f.piece, ''), NULLIF(f.piece_code, '')) = t.piece
   )
GROUP BY t.batiment, t.niveau, t.appartement, t.piece
ORDER BY t.batiment, t.niveau, t.appartement, t.piece;

