from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from data_parser.gui.pages.camera_page import CameraPage
from data_parser.gui.pages.gnss_page import GNSSPage
from data_parser.gui.pages.imu_page import IMUPage
from data_parser.gui.pages.lidar_page import LiDARPage
from data_parser.gui.theme import apply_app_style
from data_parser.gui.widgets.sensor_page_shell import SensorPageShell, resolve_icon_path


@dataclass(frozen=True)
class PageSpec:
    key: str
    title_ko: str
    title_en: str
    icon_name: str
    factory: Callable[[], QWidget]


class MainWindow(QMainWindow):
    SIDEBAR_RATIO = 0.18
    MIN_SIDEBAR_W = 220
    MAX_SIDEBAR_W = 300

    def __init__(self) -> None:
        super().__init__()

        app = QApplication.instance()
        if app is not None:
            apply_app_style(app)

        self.setObjectName("AppWindow")
        self.setWindowTitle("Data Parser")
        self.resize(1280, 820)

        self._page_specs = self._build_page_specs()
        self._buttons: dict[str, QPushButton] = {}
        self._selected_source_path = ""

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setObjectName("MainStack")

        sidebar = self._create_sidebar()
        root_layout.addWidget(sidebar)
        root_layout.addWidget(self._stack, 1)

        self._page_index: dict[str, int] = {}
        for spec in self._page_specs:
            page = spec.factory()
            index = self._stack.addWidget(page)
            self._page_index[spec.key] = index

            for shell in page.findChildren(SensorPageShell):
                shell.selected_source_changed.connect(self._update_source_card)

        self._select_page(self._page_specs[0].key)

    def _build_page_specs(self) -> list[PageSpec]:
        return [
            PageSpec(
                key="camera",
                title_ko="카메라",
                title_en="Camera",
                icon_name="camera",
                factory=CameraPage,
            ),
            PageSpec(
                key="lidar",
                title_ko="라이다",
                title_en="LiDAR",
                icon_name="lidar",
                factory=LiDARPage,
            ),
            PageSpec(
                key="gnss",
                title_ko="위성항법",
                title_en="GNSS",
                icon_name="gnss",
                factory=GNSSPage,
            ),
            PageSpec(
                key="imu",
                title_ko="관성 측정 장치",
                title_en="IMU",
                icon_name="imu",
                factory=IMUPage,
            ),
        ]

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        self._sidebar = sidebar
        self._apply_sidebar_width()

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 16, 10, 14)
        layout.setSpacing(10)

        title = QLabel("Data Parser")
        title.setObjectName("AppTitle")
        layout.addWidget(title)

        section = QLabel("센서 · Sensors")
        section.setObjectName("SidebarSection")
        layout.addWidget(section)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        for spec in self._page_specs:
            btn = QPushButton(f"{spec.title_ko}   {spec.title_en}")
            btn.setObjectName("SidebarTab")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)

            icon_path = resolve_icon_path(spec.icon_name)
            if icon_path is not None:
                btn.setIcon(QIcon(str(icon_path)))
                btn.setIconSize(QSize(18, 18))

            btn.clicked.connect(lambda checked=False, key=spec.key: self._select_page(key))

            self._button_group.addButton(btn)
            self._buttons[spec.key] = btn
            layout.addWidget(btn)

        layout.addStretch(1)

        self._source_card = QFrame()
        self._source_card.setObjectName("SourceCard")

        card_layout = QVBoxLayout(self._source_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(7)

        card_top = QHBoxLayout()
        card_top.setContentsMargins(0, 0, 0, 0)
        card_top.setSpacing(6)

        self._source_status_dot = QLabel()
        self._source_status_dot.setObjectName("StatusDotIdle")
        self._source_status_dot.setFixedSize(7, 7)

        source_title = QLabel("선택된 입력")
        source_title.setObjectName("SourceCardTitle")

        card_top.addWidget(self._source_status_dot)
        card_top.addWidget(source_title)
        card_top.addStretch(1)

        self._source_state_label = QLabel("대기")
        self._source_state_label.setObjectName("SourceState")
        card_top.addWidget(self._source_state_label)

        self._source_name_label = QLabel("아직 선택된 파일/폴더가 없습니다.")
        self._source_name_label.setObjectName("SourceName")
        self._source_name_label.setWordWrap(True)

        self._source_meta_label = QLabel("-")
        self._source_meta_label.setObjectName("SourceMeta")
        self._source_meta_label.setWordWrap(True)

        self._open_source_button = QPushButton("Open")
        self._open_source_button.setObjectName("SourceOpenButton")
        self._open_source_button.setEnabled(False)
        self._open_source_button.clicked.connect(self._open_selected_source)

        card_layout.addLayout(card_top)
        card_layout.addWidget(self._source_name_label)
        card_layout.addWidget(self._source_meta_label)
        card_layout.addWidget(self._open_source_button)

        layout.addWidget(self._source_card)

        return sidebar

    def _select_page(self, key: str) -> None:
        if key not in self._page_index:
            return

        self._stack.setCurrentIndex(self._page_index[key])

        for btn_key, btn in self._buttons.items():
            btn.setChecked(btn_key == key)

    def _update_source_card(self, path_text: str) -> None:
        self._selected_source_path = path_text

        if not path_text:
            self._source_status_dot.setObjectName("StatusDotIdle")
            self._source_status_dot.style().unpolish(self._source_status_dot)
            self._source_status_dot.style().polish(self._source_status_dot)

            self._source_state_label.setText("대기")
            self._source_name_label.setText("아직 선택된 파일/폴더가 없습니다.")
            self._source_meta_label.setText("-")
            self._open_source_button.setEnabled(False)
            return

        path = Path(path_text).expanduser()

        self._source_status_dot.setObjectName("StatusDotOk")
        self._source_status_dot.style().unpolish(self._source_status_dot)
        self._source_status_dot.style().polish(self._source_status_dot)

        self._source_state_label.setText("Open")
        self._source_name_label.setText(path.name if path.name else str(path))

        if path.exists():
            source_type = "Folder" if path.is_dir() else "File"
            self._source_meta_label.setText(f"{source_type} · {path}")
            self._open_source_button.setEnabled(True)
        else:
            self._source_meta_label.setText(f"경로 확인 필요 · {path}")
            self._open_source_button.setEnabled(False)

    def _open_selected_source(self) -> None:
        if not self._selected_source_path:
            return

        path = Path(self._selected_source_path).expanduser()

        if not path.exists():
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._apply_sidebar_width()


    def _apply_sidebar_width(self) -> None:
        if not hasattr(self, "_sidebar"):
            return

        width = max(self.width(), 1)
        sidebar_w = int(width * self.SIDEBAR_RATIO)
        sidebar_w = max(self.MIN_SIDEBAR_W, min(sidebar_w, self.MAX_SIDEBAR_W))

        self._sidebar.setFixedWidth(sidebar_w)