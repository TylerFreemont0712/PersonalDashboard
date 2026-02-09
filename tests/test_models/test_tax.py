"""Tests for the TaxSummary domain model."""
from src.models.tax import CategoryBreakdown, TaxSummary


class TestTaxSummary:
    def test_net_income_calculation(self):
        summary = TaxSummary(
            year=2025,
            gross_income=5_000_000,
            total_expenses=1_200_000,
            expense_breakdown=(),
        )
        assert summary.net_income == 3_800_000

    def test_net_income_zero_expenses(self):
        summary = TaxSummary(
            year=2025,
            gross_income=3_000_000,
            total_expenses=0,
            expense_breakdown=(),
        )
        assert summary.net_income == 3_000_000

    def test_net_income_negative_when_expenses_exceed(self):
        summary = TaxSummary(
            year=2025,
            gross_income=1_000_000,
            total_expenses=1_500_000,
            expense_breakdown=(),
        )
        assert summary.net_income == -500_000

    def test_frozen_dataclass(self):
        summary = TaxSummary(
            year=2025,
            gross_income=100,
            total_expenses=50,
            expense_breakdown=(),
        )
        try:
            summary.year = 2024  # type: ignore[misc]
            assert False, "Should not allow mutation"
        except AttributeError:
            pass


class TestCategoryBreakdown:
    def test_creation(self):
        cb = CategoryBreakdown(
            category="rent",
            category_label="Rent",
            total=120_000,
        )
        assert cb.category == "rent"
        assert cb.total == 120_000
