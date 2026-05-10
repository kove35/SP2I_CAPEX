# SP2I CAPEX

SP2I CAPEX est une plateforme métier BTP pour normaliser des DQE, analyser les coûts de construction, simuler des stratégies d'import et produire des datasets prêts pour Power BI.

Le projet combine un pipeline data Python, une API FastAPI, un frontend React, des exports BI et une base Docker pour préparer une évolution SaaS.

---

## 2. Problématique métier

Dans un projet immobilier, les DQE contiennent souvent des données hétérogènes :

- désignations non normalisées ;
- quantités ou prix manquants ;
- lots mal structurés ;
- familles travaux difficiles à analyser ;
- écarts entre prix unitaires, quantités et montants totaux ;
- absence de modèle exploitable directement dans Power BI.

Ces limites rendent le pilotage CAPEX difficile pour une direction, un maître d'ouvrage ou une équipe projet.

SP2I CAPEX répond à un besoin simple : transformer un DQE brut en données fiables pour décider, comparer et piloter.

---

## 3. Objectifs du projet

| Objectif | Description |
|---|---|
| Fiabiliser les DQE | Nettoyer les quantités, prix, unités, lots, niveaux et statuts qualité. |
| Structurer les données | Créer des clés métier, familles travaux et zones d'analyse. |
| Comparer local vs import | Simuler un coût complet d'import vers Pointe-Noire. |
| Optimiser le CAPEX | Identifier les lignes où l'import peut générer une économie. |
| Produire des datasets BI | Générer des tables FACT et DIM prêtes pour Power BI. |
| Préparer un SaaS | Exposer les traitements via FastAPI et préparer une interface React. |

---

## 4. Fonctionnalités principales

### Fonctionnalités data

- lecture d'un DQE brut au format JSON ;
- normalisation des désignations, unités, quantités et prix ;
- classification automatique par famille travaux ;
- création d'une clé métier stable ;
- détection des anomalies qualité ;
- export CSV pour exploitation métier et Power BI.

### Fonctionnalités CAPEX

- calcul du montant local ;
- estimation du prix FOB ;
- calcul du landed cost import ;
- comparaison entre achat local et import ;
- décision automatique `LOCAL` ou `IMPORT` ;
- calcul de l'économie nette.

### Fonctionnalités SaaS

- backend FastAPI ;
- routes API pour DQE et optimisation import ;
- frontend React / Vite ;
- architecture compatible Docker ;
- séparation claire entre data, API, frontend et BI.

---

## 5. Architecture SaaS

```text
UTILISATEUR
    |
    v
FRONTEND REACT
    |
    v
API BACKEND FASTAPI
    |
    +--> SERVICE DQE
    |       - upload ou lecture DQE
    |       - normalisation
    |       - contrôle qualité
    |
    +--> SERVICE IMPORT
    |       - calcul FOB
    |       - landed cost
    |       - arbitrage local/import
    |
    +--> PIPELINE DATA PYTHON
    |       - orchestration complète
    |       - exports CSV / JSON / Excel
    |
    v
DATASETS BI
    |
    v
POWER BI
```

Cette architecture sépare les responsabilités :

| Couche | Rôle |
|---|---|
| Frontend | Interface utilisateur pour lancer, consulter et analyser. |
| API | Point d'entrée applicatif pour exposer les traitements. |
| Pipeline data | Moteur de transformation et de calcul. |
| Exports BI | Données propres pour analyse décisionnelle. |
| Infra | Base Docker pour industrialiser le déploiement. |

---

## 6. Structure du projet

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
|   +-- pipeline_complet.py
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
|   +-- modele_powerbi.pbix
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

| Dossier | Description |
|---|---|
| `01_PARAMETRES` | Hypothèses modifiables, notamment les taux d'import. |
| `02_REFERENTIELS` | Référentiels métier : familles travaux, ratios FOB, règles d'analyse. |
| `03_DONNEES_ENTREE` | Fichiers DQE source et fichiers enrichis. |
| `04_TRAITEMENT` | Coeur Python : normalisation, optimisation, pipeline complet. |
| `05_RESULTATS` | Exports métier : CSV, Excel, audit qualité. |
| `06_ANALYSE_BI` | Tables propres pour Power BI. |
| `07_API_BACKEND` | Backend FastAPI. |
| `08_FRONTEND` | Frontend React. |
| `09_INFRA` | Fichiers Docker et infrastructure. |

