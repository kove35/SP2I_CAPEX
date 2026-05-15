/*
SP2I CAPEX - Correction des ratios KPI Power BI

Probleme corrige :
- une moyenne de ratios ligne par ligne peut produire un taux global faux ;
- un taux financier global doit etre calcule par ratio des totaux.

Regle SP2I :
    taux_economie = SUM(economie) / SUM(capex_local) * 100

Important PostgreSQL :
    round(double precision, integer) n'existe pas.
    Les sommes sont donc converties en numeric avant ROUND(..., 2).
*/

BEGIN;

DROP VIEW IF EXISTS
    v_kpi_capex,
    v_kpi_lot,
    v_kpi_famille,
    v_kpi_niveau,
    v_kpi_batiment,
    v_kpi_import_local,
    v_qualite_dqe;

CREATE OR REPLACE VIEW v_kpi_capex AS
SELECT
    COUNT(*) AS nombre_lignes,
    ROUND(COALESCE(SUM(capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(capex_import), 0)::NUMERIC, 2) AS capex_import_total,
    ROUND(COALESCE(SUM(capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(
        CASE
            WHEN COALESCE(SUM(capex_local), 0) = 0 THEN 0
            ELSE (
                COALESCE(SUM(economie), 0)::NUMERIC
                / NULLIF(SUM(capex_local), 0)::NUMERIC
            ) * 100
        END,
        2
    ) AS taux_economie_global
FROM fact_metre;

CREATE OR REPLACE VIEW v_kpi_lot AS
SELECT
    l.lot_id,
    l.lot,
    l.ordre_lot,
    COUNT(f.id_ligne) AS nombre_lignes,
    ROUND(COALESCE(SUM(f.capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(f.capex_import), 0)::NUMERIC, 2) AS capex_import_total,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(f.economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(
        CASE
            WHEN COALESCE(SUM(f.capex_local), 0) = 0 THEN 0
            ELSE (
                COALESCE(SUM(f.economie), 0)::NUMERIC
                / NULLIF(SUM(f.capex_local), 0)::NUMERIC
            ) * 100
        END,
        2
    ) AS taux_economie
FROM dim_lot l
LEFT JOIN fact_metre f ON f.lot_id = l.lot_id
GROUP BY l.lot_id, l.lot, l.ordre_lot;

CREATE OR REPLACE VIEW v_kpi_famille AS
SELECT
    d.famille_id,
    d.famille,
    d.categorie,
    d.importable,
    COUNT(f.id_ligne) AS nombre_lignes,
    ROUND(COALESCE(SUM(f.capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(f.capex_import), 0)::NUMERIC, 2) AS capex_import_total,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(f.economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(
        CASE
            WHEN COALESCE(SUM(f.capex_local), 0) = 0 THEN 0
            ELSE (
                COALESCE(SUM(f.economie), 0)::NUMERIC
                / NULLIF(SUM(f.capex_local), 0)::NUMERIC
            ) * 100
        END,
        2
    ) AS taux_economie
FROM dim_famille d
LEFT JOIN fact_metre f ON f.famille_id = d.famille_id
GROUP BY d.famille_id, d.famille, d.categorie, d.importable;

CREATE OR REPLACE VIEW v_kpi_niveau AS
SELECT
    n.niveau_id,
    n.niveau,
    n.ordre_niveau,
    COUNT(f.id_ligne) AS nombre_lignes,
    ROUND(COALESCE(SUM(f.capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(f.capex_import), 0)::NUMERIC, 2) AS capex_import_total,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(f.economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(
        CASE
            WHEN COALESCE(SUM(f.capex_local), 0) = 0 THEN 0
            ELSE (
                COALESCE(SUM(f.economie), 0)::NUMERIC
                / NULLIF(SUM(f.capex_local), 0)::NUMERIC
            ) * 100
        END,
        2
    ) AS taux_economie
FROM dim_niveau n
LEFT JOIN fact_metre f ON f.niveau_id = n.niveau_id
GROUP BY n.niveau_id, n.niveau, n.ordre_niveau;

CREATE OR REPLACE VIEW v_kpi_batiment AS
SELECT
    b.batiment_id,
    b.batiment,
    b.type_batiment,
    COUNT(f.id_ligne) AS nombre_lignes,
    ROUND(COALESCE(SUM(f.capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(f.capex_import), 0)::NUMERIC, 2) AS capex_import_total,
    ROUND(COALESCE(SUM(f.capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(f.economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(
        CASE
            WHEN COALESCE(SUM(f.capex_local), 0) = 0 THEN 0
            ELSE (
                COALESCE(SUM(f.economie), 0)::NUMERIC
                / NULLIF(SUM(f.capex_local), 0)::NUMERIC
            ) * 100
        END,
        2
    ) AS taux_economie
FROM dim_batiment b
LEFT JOIN fact_metre f ON f.batiment_id = b.batiment_id
GROUP BY b.batiment_id, b.batiment, b.type_batiment;

CREATE OR REPLACE VIEW v_kpi_import_local AS
SELECT
    decision_import,
    COUNT(*) AS nombre_lignes,
    ROUND(COALESCE(SUM(capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(COALESCE(SUM(capex_import), 0)::NUMERIC, 2) AS capex_import_total,
    ROUND(COALESCE(SUM(capex_optimise), 0)::NUMERIC, 2) AS capex_optimise_total,
    ROUND(COALESCE(SUM(economie), 0)::NUMERIC, 2) AS economie_totale,
    ROUND(
        CASE
            WHEN COALESCE(SUM(capex_local), 0) = 0 THEN 0
            ELSE (
                COALESCE(SUM(economie), 0)::NUMERIC
                / NULLIF(SUM(capex_local), 0)::NUMERIC
            ) * 100
        END,
        2
    ) AS taux_economie
FROM fact_metre
GROUP BY decision_import;

CREATE OR REPLACE VIEW v_qualite_dqe AS
SELECT
    statut_ligne,
    COUNT(*) AS nombre_lignes,
    ROUND(COALESCE(SUM(capex_local), 0)::NUMERIC, 2) AS capex_local_total,
    ROUND(
        (
            COUNT(*)::NUMERIC
            / NULLIF((SELECT COUNT(*) FROM fact_metre), 0)::NUMERIC
        ) * 100,
        2
    ) AS part_lignes_pct,
    CASE WHEN statut_ligne = 'OK' THEN 1 ELSE 0 END AS score_qualite_ligne
FROM fact_metre
GROUP BY statut_ligne;

COMMIT;
