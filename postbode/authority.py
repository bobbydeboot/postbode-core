from __future__ import annotations

from dataclasses import asdict, dataclass

from .contracts import PublicationError, PublicationRequest
from .destination import DestinationPolicy


@dataclass(frozen=True)
class PublicationAuthority:
    authority_id: str
    destination_id: str
    platform: str
    channel_id: str
    artifact_sha256: str
    metadata_digest: str
    privacy_status: str
    issued_at: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)

    def validate(
        self,
        request: PublicationRequest,
        policy: DestinationPolicy,
        metadata_digest: str,
    ) -> None:
        policy.validate_request(request)
        expected = (
            request.destination_id,
            request.platform,
            request.artifact_sha256,
            metadata_digest,
            request.privacy_status,
        )
        actual = (
            self.destination_id,
            self.platform,
            self.artifact_sha256,
            self.metadata_digest,
            self.privacy_status,
        )
        if actual != expected or self.channel_id != policy.expected_channel_id:
            raise PublicationError("publication authority does not match plan")
