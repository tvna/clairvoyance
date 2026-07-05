"""Model-level behaviors that the API tests exercise only indirectly."""

from datetime import UTC, datetime

from sqlalchemy.dialects import sqlite

from app.db.models import UTCDateTime

DIALECT = sqlite.dialect()


def test_utcdatetime_attaches_utc_to_naive_loads() -> None:
    naive = datetime(2026, 7, 2, 10, 0)
    loaded = UTCDateTime().process_result_value(naive, DIALECT)
    assert loaded == datetime(2026, 7, 2, 10, 0, tzinfo=UTC)


def test_utcdatetime_passes_through_aware_and_none() -> None:
    aware = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    assert UTCDateTime().process_result_value(aware, DIALECT) is aware
    assert UTCDateTime().process_result_value(None, DIALECT) is None
