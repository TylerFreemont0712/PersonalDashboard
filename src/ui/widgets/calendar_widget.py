"""Calendar & Scheduling module widget.

Custom-painted month grid with income/expense indicators and event-count
badges, a Microsoft-Teams-style 15-minute schedule grid, and day detail
panel with list + schedule views.
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta

from PyQt6.QtCore import QRectF, Qt, QTime, pyqtSignal
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

from src.models.event import Event
from src.services.event_service import EventService
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService
from src.ui.dialogs.event_dialog import EventDialog
from src.ui import theme as T

_WEEKDAY_HEADERS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


# ── Custom-Painted Month Grid ───────────────────────────────────────────


class MonthGridWidget(QWidget):
    """QPainter-rendered month calendar with financial indicators and badges."""

    date_clicked = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._year = date.today().year
        self._month = date.today().month
        self._events_by_day: dict[int, list[Event]] = {}
        self._income_by_day: dict[int, int] = {}
        self._expense_by_day: dict[int, int] = {}
        self._selected_day: int | None = date.today().day
        self._day_rects: dict[int, QRectF] = {}
        self.setMinimumHeight(300)
        self.setMouseTracking(True)
        self._hover_day: int | None = None

    def set_month(
        self,
        year: int,
        month: int,
        events: list[Event],
        income_by_day: dict[int, int] | None = None,
        expense_by_day: dict[int, int] | None = None,
    ) -> None:
        self._year = year
        self._month = month
        self._events_by_day = {}
        for ev in events:
            self._events_by_day.setdefault(ev.event_date.day, []).append(ev)
        self._income_by_day = income_by_day or {}
        self._expense_by_day = expense_by_day or {}
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

        header_h = 24
        cell_w = w / 7
        rows = 6
        cell_h = (h - header_h) / rows

        # Weekday headers
        header_font = QFont("monospace", 9, QFont.Weight.Bold)
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

        day_font = QFont("monospace", 11, QFont.Weight.Bold)
        small_font = QFont("monospace", 8)
        badge_font = QFont("monospace", 8, QFont.Weight.Bold)
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

                # ── Day number (top-left) ──
                painter.setFont(day_font)
                if is_today:
                    painter.setPen(QColor(T.ACCENT_GREEN))
                elif is_selected:
                    painter.setPen(QColor(T.ACCENT_CYAN))
                else:
                    painter.setPen(QColor(T.TEXT))
                painter.drawText(
                    QRectF(x + 4, y + 2, 24, 16),
                    Qt.AlignmentFlag.AlignLeft, str(day),
                )

                # ── Financial dots (beside day number) ──
                dot_x = x + 4 + 20
                dot_cy = y + 9
                has_income = self._income_by_day.get(day, 0) > 0
                has_expense = self._expense_by_day.get(day, 0) > 0
                if has_income:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(T.INCOME_GREEN))
                    painter.drawEllipse(QRectF(dot_x, dot_cy - 3, 6, 6))
                    dot_x += 8
                if has_expense:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(T.EXPENSE_RED))
                    painter.drawEllipse(QRectF(dot_x, dot_cy - 3, 6, 6))
                painter.setBrush(Qt.BrushStyle.NoBrush)

                # ── Event count badge (top-right corner) ──
                events_today = self._events_by_day.get(day, [])
                num_events = len(events_today)
                if num_events > 0:
                    badge_text = str(num_events)
                    painter.setFont(badge_font)
                    fm = painter.fontMetrics()
                    tw = fm.horizontalAdvance(badge_text)
                    badge_w = max(tw + 6, 14)
                    badge_h = 13
                    badge_x = x + cell_w - badge_w - 4
                    badge_y = y + 3
                    badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
                    painter.setPen(Qt.PenStyle.NoPen)
                    badge_bg = QColor(T.ACCENT_CYAN)
                    badge_bg.setAlpha(180)
                    painter.setBrush(badge_bg)
                    painter.drawRoundedRect(badge_rect, 3, 3)
                    painter.setPen(QColor(T.BG_DARKEST))
                    painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)
                    painter.setBrush(Qt.BrushStyle.NoBrush)

                # ── Event indicators (below day number row) ──
                if events_today:
                    painter.setFont(small_font)
                    ev_y = y + 20
                    max_show = max(int((cell_h - 24) / 12), 1)
                    for ev in events_today[:max_show]:
                        if ev_y + 11 > y + cell_h - 2:
                            break
                        color = QColor(ev.display_color)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(color)
                        painter.drawEllipse(QRectF(x + 4, ev_y + 1, 5, 5))
                        painter.setPen(QColor(T.TEXT_DIM))
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        max_chars = max(int(cell_w / 7) - 2, 3)
                        painter.drawText(
                            QRectF(x + 11, ev_y - 1, cell_w - 16, 11),
                            Qt.AlignmentFlag.AlignLeft
                            | Qt.AlignmentFlag.AlignVCenter,
                            ev.title[:max_chars],
                        )
                        ev_y += 12

                    remaining = num_events - max_show
                    if remaining > 0 and ev_y + 10 < y + cell_h:
                        painter.setPen(QColor(T.TEXT_DIM))
                        painter.drawText(
                            QRectF(x + 4, ev_y, cell_w - 8, 10),
                            Qt.AlignmentFlag.AlignLeft,
                            f"+{remaining}",
                        )

        painter.end()


# ── Teams-Style 15-Minute Schedule Grid ────────────────────────────────


class ScheduleGridWidget(QWidget):
    """Interactive 15-minute block schedule, similar to Microsoft Teams."""

    time_slot_double_clicked = pyqtSignal(object, object)  # start, end
    event_double_clicked = pyqtSignal(int)  # event_id
    event_context_menu = pyqtSignal(int, object)  # event_id, global QPoint

    SLOT_HEIGHT = 20
    START_HOUR = 6
    END_HOUR = 24
    LEFT_MARGIN = 50
    RIGHT_MARGIN = 10
    TOP_MARGIN = 4

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._events: list[Event] = []
        self._date = date.today()
        self._selected_slot: int | None = None
        self._hovered_slot: int | None = None
        self._event_rects: dict[int, QRectF] = {}
        self._selected_event_id: int | None = None
        self.setMouseTracking(True)
        self._update_size()

    @property
    def _total_slots(self) -> int:
        return (self.END_HOUR - self.START_HOUR) * 4

    def _update_size(self) -> None:
        h = self.TOP_MARGIN * 2 + self._total_slots * self.SLOT_HEIGHT
        self.setFixedHeight(h)
        self.setMinimumWidth(250)

    def set_data(self, d: date, events: list[Event]) -> None:
        self._date = d
        self._events = sorted(
            events, key=lambda e: e.start_time or time(0, 0)
        )
        self._selected_slot = None
        self._selected_event_id = None
        self._update_size()
        self.update()

    def _slot_for_y(self, y: float) -> int | None:
        adj = y - self.TOP_MARGIN
        if adj < 0:
            return None
        slot = int(adj / self.SLOT_HEIGHT)
        if slot >= self._total_slots:
            return None
        return slot

    def _time_for_slot(self, slot: int) -> time:
        total_minutes = self.START_HOUR * 60 + slot * 15
        h = total_minutes // 60
        m = total_minutes % 60
        return time(min(h, 23), m)

    def _event_at(self, pos) -> int | None:
        for eid, rect in self._event_rects.items():
            if rect.contains(pos):
                return eid
        return None

    # ── Painting ──

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        lm = self.LEFT_MARGIN
        rm = self.RIGHT_MARGIN
        tm = self.TOP_MARGIN
        sh = self.SLOT_HEIGHT
        track_w = w - lm - rm

        painter.fillRect(self.rect(), QColor(T.BG_DARKEST))

        time_font = QFont("monospace", 9)
        event_font = QFont("monospace", 10, QFont.Weight.Bold)
        detail_font = QFont("monospace", 8)

        # ── Grid lines & time labels ──
        for slot in range(self._total_slots + 1):
            y = tm + slot * sh
            if slot < self._total_slots:
                t = self._time_for_slot(slot)
            else:
                t = time(self.END_HOUR % 24, 0)
            minute = t.minute

            if minute == 0:
                painter.setPen(QPen(QColor(T.BORDER), 1))
                painter.drawLine(int(lm), int(y), int(w - rm), int(y))
                painter.setFont(time_font)
                painter.setPen(QColor(T.TEXT_DIM))
                painter.drawText(
                    0, int(y - 7), lm - 6, 14,
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter,
                    f"{t.hour:02d}:00",
                )
            elif minute == 30:
                pen = QPen(QColor(T.BORDER), 0.5)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(int(lm), int(y), int(w - rm), int(y))
            else:
                faint = QColor(T.BORDER)
                faint.setAlpha(60)
                pen = QPen(faint, 0.5)
                pen.setStyle(Qt.PenStyle.DotLine)
                painter.setPen(pen)
                painter.drawLine(int(lm), int(y), int(w - rm), int(y))

        # ── Hover slot highlight ──
        if self._hovered_slot is not None:
            hy = tm + self._hovered_slot * sh
            hover_color = QColor(T.BG_HOVER)
            hover_color.setAlpha(80)
            painter.fillRect(QRectF(lm, hy, track_w, sh), hover_color)

        # ── Selected slot highlight ──
        if self._selected_slot is not None:
            sy = tm + self._selected_slot * sh
            sel_color = QColor(T.ACCENT_CYAN)
            sel_color.setAlpha(35)
            painter.fillRect(QRectF(lm, sy, track_w, sh), sel_color)
            painter.setPen(QPen(QColor(T.ACCENT_CYAN), 1))
            painter.drawRect(QRectF(lm, sy, track_w, sh))

        # ── Event blocks ──
        self._event_rects.clear()
        for ev in self._events:
            st = ev.start_time
            et = ev.end_time

            if st is None:
                # All-day banner at top
                banner_h = 18
                banner_rect = QRectF(lm, 0, track_w, banner_h)
                color = QColor(ev.display_color)
                fill = QColor(color)
                fill.setAlpha(60)
                painter.fillRect(banner_rect, fill)
                painter.fillRect(
                    QRectF(lm, 0, 3, banner_h), color,
                )
                painter.setPen(QColor(T.TEXT_BRIGHT))
                painter.setFont(detail_font)
                painter.drawText(
                    QRectF(lm + 6, 0, track_w - 12, banner_h),
                    Qt.AlignmentFlag.AlignVCenter,
                    f"ALL DAY: {ev.title}",
                )
                if ev.id is not None:
                    self._event_rects[ev.id] = banner_rect
                continue

            if st.hour < self.START_HOUR:
                continue

            y1 = tm + (
                (st.hour - self.START_HOUR) * 4 + st.minute // 15
            ) * sh
            if et:
                y2 = tm + (
                    (et.hour - self.START_HOUR) * 4 + et.minute // 15
                ) * sh
            else:
                y2 = y1 + sh
            block_h = max(y2 - y1, sh)
            block_rect = QRectF(lm + 2, y1 + 1, track_w - 4, block_h - 2)

            color = QColor(ev.display_color)
            fill = QColor(color)
            fill.setAlpha(50)
            painter.fillRect(block_rect, fill)

            # Left accent bar
            painter.fillRect(
                QRectF(block_rect.x(), block_rect.y(), 3, block_rect.height()),
                color,
            )

            # Border (highlight if selected)
            is_sel = ev.id == self._selected_event_id
            if is_sel:
                painter.setPen(QPen(QColor(T.ACCENT_CYAN), 2))
            else:
                painter.setPen(QPen(color, 1))
            painter.drawRect(block_rect)

            # Title text
            text_rect = QRectF(
                block_rect.x() + 8, block_rect.y() + 2,
                block_rect.width() - 12, min(block_h - 4, 16),
            )
            painter.setPen(QColor(T.TEXT_BRIGHT))
            painter.setFont(event_font)
            painter.drawText(
                text_rect, Qt.AlignmentFlag.AlignVCenter, ev.title,
            )

            # Time range detail
            if block_h > 28:
                ts = st.strftime("%H:%M")
                if et:
                    ts += f" - {et.strftime('%H:%M')}"
                painter.setFont(detail_font)
                painter.setPen(QColor(T.TEXT_DIM))
                painter.drawText(
                    QRectF(
                        text_rect.x(), text_rect.y() + 16,
                        text_rect.width(), 12,
                    ),
                    Qt.AlignmentFlag.AlignTop, ts,
                )

            if ev.id is not None:
                self._event_rects[ev.id] = block_rect

        # ── Current time red indicator ──
        if self._date == date.today():
            now = datetime.now().time()
            if self.START_HOUR <= now.hour < self.END_HOUR:
                frac = (now.hour - self.START_HOUR) * 4 + now.minute / 15
                cy = tm + frac * sh
                painter.setPen(QPen(QColor(T.ACCENT_RED), 2))
                painter.drawLine(
                    int(lm - 4), int(cy), int(w - rm), int(cy),
                )
                painter.setBrush(QColor(T.ACCENT_RED))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(lm - 7, cy - 4, 8, 8))

        painter.end()

    # ── Mouse interaction ──

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        new_hover = self._slot_for_y(pos.y())
        if new_hover != self._hovered_slot:
            self._hovered_slot = new_hover
            self.update()

    def leaveEvent(self, event) -> None:
        self._hovered_slot = None
        self.update()

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        if event.button() != Qt.MouseButton.LeftButton:
            return
        eid = self._event_at(pos)
        if eid is not None:
            self._selected_event_id = eid
            self._selected_slot = None
        else:
            slot = self._slot_for_y(pos.y())
            self._selected_slot = slot
            self._selected_event_id = None
        self.update()

    def mouseDoubleClickEvent(self, event) -> None:
        pos = event.position()
        eid = self._event_at(pos)
        if eid is not None:
            self.event_double_clicked.emit(eid)
        else:
            slot = self._slot_for_y(pos.y())
            if slot is not None:
                start = self._time_for_slot(slot)
                end_slot = min(slot + 1, self._total_slots - 1)
                end = self._time_for_slot(end_slot)
                self.time_slot_double_clicked.emit(start, end)

    def contextMenuEvent(self, event) -> None:
        pos = event.pos()
        eid = self._event_at(pos)
        if eid is not None:
            self._selected_event_id = eid
            self.update()
            self.event_context_menu.emit(eid, event.globalPos())


# ── Day Detail Panel ────────────────────────────────────────────────────


class DayDetailPanel(QWidget):
    """Selected day's events: Teams-style schedule grid + list view."""

    events_changed = pyqtSignal()

    def __init__(
        self,
        event_service: EventService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = event_service
        self._current_date: date = date.today()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Date heading
        self._date_label = QLabel()
        self._date_label.setObjectName("sectionTitle")
        layout.addWidget(self._date_label)

        # Toggle bar
        toggle_bar = QHBoxLayout()
        toggle_bar.setSpacing(4)
        self._schedule_btn = QPushButton("SCHEDULE")
        self._schedule_btn.setFixedWidth(80)
        self._schedule_btn.clicked.connect(
            lambda: self._stack.setCurrentIndex(0)
        )
        self._list_btn = QPushButton("LIST")
        self._list_btn.setFixedWidth(50)
        self._list_btn.clicked.connect(
            lambda: self._stack.setCurrentIndex(1)
        )
        self._add_btn = QPushButton("+ ADD EVENT")
        self._add_btn.setObjectName("accentBtn")
        self._add_btn.clicked.connect(self._on_add)
        toggle_bar.addWidget(self._schedule_btn)
        toggle_bar.addWidget(self._list_btn)
        toggle_bar.addStretch()
        toggle_bar.addWidget(self._add_btn)
        layout.addLayout(toggle_bar)

        # Stacked widget: schedule (0), list (1)
        self._stack = QStackedWidget()

        # Schedule grid in scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._schedule = ScheduleGridWidget()
        self._schedule.time_slot_double_clicked.connect(
            self._on_add_at_time
        )
        self._schedule.event_double_clicked.connect(self._on_edit_by_id)
        self._schedule.event_context_menu.connect(
            self._on_schedule_context_menu
        )
        self._scroll.setWidget(self._schedule)
        self._stack.addWidget(self._scroll)

        # List view
        self._list = QListWidget()
        self._list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._list.customContextMenuRequested.connect(
            self._on_list_context_menu
        )
        self._list.doubleClicked.connect(self._on_edit_from_list)
        self._stack.addWidget(self._list)

        layout.addWidget(self._stack)

        self._empty_label = QLabel(
            "No events scheduled. Double-click a time slot to add one."
        )
        self._empty_label.setObjectName("dimNote")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)
        layout.addWidget(self._empty_label)

    def show_date(self, d: date) -> None:
        self._current_date = d
        self._date_label.setText(f"{d.strftime('%A')}  {d.isoformat()}")
        self.refresh()

    def refresh(self) -> None:
        events = self._service.get_events_for_date(self._current_date)
        self._schedule.set_data(self._current_date, events)
        self._list.clear()

        # Always show the schedule grid
        self._stack.show()
        self._stack.setCurrentIndex(0)
        self._empty_label.setVisible(not events)

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

    def scroll_to_now(self) -> None:
        """Scroll the schedule so the current time is visible."""
        now = datetime.now().time()
        sh = ScheduleGridWidget.SLOT_HEIGHT
        start_h = ScheduleGridWidget.START_HOUR
        tm = ScheduleGridWidget.TOP_MARGIN
        if now.hour >= start_h:
            y = tm + (now.hour - start_h) * 4 * sh + (now.minute // 15) * sh
            vbar = self._scroll.verticalScrollBar()
            vbar.setValue(max(0, int(y - 80)))

    # ── Add / Edit / Delete ──

    def _on_add(self) -> None:
        dlg = EventDialog(initial_date=self._current_date, parent=self)
        if dlg.exec():
            self._service.add_event(dlg.get_event())
            self.refresh()
            self.events_changed.emit()

    def _on_add_at_time(self, start_t: time, end_t: time) -> None:
        dlg = EventDialog(initial_date=self._current_date, parent=self)
        # Pre-fill the time fields
        dlg._start_time_check.setChecked(True)
        dlg._start_time_edit.setTime(QTime(start_t.hour, start_t.minute))
        dlg._end_time_check.setChecked(True)
        dlg._end_time_edit.setTime(QTime(end_t.hour, end_t.minute))
        if dlg.exec():
            self._service.add_event(dlg.get_event())
            self.refresh()
            self.events_changed.emit()

    def _on_edit_from_list(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        self._edit_event(item.data(Qt.ItemDataRole.UserRole))

    def _on_edit_by_id(self, event_id: int) -> None:
        self._edit_event(event_id)

    def _edit_event(self, event_id: int) -> None:
        ev = self._service.get_event(event_id)
        if ev is None:
            return
        dlg = EventDialog(event=ev, parent=self)
        if dlg.exec():
            self._service.update_event(dlg.get_event())
            self.refresh()
            self.events_changed.emit()

    def _delete_event(self, event_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_event(event_id)
            self.refresh()
            self.events_changed.emit()

    # ── Context menus ──

    def _on_schedule_context_menu(self, event_id: int, global_pos) -> None:
        menu = QMenu(self)
        edit_act = QAction("Edit", self)
        edit_act.triggered.connect(lambda: self._edit_event(event_id))
        del_act = QAction("Delete", self)
        del_act.triggered.connect(lambda: self._delete_event(event_id))
        menu.addAction(edit_act)
        menu.addAction(del_act)
        menu.exec(global_pos)

    def _on_list_context_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if item is None:
            return
        self._list.setCurrentItem(item)
        event_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        edit_act = QAction("Edit", self)
        edit_act.triggered.connect(lambda: self._edit_event(event_id))
        del_act = QAction("Delete", self)
        del_act.triggered.connect(lambda: self._delete_event(event_id))
        menu.addAction(edit_act)
        menu.addAction(del_act)
        menu.exec(self._list.mapToGlobal(pos))


# ── Main Calendar Widget ────────────────────────────────────────────────


class CalendarWidget(QWidget):
    """Full Calendar & Scheduling module: month grid + day schedule."""

    def __init__(
        self,
        event_service: EventService,
        income_service: IncomeService | None = None,
        expense_service: ExpenseService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = event_service
        self._income_service = income_service
        self._expense_service = expense_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Nav bar
        nav = QHBoxLayout()
        nav.setContentsMargins(8, 6, 8, 6)
        self._prev_btn = QPushButton("\u25c0")
        self._prev_btn.setFixedWidth(30)
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
        self._next_btn.setFixedWidth(30)
        self._next_btn.clicked.connect(self._go_next)
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

        # Splitter: calendar (compact) | schedule (primary)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._calendar = MonthGridWidget()
        self._calendar.date_clicked.connect(self._on_date_clicked)
        splitter.addWidget(self._calendar)

        self._detail = DayDetailPanel(event_service)
        self._detail.events_changed.connect(self.refresh_calendar)
        splitter.addWidget(self._detail)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

        today = date.today()
        self._year = today.year
        self._month = today.month
        self._detail.show_date(today)
        self.refresh_calendar()
        self._detail.scroll_to_now()

    def refresh_calendar(self) -> None:
        events = self._service.get_events_for_month(self._year, self._month)

        # Gather financial data for the month
        income_by_day: dict[int, int] = {}
        expense_by_day: dict[int, int] = {}
        if self._income_service and self._expense_service:
            _, num_days = calendar.monthrange(self._year, self._month)
            start = date(self._year, self._month, 1)
            end = date(self._year, self._month, num_days)
            for inc in self._income_service.get_incomes_in_range(start, end):
                d = inc.income_date.day
                income_by_day[d] = income_by_day.get(d, 0) + inc.amount
            for exp in self._expense_service.get_expenses_in_range(
                start, end
            ):
                d = exp.expense_date.day
                expense_by_day[d] = expense_by_day.get(d, 0) + exp.amount

        self._calendar.set_month(
            self._year, self._month, events,
            income_by_day, expense_by_day,
        )
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
        self._detail.scroll_to_now()
