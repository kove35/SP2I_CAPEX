# SP2I CAPEX

SP2I CAPEX est une plateforme metier pour analyser et optimiser les couts de construction dans un contexte BTP.

L'objectif est simple : partir d'un DQE brut, le nettoyer, l'enrichir, comparer les couts locaux avec une strategie d'import, puis produire des fichiers exploitables dans Power BI.

En clair, le projet aide a repondre a ces questions :

- Combien coute vraiment le projet ?
- Quels postes peuvent etre optimises ?
- Est-il plus interessant d'acheter localement ou d'importer ?
- Quels lots, familles ou batiments pesent le plus dans le CAPEX ?
- Comment fournir des donnees propres a Power BI ?

---

## A quoi sert SP2I CAPEX ?

SP2I CAPEX couvre toute la chaine de traitement :

1. Structurer des DQE, c'est-a-dire des Devis Quantitatifs Estimatifs.
2. Nettoyer les donnees chantier : quantites, unites, prix, lots, niveaux.
3. Classer les lignes par famille travaux : gros oeuvre, plomberie, electricite, menuiserie, etc.
4. Simuler une strategie d'import vers Pointe-Noire.
5. Comparer le cout local et le cout importe.
6. Generer des datasets propres pour Power BI.

---

## Objectifs Metier

### 1. Fiabiliser les DQE

Un DQE brut contient souvent des erreurs ou des formats heterogenes.

Le moteur de normalisation sert a :

- nettoyer les nombres ;
- harmoniser les unites ;
- completer les informations manquantes ;
- detecter les lignes suspectes ;
- creer une cle metier stable pour la BI.

### 2. Optimiser les couts d'import

Le moteur import simule un cout complet d'importation.

Il part d'une estimation FOB, puis ajoute :

- transport maritime ;
- assurance ;
- droits de douane ;
- frais portuaires ;
- logistique locale.

Le systeme compare ensuite le prix importe avec le prix local.

### 3. Piloter le CAPEX

Le CAPEX correspond aux depenses d'investissement du projet.

SP2I CAPEX permet de suivre :

- le CAPEX local ;
- le CAPEX optimise ;
- les economies potentielles ;
- les decisions IMPORT ou LOCAL ;
- les analyses par lot, famille, batiment et niveau.

---

## Architecture SaaS

Voici la logique globale du projet :

```text
UTILISATEUR
    |
    v
FRONTEND REACT
    |
    v
API BACKEND FASTAPI
    |
    +--> DQE ENGINE
    |       normalisation, nettoyage, controle qualite
    |
    +--> IMPORT ENGINE
            calcul FOB, landed cost, arbitrage import/local
    |
    v
DATASETS BI
    |
    v
POWER BI
```

Cette organisation prepare le projet a evoluer vers un vrai SaaS :

- une interface utilisateur ;
- une API ;
- des services metier separes ;
- un pipeline data ;
- des exports BI ;
- une base Docker pour l'infrastructure.

---

## Structure Du Projet

```text
SP2I_CAPEX/
|
+-- 01_PARAMETRES/
|   +-- parametres_import_pointe_noire.json
|
+-- 02_REFERENTIELS/
|   +-- mapping_familles.xlsx
|   +-- ratios_fob.xlsx
|
+-- 03_DONNEES_ENTREE/
|   +-- dqe/
|       +-- dqe_source_brut.json
|       +-- dqe_normalise.json
|       +-- dqe_enrichi.json
|
+-- 04_TRAITEMENT/
|   +-- normalisation_dqe.py
|   +-- optimisation_import.py
|   +-- pipeline_complet.pyk
|   +-- utils/
|       +-- clean_numbers.py
|       +-- helpers.py
|
+-- 05_RESULTATS/
|   +-- dqe_pret_powerbi.csv
|   +-- optimisation_capex_import.csv
|   +-- audit_qualite_dqe.xlsx
|
+-- 06_ANALYSE_BI/
|   +-- dataset/
|   |   +-- FACT_METRE.csv
|   |   +-- DIM_FAMILLE.csv
|   +-- POWERBI_CONNEXION.md
|   +-- power_query_postgresql.pq
|
+-- 07_API_BACKEND/
|   +-- app/
|       +-- main.py
|       +-- routes/
|       |   +-- dqe.py
|       |   +-- import.py
|       +-- services/
|           +-- service_dqe.py
|           +-- service_import.py
|
+-- 08_FRONTEND/
|   +-- index.html
|   +-- package.json
|   +-- src/
|       +-- main.jsx
|       +-- styles.css
|       +-- pages/
|       |   +-- Direction.jsx
|       |   +-- Chantier.jsx
|       |   +-- Import.jsx
|       +-- components/
|           +-- Indicateur.jsx
|
+-- 09_INFRA/
|   +-- docker-compose.yml
|
+-- README.md
```

