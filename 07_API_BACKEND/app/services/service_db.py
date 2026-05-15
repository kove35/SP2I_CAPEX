from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import RepositorySimulation


class ServiceDB:
    """
    Facade de compatibilite autour du repository PostgreSQL.

    Les routes et services existants peuvent continuer a utiliser `ServiceDB`,
    tandis que l'acces donnees est maintenant isole dans `RepositorySimulation`.
    """

    def __init__(self, db: Session) -> None:
        self.repository = RepositorySimulation(db)

    def insert_fact_metre(self, data: list[dict]) -> int:
        return self.repository.insert_fact_metre(data)

    def insert_dim_famille(self, data: list[dict]) -> int:
        return self.repository.insert_dim_famille(data)

    def get_summary(self) -> dict:
        return self.repository.get_summary()

    def list_fact_metre(
        self,
        famille: str | None = None,
        lot: str | None = None,
        batiment: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list:
        return self.repository.list_fact_metre(
            famille=famille,
            lot=lot,
            batiment=batiment,
            limit=limit,
            offset=offset,
        )
