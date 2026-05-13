"""Convert ROS2 GNSS bag to KML through intermediate CSV."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any

from data_parser.sensors.gnss.csv_to_kml import fix_csv_to_kml, is_fix_csv


def _normalize_output_name(output_name: str) -> str:
    name = output_name.strip()

    if name.lower().endswith(".kml"):
        name = name[:-4]

    name = name.strip()

    if not name:
        raise ValueError("KML 파일 이름을 입력해야 합니다.")

    if "/" in name or "\\" in name:
        raise ValueError("파일 이름에는 경로 구분자를 넣지 마세요.")

    return name


def _normalize_topics(topics: list[str] | tuple[str, ...] | None) -> list[str] | None:
    if not topics:
        return None

    cleaned = [topic.strip() for topic in topics if topic and topic.strip()]
    return cleaned if cleaned else None


def _collect_csv_paths(result: Any, search_dir: str | Path) -> list[Path]:
    search_dir = Path(search_dir)
    paths: list[Path] = []

    if isinstance(result, Path):
        paths.append(result)
    elif isinstance(result, str):
        paths.append(Path(result))
    elif isinstance(result, dict):
        for value in result.values():
            if isinstance(value, (str, Path)):
                paths.append(Path(value))
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, (str, Path)):
                        paths.append(Path(item))
    elif isinstance(result, (list, tuple)):
        for item in result:
            if isinstance(item, (str, Path)):
                paths.append(Path(item))

    if not paths:
        paths = sorted(search_dir.glob("*.csv"))

    return paths


def _extract_bag_to_csv(
    bag_path: str | Path,
    output_dir: str | Path,
    topics: list[str] | None,
) -> list[Path]:
    from data_parser.sensors.gnss.bag_to_csv import extract_rosbag_to_csv

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = extract_rosbag_to_csv(
        bag_path=str(bag_path),
        output_dir=str(output_dir),
        topics=topics,
    )

    return _collect_csv_paths(result, output_dir)


def convert_gnss_bag_to_kml(
    bag_path: str | Path,
    output_path: str | Path | None = None,
    output_name: str | None = None,
    topics: list[str] | tuple[str, ...] | None = None,
    output_dir: str | Path | None = None,
    min_status: int = 0,
    max_cov_xy: float | None = None,
    point_step: int = 50,
    keep_csv: bool = True,
) -> dict[str, Path]:
    """
    ROS2 bag -> GNSS CSV -> KML 변환.

    GUI 호환을 위해 output_path와 output_dir 둘 다 받음.
    새 코드에서는 output_path 사용 권장.
    """

    bag_path = Path(bag_path)

    if output_path is None:
        output_path = output_dir

    if output_path is None:
        raise ValueError("output_path 또는 output_dir이 필요합니다.")

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    if output_name is None or not output_name.strip():
        output_name = bag_path.name

    output_name = _normalize_output_name(output_name)

    if not bag_path.exists():
        raise FileNotFoundError(f"bag_path가 존재하지 않습니다: {bag_path}")

    if not bag_path.is_dir():
        raise NotADirectoryError(f"bag_path는 ROS2 bag 폴더여야 합니다: {bag_path}")

    selected_topics = _normalize_topics(topics)

    if keep_csv:
        csv_output_dir = output_path
        cleanup_context = None
    else:
        cleanup_context = tempfile.TemporaryDirectory()
        csv_output_dir = Path(cleanup_context.name)

    try:
        csv_paths = _extract_bag_to_csv(
            bag_path=bag_path,
            output_dir=csv_output_dir,
            topics=selected_topics,
        )

        fix_csv_paths = [
            path for path in csv_paths
            if path.exists() and is_fix_csv(path)
        ]

        if not fix_csv_paths:
            raise RuntimeError("bag 변환 후 NavSatFix 형식 CSV를 찾지 못했습니다.")

        csv_path = fix_csv_paths[0]
        kml_path = output_path / f"{output_name}.kml"

        fix_csv_to_kml(
            input_csv=csv_path,
            output_kml=kml_path,
            min_status=min_status,
            max_cov_xy=max_cov_xy,
            point_step=point_step,
        )

        return {
            "csv_path": csv_path,
            "kml_path": kml_path,
        }

    finally:
        if cleanup_context is not None:
            cleanup_context.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert ROS2 GNSS bag to KML.")
    parser.add_argument("bag_path")
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--output-name", default=None)
    parser.add_argument("--topics", nargs="*", default=None)
    parser.add_argument("--min-status", type=int, default=0)
    parser.add_argument("--max-cov-xy", type=float, default=None)
    parser.add_argument("--point-step", type=int, default=50)
    parser.add_argument("--remove-csv", action="store_true")
    args = parser.parse_args()

    result = convert_gnss_bag_to_kml(
        bag_path=args.bag_path,
        output_path=args.output_path,
        output_name=args.output_name,
        topics=args.topics,
        min_status=args.min_status,
        max_cov_xy=args.max_cov_xy,
        point_step=args.point_step,
        keep_csv=not args.remove_csv,
    )

    print(f"[DONE] CSV: {result['csv_path']}")
    print(f"[DONE] KML: {result['kml_path']}")


if __name__ == "__main__":
    main()