---

## 7. Pipeline data

Le pipeline complet orchestre toute la chaîne de traitement.

Commande principale :

```powershell
python 04_TRAITEMENT/pipeline_complet.py
```

### Étapes exécutées

| Étape | Nom | Description |
|---:|---|---|
| 1 | Normalisation DQE | Lecture du JSON source, nettoyage des champs et structuration des lignes. |
| 2 | Enrichissement | Ajout des familles, zones, niveaux, statuts et clés métier. |
| 3 | Optimisation import | Simulation local/import et calcul du CAPEX optimisé. |
| 4 | Génération dataset BI | Production de `FACT_METRE.csv` et `DIM_FAMILLE.csv`. |
| 5 | Audit qualité | Export des anomalies dans un fichier Excel. |

### Fichier d'entrée

```text
03_DONNEES_ENTREE/dqe/dqe_source_brut.json
```

### Fichiers générés

| Fichier | Rôle |
|---|---|
| `03_DONNEES_ENTREE/dqe/dqe_normalise.json` | DQE nettoyé et normalisé. |
| `03_DONNEES_ENTREE/dqe/dqe_enrichi.json` | DQE enrichi pour analyse. |
| `05_RESULTATS/dqe_pret_powerbi.csv` | Export tabulaire du DQE. |
| `05_RESULTATS/optimisation_capex_import.csv` | Résultat local/import. |
| `05_RESULTATS/audit_qualite_dqe.xlsx` | Audit des lignes à contrôler. |
| `06_ANALYSE_BI/dataset/FACT_METRE.csv` | Table de faits Power BI. |
| `06_ANALYSE_BI/dataset/DIM_FAMILLE.csv` | Dimension familles Power BI. |

---

## 8. Logique import

SP2I CAPEX estime un coût complet d'import à partir d'un prix FOB.

```text
LANDED COST = FOB x (1 + transport + assurance + douane + port + logistique locale)
```

### Paramètres par défaut

| Poste | Taux |
|---|---:|
| Transport maritime | 15 % |
| Assurance | 2 % |
| Droits de douane | 20 % |
| Frais portuaires | 10 % |
| Logistique locale | 5 % |

Les paramètres sont configurés ici :

```text
01_PARAMETRES/parametres_import_pointe_noire.json
```

### Principe FOB

Le FOB représente une estimation du coût produit avant transport international. Quand le DQE ne fournit pas de prix FOB, le moteur l'estime à partir :

- du prix local ;
- de la famille travaux ;
- d'un ratio métier ;
- d'un coefficient de risque.

---

## 9. Logique CAPEX

Pour chaque ligne DQE, le moteur compare deux scénarios :

| Scénario | Description |
|---|---|
| Local | Achat ou exécution au prix local du DQE. |
| Import | Achat importé avec transport, assurance, douane, port et logistique. |

Formules principales :

```text
MONTANT_LOCAL = prix_total_ht
PRIX_IMPORT_TTC = coût import complet
CAPEX_OPTIMISE = meilleur coût entre local et import
ECONOMIE_NETTE = MONTANT_LOCAL - CAPEX_OPTIMISE
```

Décision :

```text
si PRIX_IMPORT_TTC est significativement inférieur au prix local
    alors DECISION = IMPORT
sinon
    DECISION = LOCAL
```

Cette logique permet d'identifier les postes où l'import peut réduire le coût global du projet.

---

## 10. Modèle Power BI

Le modèle BI repose sur une table de faits et des dimensions simples.

### FACT_METRE

`FACT_METRE.csv` contient les lignes de métrés et les montants.

