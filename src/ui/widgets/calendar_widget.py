"""Calendar & Scheduling module widget.

Fully custom-painted month grid (no HTML in buttons), day detail panel
with timeline view, and month/day navigation.
"""
from __future__ import annotations

import calendar
from datetime import date, time, timedelta

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.event import EVENT_CATEGORY_COLORS, Event
from src.services.event_service import EventService
from src.ui.dialogs.event_dialog import EventDialog
from src.ui import theme as T

_WEEKDAY_HEADERS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


# ── Custom-Painted Month Grid ───────────────────────────────────────────

class MonthGridWidget(QWidget):
    """QPainter-rendered month calendar. No HTML, no button artifacts."""

    date_clicked = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._year = date.today().year
        self._month = date.today().month
        self._events_by_day: dict[int, list[Event]] = {}
        self._selected_day: int | None = date.today().day
        self._day_rects: dict[int, QRectF] = {}
        self.setMinimumHeight(420)
        self.setMouseTracking(True)
        self._hover_day: int | None = None

    def set_month(self, year: int, month: int, events: list[Event]) -> None:
        self._year = year
        self._month = month
        self._events_by_day = {}
        for ev in events:
            self._events_by_day.setdefault(ev.event_date.day, []).append(ev)
        if self._selected_day:
            max_day = calendar.monthrange(year, month)[1]
            if self._selected_day > max_day:
                self._selected_day = 1
        self.update()

    def set_selected(self, day: int) -> None:
        self._selected_day = day
        self.update()

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        for day, rect in self._day_rects.items():
            if rect.contains(pos):
                self._selected_day = day
                self.update()
                self.date_clicked.emit(date(self._year, self._month, day))
                return

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        new_hover = None
        for day, rect in self._day_rects.items():
            if rect.contains(pos):
                new_hover = day
                break
        if new_hover != self._hover_day:
            self._hover_day = new_hover
            self.update()

    def leaveEvent(self, event) -> None:
        self._hover_day = None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        painter.fillRect(self.rect(), QColor(T.BG_DARKEST))

        header_h = 30
        cell_w = w / 7
        rows = 6
        cell_h = (h - header_h) / rows

        # Weekday headers
        header_font = QFont("monospace", 10, QFont.Weight.Bold)
        painter.setFont(header_font)
        painter.setPen(QColor(T.ACCENT_CYAN))
        for col, hdr in enumerate(_WEEKDAY_HEADERS):
            rect = QRectF(col * cell_w, 0, cell_w, header_h)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, hdr)

        painter.setPen(QPen(QColor(T.BORDER), 1))
        painter.drawLine(0, int(header_h), w, int(header_h))

        # Day cells
        cal_obj = calendar.Calendar(firstweekday=0)
        days = list(cal_obj.itermonthdays(self._year, self._month))
        today = date.today()

        day_font = QFont("monospace", 13, QFont.Weight.Bold)
        event_font = QFont("monospace", 9)
        self._day_rects.clear()

        idx = 0
        for row in range(rows):
            for col in range(7):
                if idx >= len(days):
                    break
                day = days[idx]
                idx += 1

                x = col * cell_w
                y = header_h + row * cell_h
                cell_rect = QRectF(x + 1, y + 1, cell_w - 2, cell_h - 2)

                if day == 0:
                    painter.fillRect(cell_rect, QColor(T.CAL_EMPTY_BG))
                    painter.setPen(QPen(QColor(T.BORDER), 0.5))
                    painter.drawRect(cell_rect)
                    continue

                self._day_rects[day] = cell_rect

                is_today = (
                    self._year == today.year
                    and self._month == today.month
                    and day == today.day
                )
                is_selected = day == self._selected_day
                is_hover = day == self._hover_day

                if is_selected:
                    bg = QColor(T.CAL_SELECTED_BG)
                    border_color = QColor(T.CAL_SELECTED_BORDER)
                    border_width = 2
                elif is_today:
                    bg = QColor(T.CAL_TODAY_BG)
                    border_color = QColor(T.CAL_TODAY_BORDER)
                    border_width = 2
                elif is_hover:
                    bg = QColor(T.BG_HOVER)
                    border_color = QColor(T.BORDER)
                    border_width = 1
                else:
                    bg = QColor(T.CAL_DAY_BG)
                    border_color = QColor(T.CAL_DAY_BORDER)
                    border_width = 1

                painter.fillRect(cell_rect, bg)
                painter.setPen(QPen(border_color, border_width))
                painter.drawRect(cell_rect)

                # Day number
                painter.setFont(day_font)
                if is_today:
                    painter.setPen(QColor(T.ACCENT_GREEN))
                elif is_selected:
                    painter.setPen(QColor(T.ACCENT_CYAN))
                else:
                    painter.setPen(QColor(T.TEXT))
                painter.drawText(
                    QRectF(x + 6, y + 4, cell_w - 12, 18),
                    Qt.AlignmentFlag.AlignLeft, str(day),
                )

                # Event indicators
                events_today = self._events_by_day.get(day, [])
                if events_today:
                    painter.setFont(event_font)
                    dot_y = y + 24
                    for ev in events_today[:3]:
                        if dot_y + 13 > y + cell_h - 2:
                            break
                        color = QColor(ev.display_color)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(color)
                        painter.drawEllipse(QRectF(x + 5, dot_y + 2, 6, 6))
                        painter.setPen(QColor(T.TEXT_DIM))
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        max_chars = max(int(cell_w / 7) - 2, 4)
                        painter.drawText(
                            QRectF(x + 14, dot_y, cell_w - 20, 13),
                            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                            ev.title[:max_chars],
                        )
                        dot_y += 14

                    remaining = len(events_today) - 3
                    if remaining > 0 and dot_y + 12 < y + cell_h:
                        painter.setPen(QColor(T.TEXT_DIM))
                        painter.drawText(
                            QRectF(x + 5, dot_y, cell_w - 10, 12),
                            Qt.AlignmentFlag.AlignLeft,
                            f"+{remaining}",
                        )

        painter.end()


