from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class LiDARPage(QWidget):
    """
    LiDAR 변환 GUI 페이지.

    현재 기능:
    - Bag → PCD
    - PointCloud2 topic 입력
    - ascii/binary PCD 저장 선택
    - field preset/custom 선택
    - 프레임 간격 저장
    """

    def __init__(self) -> None:
        super().__init__()

        self.bag_input_path_edit = QLineEdit()
        self.output_dir_edit = QLineEdit()
        self.topic_edit = QLineEdit("/ouster/points")

        self.pcd_format_combo = QComboBox()
        self.field_preset_combo = QComboBox()
        self.custom_fields_edit = QLineEdit()

        self.every_n_spin = QSpinBox()
        self.start_index_spin = QSpinBox()
        self.end_index_spin = QSpinBox()
        self.use_end_index_check = QCheckBox("Use end index")
        self.skip_nans_check = QCheckBox("Skip NaN points")
        self.timestamp_filename_check = QCheckBox("Use timestamp filename")

        self.run_button = QPushButton("Run Bag to PCD")
        self.log_viewer = QTextEdit()

        self._setup_ui()
        self._update_field_ui()
        self._update_end_index_ui()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 32, 36, 32)
        root_layout.setSpacing(18)

        title_label = QLabel("LiDAR Converter")
        title_label.setObjectName("PageTitle")

        description_label = QLabel(
            "LiDAR PointCloud2 rosbag 데이터를 PCD 파일로 변환합니다."
        )
        description_label.setObjectName("PageDescription")

        root_layout.addWidget(title_label)
        root_layout.addWidget(description_label)

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

        output_layout = QHBoxLayout()
        output_browse_button = QPushButton("Browse")
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(output_browse_button)

        self.bag_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.output_dir_edit.setPlaceholderText("PCD 출력 폴더 경로")
        self.topic_edit.setPlaceholderText("/ouster/points")

        self.pcd_format_combo.addItems(["ascii", "binary"])
        self.field_preset_combo.addItems(
            [
                "xyz",
                "xyz + intensity",
                "xyz + intensity + ring",
                "xyz + intensity + ring + time",
                "all fields",
                "custom",
            ]
        )
        self.custom_fields_edit.setPlaceholderText("예: x,y,z,intensity,ring,t")

        self.every_n_spin.setRange(1, 1_000_000)
        self.every_n_spin.setValue(1)

        self.start_index_spin.setRange(0, 1_000_000_000)
        self.start_index_spin.setValue(0)

        self.end_index_spin.setRange(0, 1_000_000_000)
        self.end_index_spin.setValue(0)

        self.skip_nans_check.setChecked(True)
        self.timestamp_filename_check.setChecked(True)

        form_layout.addRow("Input rosbag", bag_input_layout)
        form_layout.addRow("Output folder", output_layout)
        form_layout.addRow("Topic", self.topic_edit)
        form_layout.addRow("PCD format", self.pcd_format_combo)
        form_layout.addRow("Fields", self.field_preset_combo)
        form_layout.addRow("Custom fields", self.custom_fields_edit)
        form_layout.addRow("Every N frames", self.every_n_spin)
        form_layout.addRow("Start index", self.start_index_spin)
        form_layout.addRow("", self.use_end_index_check)
        form_layout.addRow("End index", self.end_index_spin)
        form_layout.addRow("", self.skip_nans_check)
        form_layout.addRow("", self.timestamp_filename_check)

        root_layout.addWidget(form_widget)

        self.run_button.setFixedHeight(38)
        root_layout.addWidget(self.run_button)

        log_label = QLabel("Log")
        log_label.setObjectName("SectionTitle")
        root_layout.addWidget(log_label)

        self.log_viewer.setReadOnly(True)
        self.log_viewer.setMinimumHeight(220)
        root_layout.addWidget(self.log_viewer, stretch=1)

        bag_input_browse_button.clicked.connect(self._browse_bag_input_path)
        output_browse_button.clicked.connect(self._browse_output_dir)
        self.field_preset_combo.currentTextChanged.connect(self._update_field_ui)
        self.use_end_index_check.stateChanged.connect(self._update_end_index_ui)
        self.run_button.clicked.connect(self._run_conversion)

    def _browse_bag_input_path(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select rosbag folder",
        )

        if selected_dir:
            self.bag_input_path_edit.setText(selected_dir)

            if not self.output_dir_edit.text().strip():
                self.output_dir_edit.setText(str(Path(selected_dir) / "pcd"))

    def _browse_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
        )

        if selected_dir:
            self.output_dir_edit.setText(selected_dir)

    def _update_field_ui(self) -> None:
        is_custom = self.field_preset_combo.currentText() == "custom"
        self.custom_fields_edit.setEnabled(is_custom)

    def _update_end_index_ui(self) -> None:
        self.end_index_spin.setEnabled(self.use_end_index_check.isChecked())

    def _selected_fields(self) -> list[str] | str:
        preset = self.field_preset_combo.currentText()

        if preset == "xyz":
            return ["x", "y", "z"]

        if preset == "xyz + intensity":
            return ["x", "y", "z", "intensity"]

        if preset == "xyz + intensity + ring":
            return ["x", "y", "z", "intensity", "ring"]

        if preset == "xyz + intensity + ring + time":
            return ["x", "y", "z", "intensity", "ring", "time"]

        if preset == "all fields":
            return "all"

        custom_text = self.custom_fields_edit.text().strip()

        if not custom_text:
            raise ValueError("Custom fields를 입력해야 합니다.")

        fields = [
            field.strip()
            for field in custom_text.replace(" ", ",").split(",")
            if field.strip()
        ]

        if not fields:
            raise ValueError("Custom fields를 입력해야 합니다.")

        return fields

    def _parse_topics(self, topic_text: str) -> list[str]:
        return [
            topic.strip()
            for topic in topic_text.split(",")
            if topic.strip()
        ]

    def _run_conversion(self) -> None:
        input_path = self.bag_input_path_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()
        topic_text = self.topic_edit.text().strip()
        pcd_format = self.pcd_format_combo.currentText()

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

        try:
            fields = self._selected_fields()
        except ValueError as exc:
            self._log(f"[ERROR] {exc}")
            return

        topics = self._parse_topics(topic_text)
        end_index = (
            self.end_index_spin.value()
            if self.use_end_index_check.isChecked()
            else None
        )

        self._log("[INFO] LiDAR Bag → PCD 변환 시작")
        self._log(f"[INFO] input: {input_path}")
        self._log(f"[INFO] output folder: {output_dir}")
        self._log(f"[INFO] topics: {topics}")
        self._log(f"[INFO] pcd format: {pcd_format}")
        self._log(f"[INFO] fields: {fields}")
        self._log(f"[INFO] every_n: {self.every_n_spin.value()}")

        self.run_button.setEnabled(False)

        try:
            from data_parser.sensors.lidar.bag_to_pcd import (
                extract_lidar_bag_to_pcd,
            )

            result = extract_lidar_bag_to_pcd(
                bag_path=input_path,
                output_dir=output_dir,
                topics=topics,
                pcd_format=pcd_format,
                fields=fields,
                every_n=self.every_n_spin.value(),
                start_index=self.start_index_spin.value(),
                end_index=end_index,
                storage_id="auto",
                skip_nans=self.skip_nans_check.isChecked(),
                use_timestamp_filename=self.timestamp_filename_check.isChecked(),
            )

            self._log(f"[DONE] 저장 프레임 수: {result['saved_frames']}")
            self._log(f"[DONE] 출력 폴더: {result['output_dir']}")
            self._log("[DONE] LiDAR Bag → PCD 변환 완료")

        except ImportError as exc:
            self._log("[ERROR] LiDAR 변환 함수를 import하지 못했습니다.")
            self._log(str(exc))

        except Exception as exc:
            self._log("[ERROR] LiDAR 변환 중 오류가 발생했습니다.")
            self._log(str(exc))

        finally:
            self.run_button.setEnabled(True)

    def _log(self, message: str) -> None:
        self.log_viewer.append(message)