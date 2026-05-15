from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger("sp2i.data_lineage")


@dataclass
class LineageStep:
    """Une etape mesuree dans le pipeline data."""

    name: str
    rows_in: int | None = None
    rows_out: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def lost_rows(self) -> int | None:
        if self.rows_in is None or self.rows_out is None:
            return None
        return self.rows_in - self.rows_out

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rows_in": self.rows_in,
            "rows_out": self.rows_out,
            "lost_rows": self.lost_rows,
            "details": self.details,
        }


class DataLineageTracker:
    """
    Trace les volumes et anomalies du pipeline sans modifier la logique metier.

    Le tracker sert a rendre les pertes visibles. Une perte peut etre normale
    (ligne de titre, sous-total) ou suspecte ; dans les deux cas elle doit etre
    expliquee dans les logs.
    """

    def __init__(self, pipeline_name: str) -> None:
        self.pipeline_name = pipeline_name
        self.steps: list[LineageStep] = []

    def track(
        self,
        name: str,
        rows_in: int | None = None,
        rows_out: int | None = None,
        **details: Any,
    ) -> None:
        step = LineageStep(name=name, rows_in=rows_in, rows_out=rows_out, details=details)
        self.steps.append(step)

        message = f"[{self.pipeline_name}] {name}"
        if rows_in is not None:
            message += f" | in={rows_in}"
        if rows_out is not None:
            message += f" | out={rows_out}"
        if step.lost_rows is not None:
            message += f" | lost={step.lost_rows}"
        if details:
            message += f" | details={details}"

        logger.info(message)

    def audit_lots(self, name: str, lignes: list[dict[str, Any]], champ: str = "lot") -> None:
        lots: dict[str, int] = {}
        sans_lot = 0
        for ligne in lignes:
            lot = str(ligne.get(champ) or "").strip()
            if not lot:
                sans_lot += 1
                continue
            lots[lot] = lots.get(lot, 0) + 1

        self.track(
            name,
            rows_in=len(lignes),
            rows_out=len(lignes),
            lots_distincts=len(lots),
            sans_lot=sans_lot,
            lots=lots,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "pipeline": self.pipeline_name,
            "steps": [step.as_dict() for step in self.steps],
        }
