from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

from data_parser.utils.path_utils import ensure_parent_dir, to_path


PathLike = Union[str, Path]

DEFAULT_FIELD_ORDER = ["x", "y", "z", "intensity", "rgb"]


def _to_list(points):
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
):
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


def export_pcd(
    points: Iterable,
    output_path: PathLike,
    fields: Optional[Sequence[str]] = None,
) -> Path:
    """
    PointCloud 데이터를 ASCII PCD로 저장.

    지원 입력:
        [[x, y, z], ...]
        [[x, y, z, intensity], ...]
        [{"x": 1, "y": 2, "z": 3, "intensity": 10}, ...]

    ROS PointCloud2 메시지 파싱은 여기서 하지 않고,
    sensors/lidar/bag_to_pcd.py에서 points 형태로 변환한 뒤 넘기는 것을 권장.
    """
    path = to_path(output_path)
    ensure_parent_dir(path)

    rows, fields = _normalize_points(points, fields)
    point_count = len(rows)

    size = ["4"] * len(fields)
    field_type = ["F"] * len(fields)
    count = ["1"] * len(fields)

    header = "\n".join(
        [
            "# .PCD v0.7 - Point Cloud Data file format",
            "VERSION 0.7",
            f"FIELDS {' '.join(fields)}",
            f"SIZE {' '.join(size)}",
            f"TYPE {' '.join(field_type)}",
            f"COUNT {' '.join(count)}",
            f"WIDTH {point_count}",
            "HEIGHT 1",
            "VIEWPOINT 0 0 0 1 0 0 0",
            f"POINTS {point_count}",
            "DATA ascii",
        ]
    )

    with path.open("w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n")

        for row in rows:
            values = [str(float(value)) for value in row]
            f.write(" ".join(values))
            f.write("\n")

    return path