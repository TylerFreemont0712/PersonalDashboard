"""Business logic for expense management."""
from __future__ import annotations

from datetime import date

from src.models.expense import Expense, ExpenseCategory
from src.repositories.expense_repo import ExpenseRepository


class ExpenseService:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    def add_expense(self, expense: Expense) -> Expense:
        return self._repo.insert(expense)

    def update_expense(self, expense: Expense) -> None:
        self._repo.update(expense)

    def delete_expense(self, expense_id: int) -> None:
        self._repo.delete(expense_id)

    def get_expense(self, expense_id: int) -> Expense | None:
        return self._repo.get_by_id(expense_id)

    def get_monthly_expenses(self, year: int, month: int) -> list[Expense]:
        return self._repo.get_by_month(year, month)

    def get_yearly_expenses(self, year: int) -> list[Expense]:
        return self._repo.get_by_year(year)

    def get_expenses_in_range(self, start: date, end: date) -> list[Expense]:
        return self._repo.get_by_date_range(start, end)

    def monthly_total(self, year: int, month: int) -> int:
        expenses = self._repo.get_by_month(year, month)
        return sum(e.amount for e in expenses)

    def yearly_total(self, year: int) -> int:
        expenses = self._repo.get_by_year(year)
        return sum(e.amount for e in expenses)

    def category_totals(self, year: int) -> dict[ExpenseCategory, int]:
        expenses = self._repo.get_by_year(year)
        totals: dict[ExpenseCategory, int] = {}
        for e in expenses:
            totals[e.category] = totals.get(e.category, 0) + e.amount
        return totals

    def get_all_expenses(self) -> list[Expense]:
        return self._repo.get_all()
