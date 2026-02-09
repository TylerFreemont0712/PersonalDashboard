"""Lightweight custom chart widgets using QPainter.

No external charting library needed -- keeps the app dependency-free
and consistent with the dark hacker theme.
"""
from __future__ import annotations

import math
from typing import Sequence

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from src.ui.theme import (
    ACCENT_CYAN, ACCENT_GREEN, ACCENT_RED, ACCENT_YELLOW, ACCENT_ORANGE,
    BG_DARKEST, BG_MID, BORDER, EXPENSE_RED, INCOME_GREEN, TEXT, TEXT_DIM,
)


# ── Bar Chart ────────────────────────────────────────────────────────────

class BarChartWidget(QWidget):
    """Side-by-side bar chart comparing two data series (e.g. income vs expense)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._labels: list[str] = []
        self._series_a: list[int] = []  # e.g. income
        self._series_b: list[int] = []  # e.g. expenses
        self._label_a = "Income"
        self._label_b = "Expenses"
        self._color_a = QColor(INCOME_GREEN)
        self._color_b = QColor(EXPENSE_RED)
        self.setMinimumHeight(220)

    def set_data(
        self,
        labels: list[str],
        series_a: list[int],
        series_b: list[int],
        label_a: str = "Income",
        label_b: str = "Expenses",
    ) -> None:
        self._labels = labels
        self._series_a = series_a
        self._series_b = series_b
        self._label_a = label_a
        self._label_b = label_b
        self.update()

    def paintEvent(self, event) -> None:
        if not self._labels:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin_left = 70
        margin_right = 20
        margin_top = 30
        margin_bottom = 40
        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        # Background
        painter.fillRect(self.rect(), QColor(BG_DARKEST))

        # Draw grid / axis
        max_val = max(max(self._series_a, default=0), max(self._series_b, default=0), 1)
        # Round up to nice number
        magnitude = 10 ** (len(str(max_val)) - 1)
        max_val = math.ceil(max_val / magnitude) * magnitude

        grid_pen = QPen(QColor(BORDER))
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        text_font = QFont("monospace", 9)
        painter.setFont(text_font)

        # Y-axis gridlines
        for i in range(5):
            y = margin_top + chart_h - (i / 4) * chart_h
            val = int(max_val * i / 4)
            painter.setPen(grid_pen)
            painter.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))
            painter.setPen(QColor(TEXT_DIM))
            painter.drawText(
                0, int(y - 8), margin_left - 8, 16,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"¥{val:,}",
            )

        # Bars
        n = len(self._labels)
        group_w = chart_w / n
        bar_w = max(group_w * 0.3, 4)
        gap = max(group_w * 0.05, 2)

        for i in range(n):
            x_center = margin_left + group_w * i + group_w / 2

            # Series A bar
            h_a = (self._series_a[i] / max_val) * chart_h if max_val else 0
            x_a = x_center - bar_w - gap / 2
            painter.fillRect(
                QRectF(x_a, margin_top + chart_h - h_a, bar_w, h_a),
                self._color_a,
            )

            # Series B bar
            h_b = (self._series_b[i] / max_val) * chart_h if max_val else 0
            x_b = x_center + gap / 2
            painter.fillRect(
                QRectF(x_b, margin_top + chart_h - h_b, bar_w, h_b),
                self._color_b,
            )

            # X-axis label
            painter.setPen(QColor(TEXT_DIM))
            painter.drawText(
                int(margin_left + group_w * i), int(margin_top + chart_h + 4),
                int(group_w), 20,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self._labels[i],
            )

        # Legend
        legend_y = 8
        legend_x = margin_left
        painter.fillRect(QRectF(legend_x, legend_y, 10, 10), self._color_a)
        painter.setPen(QColor(TEXT))
        painter.drawText(legend_x + 14, legend_y + 10, self._label_a)
        offset = painter.fontMetrics().horizontalAdvance(self._label_a) + 30
        painter.fillRect(QRectF(legend_x + offset, legend_y, 10, 10), self._color_b)
        painter.drawText(legend_x + offset + 14, legend_y + 10, self._label_b)

        painter.end()


# ── Donut / Pie Chart ────────────────────────────────────────────────────

_DONUT_COLORS = [
    ACCENT_CYAN, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_ORANGE,
    ACCENT_RED, "#ba68c8", "#4fc3f7", "#81c784", "#ffb74d", "#e57373",
]


class DonutChartWidget(QWidget):
    """Donut chart for category breakdowns."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._slices: list[tuple[str, int, QColor]] = []
        self._total = 0
        self._center_label = ""
        self.setMinimumHeight(220)
        self.setMinimumWidth(300)

    def set_data(
        self,
        items: list[tuple[str, int]],  # (label, value)
        center_label: str = "",
    ) -> None:
        self._total = sum(v for _, v in items)
        self._slices = []
        for i, (label, value) in enumerate(items):
            color = QColor(_DONUT_COLORS[i % len(_DONUT_COLORS)])
            self._slices.append((label, value, color))
        self._center_label = center_label
        self.update()

    def paintEvent(self, event) -> None:
        if not self._slices or self._total == 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Donut dimensions
        chart_size = min(w * 0.5, h - 20)
        outer_r = chart_size / 2
        inner_r = outer_r * 0.55
        cx = chart_size / 2 + 10
        cy = h / 2

        painter.fillRect(self.rect(), QColor(BG_DARKEST))

        # Draw arcs
        rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
        start_angle = 90 * 16  # top

        for label, value, color in self._slices:
            span = int((value / self._total) * 360 * 16)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawPie(rect, start_angle, -span)
            start_angle -= span

        # Inner circle (donut hole)
        painter.setBrush(QColor(BG_DARKEST))
        painter.drawEllipse(
            QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
        )

        # Center text
        if self._center_label:
            painter.setPen(QColor(TEXT))
            font = QFont("monospace", 11, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(
                QRectF(cx - inner_r, cy - 12, inner_r * 2, 24),
                Qt.AlignmentFlag.AlignCenter,
                self._center_label,
            )

        # Legend (right side)
        legend_x = int(chart_size + 30)
        legend_y = max(20, int(cy - len(self._slices) * 22 / 2))
        font = QFont("monospace", 10)
        painter.setFont(font)

        for label, value, color in self._slices:
            painter.fillRect(QRectF(legend_x, legend_y, 12, 12), color)
            pct = (value / self._total * 100) if self._total else 0
            painter.setPen(QColor(TEXT))
            painter.drawText(
                legend_x + 18, legend_y + 11,
                f"{label}  ¥{value:,} ({pct:.0f}%)",
            )
            legend_y += 22

        painter.end()


# ── Sparkline ────────────────────────────────────────────────────────────

class SparklineWidget(QWidget):
    """Small inline trend line chart."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._values: list[int] = []
        self._color = QColor(ACCENT_CYAN)
        self.setFixedHeight(50)
        self.setMinimumWidth(120)

    def set_data(self, values: list[int], color: str = ACCENT_CYAN) -> None:
        self._values = values
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:
        if len(self._values) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(BG_MID))

        w = self.width() - 4
        h = self.height() - 4
        max_v = max(self._values) or 1
        n = len(self._values)

        pen = QPen(self._color, 2)
        painter.setPen(pen)

        path = QPainterPath()
        for i, v in enumerate(self._values):
            x = 2 + (i / (n - 1)) * w
            y = 2 + h - (v / max_v) * h
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.drawPath(path)
        painter.end()
