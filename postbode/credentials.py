from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from dataclasses import dataclass

from .contracts import PublicationError


class CredentialError(PublicationError):
    """Credentials are unavailable or incomplete."""


@dataclass(frozen=True)
class YouTubeCredential:
    client_id: str
    client_secret: str
    refresh_token: str

    def __post_init__(self) -> None:
        if not all((self.client_id, self.client_secret, self.refresh_token)):
            raise CredentialError("YouTube credentials are incomplete")

    def fingerprint(self) -> str:
        return hashlib.sha256(self.client_id.encode()).hexdigest()[:16]


def load_youtube_credential(env: Mapping[str, str] | None = None) -> YouTubeCredential:
    values = os.environ if env is None else env
    names = (
        "POSTBODE_YOUTUBE_CLIENT_ID",
        "POSTBODE_YOUTUBE_CLIENT_SECRET",
        "POSTBODE_YOUTUBE_REFRESH_TOKEN",
    )
    raw = tuple(values.get(name, "") for name in names)
    if not all(raw):
        raise CredentialError("YouTube credentials are unavailable")
    return YouTubeCredential(*raw)
