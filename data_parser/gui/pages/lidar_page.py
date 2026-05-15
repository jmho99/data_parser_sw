from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from data_parser.gui.widgets import (
    ChoiceBar,
    SensorPageShell,
    SummaryPanel,
    make_field_row,
    make_path_input,
)

class LiDARPage(QWidget):
    """
    LiDAR 변환 GUI 페이지.

    현재 지원:
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

        self.pcd_format_choice = ChoiceBar(
            [
                ("ascii", "ascii"),
                ("binary", "binary"),
            ],
            exclusive=True,
            default="ascii",
        )

        self.field_choice = ChoiceBar(
            [
                ("x", "x"),
                ("y", "y"),
                ("z", "z"),
                ("intensity", "intensity"),
                ("ring", "ring"),
                ("time", "time"),
                ("all fields", "all"),
                ("custom", "custom"),
            ],
            exclusive=False,
            checked_values=["x", "y", "z"],
            disabled_values=["x", "y", "z"],
        )

        self.custom_fields_edit = QLineEdit()

        self.every_n_spin = QSpinBox()
        self.start_index_spin = QSpinBox()
        self.end_index_spin = QSpinBox()
        self.use_end_index_check = QCheckBox("Use end index")
        self.skip_nans_check = QCheckBox("Skip NaN points")
        self.timestamp_filename_check = QCheckBox("Use timestamp filename")

        self.bag_pcd_summary_panel = SummaryPanel()

        self.run_button = QPushButton("Bag → PCD 변환 시작")
        self.log_viewer = QTextEdit()

        self._setup_default_values()
        self._setup_ui()
        self._update_field_ui()
        self._update_end_index_ui()

    def _setup_default_values(self) -> None:
        self.bag_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.output_dir_edit.setPlaceholderText("PCD 출력 폴더 경로")
        self.topic_edit.setPlaceholderText("/ouster/points")

        self.custom_fields_edit.setPlaceholderText("예: x,y,z,intensity,ring,t")

        self.every_n_spin.setRange(1, 1_000_000)
        self.every_n_spin.setValue(1)

        self.start_index_spin.setRange(0, 1_000_000_000)
        self.start_index_spin.setValue(0)

        self.end_index_spin.setRange(0, 1_000_000_000)
        self.end_index_spin.setValue(0)

        self.skip_nans_check.setChecked(True)
        self.timestamp_filename_check.setChecked(True)

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.shell = SensorPageShell(
            title_ko="라이다",
            title_en="LiDAR",
            description="LiDAR PointCloud2 rosbag 데이터를 PCD 파일로 변환합니다.",
            icon_name="lidar",
            conversion_count=1,
            topics=["/ouster/points"],
        )

        self.shell.add_mode(
            key="bag_pcd",
            label="Bag → PCD",
            settings_widget=self._create_bag_pcd_settings(),
            summary_widget=self.bag_pcd_summary_panel,
            run_button=self.run_button,
        )

        self.log_viewer.setReadOnly(True)
        self.shell.set_log_widget(self.log_viewer)

        root_layout.addWidget(self.shell)

        self.bag_input_path_edit.textChanged.connect(self.shell.set_selected_source_path)
        self.field_choice.changed.connect(self._update_field_ui)
        self.use_end_index_check.stateChanged.connect(self._update_end_index_ui)
        
        self._connect_summary_signals()
        self._update_summary()
        self.run_button.clicked.connect(self._run_conversion)

    def _create_bag_pcd_settings(self) -> QWidget:
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
            make_path_input(self.output_dir_edit, browse_output),
        ))
        layout.addWidget(make_field_row("토픽", "Topic", self.topic_edit))
        layout.addWidget(make_field_row("PCD 포맷", "PCD format", self.pcd_format_choice))
        layout.addWidget(make_field_row("필드 프리셋", "Fields", self.field_choice))
        layout.addWidget(make_field_row("사용자 필드", "Custom fields", self.custom_fields_edit))
        layout.addWidget(make_field_row("프레임 간격", "Every N frames", self.every_n_spin))
        layout.addWidget(make_field_row("시작 인덱스", "Start index", self.start_index_spin))
        layout.addWidget(make_field_row("종료 사용", "Use end index", self.use_end_index_check))
        layout.addWidget(make_field_row("종료 인덱스", "End index", self.end_index_spin))
        layout.addWidget(make_field_row("NaN 제거", "Skip NaN points", self.skip_nans_check))
        layout.addWidget(make_field_row("파일명", "Timestamp filename", self.timestamp_filename_check))
        layout.addStretch(1)

        browse_input.clicked.connect(self._browse_bag_input_path)
        browse_output.clicked.connect(self._browse_output_dir)

        return widget

    def _browse_bag_input_path(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select rosbag folder")

        if selected_dir:
            self.bag_input_path_edit.setText(selected_dir)

            if not self.output_dir_edit.text().strip():
                self.output_dir_edit.setText(str(Path(selected_dir) / "pcd"))

    def _browse_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select output folder")

        if selected_dir:
            self.output_dir_edit.setText(selected_dir)

    def _update_field_ui(self) -> None:
        selected = self.field_choice.selected_values()
        is_custom = "custom" in selected and "all" not in selected
        self.custom_fields_edit.setEnabled(is_custom)

    def _connect_summary_signals(self) -> None:
        for editor in (
            self.bag_input_path_edit,
            self.output_dir_edit,
            self.topic_edit,
            self.custom_fields_edit,
        ):
            editor.textChanged.connect(lambda *_: self._update_summary())
    
        for choice in (
            self.pcd_format_choice,
            self.field_choice,
        ):
            choice.changed.connect(lambda *_: self._update_summary())
    
        for spin in (
            self.every_n_spin,
            self.start_index_spin,
            self.end_index_spin,
        ):
            spin.valueChanged.connect(lambda *_: self._update_summary())
    
        for checkbox in (
            self.use_end_index_check,
            self.skip_nans_check,
            self.timestamp_filename_check,
        ):
            checkbox.stateChanged.connect(lambda *_: self._update_summary())

    
    def _update_summary(self) -> None:
        pcd_format = self.pcd_format_choice.selected_value() or "ascii"
    
        self.bag_pcd_summary_panel.update_summary(
            sensor="LiDAR",
            mode="bag → pcd",
            input_path=self.bag_input_path_edit.text(),
            output_path=self.output_dir_edit.text(),
            topic=self.topic_edit.text(),
            fmt=pcd_format,
            extra=(
                f"저장 필드: {self._selected_fields_text()}; "
                f"프레임 간격: {self.every_n_spin.value()}; "
                f"시작 인덱스: {self.start_index_spin.value()}; "
                f"종료 인덱스: {self._end_index_text()}; "
                f"NaN 제거: {self._bool_text(self.skip_nans_check.isChecked())}; "
                f"파일명: {self._filename_mode_text()}"
            ),
        )


    def _selected_fields_text(self) -> str:
        selected = self.field_choice.selected_values()
    
        if "all" in selected:
            return "all fields"
    
        fields = [
            field
            for field in ["x", "y", "z", "intensity", "ring", "time"]
            if field in selected
        ]
    
        if "custom" in selected:
            custom_text = self.custom_fields_edit.text().strip()
    
            if custom_text:
                custom_fields = [
                    field.strip()
                    for field in custom_text.replace(" ", ",").split(",")
                    if field.strip()
                ]
    
                for field in custom_fields:
                    if field not in fields:
                        fields.append(field)
            else:
                fields.append("custom 입력 필요")
    
        return ", ".join(fields) if fields else "-"
    
    
    def _end_index_text(self) -> str:
        if not self.use_end_index_check.isChecked():
            return "사용 안 함"
    
        return str(self.end_index_spin.value())
    
    
    @staticmethod
    def _bool_text(value: bool) -> str:
        return "사용" if value else "미사용"
    
    
    def _filename_mode_text(self) -> str:
        if self.timestamp_filename_check.isChecked():
            return "timestamp"
    
        return "index"
    
    def _update_end_index_ui(self) -> None:
        self.end_index_spin.setEnabled(self.use_end_index_check.isChecked())

    def _selected_fields(self) -> list[str] | str:
        selected = self.field_choice.selected_values()

        if "all" in selected:
            return "all"

        fields = [
            field
            for field in ["x", "y", "z", "intensity", "ring", "time"]
            if field in selected
        ]

        if "custom" in selected:
            custom_text = self.custom_fields_edit.text().strip()

            if not custom_text:
                raise ValueError("Custom fields를 선택한 경우 필드명을 입력해야 합니다.")

            custom_fields = [
                field.strip()
                for field in custom_text.replace(" ", ",").split(",")
                if field.strip()
            ]

            if not custom_fields:
                raise ValueError("Custom fields를 입력해야 합니다.")

            for field in custom_fields:
                if field not in fields:
                    fields.append(field)

        if not fields:
            raise ValueError("저장할 필드를 하나 이상 선택해야 합니다.")

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
        pcd_format = self.pcd_format_choice.selected_value() or "ascii"

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
            from data_parser.sensors.lidar.bag_to_pcd import extract_lidar_bag_to_pcd

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