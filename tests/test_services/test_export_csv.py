"""Tests for CSV export functions."""
import csv
import tempfile
from datetime import date
from pathlib import Path

from src.models.expense import Expense, ExpenseCategory, PaymentMethod
from src.models.income import Income, JobType
from src.models.tax import CategoryBreakdown, TaxSummary
from src.services.export_csv import (
    export_expenses_csv,
    export_income_csv,
    export_tax_summary_csv,
)


class TestExportTaxSummaryCSV:
    def test_creates_valid_csv(self, tmp_path):
        summary = TaxSummary(
            year=2025,
            gross_income=5_000_000,
            total_expenses=1_200_000,
            expense_breakdown=(
                CategoryBreakdown("rent", "Rent", 800_000),
                CategoryBreakdown("utilities", "Utilities", 400_000),
            ),
        )
        out = tmp_path / "summary.csv"
        export_tax_summary_csv(summary, out)

        content = out.read_text(encoding="utf-8-sig")
        assert "2025" in content
        assert "5,000,000" in content
        assert "1,200,000" in content
        assert "3,800,000" in content  # net income
        assert "Rent" in content
        assert "確定申告" in content


class TestExportIncomeCSV:
    def test_creates_valid_csv(self, tmp_path):
        incomes = [
            Income(amount=100_000, income_date=date(2025, 3, 1),
                   client="Alpha", job_type=JobType.CONTRACT),
            Income(amount=200_000, income_date=date(2025, 1, 15),
                   client="Beta", job_type=JobType.HOURLY),
        ]
        out = tmp_path / "income.csv"
        export_income_csv(incomes, out)

        content = out.read_text(encoding="utf-8-sig")
        lines = content.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
        # Should be sorted by date (Jan before Mar)
        assert "2025-01-15" in lines[1]
        assert "2025-03-01" in lines[2]


class TestExportExpensesCSV:
    def test_creates_valid_csv(self, tmp_path):
        expenses = [
            Expense(amount=5_000, category=ExpenseCategory.GROCERIES,
                    expense_date=date(2025, 4, 10),
                    payment_method=PaymentMethod.CASH),
        ]
        out = tmp_path / "expenses.csv"
        export_expenses_csv(expenses, out)

        content = out.read_text(encoding="utf-8-sig")
        lines = content.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
        assert "groceries" in lines[1]
