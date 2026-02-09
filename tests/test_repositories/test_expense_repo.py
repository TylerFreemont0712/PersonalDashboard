"""Tests for ExpenseRepository using an in-memory SQLite database."""
import sqlite3
from datetime import date

import pytest

from src.models.expense import Expense, ExpenseCategory, PaymentMethod, RecurrenceType
from src.repositories.database import init_db
from src.repositories.expense_repo import ExpenseRepository


@pytest.fixture()
def repo():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return ExpenseRepository(conn)


def _sample_expense(**overrides) -> Expense:
    defaults = dict(
        amount=8500,
        category=ExpenseCategory.GROCERIES,
        expense_date=date(2025, 3, 10),
        payment_method=PaymentMethod.CREDIT_CARD,
    )
    defaults.update(overrides)
    return Expense(**defaults)


class TestInsert:
    def test_returns_expense_with_id(self, repo):
        e = repo.insert(_sample_expense())
        assert e.id is not None
        assert e.amount == 8500

    def test_persists_to_db(self, repo):
        repo.insert(_sample_expense())
        all_expenses = repo.get_all()
        assert len(all_expenses) == 1


class TestUpdate:
    def test_updates_fields(self, repo):
        e = repo.insert(_sample_expense())
        updated = Expense(
            id=e.id,
            amount=9999,
            category=e.category,
            expense_date=e.expense_date,
            payment_method=e.payment_method,
        )
        repo.update(updated)
        fetched = repo.get_by_id(e.id)
        assert fetched.amount == 9999

    def test_update_without_id_raises(self, repo):
        with pytest.raises(ValueError, match="without an id"):
            repo.update(_sample_expense())


class TestDelete:
    def test_removes_expense(self, repo):
        e = repo.insert(_sample_expense())
        repo.delete(e.id)
        assert repo.get_by_id(e.id) is None


class TestQueries:
    def test_get_by_month(self, repo):
        repo.insert(_sample_expense(expense_date=date(2025, 3, 1)))
        repo.insert(_sample_expense(expense_date=date(2025, 3, 31)))
        repo.insert(_sample_expense(expense_date=date(2025, 4, 1)))
        results = repo.get_by_month(2025, 3)
        assert len(results) == 2

    def test_get_by_year(self, repo):
        repo.insert(_sample_expense(expense_date=date(2025, 1, 1)))
        repo.insert(_sample_expense(expense_date=date(2025, 12, 31)))
        repo.insert(_sample_expense(expense_date=date(2024, 12, 31)))
        results = repo.get_by_year(2025)
        assert len(results) == 2

    def test_get_by_date_range(self, repo):
        repo.insert(_sample_expense(expense_date=date(2025, 3, 1)))
        repo.insert(_sample_expense(expense_date=date(2025, 3, 15)))
        repo.insert(_sample_expense(expense_date=date(2025, 3, 31)))
        results = repo.get_by_date_range(date(2025, 3, 5), date(2025, 3, 20))
        assert len(results) == 1

    def test_get_by_id_nonexistent(self, repo):
        assert repo.get_by_id(999) is None
