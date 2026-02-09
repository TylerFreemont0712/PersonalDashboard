"""Tax Preparation (確定申告) widget.

Displays a yearly tax summary with income, expenses, net income,
and an expense breakdown table. Provides CSV export functionality.
This is a data preparation tool, not tax advice.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.export_csv import export_tax_summary_csv
from src.services.tax_service import TaxService


class TaxWidget(QWidget):
    """Widget for 確定申告 (tax filing) data preparation."""

    def __init__(self, tax_service: TaxService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tax_service = tax_service
        self._summary = None

        self._init_ui()
        self.refresh_data()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # -- Toolbar --
        layout.addLayout(self._build_toolbar())

        # -- Summary section --
        self._summary_frame = self._build_summary_section()
        layout.addWidget(self._summary_frame)

        # -- Expense breakdown table --
        self._breakdown_label = QLabel("経費内訳 (Expense Breakdown)")
        breakdown_font = QFont()
        breakdown_font.setBold(True)
        self._breakdown_label.setFont(breakdown_font)
        layout.addWidget(self._breakdown_label)

        self._table = self._build_table()
        layout.addWidget(self._table)

        # -- Empty-state message --
        self._empty_label = QLabel()
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)
        layout.addWidget(self._empty_label)

        layout.addStretch()

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()

        # Year selector
        self._year_combo = QComboBox()
        current_year = date.today().year
        for year in range(current_year, current_year - 5, -1):
            self._year_combo.addItem(str(year), year)
        self._year_combo.currentIndexChanged.connect(self._on_year_changed)
        toolbar.addWidget(QLabel("Year:"))
        toolbar.addWidget(self._year_combo)

        # Export button
        self._export_btn = QPushButton("Export Summary CSV")
        self._export_btn.clicked.connect(self._on_export_csv)
        toolbar.addWidget(self._export_btn)

        toolbar.addStretch()

        # Disclaimer note
        note_label = QLabel("※ This is a data preparation tool, not tax advice.")
        note_label.setStyleSheet("color: gray;")
        toolbar.addWidget(note_label)

        return toolbar

    def _build_summary_section(self) -> QFrame:
        frame = QFrame()
        form = QFormLayout(frame)

        self._gross_income_label = QLabel("¥0")
        self._total_expenses_label = QLabel("¥0")
        self._net_income_label = QLabel("¥0")

        # Net income gets a bold, larger font
        net_font = QFont()
        net_font.setBold(True)
        net_font.setPointSize(net_font.pointSize() + 4)
        self._net_income_label.setFont(net_font)

        form.addRow("収入合計 (Gross Income):", self._gross_income_label)
        form.addRow("経費合計 (Total Expenses):", self._total_expenses_label)
        form.addRow("差引所得 (Net Income):", self._net_income_label)

        return frame

    def _build_table(self) -> QTableWidget:
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["カテゴリ (Category)", "金額 (Amount ¥)"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        return table

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh_data(self) -> None:
        """Fetch the tax summary for the selected year and update the UI."""
        year = self._year_combo.currentData()
        if year is None:
            return

        self._summary = self._tax_service.get_tax_summary(year)

        has_data = (
            self._summary.gross_income != 0
            or self._summary.total_expenses != 0
        )

        if has_data:
            self._show_data()
        else:
            self._show_empty_state(year)

    def _show_data(self) -> None:
        """Populate summary labels and breakdown table with current data."""
        self._summary_frame.setVisible(True)
        self._breakdown_label.setVisible(True)
        self._table.setVisible(True)
        self._empty_label.setVisible(False)
        self._export_btn.setEnabled(True)

        summary = self._summary

        self._gross_income_label.setText(f"¥{summary.gross_income:,}")
        self._total_expenses_label.setText(f"¥{summary.total_expenses:,}")
        self._net_income_label.setText(f"¥{summary.net_income:,}")

        # Populate expense breakdown table (already sorted desc by service)
        breakdown = summary.expense_breakdown
        self._table.setRowCount(len(breakdown))
        for row, item in enumerate(breakdown):
            category_item = QTableWidgetItem(item.category_label)
            amount_item = QTableWidgetItem(f"¥{item.total:,}")
            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, 0, category_item)
            self._table.setItem(row, 1, amount_item)

    def _show_empty_state(self, year: int) -> None:
        """Show an informative message when no data exists for the year."""
        self._summary_frame.setVisible(False)
        self._breakdown_label.setVisible(False)
        self._table.setVisible(False)
        self._export_btn.setEnabled(False)

        self._empty_label.setVisible(True)
        self._empty_label.setText(
            f"No data for {year}. "
            "Add income and expenses in their respective modules."
        )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_year_changed(self, index: int) -> None:
        self.refresh_data()

    def _on_export_csv(self) -> None:
        if self._summary is None:
            return

        default_name = f"tax_summary_{self._summary.year}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Tax Summary CSV",
            default_name,
            "CSV Files (*.csv)",
        )
        if path:
            export_tax_summary_csv(self._summary, Path(path))
