from postbode.contracts import PublicationReceipt
from postbode.receipts import read_receipt, write_receipt


def test_receipt_roundtrip_is_secret_free(tmp_path, monkeypatch):
    from postbode import receipts

    monkeypatch.setattr(receipts, "RECEIPT_ROOT", tmp_path / "receipts")
    value = PublicationReceipt(
        "a" * 64,
        "example-destination",
        "youtube",
        "b" * 64,
        "UC_EXAMPLE_CHANNEL_ID",
        "video-001",
        "private",
        "completed",
        "now",
        "key-1",
    )
    path = write_receipt(value)
    assert read_receipt(value.request_identity) == value
    assert "refresh_token" not in path.read_text(encoding="utf-8")
