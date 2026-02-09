"""Tests for the Event domain model."""
import pytest
from datetime import date, time

from src.models.event import (
    Event,
    EventCategory,
    EventRecurrence,
    EVENT_CATEGORY_COLORS,
)


def _make_event(**overrides) -> Event:
    defaults = dict(
        title="Team meeting",
        event_date=date(2025, 4, 10),
        category=EventCategory.WORK,
    )
    defaults.update(overrides)
    return Event(**defaults)


class TestEventCreation:
    def test_basic_creation(self):
        e = _make_event()
        assert e.title == "Team meeting"
        assert e.event_date == date(2025, 4, 10)
        assert e.category == EventCategory.WORK
        assert e.start_time is None
        assert e.end_time is None
        assert e.recurrence == EventRecurrence.NONE

    def test_empty_title_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            _make_event(title="")

    def test_whitespace_title_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            _make_event(title="   ")

    def test_end_before_start_rejected(self):
        with pytest.raises(ValueError, match="End time must not be before"):
            _make_event(
                start_time=time(14, 0),
                end_time=time(10, 0),
            )

    def test_same_start_end_allowed(self):
        e = _make_event(start_time=time(10, 0), end_time=time(10, 0))
        assert e.start_time == e.end_time


class TestEventDisplayColor:
    def test_default_color_from_category(self):
        e = _make_event(category=EventCategory.WORK)
        assert e.display_color == EVENT_CATEGORY_COLORS[EventCategory.WORK]

    def test_custom_color_overrides_default(self):
        e = _make_event(color="#FF0000")
        assert e.display_color == "#FF0000"

    def test_all_categories_have_default_colors(self):
        for cat in EventCategory:
            assert cat in EVENT_CATEGORY_COLORS
