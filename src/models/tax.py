from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryBreakdown:
    """A single expense category total for tax summary."""
    category: str
    category_label: str
    total: int  # yen


@dataclass(frozen=True)
class TaxSummary:
    """Aggregated data for a single tax year (確定申告 preparation).

    Japanese tax year runs January 1 - December 31.
    Filing deadline is typically March 15 of the following year.
    """
    year: int
    gross_income: int
    total_expenses: int
    expense_breakdown: tuple[CategoryBreakdown, ...]

    @property
    def net_income(self) -> int:
        return self.gross_income - self.total_expenses
