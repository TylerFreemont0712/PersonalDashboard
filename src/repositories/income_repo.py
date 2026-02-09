from __future__ import annotations

import sqlite3
from datetime import date

from src.models.income import Income, JobType


def _row_to_income(row: sqlite3.Row) -> Income:
    return Income(
        id=row["id"],
        amount=row["amount"],
        income_date=date.fromisoformat(row["income_date"]),
        client=row["client"],
        job_type=JobType(row["job_type"]),
        notes=row["notes"],
    )


class IncomeRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, income: Income) -> Income:
        cursor = self._conn.execute(
            """INSERT INTO incomes
               (amount, income_date, client, job_type, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (
                income.amount,
                income.income_date.isoformat(),
                income.client,
                income.job_type.value,
                income.notes,
            ),
        )
        self._conn.commit()
        return Income(
            id=cursor.lastrowid,
            amount=income.amount,
            income_date=income.income_date,
            client=income.client,
            job_type=income.job_type,
            notes=income.notes,
        )

    def update(self, income: Income) -> None:
        if income.id is None:
            raise ValueError("Cannot update income without an id")
        self._conn.execute(
            """UPDATE incomes
               SET amount=?, income_date=?, client=?, job_type=?, notes=?
               WHERE id=?""",
            (
                income.amount,
                income.income_date.isoformat(),
                income.client,
                income.job_type.value,
                income.notes,
                income.id,
            ),
        )
        self._conn.commit()

    def delete(self, income_id: int) -> None:
        self._conn.execute("DELETE FROM incomes WHERE id=?", (income_id,))
        self._conn.commit()

    def get_by_id(self, income_id: int) -> Income | None:
        row = self._conn.execute(
            "SELECT * FROM incomes WHERE id=?", (income_id,)
        ).fetchone()
        return _row_to_income(row) if row else None

    def get_by_date_range(self, start: date, end: date) -> list[Income]:
        rows = self._conn.execute(
            """SELECT * FROM incomes
               WHERE income_date >= ? AND income_date <= ?
               ORDER BY income_date DESC""",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [_row_to_income(r) for r in rows]

    def get_by_month(self, year: int, month: int) -> list[Income]:
        prefix = f"{year:04d}-{month:02d}"
        rows = self._conn.execute(
            """SELECT * FROM incomes
               WHERE income_date LIKE ?
               ORDER BY income_date DESC""",
            (prefix + "%",),
        ).fetchall()
        return [_row_to_income(r) for r in rows]

    def get_by_year(self, year: int) -> list[Income]:
        prefix = f"{year:04d}"
        rows = self._conn.execute(
            """SELECT * FROM incomes
               WHERE income_date LIKE ?
               ORDER BY income_date DESC""",
            (prefix + "%",),
        ).fetchall()
        return [_row_to_income(r) for r in rows]

    def get_all(self) -> list[Income]:
        rows = self._conn.execute(
            "SELECT * FROM incomes ORDER BY income_date DESC"
        ).fetchall()
        return [_row_to_income(r) for r in rows]

    def get_distinct_clients(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT client FROM incomes ORDER BY client"
        ).fetchall()
        return [r["client"] for r in rows]
