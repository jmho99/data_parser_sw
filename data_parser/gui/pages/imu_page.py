from __future__ import annotations

import re
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
        self.bag_run_button = QPushButton("Bag → CSV 변환 시작")

        self.log_viewer = QTextEdit()
        self.bag_csv_summary_panel = SummaryPanel()

        self._setup_default_values()
        self._setup_ui()
        self._connect_summary_signals()
        self._update_summary()

    def _setup_default_values(self) -> None:
        self.bag_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.bag_output_dir_edit.setPlaceholderText("출력 폴더 경로")
        self.bag_topic_edit.setPlaceholderText("/imu/data 또는 /imu/raw")

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.shell = SensorPageShell(
            title_ko="IMU",
            title_en="IMU",
            description=(
                "IMU rosbag 데이터를 CSV 형식으로 변환합니다. "
                "orientation, angular velocity, linear acceleration을 모두 저장합니다."
            ),
            icon_name="imu",
            conversion_count=1,
            topics=["/imu/data", "/imu/raw"],
        )

        self.shell.add_mode(
            key="bag_csv",
            label="Bag → CSV",
            settings_widget=self._create_bag_csv_settings(),
            summary_widget=self.bag_csv_summary_panel,
            run_button=self.bag_run_button,
        )

        self.log_viewer.setReadOnly(True)
        self.shell.set_log_widget(self.log_viewer)

        root_layout.addWidget(self.shell)

        self.bag_input_path_edit.textChanged.connect(self.shell.set_selected_source_path)
        self.bag_run_button.clicked.connect(self._run_bag_to_csv)

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
            make_path_input(self.bag_input_path_edit, browse_input),
        ))
        layout.addWidget(make_field_row(
            "출력 폴더",
            "Output folder",
            make_path_input(self.bag_output_dir_edit, browse_output),
        ))
        layout.addWidget(make_field_row("토픽", "Topic", self.bag_topic_edit))
        layout.addStretch(1)

        browse_input.clicked.connect(self._browse_bag_input_path)
        browse_output.clicked.connect(self._browse_bag_output_dir)

        return widget

    def _connect_summary_signals(self) -> None:
        for editor in (
            self.bag_input_path_edit,
            self.bag_output_dir_edit,
            self.bag_topic_edit,
        ):
            editor.textChanged.connect(lambda *_: self._update_summary())
    
    
    def _update_summary(self) -> None:
        self.bag_csv_summary_panel.update_summary(
            sensor="IMU",
            mode="bag → csv",
            input_path=self.bag_input_path_edit.text(),
            output_path=self.bag_output_dir_edit.text(),
            topic=self.bag_topic_edit.text(),
            fmt="csv",
            extra="저장 항목: orientation, angular_velocity, linear_acceleration",
        )
    
    def _browse_bag_input_path(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select rosbag folder")
        if selected_dir:
            self.bag_input_path_edit.setText(selected_dir)

    def _browse_bag_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
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