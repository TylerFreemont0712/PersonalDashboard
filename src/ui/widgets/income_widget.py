"""Income tracking widget – displays, filters, and manages income entries."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.export_csv import export_income_csv
from src.services.income_service import IncomeService
from src.ui.dialogs.income_dialog import IncomeDialog


class IncomeWidget(QWidget):
    """Main widget for the Income Tracking module."""

    _COLUMNS = ["Date", "Amount (\u00a5)", "Client", "Job Type", "Notes"]

    def __init__(self, income_service: IncomeService, parent=None) -> None:
        super().__init__(parent)
        self._service = income_service

        # ---- main layout -------------------------------------------------------
        layout = QVBoxLayout(self)

        # ---- toolbar ------------------------------------------------------------
        toolbar = QHBoxLayout()

        self._add_btn = QPushButton("Add Income")
        self._add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self._add_btn)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("Year:"))
        self._year_combo = QComboBox()
        current_year = date.today().year
        for year in range(current_year, current_year - 5, -1):
            self._year_combo.addItem(str(year), year)
        self._year_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._year_combo)

        toolbar.addWidget(QLabel("Month:"))
        self._month_combo = QComboBox()
        self._month_combo.addItem("All", 0)
        for month in range(1, 13):
            self._month_combo.addItem(str(month), month)
        self._month_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._month_combo)

        toolbar.addStretch()

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.clicked.connect(self._on_export)
        toolbar.addWidget(self._export_btn)

        layout.addLayout(toolbar)

        # ---- table --------------------------------------------------------------
        self._table = QTableWidget(0, len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels(self._COLUMNS)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_edit)

        header = self._table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._table)

        # ---- summary panel ------------------------------------------------------
        summary_layout = QHBoxLayout()
        self._summary_label = QLabel("Gross Income: \u00a50")
        self._summary_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addStretch()
        summary_layout.addWidget(self._summary_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # ---- initial data load --------------------------------------------------
        self.refresh_data()

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    def _selected_year(self) -> int:
        return self._year_combo.currentData()

    def _selected_month(self) -> int:
        """Return the selected month (1-12) or 0 for 'All'."""
        return self._month_combo.currentData()

    def _on_filter_changed(self) -> None:
        self.refresh_data()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh_data(self) -> None:
        """Reload income entries from the service based on current filters."""
        year = self._selected_year()
        month = self._selected_month()

        if month == 0:
            incomes = self._service.get_yearly_incomes(year)
            total = self._service.yearly_total(year)
        else:
            incomes = self._service.get_monthly_incomes(year, month)
            total = self._service.monthly_total(year, month)

        self._populate_table(incomes)
        self._summary_label.setText(f"Gross Income: \u00a5{total:,}")

    def _populate_table(self, incomes) -> None:
        self._table.setRowCount(0)
        for income in incomes:
            row = self._table.rowCount()
            self._table.insertRow(row)

            date_item = QTableWidgetItem(income.income_date.isoformat())
            date_item.setData(Qt.ItemDataRole.UserRole, income.id)
            self._table.setItem(row, 0, date_item)

            amount_item = QTableWidgetItem(f"{income.amount:,}")
            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, 1, amount_item)

            self._table.setItem(row, 2, QTableWidgetItem(income.client))
            self._table.setItem(row, 3, QTableWidgetItem(income.job_type.value))
            self._table.setItem(row, 4, QTableWidgetItem(income.notes))

    # ------------------------------------------------------------------
    # Add / Edit / Delete
    # ------------------------------------------------------------------

    def _on_add(self) -> None:
        clients = self._service.get_distinct_clients()
        dialog = IncomeDialog(known_clients=clients, parent=self)
        if dialog.exec():
            income = dialog.get_income()
            self._service.add_income(income)
            self.refresh_data()

    def _on_edit(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        income_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        income = self._service.get_income(income_id)
        if income is None:
            return

        clients = self._service.get_distinct_clients()
        dialog = IncomeDialog(income=income, known_clients=clients, parent=self)
        if dialog.exec():
            updated = dialog.get_income()
            self._service.update_income(updated)
            self.refresh_data()

    def _on_delete(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        income_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this income entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_income(income_id)
            self.refresh_data()

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _on_context_menu(self, position) -> None:
        row = self._table.rowAt(position.y())
        if row < 0:
            return
        self._table.selectRow(row)

        menu = QMenu(self)

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self._on_edit)
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)

        menu.exec(self._table.viewport().mapToGlobal(position))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export(self) -> None:
        year = self._selected_year()
        month = self._selected_month()
        default_name = f"income_{year}" if month == 0 else f"income_{year}_{month:02d}"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Income CSV",
            default_name + ".csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        if month == 0:
            incomes = self._service.get_yearly_incomes(year)
        else:
            incomes = self._service.get_monthly_incomes(year, month)

        export_income_csv(incomes, Path(path))
