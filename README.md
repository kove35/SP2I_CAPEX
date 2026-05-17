# SP2I CAPEX

SP2I CAPEX signifie **Systeme de Pilotage des Investissements Immobiliers**.

Le projet est maintenant une plateforme decisionnelle cloud-native pour piloter
les investissements immobiliers, analyser les DQE, simuler le CAPEX, comparer
les strategies import/local et alimenter un cockpit BI moderne.

Le positionnement produit est clair :

```text
SP2I = cockpit decisionnel immobilier
React = cockpit operationnel
FastAPI = moteur metier et analytics
PostgreSQL = source de verite analytique
Power BI = couche de visualisation strategique
```

L'import Chine, la supply chain, les containers et la logistique restent des
moteurs d'optimisation integres. Ils ne remplacent pas le coeur du produit :
le pilotage des investissements immobiliers.

---

## Architecture actuelle

```text
Utilisateur
    |
    v
Frontend React / Vite / Vercel
    |
    v
API FastAPI / Render
    |
    +--> DQE AI Engine
    +--> CAPEX Engine
    +--> DecisionEngine
    +--> RiskEngine
    +--> ProcurementEngine
    +--> LogisticsEngine
    +--> Analytics Engine V1
    |
    v
PostgreSQL Render
    |
    +--> FACT / DIM
    +--> KPI views
    +--> Analytics views
    |
    v
Power BI Service
```

---

## Stack technique

| Couche | Technologie | Role |
|---|---|---|
| Frontend | React + Vite | Cockpit operationnel |
| Hebergement frontend | Vercel | Deploiement web |
| Backend | FastAPI | API, moteurs metier, analytics |
| Hebergement backend | Render | API cloud |
| Base de donnees | PostgreSQL Render | Donnees FACT/DIM, KPI, scenarios |
| BI | Power BI Service | Dashboards strategiques |
| IA | OpenAI + heuristiques | Analyse intelligente DQE |
| Charts cockpit | Apache ECharts | Visualisations React rapides |
| Tables cockpit | AG Grid | Tables BI interactives |
| State | Zustand | Filtres globaux cockpit |
| Data fetching | TanStack Query | Cache et chargement API |

---

## URLs de reference

```text
Frontend production : https://sp-2-i-capex.vercel.app
Backend production  : https://sp2i-backend.onrender.com
Swagger FastAPI     : https://sp2i-backend.onrender.com/docs
Healthcheck         : https://sp2i-backend.onrender.com/health
Debug config        : https://sp2i-backend.onrender.com/debug/config
```

En local :

```text
Frontend : http://localhost:5173
Backend  : http://localhost:8000
```

---

## Structure du projet

```text
SP2I_CAPEX/
|
+-- 01_PARAMETRES/              Hypotheses metier et import
+-- 02_REFERENTIELS/            Mapping familles, referentiels metier
+-- 03_DONNEES_ENTREE/          Fichiers DQE, Excel, sources de test
+-- 04_TRAITEMENT/              Scripts historiques de traitement
+-- 05_RESULTATS/               Exports et resultats locaux
+-- 06_ANALYSE_BI/              Power BI, themes, datasets BI
+-- 07_API_BACKEND/             Backend FastAPI Render
|   +-- app/
|       +-- ai/                  Regles et aide mapping Excel
|       +-- analytics/           SP2I Analytics Engine V1
|       +-- core/                Moteurs metier purs
|       +-- repositories/        Acces PostgreSQL
|       +-- routes/              Routes FastAPI existantes
|       +-- services/            Orchestration metier
|       +-- main.py              Application FastAPI
|
+-- 08_FRONTEND/                Frontend React / Vite / Vercel
|   +-- src/
|       +-- app/                 Providers React Query
|       +-- components/          KPI, charts, grids, filtres
|       +-- layouts/             Layout cockpit
|       +-- marketing/           Landing page
|       +-- modules/             Cockpit, DQE, analytics, etc.
|       +-- pages/               Pages routees
|       +-- services/            Clients API
|       +-- store/               Zustand store global
|
+-- 08_FRONTEND_STREAMLIT/       Facade Streamlit optionnelle de test cloud
+-- 09_INFRA/                    Docker et infra locale
+-- docs/                        Documentation projet
```

---

## Workflow utilisateur principal

```text
1. L'utilisateur importe un fichier Excel DQE
2. Le backend analyse le fichier
3. Les heuristiques detectent colonnes, lots, lignes et anomalies
4. La couche IA assiste le mapping quand la structure est ambigue
5. Le preview normalise est affiche dans React
6. L'utilisateur controle ou valide les donnees
7. Le backend synchronise PostgreSQL
8. Analytics Engine expose les KPI et datasets dashboard
9. React affiche le cockpit operationnel
10. Power BI affiche les dashboards decisionnels
```

L'IA aide a comprendre le fichier, mais elle n'ecrit pas directement en base
comme source de verite. La validation metier et la normalisation backend restent
prioritaires.

---

## Endpoints backend importants

### Sante et diagnostic

| Methode | Route | Role |
|---|---|---|
| GET | `/` | Informations API |
| GET | `/health` | Healthcheck Render |
| GET | `/debug/config` | Configuration non sensible |
| GET | `/monitoring/status` | Etat technique |

