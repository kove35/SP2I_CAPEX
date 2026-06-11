from __future__ import annotations

import os


FACT_SOURCE = os.getenv("SP2I_FACT_SOURCE", "vw_fact_metre_current")

ALLOWED_FACT_SOURCES = {
    "fact_metre",
    "vw_fact_metre_current",
    "vw_fact_metre_v53_financial",
}


def get_fact_source() -> str:
    fact_source = os.getenv("SP2I_FACT_SOURCE", FACT_SOURCE).strip()
    if fact_source not in ALLOWED_FACT_SOURCES:
        allowed = ", ".join(sorted(ALLOWED_FACT_SOURCES))
        raise ValueError(
            f"Invalid SP2I_FACT_SOURCE={fact_source!r}. "
            f"Allowed values are: {allowed}."
        )
    return fact_source
