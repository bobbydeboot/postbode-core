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
