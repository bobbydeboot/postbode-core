from __future__ import annotations

from datetime import UTC, datetime

from .contracts import PublicationError


def validate_schedule(value: datetime | None, *, now: datetime | None = None) -> None:
    if value is None:
        return
    reference = now or datetime.now(UTC)
    if value.tzinfo is None:
        raise PublicationError("scheduled time must include a timezone")
    if value <= reference:
        raise PublicationError("scheduled time must be in the future")
