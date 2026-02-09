"""Tests for ExpenseService."""
import sqlite3
from datetime import date

import pytest

from src.models.expense import Expense, ExpenseCategory, PaymentMethod
from src.repositories.database import init_db
from src.repositories.expense_repo import ExpenseRepository
from src.services.expense_service import ExpenseService


@pytest.fixture()
def service():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    repo = ExpenseRepository(conn)
    return ExpenseService(repo)


def _expense(**overrides) -> Expense:
    defaults = dict(
        amount=5000,
        category=ExpenseCategory.GROCERIES,
        expense_date=date(2025, 3, 1),
        payment_method=PaymentMethod.CASH,
    )
    defaults.update(overrides)
    return Expense(**defaults)


class TestMonthlyTotal:
    def test_sums_correct_month(self, service):
        service.add_expense(_expense(amount=1000, expense_date=date(2025, 3, 1)))
        service.add_expense(_expense(amount=2000, expense_date=date(2025, 3, 15)))
        service.add_expense(_expense(amount=9999, expense_date=date(2025, 4, 1)))
        assert service.monthly_total(2025, 3) == 3000

    def test_empty_month_returns_zero(self, service):
        assert service.monthly_total(2025, 1) == 0


class TestYearlyTotal:
    def test_sums_correct_year(self, service):
        service.add_expense(_expense(amount=1000, expense_date=date(2025, 1, 1)))
        service.add_expense(_expense(amount=2000, expense_date=date(2025, 12, 31)))
        service.add_expense(_expense(amount=5000, expense_date=date(2024, 6, 1)))
        assert service.yearly_total(2025) == 3000


class TestCategoryTotals:
    def test_groups_by_category(self, service):
        service.add_expense(_expense(
            amount=100_000, category=ExpenseCategory.RENT,
            expense_date=date(2025, 1, 1),
        ))
        service.add_expense(_expense(
            amount=5_000, category=ExpenseCategory.GROCERIES,
            expense_date=date(2025, 2, 1),
        ))
        service.add_expense(_expense(
            amount=3_000, category=ExpenseCategory.GROCERIES,
            expense_date=date(2025, 3, 1),
        ))
        totals = service.category_totals(2025)
        assert totals[ExpenseCategory.RENT] == 100_000
        assert totals[ExpenseCategory.GROCERIES] == 8_000
        assert ExpenseCategory.DINING not in totals
