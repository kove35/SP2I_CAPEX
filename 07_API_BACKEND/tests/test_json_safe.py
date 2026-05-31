from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import numpy as np
except Exception:
    np = None

from app.utils.json_safe import sanitize_for_json


def test_datetime_and_date_are_iso():
    obj = {"dt": datetime(2026, 5, 30, 12, 34, 56), "d": date(2026, 5, 30)}
    out = sanitize_for_json(obj)
    assert out["dt"] == "2026-05-30T12:34:56"
    assert out["d"] == "2026-05-30"


def test_decimal_and_uuid():
    dec = Decimal("123.45")
    uid = uuid4()
    obj = {"price": dec, "id": uid}
    out = sanitize_for_json(obj)
    assert isinstance(out["price"], float)
    assert out["price"] == 123.45
    assert isinstance(out["id"], str)


def test_pandas_timestamp_and_numpy_datetime():
    if pd is None and np is None:
        # nothing to test
        return

    pts = pd.Timestamp("2026-05-30T13:00:00") if pd is not None else None
    ndt = np.datetime64("2026-05-30T14:00:00") if np is not None else None
    src = {}
    if pts is not None:
        src["pts"] = pts
    if ndt is not None:
        src["ndt"] = ndt

    out = sanitize_for_json(src)
    if pts is not None:
        assert out["pts"].startswith("2026-05-30T13")
    if ndt is not None:
        assert "2026-05-30" in out["ndt"]
