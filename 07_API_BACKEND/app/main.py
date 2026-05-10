# ==========================================================
# 📦 SP2I CAPEX API – MAIN
# ==========================================================
#
# Ce fichier est le POINT D'ENTRÉE de votre API.
# Il configure le serveur, les routes, et les middlewares.
#
# Pour lancer l'API : uvicorn app.main:app --reload
# Pour voir la documentation : http://localhost:8000/docs
#
# ==========================================================

# ----------------------------------------------------------
# 📚 IMPORTS
# ----------------------------------------------------------

# from __future__ import annotations
# Permet d'utiliser des annotations de type (ex: -> "Classe")
# avec des classes qui ne sont pas encore définies.
# Utile pour éviter les imports circulaires.
from __future__ import annotations

# importlib : module pour importer dynamiquement d'autres modules
# Nous permet de charger "app.routes.import" même si son nom a des caractères
# qui ne sont pas des noms de variables Python valides (le point "." notamment)
from importlib import import_module

# FastAPI : le framework web lui-même
# Il gère les requêtes HTTP, la validation, la documentation, etc.
from fastapi import FastAPI

# CORSMiddleware : gère le partage de ressources entre origines multiples
# Permet à votre frontend (React/Vue) sur un autre port d'appeler l'API
from fastapi.middleware.cors import CORSMiddleware

# Import de notre module "dqe" qui contient les routes pour /dqe
# Ce fichier devrait se trouver dans app/routes/dqe.py
from app.routes import dqe


# ----------------------------------------------------------
# 🔧 CRÉATION DE L'APPLICATION
# ----------------------------------------------------------

# On crée une instance de FastAPI
# C'est le CŒUR de notre API. Toute la configuration lui est attachée.
app = FastAPI(
    # Titre de l'API – s'affiche dans la documentation Swagger
    title="SP2I CAPEX API",
    
    # Description – explication du rôle de l'API
    description="API SaaS pour analyse DQE, optimisation import et datasets BI.",
    
    # Version – pour le suivi des évolutions
    version="1.0.0",
)


# ----------------------------------------------------------
# 🌐 CORS (Partage de ressources entre origines)
# ----------------------------------------------------------
# CORS = Cross-Origin Resource Sharing
# 
# Par défaut, un navigateur bloque les requêtes JavaScript qui viennent d'un
# domaine différent. C'est une mesure de sécurité.
# 
# Par exemple :
# - Votre API tourne sur http://localhost:8000
# - Votre frontend tourne sur http://localhost:5173 (React)
# - Sans CORS, le frontend ne peut pas appeler l'API.
# 
# CORSMiddleware ajoute les en-têtes HTTP (Access-Control-Allow-Origin, etc.)
# pour autoriser ces requêtes.

app.add_middleware(
    CORSMiddleware,
    
    # allow_origins : liste des domaines autorisés à appeler l'API
    # 5173 = port par défaut de Vite (React/Vue)
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    
    # allow_credentials : autorise l'envoi de cookies / tokens d'authentification
    allow_credentials=True,
    
    # allow_methods : méthodes HTTP autorisées (GET, POST, PUT, DELETE, etc.)
    # "*" = toutes les méthodes
    allow_methods=["*"],
    
    # allow_headers : en-têtes HTTP autorisés (Content-Type, Authorization, etc.)
    # "*" = tous les en-têtes
    allow_headers=["*"],
)


# ----------------------------------------------------------
# 📍 ROUTES (Endpoints)
# ----------------------------------------------------------

# Inclure toutes les routes du module "dqe"
# Chaque route définie dans app/routes/dqe.py aura pour préfixe "/dqe"
# 
# Exemple : si dqe.py contient @router.get("/extract")
# → L'URL complète sera : http://localhost:8000/dqe/extract
# 
# tags=["DQE"] : regroupe ces routes dans la section "DQE" de la documentation Swagger
app.include_router(dqe.router, prefix="/dqe", tags=["DQE"])

# ----------------------------------------------------------
# 🔄 IMPORT DYNAMIQUE DU MODULE "import"
# ----------------------------------------------------------

# On importe dynamiquement le module "app.routes.import"
# "import_module" retourne l'objet module, qu'on stocke dans la variable "import_routes"
import_routes = import_module("app.routes.import")

# On inclut ce module comme routeur
# Préfixe "/import", tag "Import" pour la documentation
app.include_router(import_routes.router, prefix="/import", tags=["Import"])

@app.get("/")
def root() -> dict:
    return {
        "service": "SP2I CAPEX API",
        "version": "1.0.0",
        "status": "RUNNING",
        "environment": "DEV",
        
        "endpoints": {
            "health": "/health",
            "upload_dqe": "/dqe/upload",
            "extract_dqe": "/dqe/extract",
            "optimize_import": "/import/optimize",
            "docs": "/docs"
        },

        "description": "API metier pour analyse DQE et optimisation CAPEX import/local",
        
        "frontend": {
            "url": "http://localhost:5173"
        }
    }

# ----------------------------------------------------------
# ❤️ HEALTH CHECK (vérification de santé)
# ----------------------------------------------------------
# Un endpoint très simple pour vérifier que l'API est en vie.
# Utilisé par :
# - Les ingénieurs DevOps pour les probes de santé (monitoring)
# - Docker/Kubernetes pour vérifier qu'un conteneur fonctionne
# - Le frontend pour tester la connexion avant d'envoyer des données

@app.get("/health")
def health() -> dict[str, str]:
    """
    Endpoint de vérification de santé.
    
    Retourne un JSON simple indiquant que l'API fonctionne.
    
    Exemple de réponse :
    {
        "statut": "OK",
        "service": "SP2I CAPEX API"
    }
    """
    return {
        "statut": "OK",
        "service": "SP2I CAPEX API"
    }


# ----------------------------------------------------------
# 📚 POUR ALLER PLUS LOIN (didacticiel)
# ----------------------------------------------------------
#
# 1. LANCER L'API :
#    uvicorn app.main:app --reload
# 
# 2. VOIR LA DOCUMENTATION INTERACTIVE :
#    Swagger UI : http://localhost:8000/docs
#    ReDoc : http://localhost:8000/redoc
# 
# 3. TESTER LE HEALTH CHECK :
#    Ouvrez votre navigateur : http://localhost:8000/health
#    ou utilisez curl : curl http://localhost:8000/health
# 
# 4. CRÉER UNE ROUTE DANS app/routes/dqe.py :
#    @router.get("/test")
#    def test():
#        return {"message": "OK"}
# 
# 5. FONCTIONNEMENT DÉTAILLÉ :
#    - FastAPI convertit automatiquement les dictionnaires Python (dict) en JSON
#    - Les erreurs sont automatiquement formatées en JSON (ex: 404, 500)
#    - La validation des types est automatique (si vous utilisez Pydantic)
# 
# ==========================================================