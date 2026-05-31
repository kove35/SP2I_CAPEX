from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from typing import Any

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import numpy as np
except Exception:
    np = None


def _sanitize(obj: Any) -> Any:
    # None, bool, int, float, str are safe
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    # Datetime-like
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    # pandas Timestamp
    if pd is not None and isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    # numpy datetime64
    if np is not None and isinstance(obj, np.datetime64):
        try:
            # prefer ISO string
            return np.datetime_as_string(obj, unit="s")
        except Exception:
            return str(obj)

    # Decimal -> float
    if isinstance(obj, Decimal):
        try:
            return float(obj)
        except Exception:
            return str(obj)

    # UUID -> str
    if isinstance(obj, UUID):
        return str(obj)

    # Pydantic models with model_dump
    if hasattr(obj, "model_dump"):
        try:
            dumped = obj.model_dump(mode="json")
            return sanitize_for_json(dumped)
        except Exception:
            try:
                return sanitize_for_json(obj.model_dump())
            except Exception:
                return str(obj)

    # dict-like
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}

    # lists, tuples, sets -> list
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]

    # numpy scalars -> python native
    if np is not None and isinstance(obj, (np.integer, np.floating)):
        try:
            return obj.item()
        except Exception:
            return float(obj)

    # Fallback: try to convert to primitive via __str__
    return str(obj)


def sanitize_for_json(obj: Any) -> Any:
    """Recursively convert common non-JSON-serializable types into JSON-safe primitives.

    Supported conversions:
    - datetime/date -> ISO string
    - pandas.Timestamp -> ISO string
    - numpy.datetime64 -> ISO string
    - Decimal -> float
    - UUID -> str
    - lists/tuples/sets/dicts recursively handled
    """
    return _sanitize(obj)
