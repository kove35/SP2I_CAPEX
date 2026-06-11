-- SP2I CAPEX - Rollback non destructif V5.2.2 Energy Resilience
-- Fichier: rollback_013_v52_2.sql
--
-- Strategie:
-- - ne pas DROP TABLE ;
-- - ne pas DROP VIEW ;
-- - ne pas toucher aux objets historiques ;
-- - desactiver les referentiels energie V5.2.2 ;
-- - conserver les faits energie pour audit.

BEGIN;

UPDATE dim_energy_equipment
SET is_active = FALSE
WHERE equipment_code IN (
    'CELLULE_BT',
    'COMPTEUR_GENERAL',
    'ANALYSEUR_RESEAU',
    'SECTIONNEUR',
    'DISJONCTEUR_GENERAL',
    'TGBT',
    'JEU_BARRES',
    'DISJONCTEUR_DEPART',
    'PANNEAU_550W',
    'STRUCTURE_PV',
    'CONNECTEUR_MC4',
    'COFFRET_DC',
    'PARAFOUDRE_DC',
    'ONDULEUR_30KW',
    'BATTERIE_LIFEPO4',
    'BMS',
    'RACK_BATTERIE',
    'GEN_150KVA',
    'CUVE_3000L',
    'CUVE_5000L',
    'ATS_400A',
    'TABLEAU_SECOURS',
    'CONTROLEUR_ENERGIE',
    'PASSERELLE_MODBUS',
    'SERVEUR_MONITORING',
    'PIQUET_TERRE',
    'BARRETTE_COUPURE',
    'CUIVRE_NU',
    'PARATONNERRE',
    'DESCENTE_FOUDRE',
    'PARAFOUDRE_T1',
    'PARAFOUDRE_T2',
    'COMPTEUR_COMMUNICANT',
    'PASSERELLE_IOT',
    'DATA_LOGGER'
);

UPDATE dim_energy_system
SET is_active = FALSE
WHERE system_code IN (
    'RESEAU_PUBLIC',
    'SOLAIRE',
    'BATTERIE',
    'GROUPE',
    'ATS',
    'EMS',
    'FOUDRE',
    'TERRE',
    'TELEGESTION'
);

UPDATE dim_generator_system
SET is_active = FALSE
WHERE generator_code IN ('GEN_080KVA', 'GEN_150KVA', 'GEN_250KVA');

CREATE OR REPLACE VIEW vw_energy_resilience_dashboard AS
SELECT
    NULL::VARCHAR(120) AS project_code,
    NULL::VARCHAR(120) AS batiment,
    0::NUMERIC(14, 2) AS surface_m2,
    0::INTEGER AS apartment_count,
    0::NUMERIC(12, 2) AS solar_kwc,
    0::INTEGER AS panel_count,
    0::NUMERIC(12, 2) AS battery_capacity_kwh,
    NULL::VARCHAR(80) AS generator_code,
    NULL::VARCHAR(255) AS generator_name,
    0::NUMERIC(12, 2) AS generator_power_kva,
    0::NUMERIC(12, 2) AS fuel_tank_liters,
    0::NUMERIC(12, 2) AS estimated_daily_consumption_kwh,
    0::NUMERIC(12, 2) AS estimated_daily_solar_kwh,
    0::NUMERIC(12, 2) AS autonomie_batteries_h,
    0::NUMERIC(12, 2) AS autonomie_carburant_h,
    0::NUMERIC(12, 2) AS autonomie_totale_h,
    0::NUMERIC(12, 4) AS taux_couverture_solaire,
    0::NUMERIC(12, 4) AS kwc_m2,
    NULL::TIMESTAMPTZ AS created_at
WHERE false;

CREATE OR REPLACE VIEW vw_generator_dashboard AS
SELECT
    NULL::VARCHAR(120) AS project_code,
    NULL::VARCHAR(120) AS batiment,
    NULL::VARCHAR(80) AS generator_code,
    NULL::VARCHAR(255) AS generator_name,
    0::NUMERIC(12, 2) AS puissance_kva,
    0::NUMERIC(12, 2) AS temps_fonctionnement_h,
    0::NUMERIC(12, 2) AS consommation_l_h,
    0::NUMERIC(12, 2) AS consommation_jour_l,
    NULL::VARCHAR(80) AS fuel_type,
    FALSE::BOOLEAN AS is_recommended,
    0::NUMERIC(12, 2) AS heures_historique,
    0::NUMERIC(12, 2) AS litres_historique,
    0::NUMERIC(16, 2) AS cout_historique
WHERE false;

CREATE OR REPLACE VIEW vw_energy_sources_dashboard AS
SELECT
    NULL::VARCHAR(120) AS generation_batch,
    NULL::VARCHAR(80) AS system_code,
    NULL::VARCHAR(255) AS system_name,
    NULL::VARCHAR(120) AS lot_code,
    NULL::VARCHAR(120) AS equipment_code,
    NULL::VARCHAR(255) AS equipment_name,
    NULL::TEXT AS generated_article_code,
    NULL::TEXT AS generated_designation,
    0::NUMERIC(14, 4) AS quantity,
    NULL::VARCHAR(40) AS unit,
    0::INTEGER AS component_index,
    0::BIGINT AS total_generated_dqe_lines,
    0::NUMERIC(14, 4) AS system_quantity_total
WHERE false;

COMMIT;
