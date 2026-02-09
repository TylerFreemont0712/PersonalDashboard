"""Main application window with tab-based navigation between modules."""
from __future__ import annotations

import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QMenuBar,
    QStatusBar,
    QMessageBox,
)

from src.repositories.database import get_connection, init_db
from src.repositories.expense_repo import ExpenseRepository
from src.repositories.income_repo import IncomeRepository
from src.repositories.event_repo import EventRepository
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService
from src.services.event_service import EventService
from src.services.tax_service import TaxService
from src.ui.widgets.dashboard_widget import DashboardWidget
from src.ui.widgets.expenses_widget import ExpensesWidget
from src.ui.widgets.income_widget import IncomeWidget
from src.ui.widgets.tax_widget import TaxWidget
from src.ui.widgets.calendar_widget import CalendarWidget


class MainWindow(QMainWindow):
    def __init__(self, db_path: str | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Personal Ops Dashboard / 個人業務ダッシュボード")
        self.setMinimumSize(1000, 700)

        # Database
        if db_path:
            self._conn = get_connection(db_path)
        else:
            self._conn = get_connection()
        init_db(self._conn)

        # Repositories
        expense_repo = ExpenseRepository(self._conn)
        income_repo = IncomeRepository(self._conn)
        event_repo = EventRepository(self._conn)

        # Services
        self._expense_service = ExpenseService(expense_repo)
        self._income_service = IncomeService(income_repo)
        self._event_service = EventService(event_repo)
        self._tax_service = TaxService(self._income_service, self._expense_service)

        # Central tab widget
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.West)
        self._tabs.setDocumentMode(True)
        self.setCentralWidget(self._tabs)

        # Module widgets
        self._dashboard_widget = DashboardWidget(self._income_service, self._expense_service)
        self._expenses_widget = ExpensesWidget(self._expense_service)
        self._income_widget = IncomeWidget(self._income_service)
        self._tax_widget = TaxWidget(self._tax_service, self._income_service, self._expense_service)
        self._calendar_widget = CalendarWidget(self._event_service)

        self._tabs.addTab(self._dashboard_widget, "Dashboard")
        self._tabs.addTab(self._calendar_widget, "Calendar")
        self._tabs.addTab(self._expenses_widget, "Expenses")
        self._tabs.addTab(self._income_widget, "Income")
        self._tabs.addTab(self._tax_widget, "Tax Prep")

        # Menu bar
        self._setup_menu_bar()

        # Status bar
        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

        # Keyboard shortcuts
        self._setup_shortcuts()

    def _setup_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        dashboard_action = QAction("&Dashboard", self)
        dashboard_action.setShortcut(QKeySequence("Ctrl+1"))
        dashboard_action.triggered.connect(lambda: self._tabs.setCurrentIndex(0))
        view_menu.addAction(dashboard_action)

        calendar_action = QAction("&Calendar", self)
        calendar_action.setShortcut(QKeySequence("Ctrl+2"))
        calendar_action.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        view_menu.addAction(calendar_action)

        expenses_action = QAction("&Expenses", self)
        expenses_action.setShortcut(QKeySequence("Ctrl+3"))
        expenses_action.triggered.connect(lambda: self._tabs.setCurrentIndex(2))
        view_menu.addAction(expenses_action)

        income_action = QAction("&Income", self)
        income_action.setShortcut(QKeySequence("Ctrl+4"))
        income_action.triggered.connect(lambda: self._tabs.setCurrentIndex(3))
        view_menu.addAction(income_action)

        tax_action = QAction("&Tax Prep", self)
        tax_action.setShortcut(QKeySequence("Ctrl+5"))
        tax_action.triggered.connect(lambda: self._tabs.setCurrentIndex(4))
        view_menu.addAction(tax_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_shortcuts(self) -> None:
        pass  # Shortcuts already bound via menu actions

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Personal Ops Dashboard",
            "Personal Ops Dashboard v1.0\n\n"
            "個人業務ダッシュボード\n\n"
            "Manage bills, income, calendar, and\n"
            "prepare data for 確定申告 (tax filing).\n\n"
            "Built with Python + PyQt6 + SQLite.",
        )

    def closeEvent(self, event) -> None:
        self._conn.close()
        super().closeEvent(event)
