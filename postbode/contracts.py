from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

PublicationStatus = Literal["private", "unlisted", "public"]
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PublicationError(ValueError):
    """A request cannot safely proceed."""


@dataclass(frozen=True)
class PublicationRequest:
    destination_id: str
    platform: Literal["youtube"]
    artifact_path: Path
    artifact_sha256: str
    title: str
    description: str
    privacy_status: PublicationStatus
    idempotency_key: str
    explicit_authority: bool = False
    tags: tuple[str, ...] = ()
    language: str | None = None
    category_id: str | None = None
    made_for_kids: bool | None = None

    def validate(self) -> None:
        if not self.destination_id.strip():
            raise PublicationError("destination_id is required")
        if self.platform != "youtube":
            raise PublicationError("unsupported platform")
        if self.privacy_status not in {"private", "unlisted", "public"}:
            raise PublicationError("unsupported privacy status")
        if not self.artifact_path.is_file():
            raise PublicationError("artifact does not exist")
        if not _SHA256.fullmatch(self.artifact_sha256):
            raise PublicationError("artifact_sha256 must be a lowercase SHA-256")
        if (
            hashlib.sha256(self.artifact_path.read_bytes()).hexdigest()
            != self.artifact_sha256
        ):
            raise PublicationError("artifact SHA-256 does not match request")
        if not self.idempotency_key.strip():
            raise PublicationError("idempotency_key is required")
        if not self.title.strip() or len(self.title) > 100:
            raise PublicationError("title must contain 1-100 characters")
        if len(self.description) > 5000:
            raise PublicationError("description must contain at most 5000 characters")
        if any(
            ord(c) < 32 and c not in "\t\n\r" for c in self.title + self.description
        ):
            raise PublicationError("metadata contains control characters")
        if any(not tag.strip() for tag in self.tags):
            raise PublicationError("tags must not be empty")
        if self.privacy_status != "private" and self.made_for_kids is None:
            raise PublicationError(
                "made_for_kids must be explicit for non-private publication"
            )

    def identity(self) -> str:
        self.validate()
        value = asdict(self)
        value["artifact_path"] = str(self.artifact_path)
        value["tags"] = list(self.tags)
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class PublicationReceipt:
    request_identity: str
    destination_id: str
    platform: str
    artifact_sha256: str
    channel_id: str
    provider_video_id: str | None
    privacy_status: str | None
    state: str
    created_at: str
    idempotency_key: str | None = None
    error_class: str | None = None
    readback_privacy_status: str | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)