---

## Role De Chaque Dossier

### `01_PARAMETRES`

Contient les hypotheses modifiables du projet.

Exemple : les taux d'import pour Pointe-Noire.

### `02_REFERENTIELS`

Contient les tables de reference metier.

Exemples :

- mapping des familles travaux ;
- ratios FOB par famille.

### `03_DONNEES_ENTREE`

Contient les fichiers DQE utilises par le pipeline.

Le fichier principal d'entree est :

```text
03_DONNEES_ENTREE/dqe/dqe_source_brut.json
```

### `04_TRAITEMENT`

Contient le coeur Python du projet.

- `normalisation_dqe.py` nettoie et structure le DQE.
- `optimisation_import.py` calcule le scenario import/local.
- `pipeline_complet.py` orchestre toute la chaine.
- `utils/` contient les fonctions partagees.

### `05_RESULTATS`

Contient les exports metier.

Ces fichiers servent au controle, au partage ou a l'analyse.

### `06_ANALYSE_BI`

Contient les donnees pretes pour Power BI.

Les fichiers importants sont :

- `FACT_METRE.csv`
- `DIM_FAMILLE.csv`

### `07_API_BACKEND`

Contient l'API FastAPI.

Elle permet d'exposer les traitements Python sous forme de routes web.

### `08_FRONTEND`

Contient l'interface React.

Elle propose trois vues :

- Direction ;
- Chantier ;
- Import.

### `09_INFRA`

Contient les fichiers d'infrastructure, notamment Docker.

---

## Pipeline Data

Le pipeline complet lance toute la chaine de traitement.

Commande :

```powershell
python 04_TRAITEMENT/pipeline_complet.py
```

Etapes executees :

1. Lecture du DQE brut.
2. Nettoyage et normalisation.
3. Enrichissement avec famille, zone et cle metier.
4. Calcul import/local.
5. Generation des resultats.
6. Generation des datasets Power BI.
7. Generation de l'audit qualite DQE.

Fichier lu :

```text
03_DONNEES_ENTREE/dqe/dqe_source_brut.json
```

Fichiers produits :

```text
03_DONNEES_ENTREE/dqe/dqe_normalise.json
03_DONNEES_ENTREE/dqe/dqe_enrichi.json
05_RESULTATS/dqe_pret_powerbi.csv
05_RESULTATS/optimisation_capex_import.csv
05_RESULTATS/audit_qualite_dqe.xlsx
06_ANALYSE_BI/dataset/FACT_METRE.csv
06_ANALYSE_BI/dataset/DIM_FAMILLE.csv
```

---

## Logique Import Pointe-Noire

Le cout importe est calcule a partir du FOB.

Formule :

```text
LANDED COST = FOB x (1 + transport + assurance + douane + port + logistique locale)
```

Parametres par defaut :

| Poste | Taux |
|---|---:|
| Transport maritime | 15% |
| Assurance | 2% |
| Droits de douane | 20% |
| Frais portuaires | 10% |
| Logistique locale | 5% |

Ces parametres sont dans :

```text
01_PARAMETRES/parametres_import_pointe_noire.json
```

---

## Logique CAPEX

Pour chaque ligne du DQE :

```text
CAPEX_LOCAL = prix local
CAPEX_IMPORT = cout importe complet
CAPEX_OPTIMISE = meilleur cout entre local et import
ECONOMIE_NETTE = CAPEX_LOCAL - CAPEX_OPTIMISE
```

Decision :

```text
si CAPEX_IMPORT est meilleur -> IMPORT
sinon -> LOCAL
```

---

## Modele Power BI

### Table `FACT_METRE`

Cette table contient les lignes de metrage et les montants.

| Champ | Description |
|---|---|
| `id_ligne` | identifiant unique de la ligne |
| `designation` | description du poste |
| `quantite` | quantite mesuree |
| `unite` | unite de mesure |
| `prix_total_ht` | cout local |
| `capex_optimise` | cout final optimise |
| `economie_nette` | economie calculee |
| `decision_import` | IMPORT ou LOCAL |
| `lot` | lot travaux |
| `famille` | famille metier |
| `batiment` | batiment concerne |
| `niveau` | niveau ou etage |

### Table `DIM_FAMILLE`

