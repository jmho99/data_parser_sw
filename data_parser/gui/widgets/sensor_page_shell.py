from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


ICON_EXTENSIONS = (".svg", ".png", ".jpg", ".jpeg")


def resolve_icon_path(icon_name: str | None) -> Path | None:
    if not icon_name:
        return None

    icon_dir = Path(__file__).resolve().parents[1] / "assets" / "icons"

    for ext in ICON_EXTENSIONS:
        icon_path = icon_dir / f"{icon_name}{ext}"
        if icon_path.exists():
            return icon_path

    return None


def make_path_input(
    line_edit: QWidget,
    browse_button: QPushButton,
    browse_text: str = "Browse",
) -> QFrame:
    browse_button.setText(browse_text)
    browse_button.setObjectName("BrowseButton")

    group = QFrame()
    group.setObjectName("InputGroup")

    layout = QHBoxLayout(group)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    layout.addWidget(line_edit, 1)
    layout.addWidget(browse_button)

    return group


def make_field_row(
    label_ko: str,
    label_en: str,
    editor: QWidget,
) -> QFrame:
    row = QFrame()
    row.setObjectName("FieldRow")

    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(14)

    label_box = QWidget()
    label_box.setFixedWidth(132)

    label_layout = QVBoxLayout(label_box)
    label_layout.setContentsMargins(0, 0, 0, 0)
    label_layout.setSpacing(1)

    ko = QLabel(label_ko)
    ko.setObjectName("FieldLabelKo")
    ko.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    en = QLabel(label_en)
    en.setObjectName("FieldLabelEn")
    en.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    label_layout.addWidget(ko)
    label_layout.addWidget(en)

    layout.addWidget(label_box)
    layout.addWidget(editor, 1)

    return row

