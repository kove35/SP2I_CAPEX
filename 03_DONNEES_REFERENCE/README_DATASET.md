# Dataset de reference SP2I CAPEX DEMO

Fichier officiel :

`SP2I_CAPEX_DEMO.xlsx`

Projet represente :

`CENTRE MEDICAL POINTE-NOIRE`

Ce fichier est le dataset de demonstration, de QA et de test cloud pour SP2I CAPEX. Il sert a valider le workflow complet :

`Excel DQE/BPU -> FastAPI -> PostgreSQL -> Analytics Engine -> React/Vercel -> Power BI`

## Objectifs

Le dataset permet de tester :

- l'import Excel via `/api/upload/excel`
- la synchronisation PostgreSQL via `/api/upload/excel/sync`
- l'alimentation de `fact_metre`
- les KPI CAPEX
- les analyses import/local
- les dashboards React
- les vues Power BI
- les futures briques AG Grid, ECharts, heatmaps et drill-down

## Feuilles Excel

### METRE

Feuille principale a utiliser pour `FACT_METRE`.

Colonnes :

- `BATIMENT`
- `NIVEAU`
- `LOT`
- `DESIGNATION`
- `UNITE`
- `QUANTITE`
- `PU_LOCAL`
- `CAPEX_LOCAL_MONTANT`
- `CODE_BPU`
- `PU_IMPORT`
- `CAPEX_IMPORT`
- `ECONOMIE`
- `TAUX_ECONOMIE`
- `DECISION`
- `ZONE`
- `TYPE_ZONE`
- `STATUT_LIGNE`

### BPU_LOCAL

Referentiel prix associe au metre.

Regle importante :

Tous les `CODE_BPU` presents dans `METRE` existent dans `BPU_LOCAL`.

### RECAP_LOTS

Feuille de controle des montants officiels par lot.

Elle permet de verifier que le dataset respecte le recapitulatif officiel des 14 lots.

### PARAMETRES_DEMO

Feuille documentaire interne au classeur.

Elle decrit :

- le projet
- la ville
- la devise
- la date de generation
- le nombre de lignes
- le total officiel

## Totaux officiels

| Lot | Libelle | Montant FCFA |
| --- | --- | ---: |
| 1 | Gros Oeuvre et Demolition | 218 723 945 |
| 2 | Etancheite | 38 856 005 |
| 3 | Revetement Durs | 152 397 863 |
| 4 | Menuiserie Aluminium et Vitrerie | 109 091 760 |
| 5 | Menuiserie Metallique et Ferronnerie | 11 614 655 |
| 6 | Menuiserie Bois | 24 456 360 |
| 7 | Electricite | 175 755 050 |
| 8 | Climatisation | 68 459 500 |
| 9 | Securite Incendie et Video Surveillance | 18 079 150 |
| 10 | Plomberie Sanitaire | 47 233 525 |
| 11 | Faux Plafond et Cloisons BA13 | 27 520 144 |
| 12 | Ascenseur | 25 300 000 |
| 13 | Alucobond | 159 589 381 |
| 14 | Peinture | 52 589 814 |

Total officiel :

`1 129 667 152 FCFA`

## Contenu QA

Le fichier contient :

- 14 lots obligatoires
- 584 lignes detaillees dans `METRE`
- 584 codes BPU dans `BPU_LOCAL`
- 6 batiments metier
- 6 niveaux
- des zones medicales, techniques, administratives et publiques
- des decisions `IMPORT` et `LOCAL`
- des delais import
- des fournisseurs
- des pays source
- des risques import

## Batiments couverts

- `BATIMENT PRINCIPAL`
- `ANNEXE LABORATOIRE`
- `URGENCES`
- `PHARMACIE`
- `IMAGERIE`
- `ADMINISTRATION`

## Niveaux couverts

- `FONDATIONS`
- `RDC`
- `NIVEAU 1`
- `NIVEAU 2`
- `TERRASSE`
- `LOCAUX TECHNIQUES`

## Regles de controle

Avant d'utiliser le dataset en demo, verifier :

1. `METRE` contient bien les 14 lots.
2. La somme `CAPEX_LOCAL` par lot correspond aux montants officiels.
3. Le total `CAPEX_LOCAL` vaut `1 129 667 152`.
4. Aucun `CODE_BPU` de `METRE` n'est absent de `BPU_LOCAL`.
5. Les colonnes `QUANTITE`, `PU_LOCAL`, `CAPEX_LOCAL_MONTANT` sont numeriques.
6. Les champs `BATIMENT`, `NIVEAU`, `LOT` ne sont pas vides.

Note technique :

La colonne du montant local s'appelle `CAPEX_LOCAL_MONTANT` pour rester lisible cote metier tout en etant detectee par le moteur de mapping Excel SP2I comme un montant total. Le pipeline alimente ensuite `capex_local` dans PostgreSQL.

## Utilisation recommandee

Pour tester SP2I en local ou en cloud :

1. Ouvrir le cockpit React.
2. Aller dans `Donnees & DQE`.
3. Importer `03_DONNEES_REFERENCE/SP2I_CAPEX_DEMO.xlsx`.
4. Lancer l'analyse IA.
5. Verifier le preview.
6. Synchroniser PostgreSQL.
7. Controler `/analytics/kpis`.
8. Controler `/analytics/dashboard`.
9. Ouvrir Power BI ou les dashboards React.

## Role produit

Ce dataset represente un projet de centre medical realiste pour Pointe-Noire. Il met SP2I dans son vrai positionnement :

- pilotage immobilier
- pilotage CAPEX
- controle DQE
- arbitrage import/local
- procurement analytics
- logistique chantier
- analytics direction

Il ne s'agit pas d'un simple fichier de demonstration visuelle. C'est un dataset de reference pour tester la robustesse du moteur SP2I.
