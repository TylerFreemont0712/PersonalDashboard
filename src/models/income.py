from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


class JobType(enum.Enum):
    CONTRACT = "contract"
    HOURLY = "hourly"
    TASK_BASED = "task_based"
    RETAINER = "retainer"
    OTHER = "other"


@dataclass
class Income:
    amount: int  # Stored in yen
    income_date: date
    client: str
    job_type: JobType
    notes: str = ""
    id: Optional[int] = field(default=None)

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Income amount must not be negative")
        if not self.client.strip():
            raise ValueError("Client name must not be empty")
