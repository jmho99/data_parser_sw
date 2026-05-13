from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from data_parser.sensors.camera.bag_to_img import bag_to_img
from data_parser.sensors.camera.bag_to_video import bag_to_video
from data_parser.sensors.camera.video_to_img import video_to_img


DEFAULT_CAMERA_CONFIG = {
    "formats": {
        "image": ["png", "jpg"],
        "video": ["mp4", "avi", "webm", "mkv"],
    },
    "defaults": {
        "image_format": "png",
        "video_format": "mp4",
        "video_fps": 10,
        "every_n": 1,
    },
    "video_codecs": {
        "mp4": "mp4v",
        "avi": "MJPG",
        "webm": "VP80",
        "mkv": "XVID",
    },
}


def load_camera_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[3] / "configs" / "camera.yaml"

    if not config_path.exists():
        return DEFAULT_CAMERA_CONFIG

    try:
        import yaml
    except ImportError:
        return DEFAULT_CAMERA_CONFIG

    try:
        with config_path.open("r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
    except Exception:
        return DEFAULT_CAMERA_CONFIG

    return {
        "formats": {
            **DEFAULT_CAMERA_CONFIG["formats"],
            **(loaded.get("formats") or {}),
        },
        "defaults": {
            **DEFAULT_CAMERA_CONFIG["defaults"],
            **(loaded.get("defaults") or {}),
        },
        "video_codecs": {
            **DEFAULT_CAMERA_CONFIG["video_codecs"],
            **(loaded.get("video_codecs") or {}),
        },
    }


class BagConvertWorker(QThread):
    log = Signal(str)
    finished_ok = Signal(str)
    finished_error = Signal(str)

    def __init__(
        self,
        output_type: str,
        bag_path: str,
        output_dir: str,
        topics: list[str] | None,
        output_format: str,
        every_n: int,
        max_frames: int | None,
        fps: float,
        codec: str | None,
    ) -> None:
        super().__init__()
        self.output_type = output_type
        self.bag_path = bag_path
        self.output_dir = output_dir
        self.topics = topics
        self.output_format = output_format
        self.every_n = every_n
        self.max_frames = max_frames
        self.fps = fps
        self.codec = codec

    def run(self) -> None:
        try:
            if self.output_type == "image":
                result = bag_to_img(
                    bag_path=self.bag_path,
                    output_dir=self.output_dir,
                    topics=self.topics,
                    output_format=self.output_format,
                    every_n=self.every_n,
                    max_frames=self.max_frames,
                    log_callback=self.log.emit,
                )

                self.finished_ok.emit(
                    f"Bag → Image 변환 완료\n"
                    f"저장 위치: {result.output_dir}\n"
                    f"저장 이미지 수: {result.saved_count}"
                )
                return

            if self.output_type == "video":
                result = bag_to_video(
                    bag_path=self.bag_path,
                    output_dir=self.output_dir,
                    topics=self.topics,
                    output_format=self.output_format,
                    fps=self.fps,
                    codec=self.codec,
                    every_n=self.every_n,
                    max_frames=self.max_frames,
                    log_callback=self.log.emit,
                )

                video_lines = [
                    f"{topic}: {path}"
                    for topic, path in result.video_paths.items()
                ]

                self.finished_ok.emit(
                    "Bag → Video 변환 완료\n"
                    f"저장 위치: {result.output_dir}\n"
                    f"저장 프레임 수: {result.saved_count}\n"
                    + "\n".join(video_lines)
                )
                return

            raise RuntimeError(f"지원하지 않는 변환 타입입니다: {self.output_type}")

        except Exception as exc:
            self.finished_error.emit(str(exc))


class VideoToImgWorker(QThread):
    log = Signal(str)
    finished_ok = Signal(str)
    finished_error = Signal(str)

    def __init__(
        self,
        video_path: str,
        output_dir: str,
        output_format: str,
        every_n: int,
        max_frames: int | None,
        start_time_sec: float,
        end_time_sec: float | None,
    ) -> None:
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.output_format = output_format
        self.every_n = every_n
        self.max_frames = max_frames
        self.start_time_sec = start_time_sec
        self.end_time_sec = end_time_sec

    def run(self) -> None:
        try:
            result = video_to_img(
                video_path=self.video_path,
                output_dir=self.output_dir,
                output_format=self.output_format,
                every_n=self.every_n,
                max_frames=self.max_frames,
                start_time_sec=self.start_time_sec,
                end_time_sec=self.end_time_sec,
                log_callback=self.log.emit,
            )

            self.finished_ok.emit(
                f"Video → Image 변환 완료\n"
                f"저장 위치: {result.output_dir}\n"
                f"저장 이미지 수: {result.saved_count}"
            )

        except Exception as exc:
            self.finished_error.emit(str(exc))


class CameraPage(QWidget):
    """
    Camera 변환 GUI 페이지.

    탭 구성:
    - Bag → Image/Video
    - Video → Image
    """

    def __init__(self) -> None:
        super().__init__()

        self.config = load_camera_config()
        self.worker: QThread | None = None

        # Bag → Image/Video 탭
        self.bag_input_path_edit = QLineEdit()
        self.bag_output_dir_edit = QLineEdit()
        self.bag_topic_edit = QLineEdit()
        self.bag_type_combo = QComboBox()
        self.bag_output_format_combo = QComboBox()
        self.bag_fps_spin = QDoubleSpinBox()
        self.bag_codec_edit = QLineEdit()
        self.bag_every_n_spin = QSpinBox()
        self.bag_max_frames_spin = QSpinBox()
        self.bag_run_button = QPushButton("Run Bag Convert")

        # Video → Image 탭
        self.video_input_file_edit = QLineEdit()
        self.video_output_dir_edit = QLineEdit()
        self.video_output_format_combo = QComboBox()
        self.video_every_n_spin = QSpinBox()
        self.video_max_frames_spin = QSpinBox()
        self.video_start_time_spin = QDoubleSpinBox()
        self.video_end_time_spin = QDoubleSpinBox()
        self.video_run_button = QPushButton("Run Video to Image")

        # 공통 로그
        self.log_viewer = QTextEdit()

        self._setup_ui()
        self._setup_default_values()
        self._update_bag_format_ui()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 32, 36, 32)
        root_layout.setSpacing(18)

        title_label = QLabel("Camera Converter")
        title_label.setObjectName("PageTitle")

        description_label = QLabel(
            "Camera rosbag 또는 video 데이터를 image/video 형식으로 변환합니다."
        )
        description_label.setObjectName("PageDescription")

        root_layout.addWidget(title_label)
        root_layout.addWidget(description_label)

        tab_widget = QTabWidget()
        tab_widget.addTab(self._create_bag_convert_tab(), "Bag → Image/Video")
        tab_widget.addTab(self._create_video_to_img_tab(), "Video → Image")

        root_layout.addWidget(tab_widget)

        log_label = QLabel("Log")
        log_label.setObjectName("SectionTitle")
        root_layout.addWidget(log_label)

        self.log_viewer.setReadOnly(True)
        self.log_viewer.setMinimumHeight(220)
        root_layout.addWidget(self.log_viewer, stretch=1)

    def _setup_default_values(self) -> None:
        self.bag_type_combo.addItems(["image", "video"])

        self.bag_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.bag_output_dir_edit.setPlaceholderText("출력 폴더 경로")
        self.bag_topic_edit.setPlaceholderText("/camera/image_raw 또는 /oakd/color/image")

        self.bag_fps_spin.setRange(0.1, 240.0)
        self.bag_fps_spin.setDecimals(2)
        self.bag_fps_spin.setValue(float(self.config["defaults"].get("video_fps", 10)))

        self.bag_codec_edit.setPlaceholderText("예: mp4v, MJPG, VP80")

        self.bag_every_n_spin.setRange(1, 1_000_000)
        self.bag_every_n_spin.setValue(int(self.config["defaults"].get("every_n", 1)))

        self.bag_max_frames_spin.setRange(0, 10_000_000)
        self.bag_max_frames_spin.setValue(0)
        self.bag_max_frames_spin.setSpecialValueText("제한 없음")

        self.video_input_file_edit.setPlaceholderText("video 파일 경로")
        self.video_output_dir_edit.setPlaceholderText("이미지 출력 폴더 경로")

        self.video_output_format_combo.addItems(
            self.config["formats"].get("image", ["png", "jpg"])
        )
        self._set_combo_value(
            self.video_output_format_combo,
            self.config["defaults"].get("image_format", "png"),
        )

        self.video_every_n_spin.setRange(1, 1_000_000)
        self.video_every_n_spin.setValue(int(self.config["defaults"].get("every_n", 1)))

        self.video_max_frames_spin.setRange(0, 10_000_000)
        self.video_max_frames_spin.setValue(0)
        self.video_max_frames_spin.setSpecialValueText("제한 없음")

        self.video_start_time_spin.setRange(0.0, 1_000_000.0)
        self.video_start_time_spin.setDecimals(3)
        self.video_start_time_spin.setValue(0.0)
        self.video_start_time_spin.setSuffix(" sec")

        self.video_end_time_spin.setRange(0.0, 1_000_000.0)
        self.video_end_time_spin.setDecimals(3)
        self.video_end_time_spin.setValue(0.0)
        self.video_end_time_spin.setSpecialValueText("제한 없음")
        self.video_end_time_spin.setSuffix(" sec")

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

        form_layout.addRow("Input rosbag", bag_input_layout)
        form_layout.addRow("Output folder", bag_output_layout)
        form_layout.addRow("Topic", self.bag_topic_edit)
        form_layout.addRow("Convert type", self.bag_type_combo)
        form_layout.addRow("Format", self.bag_output_format_combo)
        form_layout.addRow("Video FPS", self.bag_fps_spin)
        form_layout.addRow("Video codec", self.bag_codec_edit)
        form_layout.addRow("Every N frame", self.bag_every_n_spin)
        form_layout.addRow("Max frames", self.bag_max_frames_spin)

        layout.addWidget(form_widget)

        self.bag_run_button.setFixedHeight(38)
        layout.addWidget(self.bag_run_button)
        layout.addStretch()

        bag_input_browse_button.clicked.connect(self._browse_bag_input_path)
        bag_output_browse_button.clicked.connect(self._browse_bag_output_dir)
        self.bag_type_combo.currentTextChanged.connect(self._update_bag_format_ui)
        self.bag_output_format_combo.currentTextChanged.connect(self._update_video_codec_ui)
        self.bag_run_button.clicked.connect(self._run_bag_conversion)

        return tab

    def _create_video_to_img_tab(self) -> QWidget:
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

        video_input_layout = QHBoxLayout()
        video_input_browse_button = QPushButton("Browse")
        video_input_layout.addWidget(self.video_input_file_edit)
        video_input_layout.addWidget(video_input_browse_button)

        video_output_layout = QHBoxLayout()
        video_output_browse_button = QPushButton("Browse")
        video_output_layout.addWidget(self.video_output_dir_edit)
        video_output_layout.addWidget(video_output_browse_button)

        form_layout.addRow("Input video", video_input_layout)
        form_layout.addRow("Output folder", video_output_layout)
        form_layout.addRow("Format", self.video_output_format_combo)
        form_layout.addRow("Every N frame", self.video_every_n_spin)
        form_layout.addRow("Max frames", self.video_max_frames_spin)
        form_layout.addRow("Start time", self.video_start_time_spin)
        form_layout.addRow("End time", self.video_end_time_spin)

        layout.addWidget(form_widget)

        self.video_run_button.setFixedHeight(38)
        layout.addWidget(self.video_run_button)
        layout.addStretch()

        video_input_browse_button.clicked.connect(self._browse_video_input_file)
        video_output_browse_button.clicked.connect(self._browse_video_output_dir)
        self.video_run_button.clicked.connect(self._run_video_to_img)

        return tab

    def _update_bag_format_ui(self, _text: str | None = None) -> None:
        convert_type = self.bag_type_combo.currentText()

        self.bag_output_format_combo.blockSignals(True)
        self.bag_output_format_combo.clear()

        if convert_type == "video":
            video_formats = self.config["formats"].get(
                "video",
                ["mp4", "avi", "webm", "mkv"],
            )
            self.bag_output_format_combo.addItems(video_formats)
            self._set_combo_value(
                self.bag_output_format_combo,
                self.config["defaults"].get("video_format", "mp4"),
            )

            self.bag_fps_spin.setEnabled(True)
            self.bag_codec_edit.setEnabled(True)
            self.bag_run_button.setText("Run Bag to Video")
            self._update_video_codec_ui()

        else:
            image_formats = self.config["formats"].get("image", ["png", "jpg"])
            self.bag_output_format_combo.addItems(image_formats)
            self._set_combo_value(
                self.bag_output_format_combo,
                self.config["defaults"].get("image_format", "png"),
            )

            self.bag_fps_spin.setEnabled(False)
            self.bag_codec_edit.setEnabled(False)
            self.bag_codec_edit.clear()
            self.bag_run_button.setText("Run Bag to Image")

        self.bag_output_format_combo.blockSignals(False)

    def _update_video_codec_ui(self, _text: str | None = None) -> None:
        if self.bag_type_combo.currentText() != "video":
            return

        output_format = self.bag_output_format_combo.currentText()
        codec = self.config["video_codecs"].get(output_format, "")
        self.bag_codec_edit.setText(codec)

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

    def _browse_video_input_file(self) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select video file",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.webm);;All Files (*)",
        )

        if selected_file:
            self.video_input_file_edit.setText(selected_file)

    def _browse_video_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
        )

        if selected_dir:
            self.video_output_dir_edit.setText(selected_dir)

    def _parse_topics(self, topic_text: str) -> list[str] | None:
        topic_text = topic_text.strip()

        if not topic_text:
            return None

        topics = [
            topic.strip()
            for topic in topic_text.replace(",", " ").split()
            if topic.strip()
        ]

        return topics or None

    def _run_bag_conversion(self) -> None:
        input_path = self.bag_input_path_edit.text().strip()
        output_dir = self.bag_output_dir_edit.text().strip()
        topic_text = self.bag_topic_edit.text().strip()
        convert_type = self.bag_type_combo.currentText()
        output_format = self.bag_output_format_combo.currentText()

        if not input_path:
            self._log("[ERROR] Input rosbag 폴더를 선택해야 합니다.")
            return

        if not output_dir:
            self._log("[ERROR] Output 폴더를 선택해야 합니다.")
            return

        input_path_obj = Path(input_path)

        if not input_path_obj.exists():
            self._log(f"[ERROR] 입력 경로가 존재하지 않습니다: {input_path}")
            return

        if not input_path_obj.is_dir():
            self._log(f"[ERROR] rosbag 입력은 폴더여야 합니다: {input_path}")
            return

        topics = self._parse_topics(topic_text)
        every_n = self.bag_every_n_spin.value()

        max_frames_value = self.bag_max_frames_spin.value()
        max_frames = None if max_frames_value == 0 else max_frames_value

        fps = float(self.bag_fps_spin.value())

        codec_text = self.bag_codec_edit.text().strip()
        codec = codec_text if codec_text else None

        self._log("[INFO] Bag 변환 시작")
        self._log(f"[INFO] input: {input_path}")
        self._log(f"[INFO] output folder: {output_dir}")
        self._log(f"[INFO] topics: {topics if topics else 'auto'}")
        self._log(f"[INFO] convert type: {convert_type}")
        self._log(f"[INFO] format: {output_format}")

        if convert_type == "video":
            self._log(f"[INFO] fps: {fps}")
            self._log(f"[INFO] codec: {codec if codec else 'auto'}")

        self.bag_run_button.setEnabled(False)

        self.worker = BagConvertWorker(
            output_type=convert_type,
            bag_path=input_path,
            output_dir=output_dir,
            topics=topics,
            output_format=output_format,
            every_n=every_n,
            max_frames=max_frames,
            fps=fps,
            codec=codec,
        )

        self.worker.log.connect(self._log)
        self.worker.finished_ok.connect(self._on_bag_finished_ok)
        self.worker.finished_error.connect(self._on_bag_finished_error)
        self.worker.start()

    def _run_video_to_img(self) -> None:
        input_file = self.video_input_file_edit.text().strip()
        output_dir = self.video_output_dir_edit.text().strip()
        output_format = self.video_output_format_combo.currentText()

        if not input_file:
            self._log("[ERROR] Input video 파일을 선택해야 합니다.")
            return

        if not output_dir:
            self._log("[ERROR] Output 폴더를 선택해야 합니다.")
            return

        input_file_obj = Path(input_file)

        if not input_file_obj.exists():
            self._log(f"[ERROR] 입력 파일이 존재하지 않습니다: {input_file}")
            return

        if not input_file_obj.is_file():
            self._log(f"[ERROR] video 입력은 파일이어야 합니다: {input_file}")
            return

        every_n = self.video_every_n_spin.value()

        max_frames_value = self.video_max_frames_spin.value()
        max_frames = None if max_frames_value == 0 else max_frames_value

        start_time_sec = float(self.video_start_time_spin.value())

        end_time_value = float(self.video_end_time_spin.value())
        end_time_sec = None if end_time_value == 0.0 else end_time_value

        if end_time_sec is not None and end_time_sec <= start_time_sec:
            self._log("[ERROR] End time은 Start time보다 커야 합니다.")
            return

        self._log("[INFO] Video → Image 변환 시작")
        self._log(f"[INFO] input video: {input_file}")
        self._log(f"[INFO] output folder: {output_dir}")
        self._log(f"[INFO] format: {output_format}")
        self._log(f"[INFO] every n frame: {every_n}")
        self._log(f"[INFO] max frames: {max_frames if max_frames else 'unlimited'}")
        self._log(f"[INFO] start time: {start_time_sec}")
        self._log(f"[INFO] end time: {end_time_sec if end_time_sec else 'end'}")

        self.video_run_button.setEnabled(False)

        self.worker = VideoToImgWorker(
            video_path=input_file,
            output_dir=output_dir,
            output_format=output_format,
            every_n=every_n,
            max_frames=max_frames,
            start_time_sec=start_time_sec,
            end_time_sec=end_time_sec,
        )

        self.worker.log.connect(self._log)
        self.worker.finished_ok.connect(self._on_video_finished_ok)
        self.worker.finished_error.connect(self._on_video_finished_error)
        self.worker.start()

    def _on_bag_finished_ok(self, message: str) -> None:
        self.bag_run_button.setEnabled(True)
        self._log("[DONE] Bag 변환 완료")
        self._log(message)

    def _on_bag_finished_error(self, message: str) -> None:
        self.bag_run_button.setEnabled(True)
        self._log("[ERROR] Bag 변환 중 오류가 발생했습니다.")
        self._log(message)

    def _on_video_finished_ok(self, message: str) -> None:
        self.video_run_button.setEnabled(True)
        self._log("[DONE] Video → Image 변환 완료")
        self._log(message)

    def _on_video_finished_error(self, message: str) -> None:
        self.video_run_button.setEnabled(True)
        self._log("[ERROR] Video → Image 변환 중 오류가 발생했습니다.")
        self._log(message)

    def _set_combo_value(self, combo: QComboBox, value: str) -> None:
        index = combo.findText(value)

        if index >= 0:
            combo.setCurrentIndex(index)

    def _log(self, message: str) -> None:
        self.log_viewer.append(message)