| Champ | Description |
|---|---|
| `id_ligne` | Identifiant unique de la ligne. |
| `cle_metier` | Clé stable pour relier les données. |
| `lot` | Lot travaux. |
| `famille` | Famille métier. |
| `batiment` | Bâtiment concerné. |
| `niveau` | Niveau ou étage. |
| `designation` | Description du poste. |
| `quantite` | Quantité mesurée. |
| `unite` | Unité de mesure. |
| `prix_total_ht` | Montant local HT. |
| `montant_local` | Montant local utilisé pour analyse. |
| `montant_import` | Coût import calculé. |
| `capex_optimise` | Coût final optimisé. |
| `economie_nette` | Économie calculée. |
| `taux_economie` | Économie rapportée au montant local. |
| `decision_import` | Décision `LOCAL` ou `IMPORT`. |
| `statut_ligne` | Statut qualité de la ligne. |

### DIM_FAMILLE

`DIM_FAMILLE.csv` décrit les familles travaux.

| Champ | Description |
|---|---|
| `famille` | Code famille. |
| `libelle_famille` | Libellé lisible. |
| `categorie_achat` | Catégorie achat : `IMPORTABLE`, `LOCAL_DOMINANT` ou `A_ANALYSER`. |

### Relation recommandée

```text
FACT_METRE[famille] -> DIM_FAMILLE[famille]
```

---

## 11. Dashboards recommandés

### Dashboard Direction

| Indicateur | Objectif |
|---|---|
| CAPEX total | Suivre le budget global. |
| CAPEX optimisé | Visualiser le scénario cible. |
| Économie nette | Mesurer le gain potentiel. |
| Taux d'économie | Comparer les gains entre lots. |
| Top familles coûteuses | Identifier les leviers prioritaires. |

### Dashboard Chantier

| Vue | Objectif |
|---|---|
| Coûts par lot | Comprendre les postes majeurs. |
| Coûts par bâtiment | Suivre les zones du projet. |
| Coûts par niveau | Analyser étage par étage. |
| Audit qualité | Repérer les lignes DQE à corriger. |

### Dashboard Import

| Vue | Objectif |
|---|---|
| Local vs import | Comparer les scénarios d'achat. |
| Décisions import | Lister les postes importables. |
| Économies par famille | Prioriser les familles à négocier. |
| Montant import | Évaluer l'exposition logistique. |

---

## 12. Installation

### Prérequis

| Outil | Usage |
|---|---|
| Python 3.11+ | Pipeline data et API FastAPI. |
| Node.js 18+ | Frontend React / Vite. |
| Docker | Lancement conteneurisé. |
| Power BI Desktop | Analyse des exports BI. |

### Installation Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Installation Node

```powershell
cd 08_FRONTEND
npm install
```

### Installation Docker

Docker doit être installé et lancé sur la machine.

Vérification :

```powershell
docker --version
docker compose version
```

---

## 13. Utilisation

### Lancer le pipeline complet

Depuis la racine du projet :

```powershell
python 04_TRAITEMENT/pipeline_complet.py
```

Le pipeline retourne un JSON avec :

- `status` : `SUCCESS` ou `ERROR` ;
- `resume` : synthèse des montants et fichiers générés ;
- `logs` : étapes exécutées.

### Lancer uniquement la normalisation

```powershell
python 04_TRAITEMENT/normalisation_dqe.py --input 03_DONNEES_ENTREE/dqe/dqe_source_brut.json --output 03_DONNEES_ENTREE/dqe/dqe_normalise.json
```

### Lancer uniquement l'optimisation import

```powershell
python 04_TRAITEMENT/optimisation_import.py --input 03_DONNEES_ENTREE/dqe/dqe_normalise.json --output 05_RESULTATS/optimisation_capex_import.csv
```

### Lancer l'API FastAPI

```powershell
uvicorn app.main:app --app-dir 07_API_BACKEND --reload --port 8000
```

Documentation interactive :

```text
http://localhost:8000/docs
```

### Lancer le frontend React

```powershell
cd 08_FRONTEND
npm run dev
```

Adresse locale :

```text
http://localhost:5173
```

### Lancer avec Docker

```powershell
cd 09_INFRA
docker compose up --build
```

