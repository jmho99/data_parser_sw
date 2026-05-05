import csv
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

from data_parser.utils.path_utils import ensure_parent_dir, to_path


PathLike = Union[str, Path]


def _collect_fieldnames(rows: list[dict]) -> list[str]:
    fieldnames = []

    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    return fieldnames


def export_csv(
    rows: Iterable,
    output_path: PathLike,
    fieldnames: Optional[Sequence[str]] = None,
    encoding: str = "utf-8",
) -> Path:
    """
    dict 리스트 또는 list/tuple 리스트를 CSV로 저장.

    예:
        export_csv([{"time": 1.0, "lat": 36.1}], "gnss.csv")

        export_csv(
            [[1.0, 36.1, 127.1]],
            "gnss.csv",
            fieldnames=["time", "lat", "lon"]
        )
    """
    path = to_path(output_path)
    ensure_parent_dir(path)

    rows = list(rows)

    with path.open("w", newline="", encoding=encoding) as f:
        if not rows:
            writer = csv.writer(f)

            if fieldnames:
                writer.writerow(fieldnames)

            return path

        first = rows[0]

        if isinstance(first, dict):
            if fieldnames is None:
                fieldnames = _collect_fieldnames(rows)

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                writer.writerow(row)

        else:
            writer = csv.writer(f)

            if fieldnames:
                writer.writerow(fieldnames)

            for row in rows:
                writer.writerow(row)

    return path