# ── Daily Timeline View ─────────────────────────────────────────────────

class DailyTimelineWidget(QWidget):
    """Visual timeline for a single day showing events as blocks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._events: list[Event] = []
        self._date = date.today()
        self.setMinimumHeight(600)
        self.setMinimumWidth(300)

    def set_data(self, d: date, events: list[Event]) -> None:
        self._date = d
        self._events = sorted(events, key=lambda e: e.start_time or time(0, 0))
        self.setMinimumHeight(max(600, 50 * 18))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        painter.fillRect(self.rect(), QColor(T.BG_DARKEST))

        start_hour = 6
        end_hour = 24
        total_hours = end_hour - start_hour
        left_margin = 55
        right_margin = 15
        top_margin = 10
        hour_h = (h - top_margin * 2) / total_hours

        time_font = QFont("monospace", 9)
        event_font = QFont("monospace", 10, QFont.Weight.Bold)
        painter.setFont(time_font)

        # Hour gridlines
        for i in range(total_hours + 1):
            y = top_margin + i * hour_h
            hr = start_hour + i
            painter.setPen(QPen(QColor(T.BORDER), 0.5))
            painter.drawLine(int(left_margin), int(y), int(w - right_margin), int(y))
            painter.setPen(QColor(T.TEXT_DIM))
            painter.drawText(
                0, int(y - 8), left_margin - 8, 16,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{hr:02d}:00",
            )

        # Current time red line
        if self._date == date.today():
            from datetime import datetime
            current = datetime.now().time()
            if start_hour <= current.hour < end_hour:
                frac = (current.hour - start_hour) + current.minute / 60
                cy = top_margin + frac * hour_h
                painter.setPen(QPen(QColor(T.ACCENT_RED), 2))
                painter.drawLine(int(left_margin - 5), int(cy), int(w - right_margin), int(cy))
                painter.setBrush(QColor(T.ACCENT_RED))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(left_margin - 9, cy - 4, 8, 8))

        # Event blocks
        track_w = w - left_margin - right_margin
        for ev in self._events:
            st = ev.start_time
            et = ev.end_time

            if st is None:
                painter.fillRect(
                    QRectF(left_margin, 0, track_w, top_margin - 1),
                    QColor(ev.display_color).darker(150),
                )
                painter.setPen(QColor(T.TEXT_BRIGHT))
                painter.setFont(event_font)
                painter.drawText(
                    QRectF(left_margin + 6, 0, track_w - 12, top_margin - 1),
                    Qt.AlignmentFlag.AlignVCenter,
                    f"ALL DAY: {ev.title}",
                )
                continue

            if st.hour < start_hour:
                continue

            y1 = top_margin + ((st.hour - start_hour) + st.minute / 60) * hour_h
            y2 = top_margin + ((et.hour - start_hour) + et.minute / 60) * hour_h if et else y1 + hour_h
            block_h = max(y2 - y1, 22)
            block_rect = QRectF(left_margin + 2, y1 + 1, track_w - 4, block_h - 2)

            color = QColor(ev.display_color)
            fill = QColor(color)
            fill.setAlpha(50)
            painter.fillRect(block_rect, fill)
            painter.fillRect(
                QRectF(block_rect.x(), block_rect.y(), 3, block_rect.height()), color,
            )
            painter.setPen(QPen(color, 1))
            painter.drawRect(block_rect)

            text_rect = QRectF(
                block_rect.x() + 8, block_rect.y() + 2,
                block_rect.width() - 12, block_rect.height() - 4,
            )
            painter.setPen(QColor(T.TEXT_BRIGHT))
            painter.setFont(event_font)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignTop, ev.title)
            if block_h > 30:
                ts = st.strftime("%H:%M")
                if et:
                    ts += f"-{et.strftime('%H:%M')}"
                painter.setFont(time_font)
                painter.setPen(QColor(T.TEXT_DIM))
                painter.drawText(
                    QRectF(text_rect.x(), text_rect.y() + 16, text_rect.width(), 14),
                    Qt.AlignmentFlag.AlignTop, ts,
                )

        painter.end()


# ── Day Detail Panel ────────────────────────────────────────────────────

class DayDetailPanel(QWidget):
    """Events for a selected day: list view + visual timeline."""

    events_changed = pyqtSignal()

    def __init__(self, event_service: EventService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = event_service
        self._current_date: date = date.today()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._date_label = QLabel()
        self._date_label.setObjectName("sectionTitle")
        layout.addWidget(self._date_label)

        toggle_bar = QHBoxLayout()
        self._list_btn = QPushButton("LIST")
        self._list_btn.setFixedWidth(60)
        self._list_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        self._timeline_btn = QPushButton("TIMELINE")
        self._timeline_btn.setFixedWidth(80)
        self._timeline_btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        self._add_btn = QPushButton("+ ADD EVENT")
        self._add_btn.setObjectName("accentBtn")
        self._add_btn.clicked.connect(self._on_add)
        toggle_bar.addWidget(self._list_btn)
        toggle_bar.addWidget(self._timeline_btn)
        toggle_bar.addStretch()
        toggle_bar.addWidget(self._add_btn)
        layout.addLayout(toggle_bar)

        self._stack = QStackedWidget()
        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.doubleClicked.connect(self._on_edit)
        self._stack.addWidget(self._list)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._timeline = DailyTimelineWidget()
        scroll.setWidget(self._timeline)
        self._stack.addWidget(scroll)
        layout.addWidget(self._stack)

        self._empty_label = QLabel("No events scheduled.")
        self._empty_label.setObjectName("dimNote")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_label)

    def show_date(self, d: date) -> None:
        self._current_date = d
        self._date_label.setText(f"{d.strftime('%A')}  {d.isoformat()}")
        self.refresh()

    def refresh(self) -> None:
        events = self._service.get_events_for_date(self._current_date)
        self._list.clear()
        self._timeline.set_data(self._current_date, events)

        if not events:
            self._stack.hide()
            self._empty_label.show()
            return

        self._empty_label.hide()
        self._stack.show()
        self._stack.setCurrentIndex(1 if any(e.start_time for e in events) else 0)

        for ev in events:
            if ev.start_time:
                ts = ev.start_time.strftime("%H:%M")
                if ev.end_time:
                    ts += f" - {ev.end_time.strftime('%H:%M')}"
                ts += "  "
            else:
                ts = "ALL DAY  "
            text = f"{ts}{ev.title}"
            if ev.recurrence.value != "none":
                text += f"  [{ev.recurrence.value}]"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, ev.id)
            item.setForeground(QColor(ev.display_color))
            self._list.addItem(item)

    def _on_add(self) -> None:
        dlg = EventDialog(initial_date=self._current_date, parent=self)
        if dlg.exec():
            self._service.add_event(dlg.get_event())
            self.refresh()
            self.events_changed.emit()

    def _on_edit(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        event = self._service.get_event(item.data(Qt.ItemDataRole.UserRole))
        if event is None:
            return
        dlg = EventDialog(event=event, parent=self)
        if dlg.exec():
            self._service.update_event(dlg.get_event())
            self.refresh()
            self.events_changed.emit()

    def _on_context_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if item is None:
            return
        self._list.setCurrentItem(item)
        menu = QMenu(self)
        edit_act = QAction("Edit", self)
        edit_act.triggered.connect(self._on_edit)
        del_act = QAction("Delete", self)
        del_act.triggered.connect(self._on_delete)
        menu.addAction(edit_act)
        menu.addAction(del_act)
        menu.exec(self._list.mapToGlobal(pos))

    def _on_delete(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete", "Delete this event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_event(item.data(Qt.ItemDataRole.UserRole))
            self.refresh()
            self.events_changed.emit()


# ── Main Calendar Widget ────────────────────────────────────────────────

class CalendarWidget(QWidget):
    """Full Calendar & Scheduling module: month grid + day detail + timeline."""

    def __init__(self, event_service: EventService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = event_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = QHBoxLayout()
        nav.setContentsMargins(12, 8, 12, 8)
        self._prev_btn = QPushButton("\u25c0")
        self._prev_btn.setFixedWidth(36)
        self._prev_btn.clicked.connect(self._go_prev)
        nav.addWidget(self._prev_btn)

        self._month_label = QLabel()
        self._month_label.setObjectName("sectionTitle")
        self._month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self._month_label, stretch=1)

        self._today_btn = QPushButton("TODAY")
        self._today_btn.setObjectName("accentBtn")
        self._today_btn.clicked.connect(self._go_today)
        nav.addWidget(self._today_btn)

        self._next_btn = QPushButton("\u25b6")
        self._next_btn.setFixedWidth(36)
        self._next_btn.clicked.connect(self._go_next)
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._calendar = MonthGridWidget()
        self._calendar.date_clicked.connect(self._on_date_clicked)
        splitter.addWidget(self._calendar)

        self._detail = DayDetailPanel(event_service)
        self._detail.events_changed.connect(self.refresh_calendar)
        splitter.addWidget(self._detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        today = date.today()
        self._year = today.year
        self._month = today.month
        self._detail.show_date(today)
        self.refresh_calendar()

    def refresh_calendar(self) -> None:
        events = self._service.get_events_for_month(self._year, self._month)
        self._calendar.set_month(self._year, self._month, events)
        self._month_label.setText(
            f"{calendar.month_name[self._month].upper()}  {self._year}"
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
