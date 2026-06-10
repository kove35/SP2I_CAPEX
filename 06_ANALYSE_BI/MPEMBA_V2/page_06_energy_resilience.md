# Page 06 - RESILIENCE_ENERGETIQUE

## Objectif

Suivre l'autonomie energetique BAT_01 et les equipements V5.2.2.

## Sources

- `vw_energy_resilience_dashboard`
- `vw_generator_dashboard`
- `vw_energy_sources_dashboard`

## KPIs

- Autonomie energetique
- Production solaire kWc
- Consommation estimee
- Couverture solaire
- Batteries kWh
- Groupe electrogene
- Autonomie eau si la table eau est exposee dans une version suivante

## Visuels

- Cartes energie.
- Donut par `system_code`.
- Table groupe electrogene: puissance, consommation, historique litres, cout.
- Matrice equipements par `lot_code` et `system_name`.

## Garde-fou

Cette page ne doit pas utiliser `fact_metre` pour calculer un cout reel. Les couts sont techniques/prospectifs.
