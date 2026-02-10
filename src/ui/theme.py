"""Dark hacker theme stylesheet for the Personal Ops Dashboard.

Design philosophy: dark backgrounds, cyan/green accent glow, monospace hints,
sharp borders, terminal-inspired aesthetic. All colors defined here so the
theme can be tuned in one place.
"""

# ── Palette ──────────────────────────────────────────────────────────────
BG_DARKEST = "#0a0e14"
BG_DARK = "#0d1117"
BG_MID = "#161b22"
BG_LIGHT = "#1c2333"
BG_HOVER = "#222e3f"
BG_SELECTED = "#1a3a4a"

BORDER = "#30363d"
BORDER_FOCUS = "#00e5ff"

TEXT = "#c9d1d9"
TEXT_DIM = "#6e7681"
TEXT_BRIGHT = "#e6edf3"

ACCENT_CYAN = "#00e5ff"
ACCENT_GREEN = "#39ff14"
ACCENT_RED = "#ff4444"
ACCENT_YELLOW = "#ffd700"
ACCENT_ORANGE = "#ff9800"

INCOME_GREEN = "#00e676"
EXPENSE_RED = "#ff5252"

# Calendar
CAL_TODAY_BG = "#1a2e1a"
CAL_TODAY_BORDER = "#39ff14"
CAL_SELECTED_BG = "#0d2a3a"
CAL_SELECTED_BORDER = "#00e5ff"
CAL_EMPTY_BG = "#0a0c10"
CAL_DAY_BG = "#0d1117"
CAL_DAY_BORDER = "#1e2630"


