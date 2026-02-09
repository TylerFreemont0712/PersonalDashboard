"""Tax preparation service for 確定申告 (kakutei shinkoku).

Aggregates income and expense data into yearly summaries suitable
for manual tax filing. This is a data preparation tool, not tax advice.
"""
from __future__ import annotations

from src.models.tax import CategoryBreakdown, TaxSummary
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService


class TaxService:
    def __init__(
        self, income_service: IncomeService, expense_service: ExpenseService
    ) -> None:
        self._income = income_service
        self._expense = expense_service

    def get_tax_summary(self, year: int) -> TaxSummary:
        gross_income = self._income.yearly_total(year)
        total_expenses = self._expense.yearly_total(year)
        category_totals = self._expense.category_totals(year)

        breakdown = tuple(
            CategoryBreakdown(
                category=cat.value,
                category_label=cat.name.replace("_", " ").title(),
                total=amount,
            )
            for cat, amount in sorted(
                category_totals.items(), key=lambda x: x[1], reverse=True
            )
        )

        return TaxSummary(
            year=year,
            gross_income=gross_income,
            total_expenses=total_expenses,
            expense_breakdown=breakdown,
        )
