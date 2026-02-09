from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional


class EventCategory(enum.Enum):
    WORK = "work"
    FAMILY = "family"
    BIRTHDAY = "birthday"
    DEADLINE = "deadline"
    APPOINTMENT = "appointment"
    HOLIDAY = "holiday"
    OTHER = "other"


# Default colors per category (hex)
EVENT_CATEGORY_COLORS: dict[EventCategory, str] = {
    EventCategory.WORK: "#4A90D9",
    EventCategory.FAMILY: "#7B68EE",
    EventCategory.BIRTHDAY: "#E91E63",
    EventCategory.DEADLINE: "#F44336",
    EventCategory.APPOINTMENT: "#FF9800",
    EventCategory.HOLIDAY: "#4CAF50",
    EventCategory.OTHER: "#9E9E9E",
}


class EventRecurrence(enum.Enum):
    NONE = "none"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class Event:
    title: str
    event_date: date
    category: EventCategory
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    recurrence: EventRecurrence = EventRecurrence.NONE
    color: Optional[str] = None  # Override default category color
    notes: str = ""
    linked_income_id: Optional[int] = None
    linked_expense_id: Optional[int] = None
    id: Optional[int] = field(default=None)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Event title must not be empty")
        if self.start_time and self.end_time and self.end_time < self.start_time:
            raise ValueError("End time must not be before start time")

    @property
    def display_color(self) -> str:
        if self.color:
            return self.color
        return EVENT_CATEGORY_COLORS[self.category]
