from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .contracts import PublicationError


@dataclass(frozen=True)
class AssetDescriptor:
    asset_id: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str


def validate_asset(
    descriptor: AssetDescriptor,
    *,
    expected_id: str,
    expected_filename: str,
    expected_mime: str,
    expected_sha256: str,
) -> None:
    if descriptor.asset_id != expected_id:
        raise PublicationError("asset ID mismatch")
    if descriptor.filename != expected_filename:
        raise PublicationError("asset filename mismatch")
    if descriptor.mime_type != expected_mime:
        raise PublicationError("asset MIME type mismatch")
    if descriptor.sha256 != expected_sha256:
        raise PublicationError("asset SHA-256 mismatch")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
