from __future__ import annotations

from app.governance.schemas import (
    GOVERNANCE_CATEGORY_DATA_INTEGRITY,
    GOVERNANCE_CATEGORY_DATA_LOSS,
    GOVERNANCE_CATEGORY_DATA_QUALITY,
    GOVERNANCE_CATEGORY_REVIEW_REQUIRED,
    GovernanceIssue,
)


PENALTIES = {
    GOVERNANCE_CATEGORY_DATA_LOSS: 40,
    GOVERNANCE_CATEGORY_DATA_INTEGRITY: 25,
    GOVERNANCE_CATEGORY_DATA_QUALITY: 10,
    GOVERNANCE_CATEGORY_REVIEW_REQUIRED: 3,
}


def trust_score_for(issues: list[GovernanceIssue]) -> int:
    score = 100
    for issue in issues:
        score -= PENALTIES.get(issue.category, 0)
    return max(0, min(100, score))
