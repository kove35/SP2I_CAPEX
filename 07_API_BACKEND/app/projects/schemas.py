from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2)
    client_name: str = ""
    city: str = "Pointe-Noire"
    country: str = "Congo-Brazzaville"
    currency: str = "FCFA"
    status: str = "ACTIVE"


class ProjectResponse(BaseModel):
    id: int
    name: str
    client_name: str
    city: str
    country: str
    currency: str
    owner_id: int
    status: str
    created_at: datetime | None = None
    trust_score: int = 87
    last_dqe: str = "DQE_PROJECT_SP2I.xlsx"
    budget: float = 0


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
