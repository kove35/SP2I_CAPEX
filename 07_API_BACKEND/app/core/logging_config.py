from __future__ import annotations

import logging
from pathlib import Path


RACINE = Path(__file__).resolve().parents[3]
LOG_DIR = RACINE / "logs"


def configure_simulation_logging() -> None:
    """
    Configure des logs fichiers sans perturber la configuration globale FastAPI.

    La fonction est idempotente : elle peut etre appelee plusieurs fois sans
    ajouter des handlers en doublon.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    targets = {
        "sp2i.simulation": LOG_DIR / "simulation.log",
        "sp2i.pipeline": LOG_DIR / "pipeline.log",
        "sp2i.errors": LOG_DIR / "errors.log",
    }

    for logger_name, path in targets.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        if any(isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == path for handler in logger.handlers):
            continue
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
