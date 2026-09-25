from datetime import UTC, datetime, timedelta

import pytest

from postbode.contracts import PublicationError
from postbode.schedule import validate_schedule


def test_past_schedule_rejected():
    now = datetime.now(UTC)
    with pytest.raises(PublicationError, match="future"):
        validate_schedule(now - timedelta(minutes=1), now=now)


def test_naive_schedule_rejected():
    with pytest.raises(PublicationError, match="timezone"):
        validate_schedule(datetime.now())