### DQE et upload

| Methode | Route | Role |
|---|---|---|
| POST | `/api/upload/excel` | Upload et analyse Excel |
| POST | `/api/upload/excel/sync` | Analyse puis synchronisation PostgreSQL |
| POST | `/dqe/upload` | Upload DQE historique |
| POST | `/dqe/extract` | Extraction DQE PDF/texte |
| POST | `/dqe/sync-current` | Synchronisation du DQE courant |

### Simulation et metier

| Methode | Route | Role |
|---|---|---|
| POST | `/simulation/simulate` | Simulation CAPEX |
| GET | `/simulation/scenarios` | Historique scenarios |
| GET | `/simulation/compare` | Comparaison scenarios |
| GET | `/decision/rules` | Regles decisionnelles |
| GET | `/decision/explain/{simulation_id}` | Explication d'une decision |
| GET | `/procurement/*` | Analyses procurement |
| GET | `/logistics/*` | Analyses logistiques |

### BI et analytics

| Methode | Route | Role |
|---|---|---|
| GET | `/capex/summary` | Resume CAPEX historique |
| GET | `/fact_metre` | Lignes analytiques |
| GET | `/analytics/dashboard` | Dataset cockpit complet |
| GET | `/analytics/kpis` | KPI centralises |
| GET | `/analytics/capex` | CAPEX par axes analytiques |
| GET | `/analytics/drilldown` | Drill-down projet -> article |
| GET | `/analytics/heatmap` | Donnees heatmap |
| GET | `/analytics/system-health` | Sante Analytics Engine |

---

## Contrat Analytics Engine V1

Les endpoints `/analytics/*` retournent un format stable pour React Query,
ECharts et AG Grid :

```json
{
  "status": "SUCCESS",
  "filters": {},
  "pagination": {},
  "kpis": {},
  "charts": {},
  "table": [],
  "metadata": {}
}
```

Ce contrat evite de disperser les calculs BI dans React. Les ratios financiers,
les KPI globaux et les aggregations restent calcules cote PostgreSQL/FastAPI.

---

## Lancer le backend en local

```powershell
cd 07_API_BACKEND
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verifier :

```text
http://localhost:8000/health
http://localhost:8000/docs
```

Variables importantes :

```text
DATABASE_URL
OPENAI_API_KEY
CORS_ORIGINS
CORS_ORIGIN_REGEX
FRONTEND_URL
MAX_UPLOAD_MB
```

---

## Lancer le frontend en local

```powershell
cd 08_FRONTEND
npm install
npm run dev
```

Verifier :

```text
http://localhost:5173
```

Variable importante :

```text
VITE_API_URL=http://localhost:8000
```

En production Vercel, l'URL backend cible est :

```text
VITE_API_URL=https://sp2i-backend.onrender.com
```

---

## Deploiement cloud

### Backend Render

Render lance l'API FastAPI et utilise PostgreSQL Render via `DATABASE_URL`.
Au demarrage, le backend verifie les tables et cree les vues analytiques
necessaires.

Commande type :

```text
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend Vercel

Le frontend React est dans `08_FRONTEND`.

Points importants :

- `vercel.json` doit rediriger les routes SPA vers `index.html`.
- `VITE_API_URL` doit pointer vers Render.
- Les domaines Vercel doivent etre autorises par CORS cote Render.

### PostgreSQL Render

PostgreSQL contient :

- `fact_metre`
- dimensions analytiques
- scenarios
- runs de simulation
- vues KPI
- vues Analytics Engine V1

Power BI doit se connecter a PostgreSQL ou consommer des vues deja calculees.

---

## Documentation utile

Le point d'entree documentaire est :

```text
docs/README_DOCUMENTATION.md
```

Documents a lire en premier :

- `docs/frontend_architecture.md`
- `docs/frontend_backend_flow.md`
- `docs/api_services.md`
- `docs/analytics_engine_v1.md`
- `docs/cloud_readiness_audit.md`
- `docs/powerbi_integration.md`
- `docs/ai_excel_engine.md`

---

## Regles d'architecture

1. Ne pas mettre de logique metier critique dans React.
2. Ne pas recalculer les KPI financiers dans Power BI.
3. Ne pas laisser l'IA ecrire directement en base sans validation.
4. Garder PostgreSQL/FastAPI comme source de verite.
5. Ajouter les evolutions progressivement, sans casser les endpoints existants.
6. Garder React comme cockpit operationnel, pas comme moteur BI complet.

---

## Resume pour demarrer

Pour un nouvel utilisateur :

1. Aller sur le frontend Vercel.
2. Ouvrir le module `DQE & Data`.
3. Importer un fichier Excel DQE.
4. Lire le score qualite, les lots detectes, les anomalies et le preview.
5. Synchroniser les donnees vers PostgreSQL si le controle est correct.
6. Ouvrir le cockpit et les dashboards.
7. Utiliser Power BI pour les analyses decisionnelles longues.

Pour un developpeur :

1. Lire ce README.
2. Lire `docs/README_DOCUMENTATION.md`.
3. Lancer FastAPI en local.
4. Lancer React en local.
5. Tester `/api/upload/excel`, `/capex/summary` et `/analytics/dashboard`.