Cette table de dimension decrit les familles travaux.

| Champ | Description |
|---|---|
| `famille` | code famille |
| `libelle_famille` | nom lisible |
| `categorie_achat` | importable ou local dominant |

Relation recommandee dans Power BI :

```text
FACT_METRE[famille] -> DIM_FAMILLE[famille]
```

---

## Idees De Dashboards Power BI

### 1. Direction

- CAPEX total.
- Economie globale.
- Taux d'optimisation.
- Top lots les plus couteux.
- Top familles avec plus fort potentiel d'economie.

### 2. Chantier

- Couts par batiment.
- Couts par niveau.
- Analyse par lot.
- Suivi des lignes DQE en anomalie.

### 3. Import

- Comparaison local vs import.
- Economies par famille.
- Decisions IMPORT / LOCAL.
- Analyse des postes importables.

---

## Lancer Le Backend FastAPI

Installer les dependances Python :

```powershell
pip install -r requirements.txt
```

Lancer l'API :

```powershell
uvicorn app.main:app --app-dir 07_API_BACKEND --reload --port 8000
```

Adresse API :

```text
http://localhost:8000
```

Documentation interactive FastAPI :

```text
http://localhost:8000/docs
```

Endpoints disponibles :

| Methode | Route | Role |
|---|---|---|
| GET | `/health` | verifier que l'API fonctionne |
| POST | `/dqe/upload` | envoyer un DQE JSON |
| POST | `/import/optimize` | lancer l'optimisation import |

---

## Lancer Le Frontend React

Aller dans le dossier frontend :

```powershell
cd 08_FRONTEND
```

Installer les dependances :

```powershell
npm install
```

Lancer l'application :

```powershell
npm run dev
```

Adresse frontend :

```text
http://localhost:5173
```

---

## Lancer Avec Docker

Docker permet de lancer l'API et le frontend ensemble.

```powershell
cd 09_INFRA
docker compose up --build
```

Services disponibles :

| Service | URL |
|---|---|
| API FastAPI | `http://localhost:8000` |
| Frontend React | `http://localhost:5173` |

---

## Controle Qualite DQE

Le moteur detecte notamment :

- quantites invalides ;
- prix unitaires invalides ;
- prix totaux invalides ;
- ecarts entre quantite x prix unitaire et prix total ;
- lignes non exploitables ;
- familles ou zones a verifier.

Le fichier d'audit est genere ici :

```text
05_RESULTATS/audit_qualite_dqe.xlsx
```

---

## Stack Technique

| Couche | Technologie |
|---|---|
| Data | Python |
| API | FastAPI |
| Frontend | React + Vite |
| BI | Power BI |
| Infra | Docker |
| Fichiers | JSON, CSV, XLSX |

---

## Commandes Utiles

Lancer le pipeline complet :

```powershell
python 04_TRAITEMENT/pipeline_complet.py
```

Lancer seulement la normalisation :

```powershell
python 04_TRAITEMENT/normalisation_dqe.py --input 03_DONNEES_ENTREE/dqe/dqe_source_brut.json --output 03_DONNEES_ENTREE/dqe/dqe_normalise.json
```

Lancer seulement l'optimisation import :

```powershell
python 04_TRAITEMENT/optimisation_import.py --input 03_DONNEES_ENTREE/dqe/dqe_normalise.json --output 05_RESULTATS/optimisation_capex_import.csv
```

Tester l'import de l'API :

```powershell
python -c "import sys, importlib; sys.path.insert(0, '07_API_BACKEND'); importlib.import_module('app.main'); print('API OK')"
```

---

## Roadmap

Prochaines evolutions possibles :

- authentification utilisateurs ;
- gestion multi-projets ;
- base PostgreSQL ;
- stockage des imports DQE ;
- extraction automatique de DQE PDF par IA ;
- gestion des fournisseurs ;
- workflow de validation Direction ;
- deploiement cloud ;
- vrais dashboards Power BI connectes.

---

## Resume Pour Debutant

Si tu decouvres le projet, retiens ceci :

1. Tu mets ton DQE brut dans `03_DONNEES_ENTREE/dqe/dqe_source_brut.json`.
2. Tu lances `python 04_TRAITEMENT/pipeline_complet.py`.
3. Le projet nettoie le DQE.
4. Il calcule les economies possibles entre local et import.
5. Il produit les fichiers Power BI dans `06_ANALYSE_BI/dataset/`.
6. Tu peux ensuite lancer l'API et le frontend pour preparer une utilisation SaaS.
