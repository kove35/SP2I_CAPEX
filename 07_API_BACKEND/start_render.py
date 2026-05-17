from __future__ import annotations

import os
import sys

import uvicorn


def main() -> None:
    """
    Point d'entree cloud pour Render.

    Render injecte dynamiquement la variable d'environnement PORT. Il faut
    toujours ecouter ce port exact, sinon le deploiement demarre mais Render ne
    detecte aucun service HTTP ouvert et coupe le process.
    """
    port = int(os.getenv("PORT", "10000"))
    host = os.getenv("HOST", "0.0.0.0")

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
