"""Business logic for calendar event management."""
from __future__ import annotations

from datetime import date

from src.models.event import Event
from src.repositories.event_repo import EventRepository


class EventService:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    def add_event(self, event: Event) -> Event:
        return self._repo.insert(event)

    def update_event(self, event: Event) -> None:
        self._repo.update(event)

    def delete_event(self, event_id: int) -> None:
        self._repo.delete(event_id)

    def get_event(self, event_id: int) -> Event | None:
        return self._repo.get_by_id(event_id)

    def get_events_for_date(self, d: date) -> list[Event]:
        return self._repo.get_by_date(d)

    def get_events_for_month(self, year: int, month: int) -> list[Event]:
        return self._repo.get_by_month(year, month)

    def get_events_in_range(self, start: date, end: date) -> list[Event]:
        return self._repo.get_by_date_range(start, end)

    def get_all_events(self) -> list[Event]:
        return self._repo.get_all()
