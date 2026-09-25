from __future__ import annotations

from dataclasses import dataclass

from .contracts import PublicationError, PublicationRequest


@dataclass(frozen=True)
class DestinationPolicy:
    destination_id: str
    platform: str
    expected_channel_id: str
    expected_channel_handle: str | None = None
    credential_alias: str = "youtube-default"
    require_private_first: bool = True

    def validate_request(
        self,
        request: PublicationRequest,
        *,
        channel_id: str | None = None,
        channel_handle: str | None = None,
    ) -> None:
        if (request.destination_id, request.platform) != (
            self.destination_id,
            self.platform,
        ):
            raise PublicationError("destination policy mismatch")
        if channel_id is not None and channel_id != self.expected_channel_id:
            raise PublicationError("authenticated channel ID mismatch")
        if (
            self.expected_channel_handle
            and channel_handle is not None
            and channel_handle.casefold() != self.expected_channel_handle.casefold()
        ):
            raise PublicationError("authenticated channel handle mismatch")
