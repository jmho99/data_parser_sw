from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

from data_parser.sensors.camera.bag_to_img import (
    COMPRESSED_IMAGE_MSG_TYPE,
    IMAGE_MSG_TYPE,
    _compressed_image_msg_to_cv_image,
    _detect_storage_id,
    _image_msg_to_cv_image,
    _normalize_topics,
    _safe_topic_dir_name,
)


LogCallback = Callable[[str], None]


@dataclass(frozen=True)
class BagToVideoResult:
    output_dir: Path
    saved_count: int
    topic_saved_counts: dict[str, int]
    video_paths: dict[str, Path]


def bag_to_video(
    bag_path: str | Path,
    output_dir: str | Path,
    topics: list[str] | None = None,
    output_format: str = "mp4",
    fps: float = 10.0,
    codec: str | None = None,
    every_n: int = 1,
    max_frames: int | None = None,
    log_callback: LogCallback | None = None,
) -> BagToVideoResult:
    """
    ROS2 bag 안의 Image / CompressedImage 토픽을 비디오 파일로 저장한다.

    여러 토픽을 입력하면 토픽별로 별도 비디오 파일을 생성한다.
    예:
      /camera/front/image_raw -> camera_front_image_raw.mp4
      /camera/rear/image_raw  -> camera_rear_image_raw.mp4
    """

    bag_path = Path(bag_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()

    if not bag_path.exists():
        raise FileNotFoundError(f"bag 경로가 존재하지 않습니다: {bag_path}")

    if not bag_path.is_dir():
        raise NotADirectoryError(f"bag_path는 rosbag2 폴더여야 합니다: {bag_path}")

    output_format = _normalize_video_format(output_format)

    if fps <= 0:
        raise ValueError("fps는 0보다 커야 합니다.")

    if every_n < 1:
        raise ValueError("every_n은 1 이상이어야 합니다.")

    if codec is None:
        codec = _default_codec(output_format)

    codec = codec.strip()

    if len(codec) != 4:
        raise ValueError("codec은 4글자 FourCC 문자열이어야 합니다. 예: mp4v, MJPG, VP80")

    output_dir.mkdir(parents=True, exist_ok=True)

    storage_id = _detect_storage_id(bag_path)

    _log(log_callback, "[INFO] Camera bag to video 변환 시작")
    _log(log_callback, f"[INFO] bag path: {bag_path}")
    _log(log_callback, f"[INFO] output dir: {output_dir}")
    _log(log_callback, f"[INFO] storage id: {storage_id}")
    _log(log_callback, f"[INFO] format: {output_format}")
    _log(log_callback, f"[INFO] fps: {fps}")
    _log(log_callback, f"[INFO] codec: {codec}")

    reader = rosbag2_py.SequentialReader()

    storage_options = rosbag2_py.StorageOptions(
        uri=str(bag_path),
        storage_id=storage_id,
    )
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )

    reader.open(storage_options, converter_options)

    topic_type_map = {
        topic_metadata.name: topic_metadata.type
        for topic_metadata in reader.get_all_topics_and_types()
    }

    image_topics = [
        topic_name
        for topic_name, topic_type in topic_type_map.items()
        if topic_type in {IMAGE_MSG_TYPE, COMPRESSED_IMAGE_MSG_TYPE}
    ]

    if not image_topics:
        raise RuntimeError("bag 안에서 Image 또는 CompressedImage 토픽을 찾지 못했습니다.")

    selected_topics = _normalize_topics(topics)

    if selected_topics:
        missing_topics = sorted(set(selected_topics) - set(topic_type_map.keys()))
        if missing_topics:
            raise RuntimeError(
                "bag 안에 존재하지 않는 토픽이 있습니다: "
                + ", ".join(missing_topics)
            )

        unsupported_topics = [
            topic_name
            for topic_name in selected_topics
            if topic_type_map[topic_name] not in {IMAGE_MSG_TYPE, COMPRESSED_IMAGE_MSG_TYPE}
        ]
        if unsupported_topics:
            raise RuntimeError(
                "Image 계열 토픽이 아닌 항목이 포함되어 있습니다: "
                + ", ".join(unsupported_topics)
            )

        target_topics = selected_topics
    else:
        target_topics = image_topics

    _log(log_callback, "[INFO] video target topics:")
    for topic_name in target_topics:
        _log(log_callback, f"  - {topic_name} ({topic_type_map[topic_name]})")

    target_topic_set = set(target_topics)
    seen_counts: dict[str, int] = {topic_name: 0 for topic_name in target_topics}
    saved_counts: dict[str, int] = {topic_name: 0 for topic_name in target_topics}

    writers: dict[str, cv2.VideoWriter] = {}
    video_paths: dict[str, Path] = {}
    video_sizes: dict[str, tuple[int, int]] = {}

    total_saved = 0

    try:
        while reader.has_next():
            topic_name, serialized_data, _timestamp_ns = reader.read_next()

            if topic_name not in target_topic_set:
                continue

            seen_counts[topic_name] += 1

            if (seen_counts[topic_name] - 1) % every_n != 0:
                continue

            msg_type = get_message(topic_type_map[topic_name])
            msg = deserialize_message(serialized_data, msg_type)

            if topic_type_map[topic_name] == IMAGE_MSG_TYPE:
                image = _image_msg_to_cv_image(msg)
            elif topic_type_map[topic_name] == COMPRESSED_IMAGE_MSG_TYPE:
                image = _compressed_image_msg_to_cv_image(msg)
            else:
                continue

            frame = _prepare_frame_for_video(image)
            height, width = frame.shape[:2]
            current_size = (width, height)

            if topic_name not in writers:
                safe_topic_name = _safe_topic_dir_name(topic_name)
                video_path = output_dir / f"{safe_topic_name}.{output_format}"

                fourcc = cv2.VideoWriter_fourcc(*codec)
                writer = cv2.VideoWriter(
                    str(video_path),
                    fourcc,
                    float(fps),
                    current_size,
                )

                if not writer.isOpened():
                    raise RuntimeError(
                        "VideoWriter를 열지 못했습니다. "
                        f"path={video_path}, format={output_format}, codec={codec}. "
                        "mp4가 실패하면 avi + MJPG 조합으로 다시 시도해보세요."
                    )

                writers[topic_name] = writer
                video_paths[topic_name] = video_path
                video_sizes[topic_name] = current_size

                _log(log_callback, f"[INFO] open video writer: {video_path}")
                _log(log_callback, f"[INFO] size: {width}x{height}")

            if video_sizes[topic_name] != current_size:
                raise RuntimeError(
                    f"프레임 크기가 중간에 변경되었습니다: {topic_name} "
                    f"{video_sizes[topic_name]} -> {current_size}"
                )

            writers[topic_name].write(frame)

            saved_counts[topic_name] += 1
            total_saved += 1

            if total_saved % 100 == 0:
                _log(log_callback, f"[INFO] saved {total_saved} video frames...")

            if max_frames is not None and total_saved >= max_frames:
                _log(log_callback, f"[INFO] max_frames 도달: {max_frames}")
                break

    finally:
        for writer in writers.values():
            writer.release()

    _log(log_callback, "[INFO] 변환 완료")
    _log(log_callback, f"[INFO] total video frames: {total_saved}")

    for topic_name, count in saved_counts.items():
        if count > 0:
            _log(log_callback, f"[INFO] {topic_name}: {count} frames -> {video_paths[topic_name]}")
        else:
            _log(log_callback, f"[WARN] {topic_name}: 저장된 프레임 없음")

    return BagToVideoResult(
        output_dir=output_dir,
        saved_count=total_saved,
        topic_saved_counts=saved_counts,
        video_paths=video_paths,
    )


