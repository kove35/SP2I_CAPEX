"""Launcher local temporaire : backend de recette sur le port 8001 (code a jour)."""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5433/sp2i_capex_recipe"
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_STARTUP_SCHEMA_MUTATIONS"] = "false"
os.environ["SP2I_JWT_SECRET"] = "recette-local-secret-change-before-production-0123456789"
os.environ["SP2I_FINANCIAL_SOURCE"] = "vw_fact_metre_financial_v6"

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="info")
