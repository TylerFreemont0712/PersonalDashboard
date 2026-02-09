from __future__ import annotations

from datetime import date
from typing import Optional

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
)

from src.models.income import Income, JobType

_JOB_TYPE_LABELS: dict[JobType, str] = {
    JobType.CONTRACT: "Contract",
    JobType.HOURLY: "Hourly",
    JobType.TASK_BASED: "Task-Based",
    JobType.RETAINER: "Retainer",
    JobType.OTHER: "Other",
}


class IncomeDialog(QDialog):
    """Dialog for adding or editing an income entry."""

    def __init__(
        self,
        income: Optional[Income] = None,
        known_clients: Optional[list[str]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._editing = income is not None
        self._original_id: Optional[int] = income.id if income else None

        self.setWindowTitle("Edit Income" if self._editing else "Add Income")

        # --- Widgets -----------------------------------------------------------
        self._amount_spin = QSpinBox()
        self._amount_spin.setRange(0, 99_999_999)
        self._amount_spin.setSuffix(" \u00a5")

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())

        self._client_combo = QComboBox()
        self._client_combo.setEditable(True)
        if known_clients:
            self._client_combo.addItems(known_clients)
        self._client_combo.setCurrentText("")

        self._job_type_combo = QComboBox()
        for job_type, label in _JOB_TYPE_LABELS.items():
            self._job_type_combo.addItem(label, job_type)

        self._notes_edit = QLineEdit()

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # --- Layout ------------------------------------------------------------
        layout = QGridLayout(self)
        row = 0

        layout.addWidget(QLabel("Amount:"), row, 0)
        layout.addWidget(self._amount_spin, row, 1)
        row += 1

        layout.addWidget(QLabel("Date:"), row, 0)
        layout.addWidget(self._date_edit, row, 1)
        row += 1

        layout.addWidget(QLabel("Client:"), row, 0)
        layout.addWidget(self._client_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Job Type:"), row, 0)
        layout.addWidget(self._job_type_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Notes:"), row, 0)
        layout.addWidget(self._notes_edit, row, 1)
        row += 1

        layout.addWidget(button_box, row, 0, 1, 2)

        # --- Pre-fill when editing ---------------------------------------------
        if income is not None:
            self._amount_spin.setValue(income.amount)
            self._date_edit.setDate(
                QDate(income.income_date.year, income.income_date.month, income.income_date.day)
            )
            self._client_combo.setCurrentText(income.client)
            index = self._job_type_combo.findData(income.job_type)
            if index >= 0:
                self._job_type_combo.setCurrentIndex(index)
            self._notes_edit.setText(income.notes)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_income(self) -> Income:
        """Return a validated :class:`Income` built from the current field values.

        When editing an existing entry the original ``id`` is preserved.
        """
        qdate = self._date_edit.date()
        income_date = date(qdate.year(), qdate.month(), qdate.day())

        return Income(
            amount=self._amount_spin.value(),
            income_date=income_date,
            client=self._client_combo.currentText().strip(),
            job_type=self._job_type_combo.currentData(),
            notes=self._notes_edit.text().strip(),
            id=self._original_id,
        )
