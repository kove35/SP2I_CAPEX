from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.spatial.utils.normalization import normalize_spatial_value


def build_spatial_timeline(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a compact spatial timeline from execution actions.

    This is intentionally data-centric and does not try to replace a planning
    engine. It creates readable ETA -> livraison -> pose -> validation steps.
    """
    today = datetime.now(timezone.utc).date()
    rows: list[dict[str, Any]] = []
    for action in actions:
        eta_days = _number(action.get("delivery_eta_days"))
        delay_days = _number(action.get("delay_days"))
        due_date = _date_or_offset(action.get("due_date"), today, max(1, eta_days))
        livraison_date = due_date
        pose_date = livraison_date + timedelta(days=2 + max(0, int(delay_days // 7)))
        validation_date = pose_date + timedelta(days=2)
        status = str(action.get("status") or "TO_DO").upper()
        risk_level = str(action.get("risk_level") or "MEDIUM").upper()
        rows.append(
            {
                "zone": _zone_label(action),
                "batiment": normalize_spatial_value(action.get("batiment"), "batiment"),
                "niveau": normalize_spatial_value(action.get("niveau"), "niveau"),
                "piece": normalize_spatial_value(action.get("piece"), "piece"),
                "lot": normalize_spatial_value(action.get("lot"), "lot"),
                "action_id": action.get("id"),
                "action_type": action.get("action_type") or "COORDINATION",
                "status": status,
                "risk_level": risk_level,
                "eta_days": eta_days,
                "delay_days": delay_days,
                "eta_date": livraison_date.isoformat(),
                "delivery_date": livraison_date.isoformat(),
                "installation_date": pose_date.isoformat(),
                "validation_date": validation_date.isoformat(),
                "is_critical": status in {"AT_RISK", "BLOCKED"} or risk_level in {"HIGH", "CRITICAL"},
                "message": _timeline_message(status, risk_level, eta_days),
            }
        )
    return sorted(rows, key=lambda row: (row["delivery_date"], row["zone"], row["lot"]))[:200]


def _zone_label(action: dict[str, Any]) -> str:
    parts = [
        normalize_spatial_value(action.get("batiment"), "batiment"),
        normalize_spatial_value(action.get("niveau"), "niveau"),
    ]
    piece = str(action.get("piece") or "").strip()
    if piece:
        parts.append(piece)
    return " > ".join(parts)


def _number(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _date_or_offset(value: Any, today, offset_days: int):
    if value:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except ValueError:
            pass
    return today + timedelta(days=offset_days)


def _timeline_message(status: str, risk_level: str, eta_days: int) -> str:
    if status == "BLOCKED":
        return "Workflow chantier bloqué sur cette zone."
    if status == "AT_RISK" or risk_level in {"HIGH", "CRITICAL"}:
        return "ETA ou dépendance critique à surveiller."
    if eta_days > 0:
        return "Livraison à coordonner avec la pose chantier."
    return "Action chantier à planifier."
