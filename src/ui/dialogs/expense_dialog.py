from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QDateEdit,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from src.models.expense import Expense, ExpenseCategory, PaymentMethod, RecurrenceType

# Human-readable labels for PaymentMethod enum values.
_PAYMENT_METHOD_LABELS: dict[PaymentMethod, str] = {
    PaymentMethod.CASH: "Cash",
    PaymentMethod.BANK_TRANSFER: "Bank Transfer",
    PaymentMethod.CREDIT_CARD: "Credit Card",
    PaymentMethod.DEBIT_CARD: "Debit Card",
    PaymentMethod.CONVENIENCE_STORE: "Convenience Store",
    PaymentMethod.DIRECT_DEBIT: "Direct Debit",
    PaymentMethod.OTHER: "Other",
}

# Human-readable labels for RecurrenceType enum values.
_RECURRENCE_LABELS: dict[RecurrenceType, str] = {
    RecurrenceType.NONE: "None",
    RecurrenceType.MONTHLY: "Monthly",
    RecurrenceType.YEARLY: "Yearly",
}


class ExpenseDialog(QDialog):
    """Dialog for adding or editing an expense entry."""

    def __init__(
        self,
        expense: Expense | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._editing = expense is not None
        self._existing_id: int | None = expense.id if expense is not None else None

        self.setWindowTitle("Edit Expense" if self._editing else "Add Expense")
        self._build_ui()

        if expense is not None:
            self._populate(expense)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        row = 0

        # Amount
        layout.addWidget(QLabel("Amount (JPY):"), row, 0)
        self._amount_spin = QSpinBox()
        self._amount_spin.setRange(0, 99_999_999)
        self._amount_spin.setSuffix(" \u00a5")
        layout.addWidget(self._amount_spin, row, 1)
        row += 1

        # Category
        layout.addWidget(QLabel("Category:"), row, 0)
        self._category_combo = QComboBox()
        for cat in ExpenseCategory:
            # Use the category_label property via a temporary Expense-less lookup.
            label = self._category_label(cat)
            self._category_combo.addItem(label, userData=cat)
        layout.addWidget(self._category_combo, row, 1)
        row += 1

        # Date
        layout.addWidget(QLabel("Date:"), row, 0)
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        today = date.today()
        self._date_edit.setDate(QDate(today.year, today.month, today.day))
        layout.addWidget(self._date_edit, row, 1)
        row += 1

        # Payment method
        layout.addWidget(QLabel("Payment Method:"), row, 0)
        self._payment_combo = QComboBox()
        for method in PaymentMethod:
            self._payment_combo.addItem(
                _PAYMENT_METHOD_LABELS[method], userData=method
            )
        layout.addWidget(self._payment_combo, row, 1)
        row += 1

        # Recurrence
        layout.addWidget(QLabel("Recurrence:"), row, 0)
        self._recurrence_combo = QComboBox()
        for rec in RecurrenceType:
            self._recurrence_combo.addItem(_RECURRENCE_LABELS[rec], userData=rec)
        layout.addWidget(self._recurrence_combo, row, 1)
        row += 1

        # Notes
        layout.addWidget(QLabel("Notes:"), row, 0)
        self._notes_edit = QLineEdit()
        layout.addWidget(self._notes_edit, row, 1)
        row += 1

        # OK / Cancel buttons
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box, row, 0, 1, 2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _category_label(cat: ExpenseCategory) -> str:
        """Return the human-readable label for *cat*.

        This reuses the same mapping that ``Expense.category_label`` provides,
        without requiring an ``Expense`` instance.
        """
        labels: dict[ExpenseCategory, str] = {
            ExpenseCategory.RENT: "\u5bb6\u8cc3 (Rent)",
            ExpenseCategory.UTILITIES: "\u5149\u71b1\u8cbb (Utilities)",
            ExpenseCategory.SUBSCRIPTIONS: "\u30b5\u30d6\u30b9\u30af (Subscriptions)",
            ExpenseCategory.GROCERIES: "\u98df\u6599\u54c1 (Groceries)",
            ExpenseCategory.TRANSPORTATION: "\u4ea4\u901a\u8cbb (Transportation)",
            ExpenseCategory.INSURANCE: "\u4fdd\u967a (Insurance)",
            ExpenseCategory.MEDICAL: "\u533b\u7642\u8cbb (Medical)",
            ExpenseCategory.DINING: "\u5916\u98df (Dining)",
            ExpenseCategory.ENTERTAINMENT: "\u5a2f\u697d (Entertainment)",
            ExpenseCategory.EDUCATION: "\u6559\u80b2 (Education)",
            ExpenseCategory.OFFICE_SUPPLIES: "\u4e8b\u52d9\u7528\u54c1 (Office Supplies)",
            ExpenseCategory.COMMUNICATION: "\u901a\u4fe1\u8cbb (Communication)",
            ExpenseCategory.TAX_PAYMENT: "\u7a0e\u91d1 (Tax Payment)",
            ExpenseCategory.PENSION: "\u5e74\u91d1 (Pension)",
            ExpenseCategory.OTHER: "\u305d\u306e\u4ed6 (Other)",
        }
        return labels[cat]

    def _populate(self, expense: Expense) -> None:
        """Fill every widget from an existing *expense*."""
        self._amount_spin.setValue(expense.amount)

        index = self._category_combo.findData(expense.category)
        if index >= 0:
            self._category_combo.setCurrentIndex(index)

        d = expense.expense_date
        self._date_edit.setDate(QDate(d.year, d.month, d.day))

        index = self._payment_combo.findData(expense.payment_method)
        if index >= 0:
            self._payment_combo.setCurrentIndex(index)

        index = self._recurrence_combo.findData(expense.recurrence)
        if index >= 0:
            self._recurrence_combo.setCurrentIndex(index)

        self._notes_edit.setText(expense.notes)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_expense(self) -> Expense:
        """Build and return a validated ``Expense`` from the current field values.

        If the dialog was opened in edit mode the original ``id`` is preserved.
        """
        qdate = self._date_edit.date()
        expense_date = date(qdate.year(), qdate.month(), qdate.day())

        return Expense(
            amount=self._amount_spin.value(),
            category=self._category_combo.currentData(),
            expense_date=expense_date,
            payment_method=self._payment_combo.currentData(),
            recurrence=self._recurrence_combo.currentData(),
            notes=self._notes_edit.text().strip(),
            id=self._existing_id,
        )
