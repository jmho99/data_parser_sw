from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class GNSSPage(QWidget):
    """
    GNSS 변환 GUI 페이지.

    탭 구성:
    - Bag → CSV/KML
    - CSV → KML
    """

    def __init__(self) -> None:
        super().__init__()

        # Bag → CSV/KML 탭
        self.bag_input_path_edit = QLineEdit()
        self.bag_output_dir_edit = QLineEdit()
        self.bag_topic_edit = QLineEdit("/gnss/fix")
        self.bag_format_combo = QComboBox()
        self.bag_run_button = QPushButton("Run Bag Convert")

        # CSV → KML 탭
        self.csv_input_file_edit = QLineEdit()
        self.csv_output_dir_edit = QLineEdit()
        self.csv_output_name_edit = QLineEdit()
        self.csv_run_button = QPushButton("Run CSV to KML")

        # 공통 로그
        self.log_viewer = QTextEdit()

        self._setup_ui()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 32, 36, 32)
        root_layout.setSpacing(18)

        title_label = QLabel("GNSS Converter")
        title_label.setObjectName("PageTitle")

        description_label = QLabel(
            "GNSS rosbag 또는 CSV 데이터를 CSV/KML 형식으로 변환합니다."
        )
        description_label.setObjectName("PageDescription")

        root_layout.addWidget(title_label)
        root_layout.addWidget(description_label)

        tab_widget = QTabWidget()
        tab_widget.addTab(self._create_bag_convert_tab(), "Bag → CSV/KML")
        tab_widget.addTab(self._create_csv_to_kml_tab(), "CSV → KML")

        root_layout.addWidget(tab_widget)

        log_label = QLabel("Log")
        log_label.setObjectName("SectionTitle")
        root_layout.addWidget(log_label)

        self.log_viewer.setReadOnly(True)
        self.log_viewer.setMinimumHeight(220)
        root_layout.addWidget(self.log_viewer, stretch=1)

    def _create_bag_convert_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(14)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(12)

        bag_input_layout = QHBoxLayout()
        bag_input_browse_button = QPushButton("Browse")
        bag_input_layout.addWidget(self.bag_input_path_edit)
        bag_input_layout.addWidget(bag_input_browse_button)

        bag_output_layout = QHBoxLayout()
        bag_output_browse_button = QPushButton("Browse")
        bag_output_layout.addWidget(self.bag_output_dir_edit)
        bag_output_layout.addWidget(bag_output_browse_button)

        self.bag_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.bag_output_dir_edit.setPlaceholderText("출력 폴더 경로")
        self.bag_topic_edit.setPlaceholderText("/gnss/fix")

        self.bag_format_combo.addItems(["csv", "kml"])

        form_layout.addRow("Input rosbag", bag_input_layout)
        form_layout.addRow("Output folder", bag_output_layout)
        form_layout.addRow("Topic", self.bag_topic_edit)
        form_layout.addRow("Format", self.bag_format_combo)

        layout.addWidget(form_widget)

        self.bag_run_button.setFixedHeight(38)
        layout.addWidget(self.bag_run_button)
        layout.addStretch()

        bag_input_browse_button.clicked.connect(self._browse_bag_input_path)
        bag_output_browse_button.clicked.connect(self._browse_bag_output_dir)
        self.bag_run_button.clicked.connect(self._run_bag_conversion)

        return tab

    def _create_csv_to_kml_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(14)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(12)

        csv_input_layout = QHBoxLayout()
        csv_input_browse_button = QPushButton("Browse")
        csv_input_layout.addWidget(self.csv_input_file_edit)
        csv_input_layout.addWidget(csv_input_browse_button)

        csv_output_layout = QHBoxLayout()
        csv_output_browse_button = QPushButton("Browse")
        csv_output_layout.addWidget(self.csv_output_dir_edit)
        csv_output_layout.addWidget(csv_output_browse_button)

        self.csv_input_file_edit.setPlaceholderText("GNSS CSV 파일 경로")
        self.csv_output_dir_edit.setPlaceholderText("KML 출력 폴더 경로")
        self.csv_output_name_edit.setPlaceholderText("KML 파일 이름, 예: gnss_path")

        form_layout.addRow("Input CSV", csv_input_layout)
        form_layout.addRow("Output folder", csv_output_layout)
        form_layout.addRow("KML name", self.csv_output_name_edit)

        layout.addWidget(form_widget)

        self.csv_run_button.setFixedHeight(38)
        layout.addWidget(self.csv_run_button)
        layout.addStretch()

        csv_input_browse_button.clicked.connect(self._browse_csv_input_file)
        csv_output_browse_button.clicked.connect(self._browse_csv_output_dir)
        self.csv_run_button.clicked.connect(self._run_csv_to_kml)

        return tab

    def _browse_bag_input_path(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select rosbag folder",
        )

        if selected_dir:
            self.bag_input_path_edit.setText(selected_dir)

    def _browse_bag_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
        )

        if selected_dir:
            self.bag_output_dir_edit.setText(selected_dir)

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
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
        )

        if selected_dir:
            self.csv_output_dir_edit.setText(selected_dir)

    def _run_bag_conversion(self) -> None:
        input_path = self.bag_input_path_edit.text().strip()
        output_dir = self.bag_output_dir_edit.text().strip()
        topic_text = self.bag_topic_edit.text().strip()
        export_format = self.bag_format_combo.currentText()

        if not input_path:
            self._log("[ERROR] Input rosbag 폴더를 선택해야 합니다.")
            return

        if not output_dir:
            self._log("[ERROR] Output 폴더를 선택해야 합니다.")
            return

        if not topic_text:
            self._log("[ERROR] Topic을 입력해야 합니다.")
            return

        input_path_obj = Path(input_path)

        if not input_path_obj.exists():
            self._log(f"[ERROR] 입력 경로가 존재하지 않습니다: {input_path}")
            return

        if not input_path_obj.is_dir():
            self._log(f"[ERROR] rosbag 입력은 폴더여야 합니다: {input_path}")
            return

        topics = [topic.strip() for topic in topic_text.split(",") if topic.strip()]

        self._log("[INFO] Bag 변환 시작")
        self._log(f"[INFO] input: {input_path}")
        self._log(f"[INFO] output: {output_dir}")
        self._log(f"[INFO] topics: {topics}")
        self._log(f"[INFO] format: {export_format}")

        self.bag_run_button.setEnabled(False)

        try:
            if export_format == "csv":
                from data_parser.sensors.gnss.bag_to_csv import (
                    extract_rosbag_to_csv,
                )

                extract_rosbag_to_csv(
                    bag_path=input_path,
                    output_dir=output_dir,
                    topics=topics,
                )

            elif export_format == "kml":
                from data_parser.sensors.gnss.bag_to_kml import (
                    convert_gnss_bag_to_kml,
                )

                convert_gnss_bag_to_kml(
                    bag_path=input_path,
                    output_dir=output_dir,
                    topics=topics,
                )

            else:
                self._log(f"[ERROR] 지원하지 않는 형식입니다: {export_format}")
                return

            self._log("[DONE] Bag 변환 완료")

        except ImportError as exc:
            self._log("[ERROR] Bag 변환 함수를 import하지 못했습니다.")
            self._log(str(exc))

        except Exception as exc:
            self._log("[ERROR] Bag 변환 중 오류가 발생했습니다.")
            self._log(str(exc))

        finally:
            self.bag_run_button.setEnabled(True)

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
        output_dir_obj = Path(output_dir)

        if not csv_path_obj.exists():
            self._log(f"[ERROR] CSV 파일이 존재하지 않습니다: {csv_path}")
            return

        if not csv_path_obj.is_file():
            self._log(f"[ERROR] CSV 입력은 파일이어야 합니다: {csv_path}")
            return

        if "/" in output_name or "\\" in output_name:
            self._log("[ERROR] KML 이름에는 경로 구분자를 넣지 마세요. 파일 이름만 입력해야 합니다.")
            return

        if output_name.lower().endswith(".kml"):
            output_name = output_name[:-4]

        output_dir_obj.mkdir(parents=True, exist_ok=True)
        output_kml_path = output_dir_obj / f"{output_name}.kml"

        self._log("[INFO] CSV → KML 변환 시작")
        self._log(f"[INFO] input csv: {csv_path}")
        self._log(f"[INFO] output kml: {output_kml_path}")

        self.csv_run_button.setEnabled(False)

        try:
            from data_parser.sensors.gnss.bag_to_kml import (
                fix_csv_to_kml,
            )
    
            fix_csv_to_kml(
                input_csv=csv_path,
                output_kml=str(output_kml_path),
            )
    
            self._log("[DONE] CSV → KML 변환 완료")

        except ImportError as exc:
            self._log("[ERROR] CSV → KML 변환 함수를 import하지 못했습니다.")
            self._log(str(exc))
            self._log(
                "[HINT] data_parser/sensors/gnss/csv_to_kml.py 안에 "
                "convert_gnss_csv_to_kml 함수가 필요합니다."
            )

        except Exception as exc:
            self._log("[ERROR] CSV → KML 변환 중 오류가 발생했습니다.")
            self._log(str(exc))

        finally:
            self.csv_run_button.setEnabled(True)

    def _log(self, message: str) -> None:
        self.log_viewer.append(message)