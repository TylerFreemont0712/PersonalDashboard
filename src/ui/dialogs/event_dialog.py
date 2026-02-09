"""Dialog for adding or editing calendar events."""

from __future__ import annotations

from datetime import date, time
from typing import Optional

from PyQt6.QtCore import QDate, QTime
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTimeEdit,
)

from src.models.event import Event, EventCategory, EventRecurrence, EVENT_CATEGORY_COLORS

_CATEGORY_DISPLAY_NAMES: dict[EventCategory, str] = {
    EventCategory.WORK: "Work",
    EventCategory.FAMILY: "Family",
    EventCategory.BIRTHDAY: "Birthday",
    EventCategory.DEADLINE: "Deadline",
    EventCategory.APPOINTMENT: "Appointment",
    EventCategory.HOLIDAY: "Holiday",
    EventCategory.OTHER: "Other",
}

_RECURRENCE_DISPLAY_NAMES: dict[EventRecurrence, str] = {
    EventRecurrence.NONE: "None",
    EventRecurrence.WEEKLY: "Weekly",
    EventRecurrence.MONTHLY: "Monthly",
    EventRecurrence.YEARLY: "Yearly",
}


class EventDialog(QDialog):
    """A dialog for creating or editing a calendar event.

    Parameters
    ----------
    event : Event | None
        An existing event to edit.  Pass *None* to create a new event.
    initial_date : date | None
        The date to pre-fill when adding a new event.  Ignored when editing.
    parent : QWidget | None
        Optional parent widget.
    """

    def __init__(
        self,
        event: Optional[Event] = None,
        initial_date: Optional[date] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._event = event
        self._editing = event is not None
        self._current_color: str = ""

        self.setWindowTitle("Edit Event" if self._editing else "Add Event")
        self.setMinimumWidth(400)

        self._build_ui(initial_date)
        self._connect_signals()

        if self._editing:
            self._populate_from_event(event)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self, initial_date: Optional[date]) -> None:
        layout = QGridLayout(self)
        row = 0

        # Title
        layout.addWidget(QLabel("Title:"), row, 0)
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Event title")
        layout.addWidget(self._title_edit, row, 1, 1, 2)
        row += 1

        # Date
        layout.addWidget(QLabel("Date:"), row, 0)
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        if initial_date is not None:
            self._date_edit.setDate(QDate(initial_date.year, initial_date.month, initial_date.day))
        else:
            today = date.today()
            self._date_edit.setDate(QDate(today.year, today.month, today.day))
        layout.addWidget(self._date_edit, row, 1, 1, 2)
        row += 1

        # Category
        layout.addWidget(QLabel("Category:"), row, 0)
        self._category_combo = QComboBox()
        for cat in EventCategory:
            self._category_combo.addItem(_CATEGORY_DISPLAY_NAMES[cat], cat)
        layout.addWidget(self._category_combo, row, 1, 1, 2)
        row += 1

        # Start time
        self._start_time_check = QCheckBox("Start time:")
        layout.addWidget(self._start_time_check, row, 0)
        self._start_time_edit = QTimeEdit()
        self._start_time_edit.setDisplayFormat("hh:mm AP")
        self._start_time_edit.setEnabled(False)
        layout.addWidget(self._start_time_edit, row, 1, 1, 2)
        row += 1

        # End time
        self._end_time_check = QCheckBox("End time:")
        layout.addWidget(self._end_time_check, row, 0)
        self._end_time_edit = QTimeEdit()
        self._end_time_edit.setDisplayFormat("hh:mm AP")
        self._end_time_edit.setEnabled(False)
        layout.addWidget(self._end_time_edit, row, 1, 1, 2)
        row += 1

        # Recurrence
        layout.addWidget(QLabel("Recurrence:"), row, 0)
        self._recurrence_combo = QComboBox()
        for rec in EventRecurrence:
            self._recurrence_combo.addItem(_RECURRENCE_DISPLAY_NAMES[rec], rec)
        layout.addWidget(self._recurrence_combo, row, 1, 1, 2)
        row += 1

        # Color
        layout.addWidget(QLabel("Color:"), row, 0)
        self._color_button = QPushButton()
        self._color_button.setFixedSize(40, 40)
        default_cat = EventCategory.WORK
        self._set_color(EVENT_CATEGORY_COLORS[default_cat])
        layout.addWidget(self._color_button, row, 1)
        row += 1

        # Notes
        layout.addWidget(QLabel("Notes:"), row, 0)
        self._notes_edit = QLineEdit()
        self._notes_edit.setPlaceholderText("Optional notes")
        layout.addWidget(self._notes_edit, row, 1, 1, 2)
        row += 1

        # OK / Cancel
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self._button_box, row, 0, 1, 3)

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._start_time_check.toggled.connect(self._start_time_edit.setEnabled)
        self._end_time_check.toggled.connect(self._end_time_edit.setEnabled)
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        self._color_button.clicked.connect(self._pick_color)
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self.reject)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_category_changed(self, index: int) -> None:
        category: EventCategory = self._category_combo.itemData(index)
        self._set_color(EVENT_CATEGORY_COLORS[category])

    def _pick_color(self) -> None:
        initial = QColor(self._current_color) if self._current_color else QColor("#9E9E9E")
        color = QColorDialog.getColor(initial, self, "Select Event Color")
        if color.isValid():
            self._set_color(color.name())

    def _on_accept(self) -> None:
        title = self._title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Title must not be empty.")
            return

        if (
            self._start_time_check.isChecked()
            and self._end_time_check.isChecked()
        ):
            st = self._start_time_edit.time()
            et = self._end_time_edit.time()
            if et < st:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "End time must not be before start time.",
                )
                return

        self.accept()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_color(self, hex_color: str) -> None:
        self._current_color = hex_color
        self._color_button.setStyleSheet(
            f"background-color: {hex_color}; border: 1px solid #888;"
        )

    def _populate_from_event(self, event: Event) -> None:
        self._title_edit.setText(event.title)

        d = event.event_date
        self._date_edit.setDate(QDate(d.year, d.month, d.day))

        index = self._category_combo.findData(event.category)
        if index >= 0:
            self._category_combo.setCurrentIndex(index)

        if event.start_time is not None:
            self._start_time_check.setChecked(True)
            st = event.start_time
            self._start_time_edit.setTime(QTime(st.hour, st.minute, st.second))

        if event.end_time is not None:
            self._end_time_check.setChecked(True)
            et = event.end_time
            self._end_time_edit.setTime(QTime(et.hour, et.minute, et.second))

        rec_index = self._recurrence_combo.findData(event.recurrence)
        if rec_index >= 0:
            self._recurrence_combo.setCurrentIndex(rec_index)

        self._set_color(event.display_color)

        self._notes_edit.setText(event.notes)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_event(self) -> Event:
        """Build and return an `Event` from the current dialog state.

        If the dialog was opened in edit mode the returned event preserves the
        original ``id``, ``linked_income_id``, and ``linked_expense_id``.
        """
        qd = self._date_edit.date()
        event_date = date(qd.year(), qd.month(), qd.day())

        start_time: Optional[time] = None
        if self._start_time_check.isChecked():
            qt_st = self._start_time_edit.time()
            start_time = time(qt_st.hour(), qt_st.minute(), qt_st.second())

        end_time: Optional[time] = None
        if self._end_time_check.isChecked():
            qt_et = self._end_time_edit.time()
            end_time = time(qt_et.hour(), qt_et.minute(), qt_et.second())

        category: EventCategory = self._category_combo.currentData()
        recurrence: EventRecurrence = self._recurrence_combo.currentData()

        # Only store a custom color when it differs from the category default.
        color: Optional[str] = None
        if self._current_color != EVENT_CATEGORY_COLORS[category]:
            color = self._current_color

        linked_income_id: Optional[int] = None
        linked_expense_id: Optional[int] = None
        event_id: Optional[int] = None
        if self._event is not None:
            linked_income_id = self._event.linked_income_id
            linked_expense_id = self._event.linked_expense_id
            event_id = self._event.id

        return Event(
            title=self._title_edit.text().strip(),
            event_date=event_date,
            category=category,
            start_time=start_time,
            end_time=end_time,
            recurrence=recurrence,
            color=color,
            notes=self._notes_edit.text(),
            linked_income_id=linked_income_id,
            linked_expense_id=linked_expense_id,
            id=event_id,
        )
