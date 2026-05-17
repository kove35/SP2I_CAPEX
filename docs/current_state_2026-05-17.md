# Etat courant SP2I - 2026-05-17

Ce document resume l'etat operationnel actuel du projet.

---

## Positionnement produit

SP2I CAPEX est une plateforme decisionnelle de pilotage des investissements
immobiliers.

Le coeur produit est :

- pilotage CAPEX ;
- analyse DQE ;
- scenarios ;
- decision import/local ;
- dashboards direction ;
- suivi projet et chantier.

La supply chain, l'import Chine, les containers et la logistique sont des
moteurs d'optimisation integres.

---

## Architecture active

```text
React/Vercel
    |
    v
FastAPI/Render
    |
    v
PostgreSQL Render
    |
    v
Power BI Service
```

---

## Frontend

Dossier principal :

```text
08_FRONTEND
```

Stack :

- React ;
- Vite ;
- Vercel ;
- Axios ;
- TanStack Query ;
- Zustand ;
- ECharts ;
- AG Grid.

Route d'entree utilisateur :

```text
/app/dqe
```

Un nouvel utilisateur doit commencer par importer ou controler un DQE.

---

## Backend

Dossier principal :

```text
07_API_BACKEND
```

Stack :

- FastAPI ;
- SQLAlchemy ;
- PostgreSQL ;
- OpenAI ;
- Analytics Engine V1.

Endpoints critiques :

```text
/health
/debug/config
/api/upload/excel
/api/upload/excel/sync
/capex/summary
/fact_metre
/simulation/scenarios
/analytics/dashboard
/analytics/kpis
```

---

## Base PostgreSQL

PostgreSQL est la source de verite pour :

- `fact_metre` ;
- dimensions ;
- scenarios ;
- runs ;
- vues KPI ;
- vues analytics.

Point de vigilance :

```text
Power BI peut etre techniquement connecte mais afficher des donnees vides
si fact_metre n'a pas encore ete synchronisee avec le bon fichier DQE.
```

---

## Tests cloud recents

Tests attendus :

1. `/health` retourne OK.
2. `/debug/config` confirme DATABASE_URL, OPENAI et CORS.
3. `/api/upload/excel` retourne `status = SUCCESS`.
4. `/capex/summary` repond sans erreur SQL.
5. `/analytics/dashboard` retourne le contrat standard.
6. `/app/dqe` fonctionne apres refresh navigateur Vercel.

---

## Points de vigilance connus

### Dependances frontend locales

Les nouvelles dependances BI sont dans `package.json`. Si `npm install` n'a pas
ete lance localement, le build local peut echouer. Vercel installe les
dependances avec son `installCommand`.

### Base vide

Une base Render vide n'est pas une panne. Le cockpit doit afficher un etat vide
et inviter a synchroniser un DQE.

### Power BI

Power BI doit etre rafraichi apres synchronisation PostgreSQL. Les KPI doivent
venir des colonnes/vues calculees, pas de DAX metier fragile.

### Fichiers temporaires Excel

Les fichiers `~$*.xlsx` sont des fichiers de verrouillage Office. Ils ne doivent
pas etre commits.

---

## Prochaine etape recommandee

Brancher le cockpit React directement sur `/analytics/dashboard` et
`/analytics/kpis`, puis garder `/capex/summary` comme fallback.
