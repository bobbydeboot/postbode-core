from __future__ import annotations

from dataclasses import dataclass

from .contracts import PublicationError


@dataclass(frozen=True)
class ChannelBranding:
    destination_id: str
    title: str
    description: str
    avatar_path: str | None = None
    banner_path: str | None = None

    def validate(self) -> None:
        if not self.destination_id.strip() or not self.title.strip():
            raise PublicationError("branding destination and title are required")
