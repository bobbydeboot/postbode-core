import hashlib

import pytest

from postbode.contracts import PublicationError, PublicationRequest


def request(tmp_path, **changes):
    artifact = tmp_path / "asset.bin"
    artifact.write_bytes(b"safe bytes")
    values = dict(
        destination_id="example-destination",
        platform="youtube",
        artifact_path=artifact,
        artifact_sha256=hashlib.sha256(b"safe bytes").hexdigest(),
        title="Example",
        description="Description",
        privacy_status="private",
        idempotency_key="example-content-001",
        explicit_authority=True,
    )
    values.update(changes)
    return PublicationRequest(**values)


def test_exact_artifact_binding(tmp_path):
    req = request(tmp_path, artifact_sha256="0" * 64)
    with pytest.raises(PublicationError, match="SHA-256"):
        req.validate()


def test_non_private_requires_explicit_audience_flag(tmp_path):
    with pytest.raises(PublicationError, match="made_for_kids"):
        request(tmp_path, privacy_status="unlisted").validate()


def test_invalid_destination_rejected(tmp_path):
    with pytest.raises(PublicationError, match="destination"):
        request(tmp_path, destination_id=" ").validate()