def _normalize_video_format(output_format: str) -> str:
    output_format = output_format.lower().lstrip(".")

    if output_format == "webp":
        raise ValueError("webp는 이미지 포맷입니다. 비디오는 webm을 사용해주세요.")

    if output_format not in {"mp4", "avi", "webm", "mkv"}:
        raise ValueError("output_format은 mp4, avi, webm, mkv 중 하나여야 합니다.")

    return output_format


def _default_codec(output_format: str) -> str:
    codec_map = {
        "mp4": "mp4v",
        "avi": "MJPG",
        "webm": "VP80",
        "mkv": "XVID",
    }
    return codec_map[output_format]


def _prepare_frame_for_video(image: np.ndarray) -> np.ndarray:
    """
    OpenCV VideoWriter에 넣을 수 있도록 frame을 uint8 BGR 3채널로 변환한다.
    """

    frame = image

    if frame.dtype != np.uint8:
        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
        frame = frame.astype(np.uint8)

    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    elif frame.ndim == 3 and frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    elif frame.ndim == 3 and frame.shape[2] == 3:
        pass
    else:
        raise RuntimeError(f"비디오로 저장할 수 없는 이미지 shape입니다: {frame.shape}")

    return frame


def _log(callback: LogCallback | None, message: str) -> None:
    if callback is not None:
        callback(message)
    else:
        print(message)