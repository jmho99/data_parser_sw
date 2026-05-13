from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2

from data_parser.exporters.pcd_exporter import export_pcd


def _detect_storage_id(bag_path: Path) -> str:
    if any(bag_path.glob("*.mcap")):
        return "mcap"

    if any(bag_path.glob("*.db3")):
        return "sqlite3"

    return "sqlite3"


def _open_reader(bag_path: Path, storage_id: str) -> rosbag2_py.SequentialReader:
    if storage_id == "auto":
        storage_id = _detect_storage_id(bag_path)

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
    return reader


def _sanitize_topic_name(topic: str) -> str:
    name = topic.strip("/").replace("/", "_")
    name = re.sub(r"[^0-9A-Za-z_.-]+", "_", name)
    return name or "pointcloud"


def _message_field_names(msg: PointCloud2) -> list[str]:
    return [field.name for field in msg.fields]


def _normalize_selected_fields(
    requested_fields: Sequence[str] | str | None,
    available_fields: Sequence[str],
) -> list[str]:
    available = list(available_fields)

    if requested_fields is None or requested_fields == "all":
        return available

    selected: list[str] = []

    for field in requested_fields:
        if field == "xyz":
            candidates = ["x", "y", "z"]
        else:
            candidates = [field]

        for candidate in candidates:
            if candidate in available and candidate not in selected:
                selected.append(candidate)

    if not selected:
        raise ValueError(
            "선택한 PointCloud field가 메시지에 없습니다. "
            f"available={available}, requested={requested_fields}"
        )

    required_xyz = {"x", "y", "z"}
    if not required_xyz.issubset(set(selected)):
        missing = sorted(required_xyz - set(selected))
        raise ValueError(f"PCD 저장에는 x, y, z 필드가 필요합니다. missing={missing}")

    return selected


def _field_specs_from_msg(
    msg: PointCloud2,
    selected_fields: Sequence[str],
) -> list[dict[str, Any]]:
    field_map = {field.name: field for field in msg.fields}
    specs: list[dict[str, Any]] = []

    for name in selected_fields:
        field = field_map[name]
        specs.append(
            {
                "name": field.name,
                "datatype": field.datatype,
                "count": field.count,
            }
        )

    return specs


def _to_python_value(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()

    return value


def _point_rows_from_msg(
    msg: PointCloud2,
    selected_fields: Sequence[str],
    skip_nans: bool,
) -> list[list[Any]]:
    raw_points = point_cloud2.read_points(
        msg,
        field_names=list(selected_fields),
        skip_nans=skip_nans,
    )

    rows: list[list[Any]] = []

    for point in raw_points:
        if hasattr(point, "dtype") and point.dtype.names:
            row = [_to_python_value(point[name]) for name in selected_fields]
        elif isinstance(point, dict):
            row = [_to_python_value(point[name]) for name in selected_fields]
        else:
            row = [_to_python_value(value) for value in point]

        if skip_nans and any(
            isinstance(value, float) and math.isnan(value)
            for value in row
        ):
            continue

        rows.append(row)

    return rows


def _output_file_path(
    output_dir: Path,
    topic: str,
    frame_index: int,
    timestamp: int,
    use_timestamp_filename: bool,
) -> Path:
    topic_name = _sanitize_topic_name(topic)

    if use_timestamp_filename:
        file_name = f"{topic_name}_{timestamp}.pcd"
    else:
        file_name = f"{topic_name}_{frame_index:06d}.pcd"

    return output_dir / file_name


def extract_lidar_bag_to_pcd(
    bag_path: str | Path,
    output_dir: str | Path,
    topics: Sequence[str] | None = None,
    pcd_format: str = "ascii",
    fields: Sequence[str] | str | None = ("x", "y", "z", "intensity"),
    every_n: int = 1,
    start_index: int = 0,
    end_index: int | None = None,
    storage_id: str = "auto",
    skip_nans: bool = True,
    use_timestamp_filename: bool = True,
) -> dict[str, Any]:
    bag_path = Path(bag_path).expanduser()
    output_dir = Path(output_dir).expanduser()

    if not bag_path.exists():
        raise FileNotFoundError(f"rosbag 경로가 존재하지 않습니다: {bag_path}")

    if not bag_path.is_dir():
        raise ValueError(f"rosbag 입력은 폴더여야 합니다: {bag_path}")

    if every_n < 1:
        raise ValueError("every_n은 1 이상이어야 합니다.")

    output_dir.mkdir(parents=True, exist_ok=True)

    reader = _open_reader(bag_path, storage_id)
    topic_type_map = {
        topic_metadata.name: topic_metadata.type
        for topic_metadata in reader.get_all_topics_and_types()
    }

    pointcloud_topics = {
        name
        for name, msg_type in topic_type_map.items()
        if msg_type == "sensor_msgs/msg/PointCloud2"
    }

    if topics:
        selected_topics = set(topics)
    else:
        selected_topics = pointcloud_topics

    selected_topics = selected_topics & pointcloud_topics

    if not selected_topics:
        raise ValueError(
            "저장 가능한 PointCloud2 토픽이 없습니다. "
            f"available_pointcloud_topics={sorted(pointcloud_topics)}"
        )

    matched_frame_index = 0
    saved_frame_count = 0
    saved_paths: list[str] = []

    while reader.has_next():
        topic, serialized_data, timestamp = reader.read_next()

        if topic not in selected_topics:
            continue

        msg_type = get_message(topic_type_map[topic])
        msg = deserialize_message(serialized_data, msg_type)

        if not isinstance(msg, PointCloud2):
            continue

        if matched_frame_index < start_index:
            matched_frame_index += 1
            continue

        if end_index is not None and matched_frame_index > end_index:
            break

        if (matched_frame_index - start_index) % every_n != 0:
            matched_frame_index += 1
            continue

        available_fields = _message_field_names(msg)
        selected_fields = _normalize_selected_fields(fields, available_fields)
        field_specs = _field_specs_from_msg(msg, selected_fields)
        rows = _point_rows_from_msg(msg, selected_fields, skip_nans)

        output_path = _output_file_path(
            output_dir=output_dir,
            topic=topic,
            frame_index=matched_frame_index,
            timestamp=timestamp,
            use_timestamp_filename=use_timestamp_filename,
        )

        export_pcd(
            points=rows,
            output_path=output_path,
            fields=selected_fields,
            field_specs=field_specs,
            pcd_format=pcd_format,
        )

        saved_paths.append(str(output_path))
        saved_frame_count += 1
        matched_frame_index += 1

    return {
        "bag_path": str(bag_path),
        "output_dir": str(output_dir),
        "saved_frames": saved_frame_count,
        "saved_paths": saved_paths,
    }