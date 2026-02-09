"""Tests for the Income domain model."""
import pytest
from datetime import date

from src.models.income import Income, JobType


def _make_income(**overrides) -> Income:
    defaults = dict(
        amount=50000,
        income_date=date(2025, 6, 1),
        client="Acme Corp",
        job_type=JobType.CONTRACT,
    )
    defaults.update(overrides)
    return Income(**defaults)


class TestIncomeCreation:
    def test_basic_creation(self):
        i = _make_income()
        assert i.amount == 50000
        assert i.client == "Acme Corp"
        assert i.job_type == JobType.CONTRACT
        assert i.notes == ""
        assert i.id is None

    def test_negative_amount_rejected(self):
        with pytest.raises(ValueError, match="must not be negative"):
            _make_income(amount=-100)

    def test_empty_client_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            _make_income(client="")

    def test_whitespace_only_client_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            _make_income(client="   ")

    def test_zero_amount_allowed(self):
        i = _make_income(amount=0)
        assert i.amount == 0
