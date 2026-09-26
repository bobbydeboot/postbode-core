from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from . import receipts
from .authority import PublicationAuthority
from .contracts import PublicationError, PublicationRequest
from .destination import DestinationPolicy


@dataclass(frozen=True)
class PublicationPlan:
    request_identity: str
    destination_id: str
    platform: str
    channel_id: str
    artifact_sha256: str
    artifact_path: str
    title: str
    description: str
    tags: tuple[str, ...]
    privacy_status: str
    metadata_digest: str
    idempotency_key: str
    authority_id: str | None
    credential_fingerprint: str | None
    created_at: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def metadata_digest(request: PublicationRequest) -> str:
    request.validate()
    value = {
        "title": request.title,
        "description": request.description,
        "tags": request.tags,
        "language": request.language,
        "category_id": request.category_id,
        "made_for_kids": request.made_for_kids,
        "privacy_status": request.privacy_status,
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_plan(
    request: PublicationRequest,
    policy: DestinationPolicy,
    *,
    channel_id: str | None = None,
    channel_handle: str | None = None,
    authority: PublicationAuthority | None = None,
    credential_fingerprint: str | None = None,
) -> PublicationPlan:
    request.validate()
    policy.validate_request(
        request, channel_id=channel_id, channel_handle=channel_handle
    )
    digest = metadata_digest(request)
    if request.privacy_status != "private" and authority is None:
        raise PublicationError("non-private publication requires exact authority")
    if authority is not None:
        authority.validate(request, policy, digest)
    identity = request.identity()
    if receipts.idempotency_conflict(identity, request.idempotency_key):
        raise PublicationError("idempotency key conflicts with prior intent")
    return PublicationPlan(
        identity,
        request.destination_id,
        request.platform,
        channel_id or policy.expected_channel_id,
        request.artifact_sha256,
        str(request.artifact_path),
        request.title,
        request.description,
        request.tags,
        request.privacy_status,
        digest,
        request.idempotency_key,
        authority.authority_id if authority else None,
        credential_fingerprint,
        receipts.now(),
    )
