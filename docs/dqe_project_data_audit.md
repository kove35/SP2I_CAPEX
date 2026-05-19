# Audit DQE et donnees projet SP2I

Date : 2026-05-19

Perimetre audite :

- `03_DONNEES_REFERENCE/SP2I_CAPEX_DEMO_V1.xlsx`
- `03_DONNEES_REFERENCE/DATASET_METADATA.json`
- pipeline Excel/DQE : `ServiceAIMapping`, `AIDQEParser`, `ServicePipeline`
- moteur CAPEX : `CalculateurCAPEX`
- couche analytics : `AnalyticsRepository`

## Synthese

Le socle DQE est sain sur le point critique : le moteur selectionne bien la feuille `METRE`, extrait 584 lignes exploitables et conserve les 14 lots officiels. Le total CAPEX brut par lot correspond au recapitulatif officiel.

Les principaux risques restants ne sont plus des problemes de parsing, mais des problemes de gouvernance de donnees :

1. trois valeurs concurrentes existent pour l'economie nette ;
2. le dataset officiel utilise `CAPEX_LOCAL_MONTANT` alors que plusieurs docs parlent encore de `CAPEX_LOCAL` ;
3. la taxonomie famille reste trop faible avec 162 lignes `default` ;
4. les analytics backend exposent encore `default` dans certaines requetes SQL ;
5. la documentation pointe parfois vers `SP2I_CAPEX_DEMO.xlsx` au lieu de `SP2I_CAPEX_DEMO_V1.xlsx`.

## Resultats quantitatifs verifies

Dataset officiel :

- fichier : `03_DONNEES_REFERENCE/SP2I_CAPEX_DEMO_V1.xlsx`
- feuilles : `METRE`, `BPU_LOCAL`, `RECAP_LOTS`, `PARAMETRES_DEMO`
- lignes `METRE` : 584
- lignes `BPU_LOCAL` : 584
- lots : 14
- codes BPU orphelins : 0
- quantites invalides : 0
- designations vides : 0
- lots vides : 0
- total `CAPEX_LOCAL_MONTANT` : 1 129 667 152 FCFA

Repartition projet :

- BATIMENT PRINCIPAL : 244 lignes
- ANNEXE LABORATOIRE : 180 lignes
- PHARMACIE : 48 lignes
- ADMINISTRATION : 44 lignes
- URGENCES : 34 lignes
- IMAGERIE : 34 lignes

Repartition niveaux :

- RDC : 256 lignes
- TERRASSE : 152 lignes
- FONDATIONS : 55 lignes
- NIVEAU 1 : 41 lignes
- NIVEAU 2 : 40 lignes
- LOCAUX TECHNIQUES : 40 lignes

## Validation moteur IA DQE

Le moteur IA retourne :

- status : `SUCCESS`
- feuille recommandee : `METRE`
- source FACT_METRE : `METRE`
- lots detectes : 14
- colonnes reconnues : 9
- score qualite : 0.96
- CAPEX detecte : 1 129 667 152 FCFA
- lignes normalisees : 584

La protection contre les feuilles recapitulatives fonctionne :

- `BPU_LOCAL` n'est pas retenue pour `FACT_METRE`
- `RECAP_LOTS` est classee comme recapitulatif
- la selection prioritaire `METRE` est active

## Ecarts detectes

### 1. Economie nette : trois sources de verite

Valeurs observees :

- Excel `METRE.ECONOMIE` : 152 213 248 FCFA
- `DATASET_METADATA.expected_kpis.economie_nette` : 131 616 229.9 FCFA
- recalcul moteur CAPEX actuel : 122 707 909.5 FCFA

Impact :

- les KPI peuvent differer selon que l'on regarde l'Excel, la metadata, le seed ou le moteur runtime ;
- les demos direction peuvent montrer des chiffres incoherents apres un nouveau seed ;
- les tests QA peuvent passer sur le CAPEX brut mais echouer sur les economies.

Cause probable :

- le fichier Excel contient des colonnes import/local pre-calculees ;
- le pipeline actuel ignore ces economies Excel et recalcule via `CalculateurCAPEX` ;
- `parametres_import_pointe_noire.json` ne fixe pas `coefficient_risque`, donc le moteur utilise le default `1.10`.

Action recommandee :

- definir une source de verite unique pour l'optimisation :
  - soit les colonnes Excel `PU_IMPORT`, `CAPEX_IMPORT`, `ECONOMIE`, `DECISION` ;
  - soit le moteur CAPEX runtime.
- si le moteur runtime est la source officielle, mettre a jour `DATASET_METADATA.json`, `README_DATASET.md` et les attentes QA.
- si l'Excel est la source officielle, adapter `ServicePipeline` pour conserver les decisions/economies du dataset officiel.

