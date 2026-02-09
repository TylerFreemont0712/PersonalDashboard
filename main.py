"""Entry point for the Personal Ops Dashboard application."""
import sys

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.ui.theme import get_stylesheet


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Personal Ops Dashboard")
    app.setStyle("Fusion")
    app.setStyleSheet(get_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
