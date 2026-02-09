"""Tests for IncomeRepository using an in-memory SQLite database."""
import sqlite3
from datetime import date

import pytest

from src.models.income import Income, JobType
from src.repositories.database import init_db
from src.repositories.income_repo import IncomeRepository


@pytest.fixture()
def repo():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return IncomeRepository(conn)


def _sample_income(**overrides) -> Income:
    defaults = dict(
        amount=100_000,
        income_date=date(2025, 6, 15),
        client="Acme Corp",
        job_type=JobType.CONTRACT,
    )
    defaults.update(overrides)
    return Income(**defaults)


class TestInsert:
    def test_returns_income_with_id(self, repo):
        i = repo.insert(_sample_income())
        assert i.id is not None
        assert i.client == "Acme Corp"

    def test_persists_to_db(self, repo):
        repo.insert(_sample_income())
        assert len(repo.get_all()) == 1


class TestUpdate:
    def test_updates_fields(self, repo):
        i = repo.insert(_sample_income())
        updated = Income(
            id=i.id,
            amount=200_000,
            income_date=i.income_date,
            client="New Client",
            job_type=i.job_type,
        )
        repo.update(updated)
        fetched = repo.get_by_id(i.id)
        assert fetched.amount == 200_000
        assert fetched.client == "New Client"

    def test_update_without_id_raises(self, repo):
        with pytest.raises(ValueError, match="without an id"):
            repo.update(_sample_income())


class TestDelete:
    def test_removes_income(self, repo):
        i = repo.insert(_sample_income())
        repo.delete(i.id)
        assert repo.get_by_id(i.id) is None


class TestQueries:
    def test_get_by_month(self, repo):
        repo.insert(_sample_income(income_date=date(2025, 6, 1)))
        repo.insert(_sample_income(income_date=date(2025, 6, 30)))
        repo.insert(_sample_income(income_date=date(2025, 7, 1)))
        assert len(repo.get_by_month(2025, 6)) == 2

    def test_get_by_year(self, repo):
        repo.insert(_sample_income(income_date=date(2025, 1, 1)))
        repo.insert(_sample_income(income_date=date(2024, 12, 31)))
        assert len(repo.get_by_year(2025)) == 1

    def test_get_distinct_clients(self, repo):
        repo.insert(_sample_income(client="Alpha"))
        repo.insert(_sample_income(client="Beta"))
        repo.insert(_sample_income(client="Alpha"))
        clients = repo.get_distinct_clients()
        assert clients == ["Alpha", "Beta"]
