import hashlib

import pytest

from postbode.contracts import PublicationError, PublicationRequest
from postbode.youtube import build_upload_metadata


def test_metadata_preserves_privacy(tmp_path):
    artifact = tmp_path / "asset.bin"
    artifact.write_bytes(b"payload")
    request = PublicationRequest(
        "example-destination",
        "youtube",
        artifact,
        hashlib.sha256(b"payload").hexdigest(),
        "Title",
        "Description",
        "unlisted",
        "key",
        True,
        ("example",),
        made_for_kids=False,
    )
    assert build_upload_metadata(request)["status"]["privacyStatus"] == "unlisted"


def test_empty_access_token_fails_closed():
    from postbode.youtube import YouTubeTransport

    with pytest.raises(PublicationError):
        YouTubeTransport("")


def test_multipart_upload_uses_exact_metadata_and_bytes(tmp_path):
    artifact = tmp_path / "asset.mp4"
    artifact.write_bytes(b"video bytes")
    request = PublicationRequest(
        "example-destination",
        "youtube",
        artifact,
        hashlib.sha256(b"video bytes").hexdigest(),
        "Title",
        "Description",
        "private",
        "upload-key",
        True,
    )
    captured = {}

    def fake_request(method, url, body=None, headers=None):
        captured.update(method=method, url=url, body=body, headers=headers)
        return {"id": "video-001"}

    from postbode.youtube import YouTubeTransport

    assert (
        YouTubeTransport("token", fake_request).upload_private(request) == "video-001"
    )
    assert captured["method"] == "POST"
    assert b'"privacyStatus":"private"' in captured["body"]
    assert b"video bytes" in captured["body"]
