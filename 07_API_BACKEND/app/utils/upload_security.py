from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile


UPLOAD_CHUNK_BYTES = 1024 * 1024


def safe_upload_name(filename: str | None) -> str:
    name = Path(str(filename or "")).name.strip()
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide.")
    return name[:255]


async def read_limited_upload(upload: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(UPLOAD_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail="Fichier trop volumineux.")
        chunks.append(chunk)
    if total == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")
    return b"".join(chunks)


def validate_file_signature(filename: str, content: bytes) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix in {".xlsx", ".xlsm"} and not content.startswith(b"PK\x03\x04"):
        raise HTTPException(status_code=400, detail="Le contenu ne correspond pas a un fichier Excel OpenXML.")
    if suffix == ".xls" and not content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        raise HTTPException(status_code=400, detail="Le contenu ne correspond pas a un fichier Excel XLS.")
    if suffix == ".pdf" and not content.lstrip().startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Le contenu ne correspond pas a un fichier PDF.")
    if suffix == ".json":
        stripped = content.lstrip(b"\xef\xbb\xbf \t\r\n")
        if not stripped.startswith((b"{", b"[")):
            raise HTTPException(status_code=400, detail="Le contenu ne correspond pas a un fichier JSON.")
    if suffix == ".csv" and b"\x00" in content[:8192]:
        raise HTTPException(status_code=400, detail="Le contenu ne correspond pas a un fichier CSV texte.")

