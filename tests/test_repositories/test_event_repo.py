"""Tests for EventRepository using an in-memory SQLite database."""
import sqlite3
from datetime import date, time

import pytest

from src.models.event import Event, EventCategory, EventRecurrence
from src.repositories.database import init_db
from src.repositories.event_repo import EventRepository


@pytest.fixture()
def repo():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return EventRepository(conn)


def _sample_event(**overrides) -> Event:
    defaults = dict(
        title="Staff meeting",
        event_date=date(2025, 5, 20),
        category=EventCategory.WORK,
    )
    defaults.update(overrides)
    return Event(**defaults)


class TestInsert:
    def test_returns_event_with_id(self, repo):
        e = repo.insert(_sample_event())
        assert e.id is not None
        assert e.title == "Staff meeting"

    def test_preserves_times(self, repo):
        e = repo.insert(
            _sample_event(start_time=time(9, 0), end_time=time(10, 30))
        )
        fetched = repo.get_by_id(e.id)
        assert fetched.start_time == time(9, 0)
        assert fetched.end_time == time(10, 30)

    def test_null_times(self, repo):
        e = repo.insert(_sample_event())
        fetched = repo.get_by_id(e.id)
        assert fetched.start_time is None
        assert fetched.end_time is None


class TestUpdate:
    def test_updates_title(self, repo):
        e = repo.insert(_sample_event())
        updated = Event(
            id=e.id,
            title="Updated meeting",
            event_date=e.event_date,
            category=e.category,
        )
        repo.update(updated)
        fetched = repo.get_by_id(e.id)
        assert fetched.title == "Updated meeting"


class TestDelete:
    def test_removes_event(self, repo):
        e = repo.insert(_sample_event())
        repo.delete(e.id)
        assert repo.get_by_id(e.id) is None


class TestQueries:
    def test_get_by_date(self, repo):
        repo.insert(_sample_event(event_date=date(2025, 5, 20)))
        repo.insert(_sample_event(event_date=date(2025, 5, 20), title="Second"))
        repo.insert(_sample_event(event_date=date(2025, 5, 21), title="Other day"))
        results = repo.get_by_date(date(2025, 5, 20))
        assert len(results) == 2

    def test_get_by_month(self, repo):
        repo.insert(_sample_event(event_date=date(2025, 5, 1)))
        repo.insert(_sample_event(event_date=date(2025, 5, 31), title="End"))
        repo.insert(_sample_event(event_date=date(2025, 6, 1), title="June"))
        assert len(repo.get_by_month(2025, 5)) == 2

    def test_get_by_date_range(self, repo):
        repo.insert(_sample_event(event_date=date(2025, 5, 10), title="A"))
        repo.insert(_sample_event(event_date=date(2025, 5, 20), title="B"))
        repo.insert(_sample_event(event_date=date(2025, 5, 30), title="C"))
        results = repo.get_by_date_range(date(2025, 5, 15), date(2025, 5, 25))
        assert len(results) == 1
        assert results[0].title == "B"
