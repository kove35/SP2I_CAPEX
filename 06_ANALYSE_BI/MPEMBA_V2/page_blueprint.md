# Pages Power BI - SP2I CAPEX MPEMBA V2

## 01_DIRECTION

Filtres :

- Projet
- Batiment
- Niveau
- Appartement
- Lot
- Sous-lot

KPI :

- `CAPEX Total`
- `CAPEX Optimise`
- `Economie`
- `Taux Economie`
- `CAPEX/m2`

Visuels :

- Waterfall CAPEX : `CAPEX Total -> CAPEX Optimise -> Economie`
- Pareto article : `dim_article_bpu[designation]` + `CAPEX Optimise` + `Pareto % Article`
- Bar chart top lots : `dim_lot[lot]` + `CAPEX Optimise`
- Bar chart top sous-lots : `dim_sous_lot_complet[sous_lot]` + `CAPEX Optimise`
- Matrix spatial : hierarchie spatiale + `CAPEX Optimise`, `CAPEX/m2`, `Economie`

## 02_COST_INTELLIGENCE

Filtres :

- Batiment
- Niveau
- Appartement
- Zone
- Piece
- Lot

KPI :

- piece la plus couteuse via Top N sur `dim_piece`
- lot le plus couteux via Top N sur `dim_lot`
- top economie via Top N sur `Economie`
- anomalies detectees via `Anomalie CAPEX/m2`

Visuels :

- benchmark appartements : `dim_appartement[appartement_code]` + `CAPEX Optimise`, `CAPEX/m2`, `Ecart CAPEX Appartement`
- benchmark pieces : `dim_piece[piece_nom]` + `CAPEX Piece Moyen`, `CAPEX Piece Ecart`
- scatter anomalies : `CAPEX/m2` vs `CAPEX Optimise`, taille `Economie`
- table anomalies : Appartement, Piece, Lot, Article, CAPEX/m2, Criticite

## 03_PROCUREMENT

Filtres :

- Decision import
- Lot
- Sous-lot
- Article
- Fournisseur si disponible

KPI :

- `CAPEX Importable`
- `CAPEX Local Retenu`
- `CAPEX Hybride`
- `ROI Import`
- `Part Import`
- `Part Local`

Visuels :

- donut Local / Import / Hybride
- bar chart ROI Import par lot
- matrice lot / sous-lot / article avec CAPEX Local, CAPEX Import, CAPEX Optimise, Economie
- table risques fournisseurs/logistiques si colonnes disponibles dans `fact_metre`

## 04_HEATMAP_BIM

Filtres :

- Projet
- Batiment
- Niveau
- Appartement
- Zone
- Piece

KPI :

- `CAPEX Optimise`
- `CAPEX/m2`
- `Economie`
- `Risque Moyen`

Visuels :

- matrice heatmap : Appartement -> Zone -> Piece, valeurs `CAPEX Optimise`
- matrice heatmap : Appartement -> Zone -> Piece, valeurs `CAPEX/m2`
- decomposition tree : Projet -> Batiment -> Niveau -> Appartement -> Zone -> Piece
- table detail : Lot, Sous-lot, Article, CAPEX Local, CAPEX Optimise, Economie

