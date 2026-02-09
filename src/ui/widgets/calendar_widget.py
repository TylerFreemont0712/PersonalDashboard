"""Calendar & Scheduling module widget.

Provides month-view calendar with color-coded events, day detail panel,
and day/week/month navigation.
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta

from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.models.event import EVENT_CATEGORY_COLORS, Event, EventCategory
from src.services.event_service import EventService
from src.ui.dialogs.event_dialog import EventDialog


_WEEKDAY_HEADERS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class CalendarGrid(QWidget):
    """A month-view calendar grid that emits a signal when a day is clicked."""

    date_clicked = pyqtSignal(object)  # emits a date

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._year = date.today().year
        self._month = date.today().month
        self._events_by_day: dict[int, list[Event]] = {}
        self._selected_day: int | None = date.today().day

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._grid = QGridLayout()
        self._grid.setSpacing(2)

        # Weekday headers
        for col, header in enumerate(_WEEKDAY_HEADERS):
            lbl = QLabel(header)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; padding: 4px;")
            self._grid.addWidget(lbl, 0, col)

        # Day cells: 6 rows x 7 cols (covers any month layout)
        self._cells: list[list[QPushButton]] = []
        for row in range(6):
            row_cells: list[QPushButton] = []
            for col in range(7):
                btn = QPushButton("")
                btn.setFixedHeight(70)
                btn.setMinimumWidth(80)
                btn.setStyleSheet(
                    "text-align: top; padding: 4px; font-size: 11px;"
                )
                btn.clicked.connect(self._make_click_handler(row, col))
                self._grid.addWidget(btn, row + 1, col)
                row_cells.append(btn)
            self._cells.append(row_cells)

        self._layout.addLayout(self._grid)

    def _make_click_handler(self, row: int, col: int):
        def handler() -> None:
            btn = self._cells[row][col]
            day_text = btn.property("day")
            if day_text and day_text > 0:
                self._selected_day = day_text
                self._render()
                self.date_clicked.emit(date(self._year, self._month, day_text))
        return handler

    def set_month(
        self, year: int, month: int, events: list[Event]
    ) -> None:
        self._year = year
        self._month = month
        self._events_by_day = {}
        for ev in events:
            day = ev.event_date.day
            self._events_by_day.setdefault(day, []).append(ev)
        self._render()

    def _render(self) -> None:
        cal = calendar.Calendar(firstweekday=0)  # Monday start
        days = list(cal.itermonthdays(self._year, self._month))

        idx = 0
        for row in range(6):
            for col in range(7):
                btn = self._cells[row][col]
                if idx < len(days):
                    day = days[idx]
                else:
                    day = 0
                idx += 1

                if day == 0:
                    btn.setText("")
                    btn.setProperty("day", 0)
                    btn.setStyleSheet(
                        "background-color: #f5f5f5; border: 1px solid #ddd;"
                        " text-align: top; padding: 4px; font-size: 11px;"
                    )
                    btn.setEnabled(False)
                    continue

                btn.setEnabled(True)
                btn.setProperty("day", day)

                # Build cell text
                lines = [f"<b>{day}</b>"]
                events_today = self._events_by_day.get(day, [])
                for ev in events_today[:3]:  # Show max 3 event indicators
                    color = ev.display_color
                    short = ev.title[:12]
                    lines.append(
                        f'<span style="color:{color};">● {short}</span>'
                    )
                if len(events_today) > 3:
                    lines.append(f"<i>+{len(events_today) - 3} more</i>")

                btn.setText("<br>".join(lines))

                # Highlight selection and today
                today = date.today()
                is_today = (
                    self._year == today.year
                    and self._month == today.month
                    and day == today.day
                )
                is_selected = day == self._selected_day

                bg = "#ffffff"
                border = "#ddd"
                if is_selected:
                    bg = "#e3f2fd"
                    border = "#1976D2"
                elif is_today:
                    bg = "#fff3e0"
                    border = "#FF9800"

                btn.setStyleSheet(
                    f"background-color: {bg}; border: 2px solid {border};"
                    f" text-align: top; padding: 4px; font-size: 11px;"
                )


class DayDetailPanel(QWidget):
    """Shows events for a selected day with add/edit/delete actions."""

    def __init__(
        self, event_service: EventService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._service = event_service
        self._current_date: date = date.today()
        self._events: list[Event] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._date_label = QLabel()
        self._date_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self._date_label)

        self._list = QListWidget()
        self._list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.doubleClicked.connect(self._on_edit)
        layout.addWidget(self._list)

        btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("Add Event")
        self._add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self._add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Empty state
        self._empty_label = QLabel("No events for this day.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #888; padding: 20px;")
        layout.addWidget(self._empty_label)

    def show_date(self, d: date) -> None:
        self._current_date = d
        self._date_label.setText(d.strftime("%A, %B %d, %Y"))
        self.refresh()

    def refresh(self) -> None:
        self._events = self._service.get_events_for_date(self._current_date)
        self._list.clear()

        if not self._events:
            self._list.hide()
            self._empty_label.show()
            return

        self._empty_label.hide()
        self._list.show()

        for ev in self._events:
            time_str = ""
            if ev.start_time:
                time_str = ev.start_time.strftime("%H:%M")
                if ev.end_time:
                    time_str += f" - {ev.end_time.strftime('%H:%M')}"
                time_str += "  "

            text = f"{time_str}{ev.title}"
            if ev.recurrence.value != "none":
                text += f"  [{ev.recurrence.value}]"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, ev.id)
            item.setForeground(QColor(ev.display_color))
            self._list.addItem(item)

    def _on_add(self) -> None:
        dlg = EventDialog(initial_date=self._current_date, parent=self)
        if dlg.exec():
            event = dlg.get_event()
            self._service.add_event(event)
            self.refresh()
            # Signal parent to refresh calendar grid
            parent = self.parent()
            if parent and hasattr(parent, "refresh_calendar"):
                parent.refresh_calendar()

    def _on_edit(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        event_id = item.data(Qt.ItemDataRole.UserRole)
        event = self._service.get_event(event_id)
        if event is None:
            return
        dlg = EventDialog(event=event, parent=self)
        if dlg.exec():
            updated = dlg.get_event()
            self._service.update_event(updated)
            self.refresh()
            parent = self.parent()
            if parent and hasattr(parent, "refresh_calendar"):
                parent.refresh_calendar()

    def _on_context_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if item is None:
            return
        self._list.setCurrentItem(item)
        menu = QMenu(self)
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self._on_edit)
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(self._list.mapToGlobal(pos))

    def _on_delete(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        event_id = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_event(event_id)
            self.refresh()
            parent = self.parent()
            if parent and hasattr(parent, "refresh_calendar"):
                parent.refresh_calendar()


class CalendarWidget(QWidget):
    """Full Calendar & Scheduling module combining month grid + day detail."""

    def __init__(
        self, event_service: EventService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._service = event_service

        layout = QVBoxLayout(self)

        # Navigation toolbar
        nav = QHBoxLayout()
        self._prev_btn = QPushButton("◀ Prev")
        self._prev_btn.clicked.connect(self._go_prev)
        nav.addWidget(self._prev_btn)

        self._month_label = QLabel()
        self._month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._month_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        nav.addWidget(self._month_label, stretch=1)

        self._today_btn = QPushButton("Today")
        self._today_btn.clicked.connect(self._go_today)
        nav.addWidget(self._today_btn)

        self._next_btn = QPushButton("Next ▶")
        self._next_btn.clicked.connect(self._go_next)
        nav.addWidget(self._next_btn)

        layout.addLayout(nav)

        # Splitter: calendar grid on left, day detail on right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._calendar = CalendarGrid()
        self._calendar.date_clicked.connect(self._on_date_clicked)
        splitter.addWidget(self._calendar)

        self._detail = DayDetailPanel(event_service, parent=self)
        splitter.addWidget(self._detail)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Initial state
        today = date.today()
        self._year = today.year
        self._month = today.month
        self._detail.show_date(today)
        self.refresh_calendar()

    def refresh_calendar(self) -> None:
        events = self._service.get_events_for_month(self._year, self._month)
        self._calendar.set_month(self._year, self._month, events)
        self._month_label.setText(
            f"{calendar.month_name[self._month]} {self._year}"
        )

    def _on_date_clicked(self, d: date) -> None:
        self._detail.show_date(d)

    def _go_prev(self) -> None:
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self.refresh_calendar()

    def _go_next(self) -> None:
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self.refresh_calendar()

    def _go_today(self) -> None:
        today = date.today()
        self._year = today.year
        self._month = today.month
        self.refresh_calendar()
        self._detail.show_date(today)
