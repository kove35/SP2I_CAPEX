-- SP2I CAPEX MPEMBA V2 - controles Neon avant refresh Power BI

-- 1. Presence des tables attendues.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'fact_metre',
    'dim_projet',
    'dim_batiment',
    'dim_niveau',
    'dim_appartement',
    'dim_zone',
    'dim_piece',
    'dim_lot',
    'dim_sous_lot_complet',
    'dim_article_bpu'
  )
ORDER BY table_name;

-- 2. Volumetrie de base.
SELECT 'fact_metre' AS table_name, COUNT(*) AS rows_count FROM fact_metre
UNION ALL SELECT 'dim_projet', COUNT(*) FROM dim_projet
UNION ALL SELECT 'dim_batiment', COUNT(*) FROM dim_batiment
UNION ALL SELECT 'dim_niveau', COUNT(*) FROM dim_niveau
UNION ALL SELECT 'dim_appartement', COUNT(*) FROM dim_appartement
UNION ALL SELECT 'dim_zone', COUNT(*) FROM dim_zone
UNION ALL SELECT 'dim_piece', COUNT(*) FROM dim_piece
UNION ALL SELECT 'dim_lot', COUNT(*) FROM dim_lot
UNION ALL SELECT 'dim_sous_lot_complet', COUNT(*) FROM dim_sous_lot_complet
UNION ALL SELECT 'dim_article_bpu', COUNT(*) FROM dim_article_bpu;

-- 3. Controle financier de reference.
SELECT
    COUNT(*) AS fact_metre_rows,
    COALESCE(SUM(capex_local), 0) AS capex_local,
    COALESCE(SUM(capex_optimise), 0) AS capex_optimise,
    COALESCE(SUM(economie), 0) AS economie
FROM fact_metre;

-- 4. Cles orphelines. Chaque resultat doit retourner 0.
SELECT 'projet_id' AS relation, COUNT(*) AS orphan_rows
FROM fact_metre f
LEFT JOIN dim_projet d ON d.projet_id = f.projet_id
WHERE f.projet_id IS NOT NULL AND d.projet_id IS NULL
UNION ALL
SELECT 'batiment_id', COUNT(*)
FROM fact_metre f
LEFT JOIN dim_batiment d ON d.batiment_id = f.batiment_id
WHERE f.batiment_id IS NOT NULL AND d.batiment_id IS NULL
UNION ALL
SELECT 'niveau_id', COUNT(*)
FROM fact_metre f
LEFT JOIN dim_niveau d ON d.niveau_id = f.niveau_id
WHERE f.niveau_id IS NOT NULL AND d.niveau_id IS NULL
UNION ALL
SELECT 'appartement_id', COUNT(*)
FROM fact_metre f
LEFT JOIN dim_appartement d ON d.appartement_id = f.appartement_id
WHERE f.appartement_id IS NOT NULL AND d.appartement_id IS NULL
UNION ALL
SELECT 'zone_id', COUNT(*)
FROM fact_metre f
LEFT JOIN dim_zone d ON d.zone_id = f.zone_id
WHERE f.zone_id IS NOT NULL AND d.zone_id IS NULL
UNION ALL
SELECT 'piece_id', COUNT(*)
FROM fact_metre f
LEFT JOIN dim_piece d ON d.piece_id = f.piece_id
WHERE f.piece_id IS NOT NULL AND d.piece_id IS NULL
UNION ALL
SELECT 'lot_id', COUNT(*)
FROM fact_metre f
LEFT JOIN dim_lot d ON d.lot_id = f.lot_id
WHERE f.lot_id IS NOT NULL AND d.lot_id IS NULL
UNION ALL
SELECT 'sous_lot_id', COUNT(*)
FROM fact_metre f
LEFT JOIN dim_sous_lot_complet d ON d.sous_lot_id = f.sous_lot_id
WHERE f.sous_lot_id IS NOT NULL AND d.sous_lot_id IS NULL
UNION ALL
SELECT 'article_id', COUNT(*)
FROM fact_metre f
LEFT JOIN dim_article_bpu d ON d.article_id = f.article_id
WHERE f.article_id IS NOT NULL AND d.article_id IS NULL;

-- 5. Tables V1 a ne pas importer dans le modele V2.
SELECT table_name AS v1_view_to_ignore
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN (
    'v_kpi_capex',
    'v_kpi_batiment',
    'v_kpi_famille',
    'v_kpi_import_local',
    'v_kpi_lot',
    'v_kpi_niveau'
  )
ORDER BY table_name;

