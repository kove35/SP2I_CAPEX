# Audit cloud readiness SP2I

## Objectif

Ce document decrit l'etat cloud actuel de SP2I et les points a surveiller pour
un environnement reel de test.

SP2I est maintenant centre sur :

- frontend React/Vite deploye sur Vercel ;
- backend FastAPI deploye sur Render ;
- PostgreSQL Render comme source de verite ;
- Power BI Service comme couche analytique ;
- OpenAI et heuristiques pour l'analyse DQE.

Streamlit reste une facade optionnelle de test, pas le frontend principal.

---

## Architecture cloud actuelle

```text
Utilisateur
    |
    v
React / Vercel
    |
    v
FastAPI / Render
    |
    +--> OpenAI API
    +--> Analytics Engine V1
    |
    v
PostgreSQL Render
    |
    v
Power BI Service
```

---

## URLs de controle

```text
Frontend : https://sp-2-i-capex.vercel.app
Backend  : https://sp2i-backend.onrender.com
Health   : https://sp2i-backend.onrender.com/health
Config   : https://sp2i-backend.onrender.com/debug/config
Swagger  : https://sp2i-backend.onrender.com/docs
```

---

## Etat valide

### Backend Render

Le backend expose :

- `/health`
- `/debug/config`
- `/api/upload/excel`
- `/api/upload/excel/sync`
- `/capex/summary`
- `/fact_metre`
- `/simulation/*`
- `/decision/*`
- `/procurement/*`
- `/logistics/*`
- `/analytics/*`

Au demarrage, FastAPI :

1. cree ou verifie les tables SQLAlchemy ;
2. applique les migrations douces Power BI ;
3. cree les vues Analytics Engine V1 ;
4. active CORS pour Vercel.

### Frontend Vercel

Le frontend de production est :

```text
08_FRONTEND
```

La variable importante est :

```text
VITE_API_URL=https://sp2i-backend.onrender.com
```

La rewrite SPA doit permettre d'ouvrir directement :

```text
/app
/app/dqe
/app/analytics
/app/procurement
```

### PostgreSQL Render

PostgreSQL contient les tables et vues necessaires pour :

- `fact_metre` ;
- dimensions Power BI ;
- scenarios ;
- runs de simulation ;
- KPI views ;
- analytics views.

### Power BI

Power BI doit lire PostgreSQL ou les vues exposees. Les mesures financieres
globales doivent utiliser le ratio des totaux, jamais la moyenne des ratios.

---

## Variables d'environnement

### Backend Render

```text
DATABASE_URL
OPENAI_API_KEY
ENVIRONMENT=production
CORS_ORIGINS=https://sp-2-i-capex.vercel.app
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
FRONTEND_URL=https://sp-2-i-capex.vercel.app
MAX_UPLOAD_MB=50
POWERBI_DIRECTION_URL
POWERBI_FINANCE_URL
POWERBI_IMPORT_URL
POWERBI_CHANTIER_URL
POWERBI_DQE_URL
```

### Frontend Vercel

```text
VITE_API_URL=https://sp2i-backend.onrender.com
```

---

## Tests cloud recommandes

### 1. Sante API

```text
GET /health
GET /debug/config
```

Attendu :

- database configuree ;
- OpenAI configure si l'IA est active ;
- CORS contient le domaine Vercel ;
- Power BI URLs indiquees selon configuration.

### 2. Upload DQE

```text
POST /api/upload/excel
```

Verifier :

- `status = SUCCESS` ;
- `ai_preview.quality_score` entre 0 et 1 ;
- `lignes_normalisees_preview` non vide ;
- anomalies affichees sans casser l'interface.

### 3. Synchronisation PostgreSQL

```text
POST /api/upload/excel/sync
GET /capex/summary
GET /fact_metre?limit=5
```

Verifier :

- les colonnes attendues existent ;
- les montants sont coherents avec Excel ;
- les lots ne disparaissent pas ;
- Power BI voit les nouvelles lignes apres refresh.

### 4. Analytics Engine

```text
GET /analytics/system-health
GET /analytics/dashboard
GET /analytics/kpis
GET /analytics/drilldown
```

Verifier :

- contrat `status = SUCCESS` ;
- temps de reponse acceptable ;
- `warnings` explicites si la base est vide.

---

## Risques restants

### Base vide

Une base Render neuve peut etre techniquement saine mais vide. Dans ce cas,
React doit afficher un etat vide et non une erreur critique.

### Render cold start

Render peut mettre quelques secondes a reveiller l'API. Le frontend doit garder
des timeouts suffisants pour les uploads et afficher des messages patients.

### Stockage fichier ephemere

Render ne garantit pas la persistance des fichiers locaux hors disque persistant.
Il faut historiser en PostgreSQL ou ajouter un stockage objet pour les sources
DQE en V2.

### Power BI non configure

Si les URLs Power BI sont absentes, `/debug/config` indique `false`. React doit
afficher un placeholder ou un message de configuration, pas une erreur.

### Migrations production

Les migrations douces au startup sont pratiques pour tester. Pour une production
plus mature, il faudra introduire Alembic.

---

## Decision d'architecture

L'architecture cloud de reference est :

```text
React/Vercel pour le cockpit
FastAPI/Render pour les moteurs
PostgreSQL/Render pour la verite analytique
Power BI Service pour la BI strategique
```

Streamlit peut rester utile pour :

- demos rapides ;
- tests internes ;
- validation de fichiers ;
- prototypes data.

Mais il ne doit pas etre considere comme le frontend principal de SP2I.
