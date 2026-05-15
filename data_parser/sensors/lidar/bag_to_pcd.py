from __future__ import annotations

import math
import re
import struct
from pathlib import Path
from typing import Any, Sequence

from data_parser.exporters.pcd_exporter import export_pcd
from data_parser.sources.rosbag_reader import open_rosbag_reader


POINTCLOUD2_MSG_TYPE = "sensor_msgs/msg/PointCloud2"

POINTFIELD_INT8 = 1
POINTFIELD_UINT8 = 2
POINTFIELD_INT16 = 3
POINTFIELD_UINT16 = 4
POINTFIELD_INT32 = 5
POINTFIELD_UINT32 = 6
POINTFIELD_FLOAT32 = 7
POINTFIELD_FLOAT64 = 8

POINTFIELD_STRUCT = {
    POINTFIELD_INT8: ("b", 1),
    POINTFIELD_UINT8: ("B", 1),
    POINTFIELD_INT16: ("h", 2),
    POINTFIELD_UINT16: ("H", 2),
    POINTFIELD_INT32: ("i", 4),
    POINTFIELD_UINT32: ("I", 4),
    POINTFIELD_FLOAT32: ("f", 4),
    POINTFIELD_FLOAT64: ("d", 8),
}


def _sanitize_topic_name(topic: str) -> str:
    name = topic.strip("/").replace("/", "_")
    name = re.sub(r"[^0-9A-Za-z_.-]+", "_", name)
    return name or "pointcloud"


def _field_name(field: Any) -> str:
    return str(getattr(field, "name"))


def _field_offset(field: Any) -> int:
    return int(getattr(field, "offset"))


def _field_datatype(field: Any) -> int:
    return int(getattr(field, "datatype"))


def _field_count(field: Any) -> int:
    return int(getattr(field, "count", 1) or 1)


def _message_field_names(msg: Any) -> list[str]:
    return [_field_name(field) for field in msg.fields]


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
    msg: Any,
    selected_fields: Sequence[str],
) -> list[dict[str, Any]]:
    field_map = {_field_name(field): field for field in msg.fields}
    specs: list[dict[str, Any]] = []

    for name in selected_fields:
        field = field_map[name]
        specs.append(
            {
                "name": _field_name(field),
                "datatype": _field_datatype(field),
                "count": _field_count(field),
            }
        )

    return specs


def _point_data_as_bytes(data: Any) -> bytes:
    if isinstance(data, bytes):
        return data

    if isinstance(data, bytearray):
        return bytes(data)

    if isinstance(data, memoryview):
        return data.tobytes()

    if hasattr(data, "tobytes"):
        return data.tobytes()

    return bytes(data)


def _read_field_value(
    data: bytes,
    base_offset: int,
    field: Any,
    endian_prefix: str,
) -> Any:
    datatype = _field_datatype(field)
    count = _field_count(field)
    offset = base_offset + _field_offset(field)

    if datatype not in POINTFIELD_STRUCT:
        raise ValueError(f"Unsupported PointField datatype: {datatype}")

    struct_char, _size = POINTFIELD_STRUCT[datatype]
    fmt = endian_prefix + (struct_char * count)
    values = struct.unpack_from(fmt, data, offset)

    if count == 1:
        return values[0]

    return list(values)


def _value_has_nan(value: Any) -> bool:
    if isinstance(value, float):
        return math.isnan(value)

    if isinstance(value, (list, tuple)):
        return any(_value_has_nan(item) for item in value)

    return False


def _point_rows_from_msg(
    msg: Any,
    selected_fields: Sequence[str],
    skip_nans: bool,
) -> list[list[Any]]:
    field_map = {_field_name(field): field for field in msg.fields}
    selected_field_objs = [field_map[name] for name in selected_fields]

    data = _point_data_as_bytes(msg.data)
    width = int(msg.width)
    height = int(msg.height)
    point_step = int(msg.point_step)
    row_step = int(msg.row_step)
    endian_prefix = ">" if bool(msg.is_bigendian) else "<"

    rows: list[list[Any]] = []

    for row_index in range(height):
        row_base = row_index * row_step

        for col_index in range(width):
            point_base = row_base + col_index * point_step
            row = [
                _read_field_value(data, point_base, field, endian_prefix)
                for field in selected_field_objs
            ]

            if skip_nans and any(_value_has_nan(value) for value in row):
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
    backend: str = "auto",
    skip_nans: bool = True,
    use_timestamp_filename: bool = True,
) -> dict[str, Any]:
    bag_path = Path(bag_path).expanduser()
    output_dir = Path(output_dir).expanduser()

    if not bag_path.exists():
        raise FileNotFoundError(f"rosbag 경로가 존재하지 않습니다: {bag_path}")

    if not bag_path.is_dir() and bag_path.suffix.lower() not in {".db3", ".mcap"}:
        raise ValueError(f"rosbag 입력은 폴더 또는 .db3/.mcap 파일이어야 합니다: {bag_path}")

    if every_n < 1:
        raise ValueError("every_n은 1 이상이어야 합니다.")

    output_dir.mkdir(parents=True, exist_ok=True)

    saved_frame_count = 0
    saved_paths: list[str] = []

    with open_rosbag_reader(
        bag_path=bag_path,
        backend=backend,
        storage_id=storage_id,
    ) as reader:
        topic_type_map = reader.topic_type_map
        pointcloud_topics = {
            name
            for name, msg_type in topic_type_map.items()
            if msg_type == POINTCLOUD2_MSG_TYPE
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

        for record in reader.messages(topics=selected_topics):
            msg = record.msg

            if record.msg_type != POINTCLOUD2_MSG_TYPE:
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
                topic=record.topic,
                frame_index=matched_frame_index,
                timestamp=record.timestamp,
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