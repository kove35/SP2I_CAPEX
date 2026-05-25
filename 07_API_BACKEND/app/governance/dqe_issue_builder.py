from __future__ import annotations

from typing import Any

from app.governance.dqe_issue_catalog import ISSUE_DEFINITIONS


def build_dqe_issue(issue_type: str, **context: Any) -> dict[str, Any]:
    definition = ISSUE_DEFINITIONS.get(issue_type)
    if not definition:
        definition = {
            "category": "GOVERNANCE",
            "severity": "REVIEW_REQUIRED",
            "blocking": False,
            "message": "Une anomalie DQE non cataloguee a ete detectee.",
            "impact": "Une validation humaine est necessaire pour confirmer l'impact metier.",
            "manual_fix": "Controlez la ligne ou la colonne signalee dans Excel, puis relancez l'analyse DQE.",
            "example": "",
        }

    issue = {
        "issue_type": issue_type,
        "category": definition["category"],
        "severity": definition["severity"],
        "blocking": bool(definition["blocking"]),
        "field": context.get("field"),
        "label": context.get("label"),
        "sheet_name": context.get("sheet_name"),
        "line_number": context.get("line_number"),
        "column_name": context.get("column_name"),
        "detected_value": context.get("detected_value"),
        "expected_value": context.get("expected_value"),
        "expected_aliases": context.get("expected_aliases") or [],
        "available_columns": context.get("available_columns") or [],
        "message": context.get("message") or definition["message"],
        "impact": context.get("impact") or definition["impact"],
        "manual_fix": context.get("manual_fix") or definition["manual_fix"],
        "example": context.get("example") or definition.get("example", ""),
    }

    for key in ("delta", "source", "row_type", "reason"):
        if key in context:
            issue[key] = context[key]

    return issue


def summarize_dqe_issues(issues: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total": len(issues),
        "blocking": sum(1 for issue in issues if issue.get("blocking")),
        "data_loss": 0,
        "data_integrity": 0,
        "data_quality": 0,
        "review_required": 0,
        "warning": 0,
        "sync_required": 0,
        "stale": 0,
    }
    severity_map = {
        "DATA_LOSS": "data_loss",
        "DATA_INTEGRITY": "data_integrity",
        "DATA_QUALITY": "data_quality",
        "REVIEW_REQUIRED": "review_required",
        "WARNING": "warning",
        "SYNC_REQUIRED": "sync_required",
        "STALE": "stale",
    }
    for issue in issues:
        key = severity_map.get(str(issue.get("severity") or ""))
        if key:
            summary[key] += 1
    return summary
