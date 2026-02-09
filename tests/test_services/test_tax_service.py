"""Tests for TaxService."""
import sqlite3
from datetime import date

import pytest

from src.models.expense import Expense, ExpenseCategory, PaymentMethod
from src.models.income import Income, JobType
from src.repositories.database import init_db
from src.repositories.expense_repo import ExpenseRepository
from src.repositories.income_repo import IncomeRepository
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService
from src.services.tax_service import TaxService


@pytest.fixture()
def tax_service():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    expense_repo = ExpenseRepository(conn)
    income_repo = IncomeRepository(conn)
    expense_svc = ExpenseService(expense_repo)
    income_svc = IncomeService(income_repo)
    return TaxService(income_svc, expense_svc), income_svc, expense_svc


class TestGetTaxSummary:
    def test_empty_year(self, tax_service):
        svc, _, _ = tax_service
        summary = svc.get_tax_summary(2025)
        assert summary.year == 2025
        assert summary.gross_income == 0
        assert summary.total_expenses == 0
        assert summary.net_income == 0
        assert summary.expense_breakdown == ()

    def test_with_data(self, tax_service):
        svc, income_svc, expense_svc = tax_service

        income_svc.add_income(Income(
            amount=500_000,
            income_date=date(2025, 3, 1),
            client="Client A",
            job_type=JobType.CONTRACT,
        ))
        income_svc.add_income(Income(
            amount=300_000,
            income_date=date(2025, 6, 1),
            client="Client B",
            job_type=JobType.HOURLY,
        ))

        expense_svc.add_expense(Expense(
            amount=100_000,
            category=ExpenseCategory.RENT,
            expense_date=date(2025, 1, 1),
            payment_method=PaymentMethod.BANK_TRANSFER,
        ))
        expense_svc.add_expense(Expense(
            amount=20_000,
            category=ExpenseCategory.UTILITIES,
            expense_date=date(2025, 2, 1),
            payment_method=PaymentMethod.DIRECT_DEBIT,
        ))

        summary = svc.get_tax_summary(2025)
        assert summary.gross_income == 800_000
        assert summary.total_expenses == 120_000
        assert summary.net_income == 680_000
        assert len(summary.expense_breakdown) == 2

        # Breakdown sorted desc by amount
        assert summary.expense_breakdown[0].total == 100_000
        assert summary.expense_breakdown[1].total == 20_000

    def test_ignores_other_years(self, tax_service):
        svc, income_svc, expense_svc = tax_service

        income_svc.add_income(Income(
            amount=100_000,
            income_date=date(2024, 12, 31),
            client="Old",
            job_type=JobType.CONTRACT,
        ))
        income_svc.add_income(Income(
            amount=200_000,
            income_date=date(2025, 1, 1),
            client="Current",
            job_type=JobType.CONTRACT,
        ))

        summary = svc.get_tax_summary(2025)
        assert summary.gross_income == 200_000
