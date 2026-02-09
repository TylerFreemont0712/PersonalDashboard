"""Tax Preparation (確定申告) widget.

Displays a yearly tax summary with income, expenses, net income,
expense breakdown charts and table, monthly income vs expense comparison,
and a filing checklist. Provides CSV export functionality.
This is a data preparation tool, not tax advice.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.export_csv import export_tax_summary_csv
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService
from src.services.tax_service import TaxService
from src.ui.widgets.charts import BarChartWidget, DonutChartWidget

_MONTH_LABELS = [
    "1月", "2月", "3月", "4月", "5月", "6月",
    "7月", "8月", "9月", "10月", "11月", "12月",
]

_CHECKLIST_ITEMS = [
    "収支内訳書を準備 (Prepare income/expense statement)",
    "源泉徴収票を確認 (Verify withholding tax slips)",
    "経費の領収書を整理 (Organize expense receipts)",
    "申告期限: 3月15日 (Filing deadline: March 15)",
    "e-Tax または税務署で提出 (Submit via e-Tax or tax office)",
]


class TaxWidget(QWidget):
    """Widget for 確定申告 (tax filing) data preparation."""

    def __init__(
        self,
        tax_service: TaxService,
        income_service: IncomeService,
        expense_service: ExpenseService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tax_service = tax_service
        self._income_service = income_service
        self._expense_service = expense_service
        self._summary = None

        self._init_ui()
        self.refresh_data()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        outer = QVBoxLayout(self)

        # -- Toolbar --
        outer.addLayout(self._build_toolbar())

        # -- Scrollable content area --
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)

        # -- Filing info header --
        self._disclaimer = QLabel(
            "※ データ準備ツール / Data preparation tool - not tax advice"
        )
        self._disclaimer.setObjectName("dimNote")
        self._disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._disclaimer)

        # -- Stat cards row --
        layout.addLayout(self._build_stat_cards())

        # -- Charts row --
        layout.addLayout(self._build_charts())

        # -- Expense breakdown table --
        breakdown_label = QLabel("経費内訳 (Expense Breakdown)")
        breakdown_label.setObjectName("sectionHeader")
        layout.addWidget(breakdown_label)

        self._table = self._build_table()
        layout.addWidget(self._table)

        # -- Empty-state message --
        self._empty_label = QLabel()
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)
        layout.addWidget(self._empty_label)

        # -- Checklist section --
        layout.addWidget(self._build_checklist())

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ---- Toolbar ----

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()

        year_label = QLabel("Year:")
        toolbar.addWidget(year_label)

        self._year_combo = QComboBox()
        current_year = date.today().year
        for year in range(current_year, current_year - 5, -1):
            self._year_combo.addItem(str(year), year)
        self._year_combo.currentIndexChanged.connect(self._on_year_changed)
        toolbar.addWidget(self._year_combo)

        self._export_btn = QPushButton("Export Summary CSV")
        self._export_btn.clicked.connect(self._on_export_csv)
        toolbar.addWidget(self._export_btn)

        toolbar.addStretch()
        return toolbar

    # ---- Stat cards ----

    def _build_stat_cards(self) -> QHBoxLayout:
        row = QHBoxLayout()

        # Gross Income card
        self._gross_card, self._gross_value = self._make_stat_card(
            "収入合計 (Gross Income)", "¥0", accent="accentGreen"
        )
        row.addWidget(self._gross_card)

        # Total Expenses card
        self._expense_card, self._expense_value = self._make_stat_card(
            "経費合計 (Total Expenses)", "¥0", accent="accentRed"
        )
        row.addWidget(self._expense_card)

        # Net Income card
        self._net_card, self._net_value = self._make_stat_card(
            "差引所得 (Net Income)", "¥0", accent=None
        )
        row.addWidget(self._net_card)

        return row

    @staticmethod
    def _make_stat_card(
        label_text: str, initial_value: str, accent: str | None
    ) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("statCard")

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel(initial_value)
        value_label.setObjectName("statValue")
        if accent:
            value_label.setObjectName(accent)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)

        desc_label = QLabel(label_text)
        desc_label.setObjectName("statLabel")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)

        return card, value_label

    # ---- Charts ----

    def _build_charts(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self._donut_chart = DonutChartWidget()
        row.addWidget(self._donut_chart, stretch=1)

        self._bar_chart = BarChartWidget()
        row.addWidget(self._bar_chart, stretch=2)

        return row

    # ---- Expense breakdown table ----

    @staticmethod
    def _build_table() -> QTableWidget:
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

    # ---- Checklist ----

    @staticmethod
    def _build_checklist() -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        header = QLabel("確定申告 CHECKLIST")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        checklist = QListWidget()
        for item_text in _CHECKLIST_ITEMS:
            checklist.addItem(item_text)
        layout.addWidget(checklist)

        return container

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
        """Populate all sections with current data."""
        self._set_content_visible(True)
        self._export_btn.setEnabled(True)

        summary = self._summary

        # -- Stat card values --
        self._gross_value.setText(f"¥{summary.gross_income:,}")
        self._expense_value.setText(f"¥{summary.total_expenses:,}")
        self._net_value.setText(f"¥{summary.net_income:,}")

        # -- Donut chart: expense category breakdown --
        donut_items = [
            (item.category_label, item.total)
            for item in summary.expense_breakdown
        ]
        self._donut_chart.set_data(donut_items, center_label="経費内訳")

        # -- Bar chart: monthly income vs expenses --
        year = summary.year
        monthly_income = [
            self._income_service.monthly_total(year, m) for m in range(1, 13)
        ]
        monthly_expense = [
            self._expense_service.monthly_total(year, m) for m in range(1, 13)
        ]
        self._bar_chart.set_data(
            labels=list(_MONTH_LABELS),
            series_a=monthly_income,
            series_b=monthly_expense,
            label_a="収入 (Income)",
            label_b="経費 (Expenses)",
        )

        # -- Expense breakdown table --
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
        self._set_content_visible(False)
        self._export_btn.setEnabled(False)

        self._empty_label.setVisible(True)
        self._empty_label.setText(
            f"No data for {year}. "
            "Add income and expenses in their respective modules."
        )

    def _set_content_visible(self, visible: bool) -> None:
        """Toggle visibility of data sections vs empty-state label."""
        self._gross_card.setVisible(visible)
        self._expense_card.setVisible(visible)
        self._net_card.setVisible(visible)
        self._donut_chart.setVisible(visible)
        self._bar_chart.setVisible(visible)
        self._table.setVisible(visible)
        self._empty_label.setVisible(not visible)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_year_changed(self, index: int) -> None:  # noqa: ARG002
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
