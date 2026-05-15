from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)


DEFAULT_SUMMARY_ROWS = [
    ("센서", "-"),
    ("변환", "-"),
    ("입력", "-"),
    ("출력", "-"),
    ("토픽", "-"),
    ("포맷", "-"),
    ("추가 옵션", "-"),
]


class SummaryPanel(QWidget):
    """
    변환 요약 패널.

    기존 make_summary_panel()과 동일한 objectName / margin / spacing을 사용해서
    theme.py의 기존 디자인이 그대로 적용되도록 한다.
    """

    def __init__(
        self,
        rows: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("SummaryPanelContent")

        self._row_keys: list[str] = []
        self._value_labels: dict[str, QLabel] = {}
        self._row_widgets: list[QFrame] = []

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)

        self._rows_widget = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(10)

        self._layout.addWidget(self._rows_widget)
        self._layout.addStretch(1)

        self.set_rows(rows or DEFAULT_SUMMARY_ROWS)

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        keys = [key for key, _value in rows]

        if keys == self._row_keys:
            for key, value in rows:
                self._value_labels[key].setText(self._display(value))
            return

        self._clear_rows()

        self._row_keys = keys

        for key, value in rows:
            item = QFrame()
            item.setObjectName("SummaryItem")

            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(10, 8, 10, 8)
            item_layout.setSpacing(2)

            key_label = QLabel(key)
            key_label.setObjectName("SummaryKey")

            value_label = QLabel(self._display(value))
            value_label.setObjectName("SummaryValue")
            value_label.setWordWrap(True)

            item_layout.addWidget(key_label)
            item_layout.addWidget(value_label)

            self._rows_layout.addWidget(item)

            self._row_widgets.append(item)
            self._value_labels[key] = value_label

    def update_summary(
        self,
        *,
        sensor: str = "-",
        mode: str = "-",
        input_path: str = "-",
        output_path: str = "-",
        topic: str = "-",
        fmt: str = "-",
        extra: str = "-",
    ) -> None:
        self.set_rows(
            [
                ("센서", sensor),
                ("변환", mode),
                ("입력", input_path),
                ("출력", output_path),
                ("토픽", topic),
                ("포맷", fmt),
                ("추가 옵션", extra),
            ]
        )

    def _clear_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self._row_widgets.clear()
        self._value_labels.clear()
        self._row_keys.clear()

    @staticmethod
    def _display(value: str | None) -> str:
        value = (value or "").strip()
        return value if value else "-"


def make_summary_panel(title: str, rows: list[tuple[str, str]]) -> SummaryPanel:
    """
    기존 코드 호환용 함수.

    이전처럼 make_summary_panel(title, rows)를 호출해도 동작하지만,
    실제 선택값과 연결할 때는 SummaryPanel 인스턴스를 저장한 뒤 update_summary()를 호출한다.
    """
    return SummaryPanel(title=title, rows=rows)