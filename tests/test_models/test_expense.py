"""Tests for the Expense domain model."""
import pytest
from datetime import date

from src.models.expense import (
    Expense,
    ExpenseCategory,
    PaymentMethod,
    RecurrenceType,
)


def _make_expense(**overrides) -> Expense:
    defaults = dict(
        amount=10000,
        category=ExpenseCategory.RENT,
        expense_date=date(2025, 3, 15),
        payment_method=PaymentMethod.BANK_TRANSFER,
    )
    defaults.update(overrides)
    return Expense(**defaults)


class TestExpenseCreation:
    def test_basic_creation(self):
        e = _make_expense()
        assert e.amount == 10000
        assert e.category == ExpenseCategory.RENT
        assert e.expense_date == date(2025, 3, 15)
        assert e.payment_method == PaymentMethod.BANK_TRANSFER
        assert e.recurrence == RecurrenceType.NONE
        assert e.notes == ""
        assert e.id is None

    def test_negative_amount_rejected(self):
        with pytest.raises(ValueError, match="must not be negative"):
            _make_expense(amount=-1)

    def test_zero_amount_allowed(self):
        e = _make_expense(amount=0)
        assert e.amount == 0


class TestExpenseProperties:
    def test_is_recurring_false_for_none(self):
        e = _make_expense()
        assert e.is_recurring is False

    def test_is_recurring_true_for_monthly(self):
        e = _make_expense(recurrence=RecurrenceType.MONTHLY)
        assert e.is_recurring is True

    def test_is_recurring_true_for_yearly(self):
        e = _make_expense(recurrence=RecurrenceType.YEARLY)
        assert e.is_recurring is True

    def test_category_label_contains_japanese_and_english(self):
        e = _make_expense(category=ExpenseCategory.RENT)
        label = e.category_label
        assert "家賃" in label
        assert "Rent" in label

    def test_all_categories_have_labels(self):
        for cat in ExpenseCategory:
            e = _make_expense(category=cat)
            assert len(e.category_label) > 0
