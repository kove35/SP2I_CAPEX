from __future__ import annotations

from collections import Counter
from typing import Any

from app.governance.explainability import issue_message, recommended_action
from app.governance.schemas import (
    GOVERNANCE_CATEGORY_DATA_INTEGRITY,
    GOVERNANCE_CATEGORY_DATA_LOSS,
    GOVERNANCE_CATEGORY_DATA_QUALITY,
    GOVERNANCE_CATEGORY_IGNORED,
    GOVERNANCE_CATEGORY_REVIEW_REQUIRED,
    GOVERNANCE_STATUS_IGNORED,
    GOVERNANCE_STATUS_REJECTED,
    GOVERNANCE_STATUS_REVIEW_REQUIRED,
    GOVERNANCE_STATUS_VALID,
    GOVERNANCE_STATUS_WARNING,
    GovernanceAssessment,
    GovernanceIssue,
)
from app.governance.scoring import trust_score_for


IGNORED_ROW_TYPES = {"vide", "lot", "total", "ratio_analytics"}


def _issue(code: str, category: str, severity: str) -> GovernanceIssue:
    return GovernanceIssue(
        code=code,
        category=category,
        severity=severity,
        message=issue_message(code),
    )


def assess_parsed_row(row_type: str, reason: str = "") -> GovernanceAssessment:
    """
    Mappe les anciens statuts du parser vers la taxonomie gouvernance.

    Regle critique : WARNING et REVIEW_REQUIRED ne sont jamais assimiles a une
    perte de donnees. Seuls DATA_LOSS et DATA_INTEGRITY bloquants peuvent
    declencher un arret du pipeline.
    """
    row_type_normalized = str(row_type or "inconnu").lower()

    if row_type_normalized == "article":
        issue = _issue("VALID_ARTICLE", GOVERNANCE_CATEGORY_DATA_QUALITY, "INFO")
        return GovernanceAssessment(
            governance_status=GOVERNANCE_STATUS_VALID,
            trust_score=100,
            governance_issues=[],
            review_required=False,
            certification_status="CERTIFIED",
            recommended_action=recommended_action(issue.code),
        )

    if row_type_normalized == "vide":
        code = "IGNORED_EMPTY"
    elif row_type_normalized == "lot":
        code = "IGNORED_TITLE"
    elif row_type_normalized == "total":
        code = "IGNORED_SUBTOTAL"
    elif row_type_normalized == "ratio_analytics":
        code = "IGNORED_ANALYTICS"
    else:
        code = ""

    if row_type_normalized in IGNORED_ROW_TYPES:
        issue = _issue(code, GOVERNANCE_CATEGORY_IGNORED, "INFO")
        return GovernanceAssessment(
            governance_status=GOVERNANCE_STATUS_IGNORED,
            trust_score=100,
            governance_issues=[issue],
            review_required=False,
            certification_status="IGNORED_NOT_A_LOSS",
            recommended_action=recommended_action(code),
        )

    if row_type_normalized == "inconnu":
        issue = _issue("REVIEW_NO_LOT", GOVERNANCE_CATEGORY_REVIEW_REQUIRED, "WARNING")
        return GovernanceAssessment(
            governance_status=GOVERNANCE_STATUS_REVIEW_REQUIRED,
            trust_score=trust_score_for([issue]),
            governance_issues=[issue],
            review_required=True,
            certification_status="HUMAN_REVIEW_REQUIRED",
            recommended_action=recommended_action(issue.code),
        )

    if "critique" in reason.lower() or "bloquant" in reason.lower():
        issue = _issue("DATA_LOSS_BLOCKING", GOVERNANCE_CATEGORY_DATA_LOSS, "CRITICAL")
        return GovernanceAssessment(
            governance_status=GOVERNANCE_STATUS_REJECTED,
            trust_score=trust_score_for([issue]),
            governance_issues=[issue],
            review_required=True,
            certification_status="BLOCKED",
            recoverable=False,
            recommended_action=recommended_action(issue.code),
        )

    issue = _issue("DATA_QUALITY_INFORMATIONAL", GOVERNANCE_CATEGORY_DATA_QUALITY, "WARNING")
    return GovernanceAssessment(
        governance_status=GOVERNANCE_STATUS_WARNING,
        trust_score=trust_score_for([issue]),
        governance_issues=[issue],
        review_required=False,
        certification_status="QUALITY_WARNING",
        recommended_action=recommended_action(issue.code),
    )


def row_has_blocking_loss(row: dict[str, Any]) -> bool:
    issues = row.get("governance_issues") or []
    for issue in issues:
        category = issue.get("category") if isinstance(issue, dict) else getattr(issue, "category", "")
        if category in {GOVERNANCE_CATEGORY_DATA_LOSS, GOVERNANCE_CATEGORY_DATA_INTEGRITY}:
            return True
    return False


def summarize_classified_rows(classified_rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("governance_status") or "UNKNOWN") for row in classified_rows)
    type_counts = Counter(str(row.get("row_type") or "inconnu") for row in classified_rows)
    issue_counts: Counter[str] = Counter()
    blocking_rows = 0
    review_rows = 0

    for row in classified_rows:
        if row_has_blocking_loss(row):
            blocking_rows += 1
        if row.get("review_required"):
            review_rows += 1
        for issue in row.get("governance_issues") or []:
            if isinstance(issue, dict):
                issue_counts[str(issue.get("code") or "UNKNOWN")] += 1

    total = len(classified_rows)
    return {
        "total_rows": total,
        "valid_rows": status_counts.get(GOVERNANCE_STATUS_VALID, 0),
        "ignored_rows": status_counts.get(GOVERNANCE_STATUS_IGNORED, 0),
        "warning_rows": status_counts.get(GOVERNANCE_STATUS_WARNING, 0),
        "review_required_rows": review_rows,
        "blocking_loss_rows": blocking_rows,
        "strict_loss_ratio": round(blocking_rows / total, 4) if total else 0,
        "review_ratio": round(review_rows / total, 4) if total else 0,
        "status_counts": dict(status_counts),
        "row_type_counts": dict(type_counts),
        "issue_counts": dict(issue_counts),
    }
