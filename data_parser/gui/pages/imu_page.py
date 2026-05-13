from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class IMUPage(QWidget):
    """
    IMU 변환 GUI 페이지.

    현재 지원:
    - Bag → CSV
    """

    def __init__(self) -> None:
        super().__init__()

        self.bag_input_path_edit = QLineEdit()
        self.bag_output_dir_edit = QLineEdit()
        self.bag_topic_edit = QLineEdit("/imu/data")
        self.bag_run_button = QPushButton("Run Bag to CSV")

        self.log_viewer = QTextEdit()

        self._setup_ui()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 32, 36, 32)
        root_layout.setSpacing(18)

        title_label = QLabel("IMU Converter")
        title_label.setObjectName("PageTitle")

        description_label = QLabel(
            "IMU rosbag 데이터를 CSV 형식으로 변환합니다. "
            "orientation, angular velocity, linear acceleration을 모두 저장합니다."
        )
        description_label.setObjectName("PageDescription")
        description_label.setWordWrap(True)

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

        bag_output_layout = QHBoxLayout()
        bag_output_browse_button = QPushButton("Browse")
        bag_output_layout.addWidget(self.bag_output_dir_edit)
        bag_output_layout.addWidget(bag_output_browse_button)

        self.bag_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.bag_output_dir_edit.setPlaceholderText("출력 폴더 경로")
        self.bag_topic_edit.setPlaceholderText("/imu/data 또는 /imu/raw")

        form_layout.addRow("Input rosbag", bag_input_layout)
        form_layout.addRow("Output folder", bag_output_layout)
        form_layout.addRow("Topic", self.bag_topic_edit)

        root_layout.addWidget(form_widget)

        self.bag_run_button.setFixedHeight(38)
        root_layout.addWidget(self.bag_run_button)

        log_label = QLabel("Log")
        log_label.setObjectName("SectionTitle")
        root_layout.addWidget(log_label)

        self.log_viewer.setReadOnly(True)
        self.log_viewer.setMinimumHeight(260)
        root_layout.addWidget(self.log_viewer, stretch=1)

        bag_input_browse_button.clicked.connect(self._browse_bag_input_path)
        bag_output_browse_button.clicked.connect(self._browse_bag_output_dir)
        self.bag_run_button.clicked.connect(self._run_bag_to_csv)

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

    def _parse_topics(self, topic_text: str) -> list[str]:
        return [
            topic.strip()
            for topic in re.split(r"[,\s]+", topic_text)
            if topic.strip()
        ]

    def _run_bag_to_csv(self) -> None:
        input_path = self.bag_input_path_edit.text().strip()
        output_dir = self.bag_output_dir_edit.text().strip()
        topic_text = self.bag_topic_edit.text().strip()

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

        topics = self._parse_topics(topic_text)

        self._log("[INFO] IMU Bag → CSV 변환 시작")
        self._log(f"[INFO] input: {input_path}")
        self._log(f"[INFO] output folder: {output_dir}")
        self._log(f"[INFO] topics: {topics}")
        self._log("[INFO] fields: orientation, angular_velocity, linear_acceleration")

        self.bag_run_button.setEnabled(False)

        try:
            from data_parser.sensors.imu.bag_to_csv import extract_imu_rosbag_to_csv

            output_paths = extract_imu_rosbag_to_csv(
                bag_path=input_path,
                output_dir=output_dir,
                topics=topics,
                include_covariance=False,
            )

            if output_paths:
                for output_path in output_paths:
                    self._log(f"[DONE] CSV 저장: {output_path}")
                self._log("[DONE] IMU Bag → CSV 변환 완료")
            else:
                self._log("[WARN] 저장된 CSV가 없습니다.")
                self._log("[HINT] Topic 이름과 메시지 타입(sensor_msgs/msg/Imu)을 확인하세요.")

        except ImportError as exc:
            self._log("[ERROR] IMU 변환 함수를 import하지 못했습니다.")
            self._log(str(exc))
            self._log(
                "[HINT] data_parser/sensors/imu/bag_to_csv.py 파일과 "
                "extract_imu_rosbag_to_csv 함수가 필요합니다."
            )

        except Exception as exc:
            self._log("[ERROR] IMU Bag → CSV 변환 중 오류가 발생했습니다.")
            self._log(str(exc))

        finally:
            self.bag_run_button.setEnabled(True)

    def _log(self, message: str) -> None:
        self.log_viewer.append(message)