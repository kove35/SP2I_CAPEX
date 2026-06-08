# SP2I CAPEX MPEMBA V2 - Modele Power BI Enterprise

Ce dossier remplace le modele Power BI V1 pour le projet `Complexe Immobilier Mpemba`.

Source unique :

- Serveur : `<NEON_HOST>`
- Base : `neondb`
- Mode Power BI : `Import`
- Referentiel : `SP2I_BIM_DQE_MASTER.xlsx`

Ne pas utiliser DirectQuery pour ce modele.

## Tables a importer

Fact :

- `fact_metre`

Dimensions :

- `dim_projet`
- `dim_batiment`
- `dim_niveau`
- `dim_appartement`
- `dim_zone`
- `dim_piece`
- `vw_dim_lot_active` importee dans Power BI sous le nom `DimLot`
- `vw_dim_sous_lot_active` importee dans Power BI sous le nom `DimSousLotComplet`
- `vw_dim_article_bpu_active` importee dans Power BI sous le nom `DimArticleBpu`

Tables a ne pas importer :

- `v_kpi_capex`
- `v_kpi_batiment`
- `v_kpi_famille`
- `v_kpi_import_local`
- `v_kpi_lot`
- `v_kpi_niveau`

Les KPI sont reconstruits en DAX sur le schema en etoile.

## Relations cible

Toutes les relations doivent etre :

- cardinalite `1 -> *`
- direction unique de la dimension vers `fact_metre`
- aucune relation Many-to-Many
- aucune relation bidirectionnelle
- aucune relation Fact vers Fact
- aucune relation Dimension vers Dimension

Relations :

```text
dim_projet[projet_id]                         1 -> * fact_metre[projet_id]
dim_batiment[batiment_id]                     1 -> * fact_metre[batiment_id]
dim_niveau[niveau_id]                         1 -> * fact_metre[niveau_id]
dim_appartement[appartement_id]               1 -> * fact_metre[appartement_id]
dim_zone[zone_id]                             1 -> * fact_metre[zone_id]
dim_piece[piece_id]                           1 -> * fact_metre[piece_id]
DimLot[lot]                                   1 -> * FactMetre[lot]
DimSousLotComplet[sous_lot_id]                1 -> * FactMetre[sous_lot_id]
DimArticleBpu[code_article]                   1 -> * FactMetre[code_article]
```

Si Power BI detecte une relation historique `lot_id` numerique vers un code BIM texte, la supprimer et recreer la relation par le code metier stable indique ci-dessus.

## Hierarchies

Hierarchie spatiale :

```text
Projet -> Batiment -> Niveau -> Appartement -> Zone -> Piece
```

Hierarchie technique :

```text
Lot -> Sous-lot -> Article
```

## Dossiers de mesures

Creer une table vide `Mesures SP2I` dans Power BI, puis ranger les mesures dans :

- `_KPI_DIRECTION`
- `_KPI_COST_INTELLIGENCE`
- `_KPI_PROCUREMENT`
- `_KPI_RISK`

Les mesures prioritaires sont dans [measures_dax.md](./measures_dax.md).

## Pages

### 01_DIRECTION

Objectif : pilotage executif.

Visuels :

- cartes KPI : CAPEX Total, CAPEX/m2, Economie, Taux economie
- Pareto CAPEX par article
- Top lots
- Top sous-lots
- Top articles
- decomposition spatiale par batiment / niveau / appartement

### 02_COST_INTELLIGENCE

Objectif : benchmark et anomalies.

Visuels :

- benchmark appartements
- benchmark pieces
- top pieces les plus couteuses
- top sous-lots
- top articles
- table anomalies

### 03_PROCUREMENT

Objectif : arbitrages achats.

Visuels :

- repartition Local / Import / Hybride
- ROI Import
- risque fournisseur
- risque logistique
- performance achats par lot / sous-lot / article

### 04_HEATMAP_BIM

Objectif : pilotage spatial.

Visuels :

- matrice Batiment / Niveau / Appartement / Zone / Piece
- heatmap CAPEX
- heatmap CAPEX/m2
- heatmap Economie
- heatmap Risque

## Optimisation Power BI

Desactiver :

- Auto Date Time
- relations automatiques apres import, si elles creent des liens texte ou bidirectionnels

Masquer :

- cles techniques
- cles etrangeres dans `fact_metre`
- colonnes de jointure
- colonnes de support non metier

Conserver visibles :

- mesures
- hierarchies
- attributs metier

## Fichiers

- [power_query_neon_import.pq](./power_query_neon_import.pq) : requetes Power Query Import.
- [measures_dax.md](./measures_dax.md) : mesures DAX prioritaires.
- [model_validation.sql](./model_validation.sql) : controles SQL Neon avant refresh Power BI.
- [page_blueprint.md](./page_blueprint.md) : structure detaillee des pages.
- [02_analyse_couts_audit.sql](./02_analyse_couts_audit.sql) : audit SQL de la page 02_ANALYSE_COUTS.
- [02_analyse_couts_report.md](./02_analyse_couts_report.md) : diagnostic et plan de correction de la page 02_ANALYSE_COUTS.
