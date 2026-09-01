from __future__ import annotations

import os


FINANCIAL_SOURCE = os.getenv("SP2I_FINANCIAL_SOURCE", "vw_fact_metre_financial_canonical")

ALLOWED_FINANCIAL_SOURCES = {
    "fact_metre",
    "vw_fact_metre_current",
    "vw_fact_metre_v53_financial",
    "vw_fact_metre_financial_canonical",
}


def get_financial_source() -> str:
    financial_source = os.getenv("SP2I_FINANCIAL_SOURCE", FINANCIAL_SOURCE).strip()
    if financial_source not in ALLOWED_FINANCIAL_SOURCES:
        allowed = ", ".join(sorted(ALLOWED_FINANCIAL_SOURCES))
        raise ValueError(
            f"Invalid SP2I_FINANCIAL_SOURCE={financial_source!r}. "
            f"Allowed values are: {allowed}."
        )
    return financial_source
