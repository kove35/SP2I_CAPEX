from __future__ import annotations

import pytest

from app.config.financial_source import get_financial_source


def test_v6_financial_source_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SP2I_FINANCIAL_SOURCE", raising=False)
    assert get_financial_source() == "vw_fact_metre_financial_v6"


def test_legacy_financial_source_remains_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SP2I_FINANCIAL_SOURCE", "vw_fact_metre_financial_canonical")
    assert get_financial_source() == "vw_fact_metre_financial_canonical"


def test_unknown_financial_source_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SP2I_FINANCIAL_SOURCE", "untrusted_view")
    with pytest.raises(ValueError, match="Invalid SP2I_FINANCIAL_SOURCE"):
        get_financial_source()
