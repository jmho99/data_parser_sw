from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from data_parser.gui.widgets import (
    SensorPageShell,
    SummaryPanel,
    make_field_row,
    make_path_input,
)


class GNSSPage(QWidget):
    """
    GNSS 변환 GUI 페이지.

    현재 지원:
    - Bag → CSV
    - Bag → KML
    - CSV → KML
    """

    def __init__(self) -> None:
        super().__init__()

        # Bag → CSV
        self.bag_csv_input_path_edit = QLineEdit()
        self.bag_csv_output_dir_edit = QLineEdit()
        self.bag_csv_topic_edit = QLineEdit("/gnss/fix")
        self.bag_csv_run_button = QPushButton("Bag → CSV 변환 시작")

        # Bag → KML
        self.bag_kml_input_path_edit = QLineEdit()
        self.bag_kml_output_dir_edit = QLineEdit()
        self.bag_kml_output_name_edit = QLineEdit()
        self.bag_kml_topic_edit = QLineEdit("/gnss/fix")
        self.bag_kml_run_button = QPushButton("Bag → KML 변환 시작")

        # CSV → KML
        self.csv_input_file_edit = QLineEdit()
        self.csv_output_dir_edit = QLineEdit()
        self.csv_output_name_edit = QLineEdit()
        self.csv_run_button = QPushButton("CSV → KML 변환 시작")

        self.log_viewer = QTextEdit()
        self.bag_csv_summary_panel = SummaryPanel()
        self.bag_kml_summary_panel = SummaryPanel()
        self.csv_kml_summary_panel = SummaryPanel()

        self._setup_default_values()
        self._setup_ui()
        self._connect_summary_signals()
        self._update_summary()

    def _setup_default_values(self) -> None:
        self.bag_csv_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.bag_csv_output_dir_edit.setPlaceholderText("CSV 출력 폴더 경로")
        self.bag_csv_topic_edit.setPlaceholderText("/gnss/fix")

        self.bag_kml_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.bag_kml_output_dir_edit.setPlaceholderText("KML 출력 폴더 경로")
        self.bag_kml_output_name_edit.setPlaceholderText("KML 파일 이름, 예: gnss_path")
        self.bag_kml_topic_edit.setPlaceholderText("/gnss/fix")

        self.csv_input_file_edit.setPlaceholderText("GNSS CSV 파일 경로")
        self.csv_output_dir_edit.setPlaceholderText("KML 출력 폴더 경로")
        self.csv_output_name_edit.setPlaceholderText("KML 파일 이름, 예: gnss_path")

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.shell = SensorPageShell(
            title_ko="GNSS",
            title_en="GNSS",
            description="GNSS rosbag 또는 CSV 데이터를 CSV/KML 형식으로 변환합니다.",
            icon_name="gnss",
            conversion_count=3,
            topics=["/gnss/fix"],
        )

        self.shell.add_mode(
            key="bag_csv",
            label="Bag → CSV",
            settings_widget=self._create_bag_csv_settings(),
            summary_widget=self.bag_csv_summary_panel,
            run_button=self.bag_csv_run_button,
        )

        self.shell.add_mode(
            key="bag_kml",
            label="Bag → KML",
            settings_widget=self._create_bag_kml_settings(),
            summary_widget=self.bag_kml_summary_panel,
            run_button=self.bag_kml_run_button,
        )

        self.shell.add_mode(
            key="csv_kml",
            label="CSV → KML",
            settings_widget=self._create_csv_kml_settings(),
            summary_widget=self.csv_kml_summary_panel,
            run_button=self.csv_run_button,
        )

        self.log_viewer.setReadOnly(True)
        self.shell.set_log_widget(self.log_viewer)

        root_layout.addWidget(self.shell)

        self.bag_csv_input_path_edit.textChanged.connect(self.shell.set_selected_source_path)
        self.bag_kml_input_path_edit.textChanged.connect(self.shell.set_selected_source_path)
        self.csv_input_file_edit.textChanged.connect(self.shell.set_selected_source_path)

        self.bag_csv_run_button.clicked.connect(self._run_bag_to_csv)
        self.bag_kml_run_button.clicked.connect(self._run_bag_to_kml)
        self.csv_run_button.clicked.connect(self._run_csv_to_kml)

    def _create_bag_csv_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(12)

        browse_input = QPushButton("Browse")
        browse_output = QPushButton("Browse")

        layout.addWidget(make_field_row(
            "입력 rosbag",
            "Input rosbag",
            make_path_input(self.bag_csv_input_path_edit, browse_input),
        ))
        layout.addWidget(make_field_row(
            "출력 폴더",
            "Output folder",
            make_path_input(self.bag_csv_output_dir_edit, browse_output),
        ))
        layout.addWidget(make_field_row("토픽", "Topic", self.bag_csv_topic_edit))
        layout.addStretch(1)

        browse_input.clicked.connect(self._browse_bag_csv_input_path)
        browse_output.clicked.connect(self._browse_bag_csv_output_dir)

        return widget

    def _create_bag_kml_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(12)

        browse_input = QPushButton("Browse")
        browse_output = QPushButton("Browse")

        layout.addWidget(make_field_row(
            "입력 rosbag",
            "Input rosbag",
            make_path_input(self.bag_kml_input_path_edit, browse_input),
        ))
        layout.addWidget(make_field_row(
            "출력 폴더",
            "Output folder",
            make_path_input(self.bag_kml_output_dir_edit, browse_output),
        ))
        layout.addWidget(make_field_row("KML 이름", "KML name", self.bag_kml_output_name_edit))
        layout.addWidget(make_field_row("토픽", "Topic", self.bag_kml_topic_edit))
        layout.addStretch(1)

        browse_input.clicked.connect(self._browse_bag_kml_input_path)
        browse_output.clicked.connect(self._browse_bag_kml_output_dir)

        return widget

    def _create_csv_kml_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(12)

        browse_input = QPushButton("Browse")
        browse_output = QPushButton("Browse")

        layout.addWidget(make_field_row(
            "입력 CSV",
            "Input CSV",
            make_path_input(self.csv_input_file_edit, browse_input),
        ))
        layout.addWidget(make_field_row(
            "출력 폴더",
            "Output folder",
            make_path_input(self.csv_output_dir_edit, browse_output),
        ))
        layout.addWidget(make_field_row("KML 이름", "KML name", self.csv_output_name_edit))
        layout.addStretch(1)

        browse_input.clicked.connect(self._browse_csv_input_file)
        browse_output.clicked.connect(self._browse_csv_output_dir)

        return widget

    def _connect_summary_signals(self) -> None:
        for editor in (
            self.bag_csv_input_path_edit,
            self.bag_csv_output_dir_edit,
            self.bag_csv_topic_edit,
            self.bag_kml_input_path_edit,
            self.bag_kml_output_dir_edit,
            self.bag_kml_output_name_edit,
            self.bag_kml_topic_edit,
            self.csv_input_file_edit,
            self.csv_output_dir_edit,
            self.csv_output_name_edit,
        ):
            editor.textChanged.connect(lambda *_: self._update_summary())
    
    
    def _update_summary(self) -> None:
        self.bag_csv_summary_panel.update_summary(
            sensor="GNSS",
            mode="bag → csv",
            input_path=self.bag_csv_input_path_edit.text(),
            output_path=self.bag_csv_output_dir_edit.text(),
            topic=self.bag_csv_topic_edit.text(),
            fmt="csv",
            extra="-",
        )
    
        self.bag_kml_summary_panel.update_summary(
            sensor="GNSS",
            mode="bag → kml",
            input_path=self.bag_kml_input_path_edit.text(),
            output_path=self._output_file_text(
                self.bag_kml_output_dir_edit.text(),
                self.bag_kml_output_name_edit.text(),
                ".kml",
            ),
            topic=self.bag_kml_topic_edit.text(),
            fmt="kml",
            extra="중간 CSV 유지",
        )
    
        self.csv_kml_summary_panel.update_summary(
            sensor="GNSS",
            mode="csv → kml",
            input_path=self.csv_input_file_edit.text(),
            output_path=self._output_file_text(
                self.csv_output_dir_edit.text(),
                self.csv_output_name_edit.text(),
                ".kml",
            ),
            topic="-",
            fmt="kml",
            extra="-",
        )
    
    
    @staticmethod
    def _output_file_text(output_dir: str, output_name: str, suffix: str) -> str:
        output_dir = output_dir.strip()
        output_name = output_name.strip()
    
        if output_name and not output_name.lower().endswith(suffix):
            output_name = f"{output_name}{suffix}"
    
        if output_dir and output_name:
            return str(Path(output_dir) / output_name)
    
        if output_name:
            return output_name
    
        return output_dir
    
    def _browse_bag_csv_input_path(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select rosbag folder")
        if selected_dir:
            self.bag_csv_input_path_edit.setText(selected_dir)

    def _browse_bag_csv_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
        if selected_dir:
            self.bag_csv_output_dir_edit.setText(selected_dir)

    def _browse_bag_kml_input_path(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select rosbag folder")
        if selected_dir:
            self.bag_kml_input_path_edit.setText(selected_dir)

            if not self.bag_kml_output_name_edit.text().strip():
                self.bag_kml_output_name_edit.setText(Path(selected_dir).name)

    def _browse_bag_kml_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
        if selected_dir:
            self.bag_kml_output_dir_edit.setText(selected_dir)

    def _browse_csv_input_file(self) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select GNSS CSV file",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )

        if selected_file:
            self.csv_input_file_edit.setText(selected_file)

            if not self.csv_output_name_edit.text().strip():
                self.csv_output_name_edit.setText(Path(selected_file).stem)

    def _browse_csv_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
        if selected_dir:
            self.csv_output_dir_edit.setText(selected_dir)

    def _normalize_output_name(self, output_name: str, suffix: str = ".kml") -> str:
        name = output_name.strip()

        if name.lower().endswith(suffix):
            name = name[: -len(suffix)]

        name = name.strip()

        if "/" in name or "\\" in name:
            raise ValueError("파일 이름에는 경로 구분자를 넣지 마세요. 파일 이름만 입력해야 합니다.")

        return name

    def _parse_topics(self, topic_text: str) -> list[str]:
        return [
            topic.strip()
            for topic in topic_text.replace(" ", ",").split(",")
            if topic.strip()
        ]

    def _validate_bag_common(
        self,
        input_path: str,
        output_dir: str,
        topic_text: str,
    ) -> list[str] | None:
        if not input_path:
            self._log("[ERROR] Input rosbag 폴더를 선택해야 합니다.")
            return None

        if not output_dir:
            self._log("[ERROR] Output 폴더를 선택해야 합니다.")
            return None

        if not topic_text:
            self._log("[ERROR] Topic을 입력해야 합니다.")
            return None

        input_path_obj = Path(input_path)

        if not input_path_obj.exists():
            self._log(f"[ERROR] 입력 경로가 존재하지 않습니다: {input_path}")
            return None

        if not input_path_obj.is_dir():
            self._log(f"[ERROR] rosbag 입력은 폴더여야 합니다: {input_path}")
            return None

        return self._parse_topics(topic_text)

    def _run_bag_to_csv(self) -> None:
        input_path = self.bag_csv_input_path_edit.text().strip()
        output_dir = self.bag_csv_output_dir_edit.text().strip()
        topic_text = self.bag_csv_topic_edit.text().strip()

        topics = self._validate_bag_common(input_path, output_dir, topic_text)
        if topics is None:
            return

        self._log("[INFO] GNSS Bag → CSV 변환 시작")
        self._log(f"[INFO] input: {input_path}")
        self._log(f"[INFO] output folder: {output_dir}")
        self._log(f"[INFO] topics: {topics}")

        self.bag_csv_run_button.setEnabled(False)

        try:
            from data_parser.sensors.gnss.bag_to_csv import extract_rosbag_to_csv

            extract_rosbag_to_csv(
                bag_path=input_path,
                output_dir=output_dir,
                topics=topics,
            )

            self._log("[DONE] GNSS Bag → CSV 변환 완료")

        except ImportError as exc:
            self._log("[ERROR] Bag → CSV 변환 함수를 import하지 못했습니다.")
            self._log(str(exc))

        except Exception as exc:
            self._log("[ERROR] GNSS Bag → CSV 변환 중 오류가 발생했습니다.")
            self._log(str(exc))

        finally:
            self.bag_csv_run_button.setEnabled(True)

    def _run_bag_to_kml(self) -> None:
        input_path = self.bag_kml_input_path_edit.text().strip()
        output_dir = self.bag_kml_output_dir_edit.text().strip()
        output_name = self.bag_kml_output_name_edit.text().strip()
        topic_text = self.bag_kml_topic_edit.text().strip()

        topics = self._validate_bag_common(input_path, output_dir, topic_text)
        if topics is None:
            return

        try:
            output_name = self._normalize_output_name(output_name, ".kml")
        except ValueError as exc:
            self._log(f"[ERROR] {exc}")
            return

        if not output_name:
            self._log("[ERROR] KML 파일 이름을 입력해야 합니다.")
            return

        self._log("[INFO] GNSS Bag → KML 변환 시작")
        self._log(f"[INFO] input: {input_path}")
        self._log(f"[INFO] output folder: {output_dir}")
        self._log(f"[INFO] topics: {topics}")
        self._log(f"[INFO] kml name: {output_name}")

        self.bag_kml_run_button.setEnabled(False)

        try:
            from data_parser.sensors.gnss.bag_to_kml import convert_gnss_bag_to_kml

            result = convert_gnss_bag_to_kml(
                bag_path=input_path,
                output_path=output_dir,
                output_name=output_name,
                topics=topics,
                keep_csv=True,
            )

            self._log(f"[DONE] CSV 저장: {result['csv_path']}")
            self._log(f"[DONE] KML 저장: {result['kml_path']}")
            self._log("[DONE] GNSS Bag → KML 변환 완료")

        except ImportError as exc:
            self._log("[ERROR] Bag → KML 변환 함수를 import하지 못했습니다.")
            self._log(str(exc))

        except Exception as exc:
            self._log("[ERROR] GNSS Bag → KML 변환 중 오류가 발생했습니다.")
            self._log(str(exc))

        finally:
            self.bag_kml_run_button.setEnabled(True)

    def _run_csv_to_kml(self) -> None:
        csv_path = self.csv_input_file_edit.text().strip()
        output_dir = self.csv_output_dir_edit.text().strip()
        output_name = self.csv_output_name_edit.text().strip()

        if not csv_path:
            self._log("[ERROR] Input CSV 파일을 선택해야 합니다.")
            return

        if not output_dir:
            self._log("[ERROR] Output 폴더를 선택해야 합니다.")
            return

        if not output_name:
            self._log("[ERROR] KML 파일 이름을 입력해야 합니다.")
            return

        csv_path_obj = Path(csv_path)

        if not csv_path_obj.exists():
            self._log(f"[ERROR] CSV 파일이 존재하지 않습니다: {csv_path}")
            return

        if not csv_path_obj.is_file():
            self._log(f"[ERROR] CSV 입력은 파일이어야 합니다: {csv_path}")
            return

        try:
            output_name = self._normalize_output_name(output_name, ".kml")
        except ValueError as exc:
            self._log(f"[ERROR] {exc}")
            return

        if not output_name:
            self._log("[ERROR] KML 파일 이름을 입력해야 합니다.")
            return

        self._log("[INFO] CSV → KML 변환 시작")
        self._log(f"[INFO] input csv: {csv_path}")
        self._log(f"[INFO] output folder: {output_dir}")
        self._log(f"[INFO] kml name: {output_name}")

        self.csv_run_button.setEnabled(False)

        try:
            from data_parser.sensors.gnss.csv_to_kml import csv_to_kml

            output_kml_path = csv_to_kml(
                input_csv=csv_path,
                output_path=output_dir,
                output_name=output_name,
            )

            self._log(f"[DONE] KML 저장: {output_kml_path}")
            self._log("[DONE] CSV → KML 변환 완료")

        except ImportError as exc:
            self._log("[ERROR] CSV → KML 변환 함수를 import하지 못했습니다.")
            self._log(str(exc))
            self._log(
                "[HINT] data_parser/sensors/gnss/csv_to_kml.py 안에 "
                "csv_to_kml 함수가 필요합니다."
            )

        except Exception as exc:
            self._log("[ERROR] CSV → KML 변환 중 오류가 발생했습니다.")
            self._log(str(exc))

        finally:
            self.csv_run_button.setEnabled(True)

    def _log(self, message: str) -> None:
        self.log_viewer.append(message)