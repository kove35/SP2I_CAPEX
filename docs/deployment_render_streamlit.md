# Deploiement Render + Streamlit Cloud

## 1. Preparer GitHub

1. Pousser le projet sur GitHub.
2. Verifier que `.env` n'est pas versionne.
3. Garder `.env.example` comme modele public.

## 2. Deployer PostgreSQL sur Render

Le fichier `render.yaml` declare une base :

```yaml
sp2i-postgres
```

Render injecte automatiquement `DATABASE_URL` dans le backend.

## 3. Deployer FastAPI sur Render

Render utilise :

- Build command : `pip install -r 07_API_BACKEND/requirements.txt`
- Start command : `uvicorn app.main:app --app-dir 07_API_BACKEND --host 0.0.0.0 --port $PORT`
- Healthcheck : `/health`

Variables a renseigner dans Render :

```text
OPENAI_API_KEY
FRONTEND_URL
CORS_ORIGINS
POWERBI_DIRECTION_URL
POWERBI_FINANCE_URL
POWERBI_IMPORT_URL
POWERBI_CHANTIER_URL
POWERBI_DQE_URL
```

Exemple `CORS_ORIGINS` :

```text
https://sp2i-build.streamlit.app,http://localhost:8501,http://localhost:5173
```

## 4. Tester le backend

Apres deploiement :

```text
GET /health
GET /debug/config
GET /capex/summary
```

`/debug/config` ne doit jamais afficher les secrets.

## 5. Deployer Streamlit Community Cloud

Dans Streamlit Cloud :

- Repository : le repo GitHub SP2I.
- Main file path : `08_FRONTEND_STREAMLIT/streamlit_app.py`.
- Python dependencies : `08_FRONTEND_STREAMLIT/requirements.txt`.

Secrets Streamlit :

```toml
API_URL = "https://sp2i-backend.onrender.com"
POWERBI_DIRECTION_URL = ""
POWERBI_FINANCE_URL = ""
POWERBI_IMPORT_URL = ""
POWERBI_CHANTIER_URL = ""
POWERBI_DQE_URL = ""
```

## 6. Tester le workflow complet

1. Ouvrir Streamlit.
2. Verifier que le backend est marque disponible.
3. Aller dans `DQE intelligent`.
4. Importer un fichier `.xlsx`, `.xlsm`, `.xls` ou `.csv`.
5. Cliquer sur `Analyser sans ecrire en base`.
6. Controler la preview IA.
7. Cliquer sur `Synchroniser PostgreSQL`.
8. Aller dans `PostgreSQL/API`.
9. Verifier `fact_metre`.
10. Ouvrir Power BI et rafraichir le dataset.

## 7. Test local Docker

```text
docker compose up --build
```

Services :

- FastAPI : `http://localhost:8000`
- Streamlit : `http://localhost:8501`
- PostgreSQL : `localhost:5432`

## 8. Regle importante

Streamlit est une interface d'exploitation et de test. Les calculs critiques restent dans :

- FastAPI
- services metier
- PostgreSQL

Power BI reste la couche analytique strategique.
