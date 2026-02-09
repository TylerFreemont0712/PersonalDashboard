"""Tests for IncomeService."""
import sqlite3
from datetime import date

import pytest

from src.models.income import Income, JobType
from src.repositories.database import init_db
from src.repositories.income_repo import IncomeRepository
from src.services.income_service import IncomeService


@pytest.fixture()
def service():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    repo = IncomeRepository(conn)
    return IncomeService(repo)


def _income(**overrides) -> Income:
    defaults = dict(
        amount=50_000,
        income_date=date(2025, 6, 15),
        client="Test Client",
        job_type=JobType.CONTRACT,
    )
    defaults.update(overrides)
    return Income(**defaults)


class TestMonthlyTotal:
    def test_sums_correct_month(self, service):
        service.add_income(_income(amount=100_000, income_date=date(2025, 6, 1)))
        service.add_income(_income(amount=200_000, income_date=date(2025, 6, 30)))
        service.add_income(_income(amount=999_999, income_date=date(2025, 7, 1)))
        assert service.monthly_total(2025, 6) == 300_000


class TestYearlyTotal:
    def test_sums_correct_year(self, service):
        service.add_income(_income(amount=100_000, income_date=date(2025, 1, 1)))
        service.add_income(_income(amount=200_000, income_date=date(2025, 12, 31)))
        assert service.yearly_total(2025) == 300_000

    def test_excludes_other_years(self, service):
        service.add_income(_income(amount=100_000, income_date=date(2024, 12, 31)))
        service.add_income(_income(amount=200_000, income_date=date(2025, 1, 1)))
        assert service.yearly_total(2025) == 200_000


class TestDistinctClients:
    def test_returns_unique_sorted(self, service):
        service.add_income(_income(client="Bravo"))
        service.add_income(_income(client="Alpha"))
        service.add_income(_income(client="Bravo"))
        assert service.get_distinct_clients() == ["Alpha", "Bravo"]
