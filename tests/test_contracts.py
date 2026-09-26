import hashlib

import pytest

from postbode.contracts import PublicationError, PublicationRequest, sha256_file


def request(tmp_path, **changes):
    artifact = tmp_path / "asset.bin"
    artifact.write_bytes(b"safe bytes")
    values = {
        "destination_id": "example-destination",
        "platform": "youtube",
        "artifact_path": artifact,
        "artifact_sha256": hashlib.sha256(b"safe bytes").hexdigest(),
        "title": "Example",
        "description": "Description",
        "privacy_status": "private",
        "idempotency_key": "example-content-001",
        "explicit_authority": True,
    }
    values.update(changes)
    return PublicationRequest(**values)


def test_exact_artifact_binding(tmp_path):
    req = request(tmp_path, artifact_sha256="0" * 64)
    with pytest.raises(PublicationError, match="SHA-256"):
        req.validate()


def test_sha256_file_reads_in_chunks(tmp_path, monkeypatch):
    artifact = tmp_path / "asset.bin"
    artifact.write_bytes(b"0123456789")
    original_open = artifact.open
    reads = []

    class TrackingStream:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size=-1):
            reads.append(size)
            return self._stream.read(size)

    def tracked_open(*args, **kwargs):
        stream = TrackingStream()
        stream._stream = original_open(*args, **kwargs)
        return stream

    class PathProxy:
        def open(self, *args, **kwargs):
            return tracked_open(*args, **kwargs)

    assert (
        sha256_file(PathProxy(), chunk_size=3)
        == hashlib.sha256(b"0123456789").hexdigest()
    )
    assert reads == [3, 3, 3, 3, 3]


def test_non_private_requires_explicit_audience_flag(tmp_path):
    with pytest.raises(PublicationError, match="made_for_kids"):
        request(tmp_path, privacy_status="unlisted").validate()


def test_invalid_destination_rejected(tmp_path):
    with pytest.raises(PublicationError, match="destination"):
        request(tmp_path, destination_id=" ").validate()