---

## 14. API

L'API FastAPI expose les services métier du projet.

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/health` | Vérifier que l'API fonctionne. |
| `POST` | `/dqe/upload` | Envoyer ou traiter un DQE JSON. |
| `POST` | `/import/optimize` | Lancer une optimisation local/import. |

### Exemple de contrôle API

```powershell
python -c "import sys, importlib; sys.path.insert(0, '07_API_BACKEND'); importlib.import_module('app.main'); print('API OK')"
```

### Contrat attendu pour le pipeline

```json
{
  "status": "SUCCESS",
  "resume": {
    "lignes_dqe": 178,
    "montant_local": 490838992.8,
    "capex_optimise": 432160767.87,
    "economie_nette": 58678224.93
  },
  "logs": [
    "STEP 1 - Normalisation DQE",
    "STEP 2 - Enrichissement",
    "STEP 3 - Optimisation import",
    "STEP 4 - Generation dataset BI",
    "STEP 5 - Audit qualite"
  ]
}
```

---

## Documentation frontend

Le frontend SP2I CAPEX est une application React construite avec Vite. Il sert de premiere interface SaaS pour consulter les vues metier du projet : Direction, Chantier et Import.

### Objectif du frontend

| Objectif | Description |
|---|---|
| Centraliser la lecture CAPEX | Donner une entree simple aux utilisateurs metier. |
| Separer les vues par profil | Adapter l'affichage aux besoins Direction, Chantier et Import. |
| Preparer l'usage SaaS | Poser la base d'une interface connectee a l'API FastAPI. |
| Faciliter la lecture | Afficher des indicateurs simples avant l'integration de tableaux dynamiques. |

### Structure frontend

```text
08_FRONTEND/
|
+-- index.html
+-- package.json
+-- src/
    +-- main.jsx
    +-- styles.css
    +-- components/
    |   +-- Indicateur.jsx
    +-- pages/
        +-- Direction.jsx
        +-- Chantier.jsx
        +-- Import.jsx
