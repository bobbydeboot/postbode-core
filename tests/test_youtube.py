import hashlib

import pytest

from postbode.contracts import PublicationError, PublicationRequest
from postbode.youtube import YouTubeResponse, YouTubeTransport, build_upload_metadata


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


def test_resumable_upload_uses_bounded_chunks_and_exact_metadata(tmp_path):
    artifact = tmp_path / "asset.mp4"
    artifact.write_bytes(b"a" * (256 * 1024 + 17))
    request = PublicationRequest(
        "example-destination",
        "youtube",
        artifact,
        hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "Title",
        "Description",
        "private",
        "upload-key",
        True,
    )
    captured = []

    def fake_request(method, url, body=None, headers=None):
        captured.append((method, url, body, headers))
        if method == "POST":
            return YouTubeResponse(200, {"Location": "https://upload.example/session"})
        if len(body) == 256 * 1024:
            return YouTubeResponse(308, {"Range": "bytes=0-262143"})
        return YouTubeResponse(201, {}, b'{"id":"video-001"}')

    assert (
        YouTubeTransport("token", fake_request).upload_private(
            request, chunk_size=256 * 1024
        )
        == "video-001"
    )
    assert captured[0][0] == "POST"
    assert b'"privacyStatus":"private"' in captured[0][2]
    uploads = captured[1:]
    assert all(len(call[2]) <= 256 * 1024 for call in uploads)
    assert uploads[0][3]["Content-Range"] == "bytes 0-262143/262161"
    assert uploads[1][3]["Content-Range"] == "bytes 262144-262160/262161"


def test_resumable_upload_reconciles_ambiguous_chunk(tmp_path):
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
    calls = []

    def fake_request(method, url, body=None, headers=None):
        calls.append((method, body, headers))
        if method == "POST":
            return YouTubeResponse(200, {"Location": "https://upload.example/session"})
        if method == "PUT" and headers.get("Content-Range") == "bytes 0-10/11":
            raise PublicationError("provider request result is ambiguous")
        if headers.get("Content-Range") == "bytes */11":
            return YouTubeResponse(201, {}, b'{"id":"video-001"}')
        return YouTubeResponse(201, {}, b'{"id":"video-001"}')

    assert (
        YouTubeTransport("token", fake_request).upload_private(
            request, chunk_size=256 * 1024
        )
        == "video-001"
    )
    assert calls[2][2]["Content-Range"] == "bytes */11"
