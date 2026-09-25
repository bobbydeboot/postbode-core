from __future__ import annotations

import json
import os
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path

from .contracts import PublicationError, PublicationReceipt

STATE_ROOT = Path(os.environ.get("POSTBODE_STATE_ROOT", Path.home() / ".postbode"))
RECEIPT_ROOT = STATE_ROOT / "receipts"


def _path(identity: str) -> Path:
    if not identity or any(c not in "0123456789abcdef" for c in identity):
        raise PublicationError("invalid request identity")
    return RECEIPT_ROOT / f"{identity}.json"


def read_receipt(identity: str) -> PublicationReceipt | None:
    path = _path(identity)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    names = {field.name for field in fields(PublicationReceipt)}
    return PublicationReceipt(**{name: payload[name] for name in names})


def write_receipt(receipt: PublicationReceipt) -> Path:
    RECEIPT_ROOT.mkdir(parents=True, exist_ok=True)
    path = _path(receipt.request_identity)
    path.write_text(
        json.dumps(receipt.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def idempotency_conflict(identity: str, key: str) -> bool:
    receipt = read_receipt(identity)
    if receipt is not None:
        return False
    if not RECEIPT_ROOT.exists():
        return False
    for path in RECEIPT_ROOT.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            payload.get("idempotency_key") == key
            and payload.get("request_identity") != identity
        ):
            return True
    return False


def now() -> str:
    return datetime.now(UTC).isoformat()
