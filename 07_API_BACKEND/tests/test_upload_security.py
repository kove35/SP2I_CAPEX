from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.utils.upload_security import safe_upload_name, validate_file_signature


def test_upload_filename_is_reduced_to_basename() -> None:
    assert safe_upload_name("../../DQE_MPEMBA.xlsx") == "DQE_MPEMBA.xlsx"


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("dqe.xlsx", b"not-a-zip"),
        ("dqe.pdf", b"not-a-pdf"),
        ("dqe.json", b"not-json"),
        ("dqe.csv", b"designation\x00quantite"),
    ],
)
def test_invalid_file_signatures_are_rejected(filename: str, content: bytes) -> None:
    with pytest.raises(HTTPException) as error:
        validate_file_signature(filename, content)
    assert error.value.status_code == 400


def test_valid_signatures_are_accepted() -> None:
    validate_file_signature("dqe.xlsx", b"PK\x03\x04payload")
    validate_file_signature("dqe.pdf", b"%PDF-1.7 payload")
    validate_file_signature("dqe.json", b'{"lignes": []}')
    validate_file_signature("dqe.csv", b"designation;quantite\nCable;10")

