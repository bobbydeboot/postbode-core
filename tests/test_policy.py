import hashlib
from datetime import UTC, datetime

import pytest

from postbode.authority import PublicationAuthority
from postbode.contracts import PublicationError, PublicationRequest
from postbode.destination import DestinationPolicy
from postbode.plan import build_plan, metadata_digest


def make_request(tmp_path, **changes):
    asset = tmp_path / "asset.bin"
    asset.write_bytes(b"payload")
    values = {
        "destination_id": "example-destination",
        "platform": "youtube",
        "artifact_path": asset,
        "artifact_sha256": hashlib.sha256(b"payload").hexdigest(),
        "title": "Example",
        "description": "Safe",
        "privacy_status": "private",
        "idempotency_key": "key-1",
        "explicit_authority": True,
    }
    values.update(changes)
    return PublicationRequest(**values)


def test_unknown_destination_and_channel_rejected(tmp_path):
    req = make_request(tmp_path)
    policy = DestinationPolicy(
        "example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"
    )
    with pytest.raises(PublicationError):
        build_plan(req, policy, channel_id="wrong")
    with pytest.raises(PublicationError):
        build_plan(make_request(tmp_path, destination_id="unknown"), policy)


def test_non_private_requires_matching_authority(tmp_path):
    req = make_request(tmp_path, privacy_status="unlisted", made_for_kids=False)
    policy = DestinationPolicy(
        "example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"
    )
    with pytest.raises(PublicationError, match="authority"):
        build_plan(req, policy)
    authority = PublicationAuthority(
        "authority-1",
        req.destination_id,
        req.platform,
        policy.expected_channel_id,
        req.artifact_sha256,
        metadata_digest(req),
        req.privacy_status,
        datetime.now(UTC).isoformat(),
    )
    assert build_plan(req, policy, authority=authority).privacy_status == "unlisted"
