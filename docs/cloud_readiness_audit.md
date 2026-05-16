# Audit cloud readiness SP2I BUILD

## Objectif

Ce document prepare SP2I BUILD pour un environnement reel de test :

- Backend FastAPI sur Render.
- PostgreSQL sur Render.
- Frontend de test Streamlit Community Cloud.
- Power BI Service pour les dashboards.
- OpenAI pour l'analyse intelligente DQE.

L'architecture existante est conservee. Les ajouts cloud sont progressifs et ne remplacent pas le cockpit React actuel.

## Architecture cible de test

```text
Utilisateur
    |
    v
Streamlit Community Cloud
    |
    v
FastAPI Render
    |
    +--> OpenAI API
    |
    v
PostgreSQL Render
    |
    v
Power BI Service
```

## Points solides constates

- Le backend FastAPI est deja separe en routes, services, core et repositories.
- La base PostgreSQL contient deja des tables analytiques et des vues KPI.
- Le pipeline DQE sait normaliser, simuler et synchroniser `fact_metre`.
- La logique metier reste cote backend/PostgreSQL, ce qui est sain pour Power BI.
- Les endpoints `/health` et `/capex/summary` permettent deja un controle simple.

## Points bloquants corriges

### CORS local uniquement

Avant, l'API acceptait seulement `localhost:5173`.
Maintenant, les origines sont configurees avec `CORS_ORIGINS`.

### Upload trop limite

L'upload acceptait seulement `.xlsx` et `.xlsm`.
Le backend accepte maintenant :

- `.xlsx`
- `.xlsm`
- `.xls`
- `.csv`

Le PDF reste gere par `/dqe/extract`.

### Secrets non formalises

`.env.example` documente maintenant :

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `CORS_ORIGINS`
- `MAX_UPLOAD_MB`
- URLs Power BI

### Diagnostic cloud manquant

L'endpoint `/debug/config` expose uniquement des indicateurs non sensibles :

- database configuree ou non
- OpenAI configure ou non
- CORS actifs
- dashboards Power BI configures ou non

## Risques restants a surveiller

### Stockage fichier Render

Render fournit un disque ephemere par defaut. Les fichiers generes dans `03_DONNEES_ENTREE`, `05_RESULTATS` ou `logs` peuvent disparaitre au redeploiement.

Recommandation V2 :

- Stockage objet pour les fichiers sources.
- Historisation PostgreSQL pour les resultats.
- Volume persistant Render si necessaire.

### Power BI

Power BI doit consommer PostgreSQL ou les vues analytiques exposees. React/Streamlit ne doivent pas recalculer les KPI metier.

### Migrations PostgreSQL

Le backend cree encore certaines tables via SQLAlchemy au demarrage. Pour la production, ajouter Alembic.

## Decision d'architecture

Pour le test cloud, on ajoute Streamlit comme interface simple de validation :

- Upload DQE.
- Preview IA.
- Synchronisation PostgreSQL.
- Controle KPI.
- Integration Power BI.

Le frontend React existant reste disponible pour la trajectoire cockpit enterprise.
