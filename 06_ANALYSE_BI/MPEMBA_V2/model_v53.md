# Modele Power BI V5.3

Objectif: integrer les couches generatives sans casser le modele reel existant.

## Univers 1 - Reel

Tables:
- `fact_metre`
- `fact_simulation`
- `procurement_decisions`
- dimensions existantes: `dim_batiment`, `dim_niveau`, `dim_appartement`, `dim_piece`, `dim_lot`

Usage: CAPEX officiel, simulation validee, arbitrages achat.

## Univers 2 - Generatif

Tables/vues:
- `vw_sp2i_generated_capex`
- `vw_sp2i_generated_quantities`
- `vw_energy_resilience_dashboard`
- `vw_generator_dashboard`
- `vw_energy_sources_dashboard`

Usage: projection DQE, quantites detaillees, energie, autonomie, equipements techniques.

## Univers 3 - Completude batiment

Tables/vues:
- `vw_sp2i_generated_building`
- `vw_sp2i_generated_envelope`
- `vw_sp2i_generated_special_systems`

Usage: GO, maconnerie, toiture, facade, menuiseries, VRD, securite, incendie, ascenseur.

## Regle anti double comptage

`fact_metre` reste le CAPEX reel. Les vues `vw_sp2i_generated_*` restent le CAPEX genere ou les lignes de couverture. Toute comparaison doit passer par des mesures DAX nommees `Reel`, `Genere`, `Comparaison` ou `Couverture`.