class ChoiceBar(QFrame):
    """
    ComboBox 대신 사용하는 나열형 선택 바.

    - exclusive=True  : 하나만 선택
    - exclusive=False : 복수 선택 가능
    """

    changed = Signal()

    def __init__(
        self,
        options: list[tuple[str, str]],
        *,
        exclusive: bool = True,
        default: str | None = None,
        checked_values: list[str] | None = None,
        disabled_values: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("ChoiceBar")

        self._buttons: dict[str, QPushButton] = {}
        self._exclusive = exclusive

        checked_set = set(checked_values or [])
        disabled_set = set(disabled_values or [])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        self._group = QButtonGroup(self)
        self._group.setExclusive(exclusive)

        for label, value in options:
            button = QPushButton(label)
            button.setObjectName("ChoiceChip")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

            self._buttons[value] = button
            self._group.addButton(button)
            layout.addWidget(button)

            if value in checked_set:
                button.setChecked(True)

            if value in disabled_set:
                button.setChecked(True)
                button.setEnabled(False)

            button.toggled.connect(lambda _checked=False: self.changed.emit())

        if exclusive:
            selected = default or (options[0][1] if options else None)
            if selected in self._buttons:
                self._buttons[selected].setChecked(True)

    def selected_value(self) -> str | None:
        for value, button in self._buttons.items():
            if button.isChecked():
                return value

        return None

    def selected_values(self) -> list[str]:
        return [
            value
            for value, button in self._buttons.items()
            if button.isChecked()
        ]

    def set_selected_value(self, value: str) -> None:
        if value in self._buttons:
            self._buttons[value].setChecked(True)

    def set_checked(self, value: str, checked: bool) -> None:
        if value in self._buttons:
            self._buttons[value].setChecked(checked)

    def button(self, value: str) -> QPushButton | None:
        return self._buttons.get(value)

class SensorPageShell(QWidget):
    """
    센서별 페이지 공통 shell.

    구성:
    - 상단: 아이콘 / 센서명 / 영문명 / 설명 / 변환 개수
    - 중단: segmented 변환 모드 탭
    - 본문: 좌측 설정 입력 + 우측 요약/실행 버튼
    - 하단: 로그 영역

    각 센서 페이지는 변환 로직은 그대로 두고,
    설정 위젯과 버튼만 이 shell에 넣으면 된다.
    """

    selected_source_changed = Signal(str)

    HEADER_RATIO = 0.17
    MODE_RATIO = 0.07
    LOG_RATIO = 0.17

    SUMMARY_RATIO = 0.28

    MIN_HEADER_H = 118
    MIN_MODE_H = 48
    MIN_LOG_H = 130

    MIN_SUMMARY_W = 260
    MAX_SUMMARY_W = 360

    MODE_BAR_H = 32
    MODE_BUTTON_H = 26

    def __init__(
        self,
        *,
        title_ko: str,
        title_en: str,
        description: str,
        icon_name: str | None = None,
        conversion_count: int = 1,
        topics: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._mode_buttons: dict[str, QPushButton] = {}
        self._mode_index: dict[str, int] = {}

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        self._settings_stack = QStackedWidget()
        self._summary_stack = QStackedWidget()

        self._setup_ui(
            title_ko=title_ko,
            title_en=title_en,
            description=description,
            icon_name=icon_name,
            conversion_count=conversion_count,
            topics=topics or [],
        )

    def _setup_ui(
        self,
        *,
        title_ko: str,
        title_en: str,
        description: str,
        icon_name: str | None,
        conversion_count: int,
        topics: list[str],
    ) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self._header = QFrame()
        self._header.setObjectName("SensorHeader")

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(24, 18, 24, 14)
        header_layout.setSpacing(16)

        icon_label = QLabel()
        icon_label.setObjectName("SensorIcon")
        icon_label.setFixedSize(46, 46)
        icon_label.setAlignment(Qt.AlignCenter)

        icon_path = resolve_icon_path(icon_name)
        if icon_path is not None:
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(
                        QSize(30, 30),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            else:
                icon_label.setText(title_en[:1].upper())
        else:
            icon_label.setText(title_en[:1].upper())

        title_area = QWidget()
        title_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_layout = QVBoxLayout(title_area)
        title_layout.setAlignment(Qt.AlignVCenter)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(7)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(10)

        title = QLabel(title_ko)
        title.setObjectName("PageTitle")

        subtitle = QLabel(title_en)
        subtitle.setObjectName("PageTitleEn")

        title_row.addWidget(title)
        title_row.addWidget(subtitle)
        title_row.addStretch(1)

        desc = QLabel(description)
        desc.setObjectName("PageDescription")
        desc.setWordWrap(True)

        title_layout.addLayout(title_row)
        title_layout.addWidget(desc)

        header_layout.addWidget(icon_label, 0, Qt.AlignVCenter)
        header_layout.addWidget(title_area, 1, Qt.AlignVCenter)

        root.addWidget(self._header)

        # Mode section
        self._mode_section = QFrame()
        self._mode_section.setObjectName("ModeSection")

        mode_layout = QHBoxLayout(self._mode_section)
        mode_layout.setContentsMargins(24, 8, 24, 8)
        mode_layout.setSpacing(12)

        self._mode_bar = QFrame()
        self._mode_bar.setObjectName("ModeBar")
        self._mode_bar.setFixedHeight(self.MODE_BAR_H)
        self._mode_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._mode_bar_layout = QHBoxLayout(self._mode_bar)
        self._mode_bar_layout.setContentsMargins(3, 3, 3, 3)
        self._mode_bar_layout.setSpacing(2)

        self._mode_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        mode_layout.addWidget(self._mode_bar, 0, Qt.AlignLeft | Qt.AlignVCenter)
        mode_layout.addStretch(1)

        root.addWidget(self._mode_section)

        # Body
        self._body = QFrame()
        self._body.setObjectName("PageBody")

        body_layout = QHBoxLayout(self._body)
        body_layout.setContentsMargins(24, 18, 24, 18)
        body_layout.setSpacing(18)

        settings_card = QFrame()
        settings_card.setObjectName("SettingsCard")

        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(0)

        settings_header = QLabel("설정 입력")
        settings_header.setObjectName("CardTitle")
        settings_header.setContentsMargins(16, 13, 16, 8)
        settings_layout.addWidget(settings_header)

        self._settings_stack.setObjectName("SettingsStack")
        settings_layout.addWidget(self._settings_stack, 1)

        self._summary_card = QFrame()
        self._summary_card.setObjectName("SummaryCard")
        self._summary_card.setFixedWidth(290)

        summary_layout = QVBoxLayout(self._summary_card)
        summary_layout.setContentsMargins(14, 14, 14, 14)
        summary_layout.setSpacing(12)

        summary_header = QLabel("요약")
        summary_header.setObjectName("CardTitle")
        summary_layout.addWidget(summary_header)

        summary_layout.addWidget(self._summary_stack, 1)

        body_layout.addWidget(settings_card, 1)
        body_layout.addWidget(self._summary_card)

        root.addWidget(self._body, 1)

        # Log
        self._log_section = QFrame()
        self._log_section.setObjectName("LogSection")

        self._log_layout = QVBoxLayout(self._log_section)
        self._log_layout.setContentsMargins(24, 0, 24, 18)
        self._log_layout.setSpacing(8)

        log_header = QLabel("Log")
        log_header.setObjectName("LogTitle")
        self._log_layout.addWidget(log_header)

        root.addWidget(self._log_section, 0)

    def add_mode(
        self,
        *,
        key: str,
        label: str,
        settings_widget: QWidget,
        summary_widget: QWidget,
        run_button: QPushButton,
    ) -> None:
        index = self._settings_stack.count()
    
        button = QPushButton()
        button.setObjectName("ModeTab")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setText(f"{label}")
        button.setFixedHeight(self.MODE_BUTTON_H)
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        button.clicked.connect(lambda checked=False, mode_key=key: self.set_mode(mode_key))
    
        self._button_group.addButton(button)
        self._mode_buttons[key] = button
        self._mode_index[key] = index
    
        self._mode_bar_layout.addWidget(button)
    
        # 설정 영역 스크롤
        settings_scroll = QScrollArea()
        settings_scroll.setObjectName("SettingsScroll")
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        settings_scroll.setFrameShape(QFrame.NoFrame)
    
        settings_widget.setObjectName("SettingsForm")
        settings_scroll.setWidget(settings_widget)
    
        self._settings_stack.addWidget(settings_scroll)
    
        # 실행 버튼
        run_button.setObjectName("PrimaryButton")
        run_button.setMinimumHeight(36)
    
        # 요약 컨테이너
        summary_container = QWidget()
        summary_container.setObjectName("SummaryContainer")
    
        summary_layout = QVBoxLayout(summary_container)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(12)
    
        # 요약 내용만 스크롤
        summary_scroll = QScrollArea()
        summary_scroll.setObjectName("SummaryScroll")
        summary_scroll.setWidgetResizable(True)
        summary_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        summary_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        summary_scroll.setFrameShape(QFrame.NoFrame)
    
        summary_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        summary_scroll.setWidget(summary_widget)
    
        summary_layout.addWidget(summary_scroll, 1)
    
        # 실행 버튼은 스크롤 밖에 고정
        summary_layout.addWidget(run_button)
    
        self._summary_stack.addWidget(summary_container)
    
        if index == 0:
            self.set_mode(key)
    
    def set_mode(self, key: str) -> None:
        if key not in self._mode_index:
            return

        index = self._mode_index[key]

        self._settings_stack.setCurrentIndex(index)
        self._summary_stack.setCurrentIndex(index)

        for mode_key, button in self._mode_buttons.items():
            button.setChecked(mode_key == key)

    def set_log_widget(self, log_widget: QWidget) -> None:
        log_widget.setObjectName("LogView")
        log_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._log_layout.addWidget(log_widget, 1)
        self._apply_ratio_sizes()

    def set_selected_source_path(self, path: str) -> None:
        self.selected_source_changed.emit(path.strip())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._apply_ratio_sizes()


    def _apply_ratio_sizes(self) -> None:
        total_h = max(self.height(), 1)
        total_w = max(self.width(), 1)

        header_h = max(int(total_h * self.HEADER_RATIO), self.MIN_HEADER_H)
        mode_h = max(int(total_h * self.MODE_RATIO), self.MIN_MODE_H)
        log_h = max(int(total_h * self.LOG_RATIO), self.MIN_LOG_H)

        self._header.setFixedHeight(header_h)
        self._mode_section.setFixedHeight(mode_h)
        self._log_section.setFixedHeight(log_h)

        summary_w = int(total_w * self.SUMMARY_RATIO)
        summary_w = max(self.MIN_SUMMARY_W, min(summary_w, self.MAX_SUMMARY_W))
        self._summary_card.setFixedWidth(summary_w)