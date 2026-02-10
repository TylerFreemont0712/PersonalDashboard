"""Dashboard overview widget showing key financial metrics at a glance."""
from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService
from src.ui.widgets.charts import BarChartWidget, SparklineWidget
from src.ui import theme as T


class DashboardWidget(QWidget):
    """Top-level overview: income vs expenses bar chart, stat cards, sparklines."""

    def __init__(
        self,
        income_service: IncomeService,
        expense_service: ExpenseService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._income_svc = income_service
        self._expense_svc = expense_service

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("DASHBOARD")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        header.addWidget(QLabel("Year:"))
        self._year_combo = QComboBox()
        current_year = date.today().year
        for y in range(current_year, current_year - 5, -1):
            self._year_combo.addItem(str(y), y)
        self._year_combo.currentIndexChanged.connect(lambda _: self.refresh())
        header.addWidget(self._year_combo)
        layout.addLayout(header)

        # Stat cards row
        cards = QHBoxLayout()
        cards.setSpacing(12)

        self._ytd_income_val, self._ytd_income_card = self._make_card("YTD INCOME")
        self._ytd_expense_val, self._ytd_expense_card = self._make_card("YTD EXPENSES")
        self._net_val, self._net_card = self._make_card("NET INCOME")
        self._monthly_avg_val, self._monthly_avg_card = self._make_card("AVG MONTHLY NET")

        cards.addWidget(self._ytd_income_card)
        cards.addWidget(self._ytd_expense_card)
        cards.addWidget(self._net_card)
        cards.addWidget(self._monthly_avg_card)
        layout.addLayout(cards)

        # Sparklines row
        spark_row = QHBoxLayout()
        spark_row.setSpacing(12)

        # Income sparkline
        income_spark_frame = QFrame()
        income_spark_frame.setObjectName("statCard")
        isl = QVBoxLayout(income_spark_frame)
        isl.setContentsMargins(12, 8, 12, 8)
        il = QLabel("INCOME TREND")
        il.setObjectName("statLabel")
        isl.addWidget(il)
        self._income_sparkline = SparklineWidget()
        isl.addWidget(self._income_sparkline)
        spark_row.addWidget(income_spark_frame)

        # Expense sparkline
        expense_spark_frame = QFrame()
        expense_spark_frame.setObjectName("statCard")
        esl = QVBoxLayout(expense_spark_frame)
        esl.setContentsMargins(12, 8, 12, 8)
        el = QLabel("EXPENSE TREND")
        el.setObjectName("statLabel")
        esl.addWidget(el)
        self._expense_sparkline = SparklineWidget()
        esl.addWidget(self._expense_sparkline)
        spark_row.addWidget(expense_spark_frame)

        layout.addLayout(spark_row)

        # Bar chart: monthly income vs expenses
        chart_label = QLabel("MONTHLY INCOME vs EXPENSES")
        chart_label.setObjectName("sectionTitle")
        layout.addWidget(chart_label)

        self._bar_chart = BarChartWidget()
        self._bar_chart.setMinimumHeight(280)
        layout.addWidget(self._bar_chart)

        layout.addStretch()

        self.refresh()

    @staticmethod
    def _make_card(label_text: str) -> tuple[QLabel, QFrame]:
        frame = QFrame()
        frame.setObjectName("statCard")
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(10, 8, 10, 8)
        vl.setSpacing(4)
        val = QLabel("\u00a50")
        val.setObjectName("statValue")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(label_text)
        lbl.setObjectName("statLabel")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(val)
        vl.addWidget(lbl)
        return val, frame

    def refresh(self) -> None:
        year = self._year_combo.currentData()
        if year is None:
            return

        # Monthly data
        income_months: list[int] = []
        expense_months: list[int] = []
        labels: list[str] = []
        for m in range(1, 13):
            income_months.append(self._income_svc.monthly_total(year, m))
            expense_months.append(self._expense_svc.monthly_total(year, m))
            labels.append(f"{m}月")

        ytd_income = sum(income_months)
        ytd_expense = sum(expense_months)
        net = ytd_income - ytd_expense

        # Determine how many months have passed for the average
        today = date.today()
        months_elapsed = 12 if year < today.year else max(today.month, 1)
        avg_net = net // months_elapsed if months_elapsed else 0

        # Update stat cards
        self._ytd_income_val.setText(f"\u00a5{ytd_income:,}")
        self._ytd_income_val.setObjectName("accentGreen")
        self._ytd_income_val.style().unpolish(self._ytd_income_val)
        self._ytd_income_val.style().polish(self._ytd_income_val)

        self._ytd_expense_val.setText(f"\u00a5{ytd_expense:,}")
        self._ytd_expense_val.setObjectName("accentRed")
        self._ytd_expense_val.style().unpolish(self._ytd_expense_val)
        self._ytd_expense_val.style().polish(self._ytd_expense_val)

        self._net_val.setText(f"\u00a5{net:,}")
        self._monthly_avg_val.setText(f"\u00a5{avg_net:,}")

        # Sparklines
        self._income_sparkline.set_data(income_months, T.INCOME_GREEN)
        self._expense_sparkline.set_data(expense_months, T.EXPENSE_RED)

        # Bar chart
        self._bar_chart.set_data(
            labels, income_months, expense_months,
            label_a="Income", label_b="Expenses",
        )
