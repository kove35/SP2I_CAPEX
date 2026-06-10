# Relations Power BI V5.3

## Relations conservees - univers Reel

- `dim_batiment[batiment]` -> `fact_metre[batiment]`
- `dim_niveau[niveau]` -> `fact_metre[niveau]`
- `dim_lot[lot_code]` -> `fact_metre[lot]`
- `dim_piece[piece_id]` -> `fact_metre[piece_id]` si disponible

Cardinalite recommandee: dimensions en 1 vers faits en N, filtre simple direction dimension vers fait.

## Relations Generatif

- `dim_batiment[batiment_id]` -> `vw_sp2i_generated_quantities[batiment_id]`
- `dim_niveau[niveau_id]` -> `vw_sp2i_generated_quantities[niveau_id]`
- `dim_piece[piece_id]` -> `vw_sp2i_generated_quantities[piece_id]`
- `dim_lot[lot_code]` -> `vw_sp2i_generated_quantities[lot_code]`

`vw_sp2i_generated_capex` peut rester en table KPI isolee par `generation_batch`.

## Relations Energie

- `vw_energy_resilience_dashboard[batiment]` peut filtrer par dimension batiment si les libelles sont normalises.
- `vw_energy_sources_dashboard[lot_code]` -> `dim_lot[lot_code]`.
- `vw_generator_dashboard` reste table detail groupe, reliee par `project_code` et `batiment` uniquement si necessaire.

## Relations Completude batiment

Relier par `lot_code` vers `dim_lot` si les codes existent. Garder les vues V5.3 de completude separees de `fact_metre`.

## Interdictions

- Pas de relation active directe entre `fact_metre` et `vw_sp2i_generated_capex`.
- Pas de mesure additionnant `SUM(fact_metre[capex])` et `SUM(vw_sp2i_generated_capex[capex])`.
- Pas de relation bi-directionnelle entre univers Reel et Generatif.
