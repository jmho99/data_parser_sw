from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np

from data_parser.sources.rosbag_reader import open_rosbag_reader


IMAGE_MSG_TYPE = "sensor_msgs/msg/Image"
COMPRESSED_IMAGE_MSG_TYPE = "sensor_msgs/msg/CompressedImage"


LogCallback = Callable[[str], None]


@dataclass(frozen=True)
class BagToImgResult:
    output_dir: Path
    saved_count: int
    topic_saved_counts: dict[str, int]


def bag_to_img(
    bag_path: str | Path,
    output_dir: str | Path,
    topics: list[str] | None = None,
    output_format: str = "png",
    every_n: int = 1,
    max_frames: int | None = None,
    backend: str = "auto",
    storage_id: str = "auto",
    log_callback: LogCallback | None = None,
) -> BagToImgResult:
    bag_path = Path(bag_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()

    if not bag_path.exists():
        raise FileNotFoundError(f"bag 경로가 존재하지 않습니다: {bag_path}")

    if not bag_path.is_dir() and bag_path.suffix.lower() not in {".db3", ".mcap"}:
        raise NotADirectoryError(f"bag_path는 rosbag2 폴더 또는 .db3/.mcap 파일이어야 합니다: {bag_path}")

    output_format = output_format.lower().lstrip(".")
    if output_format == "jpeg":
        output_format = "jpg"

    if output_format not in {"png", "jpg"}:
        raise ValueError("output_format은 png, jpg, jpeg 중 하나여야 합니다.")

    if every_n < 1:
        raise ValueError("every_n은 1 이상이어야 합니다.")

    output_dir.mkdir(parents=True, exist_ok=True)

    _log(log_callback, f"[INFO] bag path: {bag_path}")
    _log(log_callback, f"[INFO] output dir: {output_dir}")
    _log(log_callback, f"[INFO] backend: {backend}")

    with open_rosbag_reader(
        bag_path=bag_path,
        backend=backend,
        storage_id=storage_id,
    ) as reader:
        topic_type_map = reader.topic_type_map
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

        _log(log_callback, "[INFO] image topics:")
        for topic_name in target_topics:
            _log(log_callback, f"  - {topic_name} ({topic_type_map[topic_name]})")

        seen_counts: dict[str, int] = {topic_name: 0 for topic_name in target_topics}
        saved_counts: dict[str, int] = {topic_name: 0 for topic_name in target_topics}

        total_saved = 0
        target_topic_set = set(target_topics)

        for record in reader.messages(topics=target_topic_set):
            topic_name = record.topic

            seen_counts[topic_name] += 1

            if (seen_counts[topic_name] - 1) % every_n != 0:
                continue

            if record.msg_type == IMAGE_MSG_TYPE:
                image = _image_msg_to_cv_image(record.msg)
            elif record.msg_type == COMPRESSED_IMAGE_MSG_TYPE:
                image = _compressed_image_msg_to_cv_image(record.msg)
            else:
                continue

            topic_dir = output_dir / _safe_topic_dir_name(topic_name)
            topic_dir.mkdir(parents=True, exist_ok=True)

            saved_counts[topic_name] += 1
            frame_index = saved_counts[topic_name]

            filename = f"frame_{frame_index:06d}_{record.timestamp}.{output_format}"
            save_path = topic_dir / filename

            _write_image(save_path, image, output_format)

            total_saved += 1

            if total_saved % 100 == 0:
                _log(log_callback, f"[INFO] saved {total_saved} images...")

            if max_frames is not None and total_saved >= max_frames:
                _log(log_callback, f"[INFO] max_frames 도달: {max_frames}")
                break

    _log(log_callback, "[INFO] 변환 완료")
    _log(log_callback, f"[INFO] total saved: {total_saved}")

    for topic_name, count in saved_counts.items():
        _log(log_callback, f"[INFO] {topic_name}: {count} images")

    return BagToImgResult(
        output_dir=output_dir,
        saved_count=total_saved,
        topic_saved_counts=saved_counts,
    )


def _normalize_topics(topics: list[str] | None) -> list[str]:
    if not topics:
        return []

    normalized: list[str] = []

    for topic in topics:
        if not topic:
            continue

        split_topics = topic.split(",")

        for split_topic in split_topics:
            clean_topic = split_topic.strip()
            if clean_topic:
                normalized.append(clean_topic)

    return normalized


def _safe_topic_dir_name(topic_name: str) -> str:
    name = topic_name.strip("/").replace("/", "_")

    if not name:
        name = "root"

    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name)


def _msg_data_to_numpy(data: Any, dtype: Any = np.uint8) -> np.ndarray:
    if isinstance(data, bytes):
        return np.frombuffer(data, dtype=dtype)

    if isinstance(data, bytearray):
        return np.frombuffer(data, dtype=dtype)

    if isinstance(data, memoryview):
        return np.frombuffer(data, dtype=dtype)

    return np.asarray(data, dtype=dtype)


def _image_msg_to_cv_image(msg: Any) -> np.ndarray:
    encoding = str(msg.encoding).lower()

    if encoding in {"bgr8", "rgb8", "bgra8", "rgba8"}:
        image = _reshape_image_data(msg, dtype=np.uint8, channels=4 if "a8" in encoding else 3)

        if encoding == "rgb8":
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        elif encoding == "rgba8":
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)

        return image

    if encoding in {"mono8", "8uc1"}:
        return _reshape_image_data(msg, dtype=np.uint8, channels=1)

    if encoding in {"mono16", "16uc1"}:
        image = _reshape_image_data(msg, dtype=np.uint16, channels=1)

        if bool(msg.is_bigendian):
            image = image.byteswap()

        return image

    if encoding.startswith("bayer_"):
        return _reshape_image_data(msg, dtype=np.uint8, channels=1)

    raise RuntimeError(
        f"지원하지 않는 Image encoding입니다: {msg.encoding} "
        f"(현재 지원: bgr8, rgb8, bgra8, rgba8, mono8, mono16, bayer_*)"
    )


def _reshape_image_data(msg: Any, dtype: Any, channels: int) -> np.ndarray:
    height = int(msg.height)
    width = int(msg.width)
    step = int(msg.step)

    dtype_size = np.dtype(dtype).itemsize
    data = _msg_data_to_numpy(msg.data, dtype=dtype)

    if channels == 1:
        row_items = step // dtype_size
        image = data.reshape(height, row_items)
        image = image[:, :width]
        return image.copy()

    row_pixels = step // (dtype_size * channels)
    image = data.reshape(height, row_pixels, channels)
    image = image[:, :width, :]
    return image.copy()


def _compressed_image_msg_to_cv_image(msg: Any) -> np.ndarray:
    data = _msg_data_to_numpy(msg.data, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise RuntimeError("CompressedImage 디코딩에 실패했습니다.")

    return image


def _write_image(save_path: Path, image: np.ndarray, output_format: str) -> None:
    if output_format == "jpg":
        image = _convert_for_jpg(image)
        success = cv2.imwrite(
            str(save_path),
            image,
            [int(cv2.IMWRITE_JPEG_QUALITY), 95],
        )
    else:
        success = cv2.imwrite(str(save_path), image)

    if not success:
        raise RuntimeError(f"이미지 저장 실패: {save_path}")


def _convert_for_jpg(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image

    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    return image


def _log(callback: LogCallback | None, message: str) -> None:
    if callback is not None:
        callback(message)
    else:
        print(message)