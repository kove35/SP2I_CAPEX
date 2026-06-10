# Page 05 - GENERATION_ENGINE

## Objectif

Afficher le moteur generatif V5.2/V5.2.1 sans le melanger au CAPEX reel.

## Sources

- `vw_sp2i_generated_capex`
- `vw_sp2i_generated_quantities`

## KPIs

- Nb lignes BIM
- Nb lignes reseaux
- Nb lignes DQE
- Nb lignes expansion
- Nb lignes batiment
- Couverture projet
- CAPEX genere local
- CAPEX genere import
- Economie potentielle

## Visuels

- Cartes KPI haut de page.
- Bar chart par `lot_code`.
- Matrice `lot_code` x `generated_article_code`.
- Table detaillee: `generated_designation`, `quantity`, `unit`, `source_quantity`, `source_surface_m2`.

## Mesures

Utiliser uniquement les mesures prefixees `Genere` et `Couverture`. Les mesures `Reel` peuvent etre affichees dans un bloc comparaison separe, jamais additionnees.
