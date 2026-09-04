-- SP2I CAPEX - Phase 033 V6 financial reconciliation and project isolation
-- Creates a parallel, project-scoped V6 read model. Legacy V5/V6 views remain intact.

BEGIN;

DO $$
BEGIN
    IF to_regclass('vw_fact_metre_financial_canonical') IS NULL THEN
        RAISE EXCEPTION '033 blocked: missing vw_fact_metre_financial_canonical';
    END IF;
    IF to_regclass('vw_fact_metre_current') IS NULL THEN
        RAISE EXCEPTION '033 blocked: missing vw_fact_metre_current';
    END IF;
    IF to_regclass('vw_bpu_v53_priced_v2') IS NULL THEN
        RAISE EXCEPTION '033 blocked: missing vw_bpu_v53_priced_v2';
    END IF;
    IF to_regclass('dim_projet') IS NULL THEN
        RAISE EXCEPTION '033 blocked: missing dim_projet';
    END IF;
END $$;

CREATE OR REPLACE VIEW vw_fact_metre_financial_v6 AS
WITH direct_candidates AS (
    SELECT DISTINCT
        c.id_ligne AS canonical_id_ligne,
        dp.projet_id,
        dp.projet_code
    FROM vw_fact_metre_financial_canonical c
    JOIN vw_fact_metre_current f
      ON f.article_code = c.article_code
     AND f.lot IS NOT DISTINCT FROM c.lot
     AND f.batiment IS NOT DISTINCT FROM c.batiment
     AND f.niveau IS NOT DISTINCT FROM c.niveau
     AND f.appartement IS NOT DISTINCT FROM c.appartement
     AND f.piece IS NOT DISTINCT FROM c.piece
    JOIN dim_projet dp
      ON (f.projet_id IS NOT NULL AND dp.projet_id = f.projet_id)
      OR (
          NULLIF(TRIM(CAST(f.project_code AS text)), '') IS NOT NULL
          AND LOWER(dp.projet_code) = LOWER(TRIM(CAST(f.project_code AS text)))
      )
),
single_project AS (
    SELECT MIN(projet_id) AS projet_id, MIN(projet_code) AS projet_code
    FROM dim_projet
    HAVING COUNT(*) = 1
),
all_candidates AS (
    SELECT * FROM direct_candidates
    UNION ALL
    SELECT c.id_ligne, sp.projet_id, sp.projet_code
    FROM vw_fact_metre_financial_canonical c
    CROSS JOIN single_project sp
    WHERE NOT EXISTS (
        SELECT 1 FROM direct_candidates dc WHERE dc.canonical_id_ligne = c.id_ligne
    )
),
resolved_project AS (
    SELECT
        canonical_id_ligne,
        MIN(projet_id) AS projet_id,
        MIN(projet_code) AS project_code,
        COUNT(DISTINCT projet_id) AS candidate_count
    FROM all_candidates
    GROUP BY canonical_id_ligne
)
SELECT
    md5(CONCAT_WS('|', rp.projet_id::text, c.id_ligne::text)) AS id_ligne,
    c.id_ligne AS canonical_id_ligne,
    rp.projet_id,
    rp.project_code,
    c.designation,
    c.quantite::numeric AS quantite,
    c.unite,
    c.lot,
    c.lot AS lot_code,
    c.article_code,
    c.sous_lot,
    c.batiment,
    c.niveau,
    c.appartement,
    c.piece,
    c.famille,
    p.prix_local_fcfa::numeric AS prix_local_fcfa,
    p.prix_import_fcfa::numeric AS prix_import_fcfa,
    p.prix_optimise_fcfa::numeric AS prix_optimise_fcfa,
    (c.quantite * p.prix_local_fcfa)::numeric AS capex_local,
    (c.quantite * p.prix_import_fcfa)::numeric AS capex_import,
    (c.quantite * p.prix_optimise_fcfa)::numeric AS capex_optimise,
    (c.quantite * (p.prix_local_fcfa - p.prix_optimise_fcfa))::numeric AS economie,
    CASE WHEN COALESCE(c.quantite * p.prix_local_fcfa, 0) = 0 THEN 0::numeric
         ELSE (c.quantite * (p.prix_local_fcfa - p.prix_optimise_fcfa))
              / NULLIF(c.quantite * p.prix_local_fcfa, 0)
    END AS taux_economie,
    p.decision_import,
    p.pricing_scope,
    p.pricing_confidence,
    p.price_reference_code,
    p.source_prix,
    c.created_at,
    c.date_import
FROM vw_fact_metre_financial_canonical c
JOIN resolved_project rp
  ON rp.canonical_id_ligne = c.id_ligne
 AND rp.candidate_count = 1
JOIN vw_bpu_v53_priced_v2 p
  ON p.article_code = c.article_code;

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

DO $$
DECLARE
    v_canonical BIGINT;
    v_v6 BIGINT;
    v_unresolved BIGINT;
    v_unpriced BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_canonical FROM vw_fact_metre_financial_canonical;
    SELECT COUNT(*) INTO v_v6 FROM vw_fact_metre_financial_v6;
    SELECT COUNT(*) INTO v_unresolved FROM vw_fact_metre_financial_v6
     WHERE projet_id IS NULL OR NULLIF(TRIM(project_code), '') IS NULL;
    SELECT COUNT(*) INTO v_unpriced FROM vw_fact_metre_financial_v6
     WHERE prix_local_fcfa IS NULL OR prix_import_fcfa IS NULL OR prix_optimise_fcfa IS NULL;

    IF v_v6 <> v_canonical THEN
        RAISE EXCEPTION '033 blocked: project lineage mismatch (canonical %, V6 %)', v_canonical, v_v6;
    END IF;
    IF v_unresolved <> 0 THEN
        RAISE EXCEPTION '033 blocked: % V6 rows have no project', v_unresolved;
    END IF;
    IF v_unpriced <> 0 THEN
        RAISE EXCEPTION '033 blocked: % V6 rows have incomplete pricing', v_unpriced;
    END IF;
END $$;

COMMENT ON VIEW vw_fact_metre_financial_v6 IS
'Authoritative V6 financial grain: canonical DQE quantities, V6 article pricing and mandatory project lineage.';
COMMENT ON VIEW vw_project_cost_summary_v6 IS
'Project-scoped V6 project cost summary. Policy rates are exposed explicitly for audit.';
COMMENT ON VIEW vw_dashboard_direction_v6_scoped IS
'Project-scoped V6 direction dashboard; totals cannot cross project boundaries.';
COMMENT ON VIEW vw_cost_intelligence_v6_scoped IS
'Project-scoped V6 cost intelligence by article.';

COMMIT;
