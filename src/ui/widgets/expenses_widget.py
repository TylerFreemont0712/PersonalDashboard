"""Bills & Expenses widget for the personal dashboard."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QLabel, QMessageBox, QFileDialog,
    QHeaderView, QAbstractItemView, QMenu)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QAction

from src.services.expense_service import ExpenseService
from src.services.export_csv import export_expenses_csv
from src.ui.dialogs.expense_dialog import ExpenseDialog


_COLUMNS = ["Date", "Amount (\u00a5)", "Category", "Payment Method", "Recurrence", "Notes"]


class ExpensesWidget(QWidget):
    """Main widget for viewing and managing bills and expenses."""

    def __init__(self, expense_service: ExpenseService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = expense_service
        self._build_ui()
        self._connect_signals()
        self.refresh_data()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        # --- Toolbar ---
        toolbar_layout = QHBoxLayout()

        self._add_btn = QPushButton("Add Expense")
        toolbar_layout.addWidget(self._add_btn)

        toolbar_layout.addStretch()

        # Year filter
        toolbar_layout.addWidget(QLabel("Year:"))
        self._year_combo = QComboBox()
        current_year = date.today().year
        for year in range(current_year, current_year - 5, -1):
            self._year_combo.addItem(str(year), userData=year)
        toolbar_layout.addWidget(self._year_combo)

        # Month filter
        toolbar_layout.addWidget(QLabel("Month:"))
        self._month_combo = QComboBox()
        self._month_combo.addItem("All", userData=0)
        for month in range(1, 13):
            self._month_combo.addItem(str(month), userData=month)
        toolbar_layout.addWidget(self._month_combo)

        toolbar_layout.addStretch()

        self._export_btn = QPushButton("Export CSV")
        toolbar_layout.addWidget(self._export_btn)

        root_layout.addLayout(toolbar_layout)

        # --- Table ---
        self._table = QTableWidget()
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header = self._table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        root_layout.addWidget(self._table)

        # --- Summary panel ---
        summary_layout = QHBoxLayout()
        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addStretch()
        summary_layout.addWidget(self._summary_label)
        summary_layout.addStretch()
        root_layout.addLayout(summary_layout)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._add_btn.clicked.connect(self._on_add)
        self._export_btn.clicked.connect(self._on_export)
        self._year_combo.currentIndexChanged.connect(lambda _: self.refresh_data())
        self._month_combo.currentIndexChanged.connect(lambda _: self.refresh_data())
        self._table.doubleClicked.connect(self._on_edit)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def _selected_year(self) -> int:
        return self._year_combo.currentData()

    def _selected_month(self) -> int:
        """Return the selected month (1-12), or 0 for 'All'."""
        return self._month_combo.currentData()

    def _fetch_expenses(self) -> list:
        year = self._selected_year()
        month = self._selected_month()
        if month == 0:
            return self._service.get_yearly_expenses(year)
        return self._service.get_monthly_expenses(year, month)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh_data(self) -> None:
        """Reload expenses from the service and repopulate the table."""
        expenses = self._fetch_expenses()

        self._table.setRowCount(len(expenses))
        for row, expense in enumerate(expenses):
            # Date
            date_item = QTableWidgetItem(expense.expense_date.isoformat())
            date_item.setData(Qt.ItemDataRole.UserRole, expense.id)
            self._table.setItem(row, 0, date_item)

            # Amount
            amount_item = QTableWidgetItem(f"\u00a5{expense.amount:,}")
            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, 1, amount_item)

            # Category
            self._table.setItem(row, 2, QTableWidgetItem(expense.category_label))

            # Payment method
            self._table.setItem(row, 3, QTableWidgetItem(expense.payment_method.value))

            # Recurrence
            self._table.setItem(row, 4, QTableWidgetItem(expense.recurrence.value))

            # Notes
            self._table.setItem(row, 5, QTableWidgetItem(expense.notes))

        self._update_summary(expenses)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _update_summary(self, expenses: list) -> None:
        total = sum(e.amount for e in expenses)
        month = self._selected_month()
        year = self._selected_year()
        if month == 0:
            period = f"{year} Yearly"
        else:
            period = f"{year}/{month:02d} Monthly"
        self._summary_label.setText(f"{period} Total: \u00a5{total:,}")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_add(self) -> None:
        dialog = ExpenseDialog(parent=self)
        if dialog.exec() == ExpenseDialog.DialogCode.Accepted:
            expense = dialog.get_expense()
            self._service.add_expense(expense)
            self.refresh_data()

    def _on_edit(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        expense_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if expense_id is None:
            return
        expense = self._service.get_expense(expense_id)
        if expense is None:
            return

        dialog = ExpenseDialog(expense=expense, parent=self)
        if dialog.exec() == ExpenseDialog.DialogCode.Accepted:
            updated = dialog.get_expense()
            self._service.update_expense(updated)
            self.refresh_data()

    def _on_delete(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        expense_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if expense_id is None:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this expense?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_expense(expense_id)
            self.refresh_data()

    def _on_export(self) -> None:
        default_name = f"expenses_{self._selected_year()}"
        month = self._selected_month()
        if month != 0:
            default_name += f"_{month:02d}"
        default_name += ".csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Expenses to CSV",
            default_name,
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        expenses = self._fetch_expenses()
        export_expenses_csv(expenses, Path(file_path))

    def _on_context_menu(self, position) -> None:
        item = self._table.itemAt(position)
        if item is None:
            return

        menu = QMenu(self)

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self._on_edit)
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)

        menu.exec(self._table.viewport().mapToGlobal(position))
