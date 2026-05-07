from __future__ import annotations

from fastapi import APIRouter

from app.services.service_import import ServiceImport


router = APIRouter()


@router.post("/optimize")
def optimize_import() -> dict:
    return ServiceImport().optimiser_source_courante()
