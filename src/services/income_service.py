"""Business logic for income management."""
from __future__ import annotations

from datetime import date

from src.models.income import Income
from src.repositories.income_repo import IncomeRepository


class IncomeService:
    def __init__(self, repo: IncomeRepository) -> None:
        self._repo = repo

    def add_income(self, income: Income) -> Income:
        return self._repo.insert(income)

    def update_income(self, income: Income) -> None:
        self._repo.update(income)

    def delete_income(self, income_id: int) -> None:
        self._repo.delete(income_id)

    def get_income(self, income_id: int) -> Income | None:
        return self._repo.get_by_id(income_id)

    def get_monthly_incomes(self, year: int, month: int) -> list[Income]:
        return self._repo.get_by_month(year, month)

    def get_yearly_incomes(self, year: int) -> list[Income]:
        return self._repo.get_by_year(year)

    def get_incomes_in_range(self, start: date, end: date) -> list[Income]:
        return self._repo.get_by_date_range(start, end)

    def monthly_total(self, year: int, month: int) -> int:
        incomes = self._repo.get_by_month(year, month)
        return sum(i.amount for i in incomes)

    def yearly_total(self, year: int) -> int:
        incomes = self._repo.get_by_year(year)
        return sum(i.amount for i in incomes)

    def get_distinct_clients(self) -> list[str]:
        return self._repo.get_distinct_clients()

    def get_all_incomes(self) -> list[Income]:
        return self._repo.get_all()
