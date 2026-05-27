from __future__ import annotations

from typing import Any


class ApprovalNotificationService:
    """Point d'extension pour email, Teams ou notifications in-app."""

    def build_notification(self, event_type: str, approval: Any) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "approval_id": getattr(approval, "approval_id", None),
            "project_id": getattr(approval, "project_id", None),
            "status": getattr(approval, "status", ""),
            "assigned_to": getattr(approval, "assigned_to", ""),
            "role_required": getattr(approval, "role_required", ""),
        }
