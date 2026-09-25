import hashlib
from pathlib import Path

import pytest

from postbode import receipts
from postbode.contracts import PublicationError, PublicationRequest
from postbode.destination import DestinationPolicy
from postbode.plan import build_plan
from postbode.youtube import publish_plan


class FakeTransport:
    def __init__(self, channel="UC_EXAMPLE_CHANNEL_ID", readback="private"):
        self.channel_id = channel
        self.readback = readback
        self.uploads = 0

    def channel(self):
        return self.channel_id, "@examplechannel"

    def upload_private(self, request):
        self.uploads += 1
        return "video-001"

    def video(self, video_id):
        return {
            "id": video_id,
            "snippet": {"channelId": self.channel_id},
            "status": {"privacyStatus": self.readback},
        }


def make_plan(tmp_path: Path):
    artifact = tmp_path / "asset.bin"
    artifact.write_bytes(b"safe")
    request = PublicationRequest(
        "example-destination",
        "youtube",
        artifact,
        hashlib.sha256(b"safe").hexdigest(),
        "Example",
        "Safe",
        "private",
        "key-1",
        True,
    )
    return build_plan(
        request,
        DestinationPolicy("example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"),
    )


def test_idempotency_prevents_second_upload(tmp_path, monkeypatch):
    monkeypatch.setattr(receipts, "RECEIPT_ROOT", tmp_path / "receipts")
    plan = make_plan(tmp_path)
    transport = FakeTransport()
    first, _ = publish_plan(
        plan,
        None,
        DestinationPolicy("example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"),
        transport,
    )
    second, _ = publish_plan(
        plan,
        None,
        DestinationPolicy("example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"),
        transport,
    )
    assert first.provider_video_id == second.provider_video_id == "video-001"
    assert transport.uploads == 1


def test_ambiguous_result_is_not_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(receipts, "RECEIPT_ROOT", tmp_path / "receipts")
    plan = make_plan(tmp_path)

    class LostResponse(FakeTransport):
        def upload_private(self, request):
            self.uploads += 1
            raise RuntimeError("response lost after submission")

    with pytest.raises(RuntimeError):
        publish_plan(
            plan,
            None,
            DestinationPolicy(
                "example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"
            ),
            LostResponse(),
        )
    safe_retry = FakeTransport()
    with pytest.raises(PublicationError, match="ambiguous"):
        publish_plan(
            plan,
            None,
            DestinationPolicy(
                "example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"
            ),
            safe_retry,
        )
    assert safe_retry.uploads == 0


def test_readback_mismatch_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(receipts, "RECEIPT_ROOT", tmp_path / "receipts")
    plan = make_plan(tmp_path)
    with pytest.raises(PublicationError, match="readback"):
        publish_plan(
            plan,
            None,
            DestinationPolicy(
                "example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"
            ),
            FakeTransport(readback="unlisted"),
        )