```

| Fichier | Role |
|---|---|
| `index.html` | Point d'entree HTML de l'application. |
| `package.json` | Scripts NPM et dependances React/Vite. |
| `src/main.jsx` | Initialisation React, navigation interne et choix de la vue active. |
| `src/styles.css` | Styles globaux de l'interface. |
| `src/components/Indicateur.jsx` | Composant reutilisable pour afficher un indicateur metier. |
| `src/pages/Direction.jsx` | Vue de pilotage global CAPEX. |
| `src/pages/Chantier.jsx` | Vue controle DQE et metriques terrain. |
| `src/pages/Import.jsx` | Vue arbitrage import/local Pointe-Noire. |

### Vues disponibles

| Vue | Public cible | Contenu actuel |
|---|---|---|
| Direction | Direction, client, maitrise d'ouvrage | CAPEX local, CAPEX optimise, economies nettes. |
| Chantier | Equipe travaux, controle projet | Lignes DQE, anomalies qualite, zones batiment/niveau. |
| Import | Achats, logistique, direction projet | FOB, Pointe-Noire, decision import/local. |

### Commandes frontend

Toutes les commandes frontend se lancent depuis le dossier `08_FRONTEND`.

```powershell
cd 08_FRONTEND
```

Installer les dependances :

```powershell
npm install
```

Lancer le mode developpement :

```powershell
npm run dev
```

Construire la version production :

```powershell
npm run build
```

Previsualiser le build production :

```powershell
npm run preview
```

Adresse locale en developpement :

```text
http://localhost:5173
```

### Lien avec le backend

Le backend FastAPI doit tourner sur le port `8000` pour les futurs appels API du frontend.

```powershell
uvicorn app.main:app --app-dir 07_API_BACKEND --reload --port 8000
```

Endpoints utiles pour connecter l'interface :

| Endpoint | Usage frontend attendu |
|---|---|
| `GET /health` | Verifier que l'API est disponible. |
| `POST /dqe/upload` | Envoyer un DQE JSON depuis une interface d'upload. |
| `POST /import/optimize` | Lancer une optimisation import/local. |

### Evolution frontend recommandee

| Evolution | Objectif |
|---|---|
| Upload DQE dans l'interface | Permettre a l'utilisateur de charger un fichier sans passer par Swagger. |
| Appels API reels | Remplacer les valeurs statiques par les resultats FastAPI. |
| Tableaux de resultats | Afficher lignes DQE, anomalies et decisions import/local. |
| Etats de chargement | Montrer clairement quand le pipeline est en cours. |
| Gestion d'erreur | Afficher les erreurs API dans une zone lisible. |
| Filtres metier | Filtrer par lot, famille, batiment, niveau et decision import. |

---

## 15. Stack technique

| Couche | Technologie | Rôle |
|---|---|---|
| Data | Python | Normalisation, enrichissement, calculs CAPEX. |
| API | FastAPI | Exposition des traitements. |
| Frontend | React + Vite | Interface utilisateur. |
| BI | Power BI | Analyse décisionnelle. |
| Fichiers | JSON, CSV, XLSX | Entrées et sorties data. |
| Infra | Docker Compose | Lancement multi-services. |

---

## 16. Roadmap produit

### Vision produit SaaS

SP2I CAPEX peut évoluer vers une plateforme SaaS de pilotage CAPEX pour projets immobiliers et BTP.

La vision cible :

- importer plusieurs DQE par projet ;
- comparer plusieurs scénarios d'achat ;
- suivre les versions de budget ;
- connecter les exports à Power BI ou une base analytique ;
- gérer plusieurs utilisateurs ;
- historiser les décisions ;
- industrialiser le traitement dans une API sécurisée.

### Limites actuelles

| Limite | Impact |
|---|---|
| Données principalement fichier | Pas encore de base de données centrale. |
| Authentification absente | Pas encore adapté à un usage multi-utilisateur sécurisé. |
| Référentiels simples | Les règles métier doivent être enrichies projet par projet. |
| Frontend initial | L'interface doit encore couvrir tous les cas métier. |
| Power BI fichier | Connexion directe à une base analytique non encore mise en place. |

### Axes d'amélioration

| Axe | Objectif |
|---|---|
| Base PostgreSQL | Stocker projets, DQE, scénarios et historiques. |
| Authentification | Sécuriser l'accès par utilisateur et organisation. |
| Multi-projets | Gérer plusieurs opérations immobilières. |
| Workflow validation | Ajouter des étapes Direction, Achat, Chantier. |
| Référentiels avancés | Améliorer familles, ratios FOB et règles d'import. |
| API complète | Exposer le pipeline complet et les exports BI. |
| Observabilité | Ajouter logs techniques, suivi d'erreurs et métriques. |
| Déploiement cloud | Préparer un environnement SaaS exploitable. |

---

## 17. Guide rapide débutant

### 1. Préparer le DQE

Place le fichier source ici :

```text
03_DONNEES_ENTREE/dqe/dqe_source_brut.json
```

### 2. Installer les dépendances

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Lancer le pipeline

```powershell
python 04_TRAITEMENT/pipeline_complet.py
```

### 4. Vérifier les résultats

| Besoin | Fichier |
|---|---|
| DQE nettoyé | `03_DONNEES_ENTREE/dqe/dqe_normalise.json` |
| Export métier | `05_RESULTATS/dqe_pret_powerbi.csv` |
| Optimisation import | `05_RESULTATS/optimisation_capex_import.csv` |
| Audit qualité | `05_RESULTATS/audit_qualite_dqe.xlsx` |
| Table Power BI | `06_ANALYSE_BI/dataset/FACT_METRE.csv` |
| Dimension Power BI | `06_ANALYSE_BI/dataset/DIM_FAMILLE.csv` |

### 5. Lancer l'API

```powershell
uvicorn app.main:app --app-dir 07_API_BACKEND --reload --port 8000
```

Ouvrir :

```text
http://localhost:8000/docs
```

### 6. Lancer le frontend

```powershell
cd 08_FRONTEND
npm run dev
```

Ouvrir :

```text
http://localhost:5173
```
