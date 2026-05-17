# Flux frontend backend

## Principe

SP2I separe les responsabilites :

```text
React / Vercel
    |
    v
services API Axios
    |
    v
FastAPI / Render
    |
    +--> moteurs metier
    +--> Analytics Engine
    +--> PostgreSQL
    |
    v
Power BI Service
```

React affiche et orchestre. FastAPI calcule. PostgreSQL historise et agrege.
Power BI visualise les dashboards decisionnels.

---

## Configuration API

Le client HTTP principal est :

```text
08_FRONTEND/src/services/apiClient.js
```

Il determine automatiquement l'URL backend :

```text
local navigateur -> http://localhost:8000
production       -> https://sp2i-backend.onrender.com
override         -> VITE_API_URL ou VITE_API_BASE_URL
```

En production Vercel, la variable recommandee est :

```text
VITE_API_URL=https://sp2i-backend.onrender.com
```

---

## Gestion des erreurs

Le frontend distingue deux cas :

1. L'API globale est injoignable.
2. Une action precise echoue, par exemple `/simulation/scenarios`.

Le message utilisateur doit donc rester precis :

```text
Connexion interrompue sur /simulation/scenarios.
Si l'import fonctionne, le probleme vient probablement de cette action precise
et non de l'API globale.
```

Cette nuance evite de diagnostiquer a tort un probleme CORS ou Render quand un
endpoint specifique est en erreur.

---

## Workflow DQE Excel

```text
Utilisateur
    |
    v
/app/dqe
    |
    v
excelUploadService
    |
    v
POST /api/upload/excel
    |
    v
FastAPI analyse le fichier
    |
    +--> heuristiques colonnes
    +--> IA si ambiguite
    +--> normalisation lignes
    +--> anomalies
    |
    v
React affiche KPI, preview, anomalies
```

Reponse backend attendue :

```json
{
  "status": "SUCCESS",
  "file_id": "...",
  "lignes_normalisees_preview": [],
  "ai_preview": {
    "lots_detected": 9,
    "recognized_columns": 10,
    "quality_score": 0.48,
    "estimated_capex_detected": 218723945
  },
  "ai_anomalies": [],
  "analyses": [],
  "ai_suggestions": {}
}
```

Regle importante :

```text
quality_score backend = nombre entre 0 et 1
affichage frontend    = Math.round(quality_score * 100)
```

---

## Workflow synchronisation PostgreSQL

```text
Excel DQE
    |
    v
POST /api/upload/excel/sync
    |
    v
normalisation backend
    |
    v
fact_metre + dimensions
    |
    v
/capex/summary et /analytics/*
    |
    v
React + Power BI
```

La synchronisation ne doit pas supprimer silencieusement des lignes valides.
Les controles se font cote backend avec logs, lineage et warnings.

---

## Workflow cockpit BI React

```text
/app
    |
    v
TanStack Query
    |
    +--> /capex/summary
    +--> /fact_metre
    +--> /monitoring/status
    +--> /simulation/scenarios
    +--> /analytics/dashboard
```

Les donnees sont ensuite distribuees vers :

- KPI cards ;
- ECharts ;
- AG Grid ;
- filtres Zustand ;
- panneaux de contexte.

---

## Workflow Analytics Engine

```text
React filters
    |
    v
/analytics/dashboard?lot=...&famille=...
    |
    v
AnalyticsService
    |
    v
AnalyticsRepository
    |
    v
PostgreSQL views
    |
    v
contrat standard SUCCESS
```

Le contrat standard est :

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

---

## Workflow Power BI

```text
PostgreSQL Render
    |
    v
Power BI Service
    |
    v
/app/analytics
```

Power BI reste la couche analytique strategique. React peut l'embarquer ou
l'ouvrir depuis le cockpit, mais ne doit pas refaire les mesures metier.

---

## Regles de compatibilite

1. Ne pas casser les endpoints existants.
2. Ajouter les nouveaux endpoints sous `/analytics/*` plutot que remplacer les anciens.
3. Garder les services API comme point unique d'appel HTTP.
4. Ne pas appeler `fetch` directement dans les composants metier.
5. Garder les erreurs lisibles et actionnables.
6. Logger temporairement les reponses API pendant les phases de stabilisation.
