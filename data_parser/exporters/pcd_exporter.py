from __future__ import annotations

import struct
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Union

from data_parser.utils.path_utils import ensure_parent_dir, to_path


PathLike = Union[str, Path]

# sensor_msgs/msg/PointField constants.
# ROS2 없이도 쓰기 위해 직접 정의한다.
POINTFIELD_INT8 = 1
POINTFIELD_UINT8 = 2
POINTFIELD_INT16 = 3
POINTFIELD_UINT16 = 4
POINTFIELD_INT32 = 5
POINTFIELD_UINT32 = 6
POINTFIELD_FLOAT32 = 7
POINTFIELD_FLOAT64 = 8

DEFAULT_FIELD_ORDER = ["x", "y", "z", "intensity", "ring", "t", "time", "timestamp", "rgb"]

POINTFIELD_TO_PCD = {
    POINTFIELD_INT8: ("1", "I", "b"),
    POINTFIELD_UINT8: ("1", "U", "B"),
    POINTFIELD_INT16: ("2", "I", "h"),
    POINTFIELD_UINT16: ("2", "U", "H"),
    POINTFIELD_INT32: ("4", "I", "i"),
    POINTFIELD_UINT32: ("4", "U", "I"),
    POINTFIELD_FLOAT32: ("4", "F", "f"),
    POINTFIELD_FLOAT64: ("8", "F", "d"),
}


def _to_list(points: Iterable) -> list[Any]:
    if hasattr(points, "tolist"):
        return points.tolist()

    return list(points)


def _default_fields_from_column_count(column_count: int) -> list[str]:
    if column_count == 3:
        return ["x", "y", "z"]

    if column_count == 4:
        return ["x", "y", "z", "intensity"]

    return [f"field_{i}" for i in range(column_count)]


def _normalize_points(
    points: Iterable,
    fields: Optional[Sequence[str]] = None,
) -> tuple[list[list[Any]], list[str]]:
    rows = _to_list(points)

    if not rows:
        raise ValueError("No points to export as PCD")

    first = rows[0]

    if isinstance(first, dict):
        if fields is None:
            fields = [name for name in DEFAULT_FIELD_ORDER if name in first]

            if not fields:
                fields = list(first.keys())

        normalized = []

        for point in rows:
            normalized.append([point.get(field, 0.0) for field in fields])

        return normalized, list(fields)

    normalized = [list(point) for point in rows]
    column_count = len(normalized[0])

    for point in normalized:
        if len(point) != column_count:
            raise ValueError("All points must have the same number of fields")

    if fields is None:
        fields = _default_fields_from_column_count(column_count)

    if len(fields) != column_count:
        raise ValueError(
            f"Field count mismatch. fields={len(fields)}, point columns={column_count}"
        )

    return normalized, list(fields)


def _default_field_specs(fields: Sequence[str]) -> list[dict[str, Any]]:
    return [
        {
            "name": field,
            "datatype": POINTFIELD_FLOAT32,
            "count": 1,
        }
        for field in fields
    ]


