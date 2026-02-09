from __future__ import annotations

import sqlite3
from datetime import date, time

from src.models.event import Event, EventCategory, EventRecurrence


def _parse_time(val: str | None) -> time | None:
    if val is None:
        return None
    parts = val.split(":")
    return time(int(parts[0]), int(parts[1]))


def _format_time(t: time | None) -> str | None:
    if t is None:
        return None
    return t.strftime("%H:%M")


def _row_to_event(row: sqlite3.Row) -> Event:
    return Event(
        id=row["id"],
        title=row["title"],
        event_date=date.fromisoformat(row["event_date"]),
        category=EventCategory(row["category"]),
        start_time=_parse_time(row["start_time"]),
        end_time=_parse_time(row["end_time"]),
        recurrence=EventRecurrence(row["recurrence"]),
        color=row["color"],
        notes=row["notes"],
        linked_income_id=row["linked_income_id"],
        linked_expense_id=row["linked_expense_id"],
    )


class EventRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, event: Event) -> Event:
        cursor = self._conn.execute(
            """INSERT INTO events
               (title, event_date, category, start_time, end_time,
                recurrence, color, notes, linked_income_id, linked_expense_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event.title,
                event.event_date.isoformat(),
                event.category.value,
                _format_time(event.start_time),
                _format_time(event.end_time),
                event.recurrence.value,
                event.color,
                event.notes,
                event.linked_income_id,
                event.linked_expense_id,
            ),
        )
        self._conn.commit()
        return Event(
            id=cursor.lastrowid,
            title=event.title,
            event_date=event.event_date,
            category=event.category,
            start_time=event.start_time,
            end_time=event.end_time,
            recurrence=event.recurrence,
            color=event.color,
            notes=event.notes,
            linked_income_id=event.linked_income_id,
            linked_expense_id=event.linked_expense_id,
        )

    def update(self, event: Event) -> None:
        if event.id is None:
            raise ValueError("Cannot update event without an id")
        self._conn.execute(
            """UPDATE events
               SET title=?, event_date=?, category=?, start_time=?, end_time=?,
                   recurrence=?, color=?, notes=?,
                   linked_income_id=?, linked_expense_id=?
               WHERE id=?""",
            (
                event.title,
                event.event_date.isoformat(),
                event.category.value,
                _format_time(event.start_time),
                _format_time(event.end_time),
                event.recurrence.value,
                event.color,
                event.notes,
                event.linked_income_id,
                event.linked_expense_id,
                event.id,
            ),
        )
        self._conn.commit()

    def delete(self, event_id: int) -> None:
        self._conn.execute("DELETE FROM events WHERE id=?", (event_id,))
        self._conn.commit()

    def get_by_id(self, event_id: int) -> Event | None:
        row = self._conn.execute(
            "SELECT * FROM events WHERE id=?", (event_id,)
        ).fetchone()
        return _row_to_event(row) if row else None

    def get_by_date(self, d: date) -> list[Event]:
        rows = self._conn.execute(
            "SELECT * FROM events WHERE event_date=? ORDER BY start_time",
            (d.isoformat(),),
        ).fetchall()
        return [_row_to_event(r) for r in rows]

    def get_by_month(self, year: int, month: int) -> list[Event]:
        prefix = f"{year:04d}-{month:02d}"
        rows = self._conn.execute(
            """SELECT * FROM events
               WHERE event_date LIKE ?
               ORDER BY event_date, start_time""",
            (prefix + "%",),
        ).fetchall()
        return [_row_to_event(r) for r in rows]

    def get_by_date_range(self, start: date, end: date) -> list[Event]:
        rows = self._conn.execute(
            """SELECT * FROM events
               WHERE event_date >= ? AND event_date <= ?
               ORDER BY event_date, start_time""",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [_row_to_event(r) for r in rows]

    def get_all(self) -> list[Event]:
        rows = self._conn.execute(
            "SELECT * FROM events ORDER BY event_date DESC, start_time"
        ).fetchall()
        return [_row_to_event(r) for r in rows]