### 2. Nom de colonne montant local non standard

Le dataset contient :

- `CAPEX_LOCAL_MONTANT`

La spec initiale et plusieurs docs parlent de :

- `CAPEX_LOCAL`

Le moteur mappe bien `CAPEX_LOCAL_MONTANT` vers `prix_total_ht`, donc le parsing fonctionne. Le risque est surtout contractuel : les utilisateurs, Power BI ou des scripts externes peuvent chercher `CAPEX_LOCAL`.

Action recommandee :

- ajouter une colonne alias `CAPEX_LOCAL` dans `METRE`, ou
- acter officiellement `CAPEX_LOCAL_MONTANT` comme contrat public et corriger toutes les docs qui disent `CAPEX_LOCAL`.

### 3. Taxonomie famille trop faible

Apres normalisation :

- `default` : 162 lignes
- `menuiserie` : 114 lignes
- `gros_oeuvre` : 98 lignes
- `electricite` : 60 lignes
- `plomberie` : 57 lignes
- `climatisation` : 38 lignes
- `peinture` : 36 lignes
- `ascenseur` : 19 lignes

Impact :

- heatmap et sankey ont besoin d'une vraie famille metier ;
- `default` degrade la comprehension par des utilisateurs non techniques ;
- les filtres et insights peuvent etre moins pertinents.

Action recommandee :

- enrichir `DataCleaner.classifier_famille` avec les 14 lots et les familles metier :
  - structure beton ;
  - etancheite ;
  - revetement ;
  - facade ;
  - menuiserie aluminium ;
  - metallerie ;
  - menuiserie bois ;
  - electricite ;
  - CVC ;
  - securite incendie ;
  - plomberie ;
  - cloisons/plafonds ;
  - ascenseur ;
  - peinture.
- remplacer le fallback technique `default` par `classification_en_attente` cote donnees.

### 4. Analytics SQL expose encore `default`

Emplacements observes :

- `AnalyticsRepository.heatmap_rows`
- `AnalyticsRepository.heatmap`
- `vw_procurement_risk`
- `ServicePipeline._generer_dataset_bi`
- `DataCleaner.clean_famille`

Impact :

- meme si le frontend renomme `default`, Power BI et les exports SQL peuvent encore afficher une valeur technique.

Action recommandee :

- normaliser dans PostgreSQL avant exposition ;
- utiliser `classification_en_attente` ou une famille metier deduite du lot.

### 5. Documentation dataset incoherente sur le nom de fichier

`README_DATASET.md` indique encore :

- `SP2I_CAPEX_DEMO.xlsx`

alors que le dataset immutable officiel est :

- `SP2I_CAPEX_DEMO_V1.xlsx`

Action recommandee :

- mettre `README_DATASET.md` a jour ;
- garder `SP2I_CAPEX_DEMO.xlsx` seulement comme alias non immutable si necessaire.

## Points solides

- Le fichier `METRE` contient toutes les lignes attendues.
- Les 14 lots officiels sont presents.
- Les totaux par lot correspondent au recapitulatif officiel.
- Les codes BPU matchent a 100 %.
- Le moteur IA ne prend plus `RECAP_LOTS` comme source principale.
- Les garde-fous de perte massive sont en place.
- La sync DB bloque un `FACT_METRE` vide ou sans CAPEX positif.
- Le seed database verifie lignes, lots et CAPEX brut.

## Priorites recommandees

Priorite 1 :

- choisir la source de verite pour `CAPEX_IMPORT`, `CAPEX_OPTIMISE`, `ECONOMIE`, `DECISION`.
- aligner `DATASET_METADATA.json`, `README_DATASET.md`, seed et moteur CAPEX sur cette source.

Priorite 2 :

- ameliorer la taxonomie famille pour supprimer `default`.

Priorite 3 :

- ajouter un test automatique dataset officiel :
  - 584 lignes extraites ;
  - 14 lots ;
  - total CAPEX brut exact ;
  - 0 code BPU orphelin ;
  - economies attendues selon la source de verite choisie.

Priorite 4 :

- exposer dans `/analytics/qa-summary` un champ de coherence dataset :
  - `metadata_expected_kpis`;
  - `runtime_kpis`;
  - `delta_economie`;
  - `delta_capex_optimise`.

## Conclusion

SP2I n'a plus un probleme majeur de parsing DQE sur le dataset officiel. Le risque principal est maintenant la coherence business des donnees projet : il faut verrouiller la source de verite import/local et renforcer la taxonomie metier avant de faire de ce fichier le standard demo/QA/Power BI definitif.
