from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from data_parser.gui.pages import GNSSPage


class MainWindow(QMainWindow):
    """
    Data Parser GUI 메인 윈도우.

    현재 상태:
    - GNSS만 활성화
    - Camera / LiDAR / IMU는 비활성화
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Data Parser")
        self.resize(1000, 650)

        self._nav_buttons: list[QPushButton] = []
        self._stack = QStackedWidget()

        self._setup_ui()
        self._apply_style()
        self.set_page(0)

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self._create_sidebar()

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self._stack, stretch=1)

        self.setCentralWidget(central_widget)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(10)

        title_label = QLabel("Data Parser")
        title_label.setObjectName("AppTitle")
        layout.addWidget(title_label)

        subtitle_label = QLabel("Sensor data converter")
        subtitle_label.setObjectName("AppSubtitle")
        layout.addWidget(subtitle_label)

        layout.addSpacing(16)

        pages = [
            {
                "button_text": "GNSS",
                "widget": GNSSPage(),
                "enabled": True,
            },
            {
                "button_text": "Camera",
                "widget": self._create_disabled_page(
                    "Camera",
                    "Camera 기능은 아직 GUI에 연결하지 않았습니다.",
                ),
                "enabled": False,
            },
            {
                "button_text": "LiDAR",
                "widget": self._create_disabled_page(
                    "LiDAR",
                    "LiDAR 기능은 아직 GUI에 연결하지 않았습니다.",
                ),
                "enabled": False,
            },
            {
                "button_text": "IMU",
                "widget": self._create_disabled_page(
                    "IMU",
                    "IMU 기능은 아직 GUI에 연결하지 않았습니다.",
                ),
                "enabled": False,
            },
        ]

        for index, page in enumerate(pages):
            button = QPushButton(page["button_text"])
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setEnabled(page["enabled"])
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            if page["enabled"]:
                button.clicked.connect(lambda checked=False, i=index: self.set_page(i))

            self._nav_buttons.append(button)
            layout.addWidget(button)

            self._stack.addWidget(page["widget"])

        layout.addStretch()

        return sidebar

    def _create_disabled_page(self, title: str, description: str) -> QWidget:
        page = QWidget()
        page.setObjectName("Page")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(14)

        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")

        description_label = QLabel(description)
        description_label.setObjectName("PageDescription")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()

        return page

    def set_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)

        for button_index, button in enumerate(self._nav_buttons):
            button.setChecked(button_index == index)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f6f8;
            }

            QWidget#Sidebar {
                background-color: #20242c;
            }

            QLabel#AppTitle {
                color: #ffffff;
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#AppSubtitle {
                color: #aab0bd;
                font-size: 12px;
            }

            QPushButton#NavButton {
                background-color: transparent;
                color: #d7dce5;
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                text-align: left;
                font-size: 14px;
            }

            QPushButton#NavButton:hover {
                background-color: #2d3340;
            }

            QPushButton#NavButton:checked {
                background-color: #3b82f6;
                color: white;
                font-weight: 600;
            }

            QPushButton#NavButton:disabled {
                color: #666d7a;
            }

            QWidget#Page {
                background-color: #f5f6f8;
            }

            QLabel#PageTitle {
                color: #20242c;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#PageDescription {
                color: #333844;
                font-size: 15px;
            }

            QLabel#SectionTitle {
                color: #20242c;
                font-size: 16px;
                font-weight: 600;
            }

            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #d7dce5;
                border-radius: 6px;
                padding: 7px 9px;
                font-size: 13px;
            }

            QComboBox {
                background-color: #ffffff;
                border: 1px solid #d7dce5;
                border-radius: 6px;
                padding: 7px 9px;
                font-size: 13px;
            }

            QPushButton {
                background-color: #ffffff;
                border: 1px solid #d7dce5;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: #eef1f5;
            }

            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #d7dce5;
                border-radius: 8px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
            }
            """
        )