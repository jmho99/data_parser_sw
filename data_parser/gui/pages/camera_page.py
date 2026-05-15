from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
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


def make_choice_options(values: list[str]) -> list[tuple[str, str]]:
    return [(value, value) for value in values]


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

    현재 지원:
    - Bag → Image
    - Bag → Video
    - Video → Image
    """

    def __init__(self) -> None:
        super().__init__()

        self.config = load_camera_config()
        self.worker: QThread | None = None
        self._active_run_button: QPushButton | None = None

        image_formats = self.config["formats"].get("image", ["png", "jpg"])
        video_formats = self.config["formats"].get("video", ["mp4", "avi", "webm", "mkv"])

        default_image_format = str(self.config["defaults"].get("image_format", "png"))
        default_video_format = str(self.config["defaults"].get("video_format", "mp4"))

        # Bag → Image
        self.bag_image_input_path_edit = QLineEdit()
        self.bag_image_output_dir_edit = QLineEdit()
        self.bag_image_topic_edit = QLineEdit()
        self.bag_image_format_choice = ChoiceBar(
            make_choice_options(image_formats),
            exclusive=True,
            default=default_image_format,
        )
        self.bag_image_every_n_spin = QSpinBox()
        self.bag_image_max_frames_spin = QSpinBox()
        self.bag_image_run_button = QPushButton("Bag → Image 변환 시작")

        # Bag → Video
        self.bag_video_input_path_edit = QLineEdit()
        self.bag_video_output_dir_edit = QLineEdit()
        self.bag_video_topic_edit = QLineEdit()
        self.bag_video_format_choice = ChoiceBar(
            make_choice_options(video_formats),
            exclusive=True,
            default=default_video_format,
        )
        self.bag_video_fps_spin = QDoubleSpinBox()
        self.bag_video_codec_edit = QLineEdit()
        self.bag_video_every_n_spin = QSpinBox()
        self.bag_video_max_frames_spin = QSpinBox()
        self.bag_video_run_button = QPushButton("Bag → Video 변환 시작")

        # Video → Image
        self.video_input_file_edit = QLineEdit()
        self.video_output_dir_edit = QLineEdit()
        self.video_output_format_choice = ChoiceBar(
            make_choice_options(image_formats),
            exclusive=True,
            default=default_image_format,
        )
        self.video_every_n_spin = QSpinBox()
        self.video_max_frames_spin = QSpinBox()
        self.video_start_time_spin = QDoubleSpinBox()
        self.video_end_time_spin = QDoubleSpinBox()
        self.video_run_button = QPushButton("Video → Image 변환 시작")

        self.log_viewer = QTextEdit()
        self.bag_image_summary_panel = SummaryPanel()
        self.bag_video_summary_panel = SummaryPanel()
        self.video_image_summary_panel = SummaryPanel()

        self._setup_default_values()
        self._setup_ui()
        self._update_video_codec_ui()
        self._connect_summary_signals()
        self._update_summary()

    def _setup_default_values(self) -> None:
        # Bag → Image
        self.bag_image_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.bag_image_output_dir_edit.setPlaceholderText("이미지 출력 폴더 경로")
        self.bag_image_topic_edit.setPlaceholderText("/camera/image_raw 또는 /oakd/color/image")

        self.bag_image_every_n_spin.setRange(1, 1_000_000)
        self.bag_image_every_n_spin.setValue(int(self.config["defaults"].get("every_n", 1)))

        self.bag_image_max_frames_spin.setRange(0, 10_000_000)
        self.bag_image_max_frames_spin.setValue(0)
        self.bag_image_max_frames_spin.setSpecialValueText("제한 없음")

        # Bag → Video
        self.bag_video_input_path_edit.setPlaceholderText("rosbag 폴더 경로")
        self.bag_video_output_dir_edit.setPlaceholderText("비디오 출력 폴더 경로")
        self.bag_video_topic_edit.setPlaceholderText("/camera/image_raw 또는 /oakd/color/image")

        self.bag_video_fps_spin.setRange(0.1, 240.0)
        self.bag_video_fps_spin.setDecimals(2)
        self.bag_video_fps_spin.setValue(float(self.config["defaults"].get("video_fps", 10)))

        self.bag_video_codec_edit.setPlaceholderText("예: mp4v, MJPG, VP80")

        self.bag_video_every_n_spin.setRange(1, 1_000_000)
        self.bag_video_every_n_spin.setValue(int(self.config["defaults"].get("every_n", 1)))

        self.bag_video_max_frames_spin.setRange(0, 10_000_000)
        self.bag_video_max_frames_spin.setValue(0)
        self.bag_video_max_frames_spin.setSpecialValueText("제한 없음")

        # Video → Image
        self.video_input_file_edit.setPlaceholderText("video 파일 경로")
        self.video_output_dir_edit.setPlaceholderText("이미지 출력 폴더 경로")

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

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.shell = SensorPageShell(
            title_ko="카메라",
            title_en="Camera",
            description="Camera rosbag 또는 video 데이터를 image/video 형식으로 변환합니다.",
            icon_name="camera",
            conversion_count=3,
            topics=["/camera/image_raw", "/oakd/color/image"],
        )

        self.shell.add_mode(
            key="bag_image",
            label="Bag → Image",
            settings_widget=self._create_bag_image_settings(),
            summary_widget=self.bag_image_summary_panel,
            run_button=self.bag_image_run_button,
        )

        self.shell.add_mode(
            key="bag_video",
            label="Bag → Video",
            settings_widget=self._create_bag_video_settings(),
            summary_widget=self.bag_video_summary_panel,
            run_button=self.bag_video_run_button,
        )

        self.shell.add_mode(
            key="video_image",
            label="Video → Image",
            settings_widget=self._create_video_image_settings(),
            summary_widget=self.video_image_summary_panel,
            run_button=self.video_run_button,
        )

        self.log_viewer.setReadOnly(True)
        self.shell.set_log_widget(self.log_viewer)

        root_layout.addWidget(self.shell)

        self.bag_image_input_path_edit.textChanged.connect(self.shell.set_selected_source_path)
        self.bag_video_input_path_edit.textChanged.connect(self.shell.set_selected_source_path)
        self.video_input_file_edit.textChanged.connect(self.shell.set_selected_source_path)

        self.bag_video_format_choice.changed.connect(self._update_video_codec_ui)

        self.bag_image_run_button.clicked.connect(self._run_bag_image_conversion)
        self.bag_video_run_button.clicked.connect(self._run_bag_video_conversion)
        self.video_run_button.clicked.connect(self._run_video_to_img)

    def _create_bag_image_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(12)

        browse_input = QPushButton("Browse")
        browse_output = QPushButton("Browse")

        layout.addWidget(make_field_row(
            "입력 rosbag",
            "Input rosbag",
            make_path_input(self.bag_image_input_path_edit, browse_input),
        ))
        layout.addWidget(make_field_row(
            "출력 폴더",
            "Output folder",
            make_path_input(self.bag_image_output_dir_edit, browse_output),
        ))
        layout.addWidget(make_field_row("토픽", "Topic", self.bag_image_topic_edit))
        layout.addWidget(make_field_row("저장 포맷", "Format", self.bag_image_format_choice))
        layout.addWidget(make_field_row("프레임 간격", "Every N frame", self.bag_image_every_n_spin))
        layout.addWidget(make_field_row("최대 프레임", "Max frames", self.bag_image_max_frames_spin))
        layout.addStretch(1)

        browse_input.clicked.connect(self._browse_bag_image_input_path)
        browse_output.clicked.connect(self._browse_bag_image_output_dir)

        return widget

    def _create_bag_video_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(12)

        browse_input = QPushButton("Browse")
        browse_output = QPushButton("Browse")

        layout.addWidget(make_field_row(
            "입력 rosbag",
            "Input rosbag",
            make_path_input(self.bag_video_input_path_edit, browse_input),
        ))
        layout.addWidget(make_field_row(
            "출력 폴더",
            "Output folder",
            make_path_input(self.bag_video_output_dir_edit, browse_output),
        ))
        layout.addWidget(make_field_row("토픽", "Topic", self.bag_video_topic_edit))
        layout.addWidget(make_field_row("저장 포맷", "Format", self.bag_video_format_choice))
        layout.addWidget(make_field_row("비디오 FPS", "Video FPS", self.bag_video_fps_spin))
        layout.addWidget(make_field_row("비디오 코덱", "Video codec", self.bag_video_codec_edit))
        layout.addWidget(make_field_row("프레임 간격", "Every N frame", self.bag_video_every_n_spin))
        layout.addWidget(make_field_row("최대 프레임", "Max frames", self.bag_video_max_frames_spin))
        layout.addStretch(1)

        browse_input.clicked.connect(self._browse_bag_video_input_path)
        browse_output.clicked.connect(self._browse_bag_video_output_dir)

        return widget

    def _create_video_image_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(12)

        browse_input = QPushButton("Browse")
        browse_output = QPushButton("Browse")

        layout.addWidget(make_field_row(
            "입력 비디오",
            "Input video",
            make_path_input(self.video_input_file_edit, browse_input),
        ))
        layout.addWidget(make_field_row(
            "출력 폴더",
            "Output folder",
            make_path_input(self.video_output_dir_edit, browse_output),
        ))
        layout.addWidget(make_field_row("저장 포맷", "Format", self.video_output_format_choice))
        layout.addWidget(make_field_row("프레임 간격", "Every N frame", self.video_every_n_spin))
        layout.addWidget(make_field_row("최대 프레임", "Max frames", self.video_max_frames_spin))
        layout.addWidget(make_field_row("시작 시간", "Start time", self.video_start_time_spin))
        layout.addWidget(make_field_row("종료 시간", "End time", self.video_end_time_spin))
        layout.addStretch(1)

        browse_input.clicked.connect(self._browse_video_input_file)
        browse_output.clicked.connect(self._browse_video_output_dir)

        return widget
    def _connect_summary_signals(self) -> None:
        for editor in (
            self.bag_image_input_path_edit,
            self.bag_image_output_dir_edit,
            self.bag_image_topic_edit,
            self.bag_video_input_path_edit,
            self.bag_video_output_dir_edit,
            self.bag_video_topic_edit,
            self.bag_video_codec_edit,
            self.video_input_file_edit,
            self.video_output_dir_edit,
        ):
            editor.textChanged.connect(lambda *_: self._update_summary())
    
        for choice in (
            self.bag_image_format_choice,
            self.bag_video_format_choice,
            self.video_output_format_choice,
        ):
            choice.changed.connect(lambda *_: self._update_summary())
    
        for spin in (
            self.bag_image_every_n_spin,
            self.bag_image_max_frames_spin,
            self.bag_video_fps_spin,
            self.bag_video_every_n_spin,
            self.bag_video_max_frames_spin,
            self.video_every_n_spin,
            self.video_max_frames_spin,
            self.video_start_time_spin,
            self.video_end_time_spin,
        ):
            spin.valueChanged.connect(lambda *_: self._update_summary())


    def _update_summary(self) -> None:
        bag_image_format = self.bag_image_format_choice.selected_value() or "png"
        bag_video_format = self.bag_video_format_choice.selected_value() or "mp4"
        video_image_format = self.video_output_format_choice.selected_value() or "png"
    
        self.bag_image_summary_panel.update_summary(
            sensor="Camera",
            mode="bag → image",
            input_path=self.bag_image_input_path_edit.text(),
            output_path=self.bag_image_output_dir_edit.text(),
            topic=self.bag_image_topic_edit.text() or "auto",
            fmt=bag_image_format,
            extra=(
                f"프레임 간격: {self.bag_image_every_n_spin.value()}, "
                f"최대 프레임: {self._max_frames_text(self.bag_image_max_frames_spin.value())}"
            ),
        )
    
        self.bag_video_summary_panel.update_summary(
            sensor="Camera",
            mode="bag → video",
            input_path=self.bag_video_input_path_edit.text(),
            output_path=self.bag_video_output_dir_edit.text(),
            topic=self.bag_video_topic_edit.text() or "auto",
            fmt=bag_video_format,
            extra=(
                f"FPS: {self.bag_video_fps_spin.value():.2f}, "
                f"Codec: {self.bag_video_codec_edit.text() or 'auto'}, "
                f"프레임 간격: {self.bag_video_every_n_spin.value()}, "
                f"최대 프레임: {self._max_frames_text(self.bag_video_max_frames_spin.value())}"
            ),
        )
    
        self.video_image_summary_panel.update_summary(
            sensor="Camera",
            mode="video → image",
            input_path=self.video_input_file_edit.text(),
            output_path=self.video_output_dir_edit.text(),
            topic="-",
            fmt=video_image_format,
            extra=(
                f"프레임 간격: {self.video_every_n_spin.value()}, "
                f"최대 프레임: {self._max_frames_text(self.video_max_frames_spin.value())}, "
                f"시간: {self.video_start_time_spin.value():.3f}s ~ "
                f"{self._end_time_text(self.video_end_time_spin.value())}"
            ),
        )
    
    
    @staticmethod
    def _max_frames_text(value: int) -> str:
        return "제한 없음" if value == 0 else str(value)
    
    
    @staticmethod
    def _end_time_text(value: float) -> str:
        return "끝" if value == 0.0 else f"{value:.3f}s"

    def _browse_bag_image_input_path(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select rosbag folder")
        if selected_dir:
            self.bag_image_input_path_edit.setText(selected_dir)

    def _browse_bag_image_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
        if selected_dir:
            self.bag_image_output_dir_edit.setText(selected_dir)

    def _browse_bag_video_input_path(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select rosbag folder")
        if selected_dir:
            self.bag_video_input_path_edit.setText(selected_dir)

    def _browse_bag_video_output_dir(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
        if selected_dir:
            self.bag_video_output_dir_edit.setText(selected_dir)

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
        selected_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
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

    def _run_bag_image_conversion(self) -> None:
        output_format = self.bag_image_format_choice.selected_value() or "png"

        self._run_bag_conversion(
            output_type="image",
            input_path=self.bag_image_input_path_edit.text().strip(),
            output_dir=self.bag_image_output_dir_edit.text().strip(),
            topic_text=self.bag_image_topic_edit.text().strip(),
            output_format=output_format,
            every_n=self.bag_image_every_n_spin.value(),
            max_frames_value=self.bag_image_max_frames_spin.value(),
            fps=0.0,
            codec=None,
            run_button=self.bag_image_run_button,
        )

    def _run_bag_video_conversion(self) -> None:
        output_format = self.bag_video_format_choice.selected_value() or "mp4"
        codec_text = self.bag_video_codec_edit.text().strip()

        self._run_bag_conversion(
            output_type="video",
            input_path=self.bag_video_input_path_edit.text().strip(),
            output_dir=self.bag_video_output_dir_edit.text().strip(),
            topic_text=self.bag_video_topic_edit.text().strip(),
            output_format=output_format,
            every_n=self.bag_video_every_n_spin.value(),
            max_frames_value=self.bag_video_max_frames_spin.value(),
            fps=float(self.bag_video_fps_spin.value()),
            codec=codec_text if codec_text else None,
            run_button=self.bag_video_run_button,
        )

    def _run_bag_conversion(
        self,
        *,
        output_type: str,
        input_path: str,
        output_dir: str,
        topic_text: str,
        output_format: str,
        every_n: int,
        max_frames_value: int,
        fps: float,
        codec: str | None,
        run_button: QPushButton,
    ) -> None:
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
        max_frames = None if max_frames_value == 0 else max_frames_value

        self._log("[INFO] Bag 변환 시작")
        self._log(f"[INFO] input: {input_path}")
        self._log(f"[INFO] output folder: {output_dir}")
        self._log(f"[INFO] topics: {topics if topics else 'auto'}")
        self._log(f"[INFO] convert type: {output_type}")
        self._log(f"[INFO] format: {output_format}")

        if output_type == "video":
            self._log(f"[INFO] fps: {fps}")
            self._log(f"[INFO] codec: {codec if codec else 'auto'}")

        run_button.setEnabled(False)
        self._active_run_button = run_button

        self.worker = BagConvertWorker(
            output_type=output_type,
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
        self.worker.finished_ok.connect(self._on_worker_finished_ok)
        self.worker.finished_error.connect(self._on_worker_finished_error)
        self.worker.start()

    def _run_video_to_img(self) -> None:
        input_file = self.video_input_file_edit.text().strip()
        output_dir = self.video_output_dir_edit.text().strip()
        output_format = self.video_output_format_choice.selected_value() or "png"

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
        self._active_run_button = self.video_run_button

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
        self.worker.finished_ok.connect(self._on_worker_finished_ok)
        self.worker.finished_error.connect(self._on_worker_finished_error)
        self.worker.start()

    def _on_worker_finished_ok(self, message: str) -> None:
        if self._active_run_button is not None:
            self._active_run_button.setEnabled(True)

        self._log("[DONE] 변환 완료")
        self._log(message)

    def _on_worker_finished_error(self, message: str) -> None:
        if self._active_run_button is not None:
            self._active_run_button.setEnabled(True)

        self._log("[ERROR] 변환 중 오류가 발생했습니다.")
        self._log(message)

    def _update_video_codec_ui(self, _text: str | None = None) -> None:
        output_format = self.bag_video_format_choice.selected_value() or "mp4"
        codec = self.config["video_codecs"].get(output_format, "")
        self.bag_video_codec_edit.setText(codec)

    def _log(self, message: str) -> None:
        self.log_viewer.append(message)