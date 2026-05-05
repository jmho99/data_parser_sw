from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from data_parser.gui.main_window import MainWindow


def run_app(argv: list[str] | None = None) -> int:
    """
    GUI 애플리케이션 실행 함수.

    나중에 main.py 또는 CLI에서 GUI 모드를 추가할 때
    이 함수를 호출하면 된다.
    """
    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("Data Parser")

    window = MainWindow()
    window.show()

    return app.exec()


def main() -> None:
    raise SystemExit(run_app())


if __name__ == "__main__":
    main()