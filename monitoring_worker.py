"""
Worker de monitoring continu pour SP2I CAPEX.

Commande :
    python monitoring_worker.py

Toutes les 10 secondes, ce script :
- teste la connexion PostgreSQL ;
- calcule la qualite DQE ;
- ecrit les resultats dans `monitoring_logs`.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parent
API_BACKEND_PATH = PROJECT_ROOT / "07_API_BACKEND"
sys.path.insert(0, str(API_BACKEND_PATH))

from app.database import SessionLocal
from app.services.monitoring import MonitoringService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("sp2i-monitoring-worker")


def run_once() -> dict:
    """Execute un cycle de monitoring."""
    db: Session = SessionLocal()
    try:
        service = MonitoringService(db)
        status = service.get_status()
        logger.info("Monitoring status: %s", status)
        return status
    finally:
        db.close()


def main() -> None:
    """Lance une boucle de monitoring continue."""
    logger.info("Monitoring worker started.")

    while True:
        try:
            run_once()
        except Exception as erreur:
            logger.error("Monitoring worker error: %s", erreur)

        time.sleep(10)


if __name__ == "__main__":
    main()
