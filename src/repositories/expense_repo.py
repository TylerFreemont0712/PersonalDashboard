from __future__ import annotations

import sqlite3
from datetime import date

from src.models.expense import (
    Expense,
    ExpenseCategory,
    PaymentMethod,
    RecurrenceType,
)


def _row_to_expense(row: sqlite3.Row) -> Expense:
    return Expense(
        id=row["id"],
        amount=row["amount"],
        category=ExpenseCategory(row["category"]),
        expense_date=date.fromisoformat(row["expense_date"]),
        payment_method=PaymentMethod(row["payment_method"]),
        recurrence=RecurrenceType(row["recurrence"]),
        notes=row["notes"],
    )


class ExpenseRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, expense: Expense) -> Expense:
        cursor = self._conn.execute(
            """INSERT INTO expenses
               (amount, category, expense_date, payment_method, recurrence, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                expense.amount,
                expense.category.value,
                expense.expense_date.isoformat(),
                expense.payment_method.value,
                expense.recurrence.value,
                expense.notes,
            ),
        )
        self._conn.commit()
        return Expense(
            id=cursor.lastrowid,
            amount=expense.amount,
            category=expense.category,
            expense_date=expense.expense_date,
            payment_method=expense.payment_method,
            recurrence=expense.recurrence,
            notes=expense.notes,
        )

    def update(self, expense: Expense) -> None:
        if expense.id is None:
            raise ValueError("Cannot update expense without an id")
        self._conn.execute(
            """UPDATE expenses
               SET amount=?, category=?, expense_date=?, payment_method=?,
                   recurrence=?, notes=?
               WHERE id=?""",
            (
                expense.amount,
                expense.category.value,
                expense.expense_date.isoformat(),
                expense.payment_method.value,
                expense.recurrence.value,
                expense.notes,
                expense.id,
            ),
        )
        self._conn.commit()

    def delete(self, expense_id: int) -> None:
        self._conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        self._conn.commit()

    def get_by_id(self, expense_id: int) -> Expense | None:
        row = self._conn.execute(
            "SELECT * FROM expenses WHERE id=?", (expense_id,)
        ).fetchone()
        return _row_to_expense(row) if row else None

    def get_by_date_range(self, start: date, end: date) -> list[Expense]:
        rows = self._conn.execute(
            """SELECT * FROM expenses
               WHERE expense_date >= ? AND expense_date <= ?
               ORDER BY expense_date DESC""",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [_row_to_expense(r) for r in rows]

    def get_by_month(self, year: int, month: int) -> list[Expense]:
        prefix = f"{year:04d}-{month:02d}"
        rows = self._conn.execute(
            """SELECT * FROM expenses
               WHERE expense_date LIKE ?
               ORDER BY expense_date DESC""",
            (prefix + "%",),
        ).fetchall()
        return [_row_to_expense(r) for r in rows]

    def get_by_year(self, year: int) -> list[Expense]:
        prefix = f"{year:04d}"
        rows = self._conn.execute(
            """SELECT * FROM expenses
               WHERE expense_date LIKE ?
               ORDER BY expense_date DESC""",
            (prefix + "%",),
        ).fetchall()
        return [_row_to_expense(r) for r in rows]

    def get_all(self) -> list[Expense]:
        rows = self._conn.execute(
            "SELECT * FROM expenses ORDER BY expense_date DESC"
        ).fetchall()
        return [_row_to_expense(r) for r in rows]