def _normalize_field_specs(
    fields: Sequence[str],
    field_specs: Optional[Sequence[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    if field_specs is None:
        return _default_field_specs(fields)

    spec_map = {spec["name"]: spec for spec in field_specs}
    normalized = []

    for field in fields:
        if field in spec_map:
            spec = dict(spec_map[field])
            spec.setdefault("count", 1)
            spec.setdefault("datatype", POINTFIELD_FLOAT32)
            normalized.append(spec)
        else:
            normalized.append(
                {
                    "name": field,
                    "datatype": POINTFIELD_FLOAT32,
                    "count": 1,
                }
            )

    return normalized


def _pcd_layout_from_specs(
    specs: Sequence[dict[str, Any]],
) -> tuple[list[str], list[str], list[str], list[str]]:
    field_names: list[str] = []
    sizes: list[str] = []
    types: list[str] = []
    counts: list[str] = []

    for spec in specs:
        datatype = int(spec.get("datatype", POINTFIELD_FLOAT32))
        size, pcd_type, _ = POINTFIELD_TO_PCD.get(
            datatype,
            POINTFIELD_TO_PCD[POINTFIELD_FLOAT32],
        )

        field_names.append(str(spec["name"]))
        sizes.append(size)
        types.append(pcd_type)
        counts.append(str(int(spec.get("count", 1))))

    return field_names, sizes, types, counts


def _make_header(
    point_count: int,
    field_names: Sequence[str],
    sizes: Sequence[str],
    types: Sequence[str],
    counts: Sequence[str],
    pcd_format: str,
) -> str:
    return "\n".join(
        [
            "# .PCD v0.7 - Point Cloud Data file format",
            "VERSION 0.7",
            f"FIELDS {' '.join(field_names)}",
            f"SIZE {' '.join(sizes)}",
            f"TYPE {' '.join(types)}",
            f"COUNT {' '.join(counts)}",
            f"WIDTH {point_count}",
            "HEIGHT 1",
            "VIEWPOINT 0 0 0 1 0 0 0",
            f"POINTS {point_count}",
            f"DATA {pcd_format}",
        ]
    )


def _write_ascii(path: Path, header: str, rows: Sequence[Sequence[Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n")

        for row in rows:
            values = [str(value) for value in row]
            f.write(" ".join(values))
            f.write("\n")


def _struct_format_from_specs(specs: Sequence[dict[str, Any]]) -> str:
    format_chars: list[str] = []

    for spec in specs:
        datatype = int(spec.get("datatype", POINTFIELD_FLOAT32))
        count = int(spec.get("count", 1))
        _, _, struct_char = POINTFIELD_TO_PCD.get(
            datatype,
            POINTFIELD_TO_PCD[POINTFIELD_FLOAT32],
        )

        format_chars.extend([struct_char] * count)

    return "<" + "".join(format_chars)


def _flatten_binary_row(
    row: Sequence[Any],
    specs: Sequence[dict[str, Any]],
) -> list[Any]:
    flattened: list[Any] = []

    for value, spec in zip(row, specs):
        count = int(spec.get("count", 1))

        if count == 1:
            if hasattr(value, "item"):
                value = value.item()

            flattened.append(value)
            continue

        if hasattr(value, "tolist"):
            values = value.tolist()
        else:
            values = list(value)

        if len(values) != count:
            raise ValueError(
                f"Field {spec['name']} requires {count} values, got {len(values)}"
            )

        flattened.extend(values)

    return flattened


def _write_binary(
    path: Path,
    header: str,
    rows: Sequence[Sequence[Any]],
    specs: Sequence[dict[str, Any]],
) -> None:
    row_struct = struct.Struct(_struct_format_from_specs(specs))

    with path.open("wb") as f:
        f.write(header.encode("utf-8"))
        f.write(b"\n")

        for row in rows:
            flattened = _flatten_binary_row(row, specs)
            f.write(row_struct.pack(*flattened))


def _write_binary_compressed(
    path: Path,
    header: str,
    rows: Sequence[Sequence[Any]],
    specs: Sequence[dict[str, Any]],
) -> None:
    raise NotImplementedError(
        "binary_compressed PCD export is connected but not implemented yet. "
        "Use ascii or binary."
    )


def export_pcd(
    points: Iterable,
    output_path: PathLike,
    fields: Optional[Sequence[str]] = None,
    field_specs: Optional[Sequence[dict[str, Any]]] = None,
    pcd_format: str = "ascii",
) -> Path:
    """
    PointCloud 데이터를 PCD로 저장한다.
    ROS2 / sensor_msgs import 없이 동작한다.
    """
    path = to_path(output_path)
    ensure_parent_dir(path)

    pcd_format = pcd_format.lower().strip()

    if pcd_format not in {"ascii", "binary", "binary_compressed"}:
        raise ValueError(f"Unsupported PCD format: {pcd_format}")

    rows, fields = _normalize_points(points, fields)
    specs = _normalize_field_specs(fields, field_specs)
    point_count = len(rows)

    field_names, sizes, types, counts = _pcd_layout_from_specs(specs)

    header = _make_header(
        point_count=point_count,
        field_names=field_names,
        sizes=sizes,
        types=types,
        counts=counts,
        pcd_format=pcd_format,
    )

    if pcd_format == "ascii":
        _write_ascii(path, header, rows)
    elif pcd_format == "binary":
        _write_binary(path, header, rows, specs)
    elif pcd_format == "binary_compressed":
        _write_binary_compressed(path, header, rows, specs)

    return path