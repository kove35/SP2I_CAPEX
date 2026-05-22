from __future__ import annotations

from dataclasses import dataclass, field


GOVERNANCE_STATUS_VALID = "VALID"
GOVERNANCE_STATUS_WARNING = "WARNING"
GOVERNANCE_STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
GOVERNANCE_STATUS_IGNORED = "IGNORED"
GOVERNANCE_STATUS_REJECTED = "REJECTED"

GOVERNANCE_CATEGORY_DATA_LOSS = "DATA_LOSS"
GOVERNANCE_CATEGORY_DATA_INTEGRITY = "DATA_INTEGRITY"
GOVERNANCE_CATEGORY_DATA_QUALITY = "DATA_QUALITY"
GOVERNANCE_CATEGORY_REVIEW_REQUIRED = "REVIEW_REQUIRED"
GOVERNANCE_CATEGORY_IGNORED = "IGNORED"


@dataclass(frozen=True)
class GovernanceIssue:
    code: str
    category: str
    severity: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass(frozen=True)
class GovernanceAssessment:
    governance_status: str
    trust_score: int
    governance_issues: list[GovernanceIssue] = field(default_factory=list)
    review_required: bool = False
    certification_status: str = "CERTIFIED"
    recoverable: bool = True
    recommended_action: str = "Aucune action requise."

    def as_dict(self) -> dict[str, object]:
        return {
            "governance_status": self.governance_status,
            "trust_score": self.trust_score,
            "governance_issues": [issue.as_dict() for issue in self.governance_issues],
            "review_required": self.review_required,
            "certification_status": self.certification_status,
            "recoverable": self.recoverable,
            "recommended_action": self.recommended_action,
        }