def get_stylesheet() -> str:
    return f"""
    /* ── Global ──────────────────────────────────────────── */
    QMainWindow, QWidget {{
        background-color: {BG_DARK};
        color: {TEXT};
        font-family: "Fira Code", "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
        font-size: 13px;
    }}

    /* ── Tab Bar ─────────────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        background: {BG_DARK};
    }}
    QTabBar {{
        background: {BG_DARKEST};
    }}
    QTabBar::tab {{
        background: {BG_MID};
        color: {TEXT_DIM};
        padding: 8px 4px;
        border: 1px solid {BORDER};
        border-right: none;
        min-width: 26px;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 0.5px;
    }}
    QTabBar::tab:selected {{
        background: {BG_DARK};
        color: {ACCENT_CYAN};
        border-left: 2px solid {ACCENT_CYAN};
    }}
    QTabBar::tab:hover:!selected {{
        background: {BG_HOVER};
        color: {TEXT};
    }}

    /* ── Buttons ─────────────────────────────────────────── */
    QPushButton {{
        background-color: {BG_MID};
        color: {TEXT};
        border: 1px solid {BORDER};
        padding: 6px 16px;
        border-radius: 3px;
        font-weight: bold;
        font-size: 12px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        border-color: {ACCENT_CYAN};
        color: {ACCENT_CYAN};
    }}
    QPushButton:pressed {{
        background-color: {BG_SELECTED};
    }}
    QPushButton:disabled {{
        color: {TEXT_DIM};
        border-color: {BG_MID};
    }}
    QPushButton#accentBtn {{
        background-color: rgba(0, 229, 255, 0.12);
        border: 1px solid {ACCENT_CYAN};
        color: {ACCENT_CYAN};
    }}
    QPushButton#accentBtn:hover {{
        background-color: rgba(0, 229, 255, 0.25);
    }}
    QPushButton#dangerBtn {{
        border: 1px solid {ACCENT_RED};
        color: {ACCENT_RED};
    }}

    /* ── Tables ──────────────────────────────────────────── */
    QTableWidget {{
        background-color: {BG_DARKEST};
        alternate-background-color: {BG_MID};
        gridline-color: {BORDER};
        border: 1px solid {BORDER};
        selection-background-color: {BG_SELECTED};
        selection-color: {TEXT_BRIGHT};
        font-size: 12px;
    }}
    QTableWidget::item {{
        padding: 4px 8px;
        border-bottom: 1px solid {BORDER};
    }}
    QHeaderView::section {{
        background-color: {BG_MID};
        color: {ACCENT_CYAN};
        border: 1px solid {BORDER};
        padding: 6px 8px;
        font-weight: bold;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QTableWidget QTableCornerButton::section {{
        background-color: {BG_MID};
        border: 1px solid {BORDER};
    }}

    /* ── Inputs ──────────────────────────────────────────── */
    QLineEdit, QSpinBox, QDateEdit, QTimeEdit {{
        background-color: {BG_DARKEST};
        color: {TEXT_BRIGHT};
        border: 1px solid {BORDER};
        border-radius: 3px;
        padding: 5px 8px;
        selection-background-color: {BG_SELECTED};
    }}
    QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {{
        border-color: {ACCENT_CYAN};
    }}

    QComboBox {{
        background-color: {BG_DARKEST};
        color: {TEXT_BRIGHT};
        border: 1px solid {BORDER};
        border-radius: 3px;
        padding: 5px 8px;
        min-width: 80px;
    }}
    QComboBox:focus {{
        border-color: {ACCENT_CYAN};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid {TEXT_DIM};
        margin-right: 6px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_MID};
        color: {TEXT};
        border: 1px solid {BORDER};
        selection-background-color: {BG_SELECTED};
        selection-color: {ACCENT_CYAN};
    }}

    /* ── Labels ──────────────────────────────────────────── */
    QLabel {{
        color: {TEXT};
    }}
    QLabel#sectionTitle {{
        color: {ACCENT_CYAN};
        font-size: 16px;
        font-weight: bold;
        letter-spacing: 2px;
    }}
    QLabel#statValue {{
        color: {TEXT_BRIGHT};
        font-size: 22px;
        font-weight: bold;
    }}
    QLabel#statLabel {{
        color: {TEXT_DIM};
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QLabel#accentGreen {{
        color: {INCOME_GREEN};
    }}
    QLabel#accentRed {{
        color: {EXPENSE_RED};
    }}
    QLabel#dimNote {{
        color: {TEXT_DIM};
        font-size: 11px;
    }}

    /* ── Frames / Panels ────────────────────────────────── */
    QFrame#statCard {{
        background-color: {BG_MID};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 16px;
    }}
    QFrame#statCard:hover {{
        border-color: {ACCENT_CYAN};
    }}

    /* ── List widgets ────────────────────────────────────── */
    QListWidget {{
        background-color: {BG_DARKEST};
        border: 1px solid {BORDER};
        color: {TEXT};
    }}
    QListWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {BORDER};
    }}
    QListWidget::item:selected {{
        background-color: {BG_SELECTED};
        color: {TEXT_BRIGHT};
    }}
    QListWidget::item:hover {{
        background-color: {BG_HOVER};
    }}

    /* ── Scrollbars ──────────────────────────────────────── */
    QScrollBar:vertical {{
        background: {BG_DARKEST};
        width: 10px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        min-height: 30px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_DIM};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {BG_DARKEST};
        height: 10px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        min-width: 30px;
        border-radius: 5px;
    }}

    /* ── Splitter ─────────────────────────────────────────── */
    QSplitter::handle {{
        background-color: {BORDER};
        width: 2px;
    }}
    QSplitter::handle:hover {{
        background-color: {ACCENT_CYAN};
    }}

    /* ── Menu / Context Menu ─────────────────────────────── */
    QMenuBar {{
        background-color: {BG_DARKEST};
        color: {TEXT};
        border-bottom: 1px solid {BORDER};
    }}
    QMenuBar::item:selected {{
        background-color: {BG_HOVER};
        color: {ACCENT_CYAN};
    }}
    QMenu {{
        background-color: {BG_MID};
        color: {TEXT};
        border: 1px solid {BORDER};
    }}
    QMenu::item:selected {{
        background-color: {BG_SELECTED};
        color: {ACCENT_CYAN};
    }}
    QMenu::separator {{
        height: 1px;
        background: {BORDER};
    }}

    /* ── Status Bar ──────────────────────────────────────── */
    QStatusBar {{
        background-color: {BG_DARKEST};
        color: {TEXT_DIM};
        border-top: 1px solid {BORDER};
        font-size: 11px;
    }}

    /* ── Dialogs ─────────────────────────────────────────── */
    QDialog {{
        background-color: {BG_DARK};
    }}
    QDialogButtonBox QPushButton {{
        min-width: 80px;
    }}

    /* ── Checkbox ─────────────────────────────────────────── */
    QCheckBox {{
        color: {TEXT};
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {BORDER};
        border-radius: 3px;
        background: {BG_DARKEST};
    }}
    QCheckBox::indicator:checked {{
        background: {ACCENT_CYAN};
        border-color: {ACCENT_CYAN};
    }}

    /* ── Message Box ─────────────────────────────────────── */
    QMessageBox {{
        background-color: {BG_DARK};
    }}

    /* ── ToolTip ──────────────────────────────────────────── */
    QToolTip {{
        background-color: {BG_MID};
        color: {TEXT_BRIGHT};
        border: 1px solid {ACCENT_CYAN};
        padding: 4px 8px;
    }}
    """
