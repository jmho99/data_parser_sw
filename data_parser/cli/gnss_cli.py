"""GNSS CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path


def add_gnss_subparser(sensor_subparsers) -> None:
    """Attach GNSS commands to an existing top-level sensor subparser group."""
    gnss_parser = sensor_subparsers.add_parser("gnss", help="GNSS converters")
    gnss_subparsers = gnss_parser.add_subparsers(dest="command", required=True)

    bag_csv = gnss_subparsers.add_parser(
        "bag-to-csv",
        help="ROS2 bag GNSS topics to CSV",
    )
    bag_csv.add_argument("input", help="ROS2 bag directory path")
    bag_csv.add_argument("-o", "--output-dir", default="csv_output")
    bag_csv.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help="Example: --topics /fix /gnss/fix /nmea",
    )
    _add_rosbag_backend_args(bag_csv)
    bag_csv.set_defaults(func=_run_bag_to_csv)

    csv_kml = gnss_subparsers.add_parser(
        "csv-to-kml",
        help="GNSS fix CSV to KML",
    )
    csv_kml.add_argument("input", help="GNSS fix CSV path")
    csv_kml.add_argument("output", help="Output KML path")
    csv_kml.add_argument("--min-status", type=int, default=0)
    csv_kml.add_argument("--max-cov-xy", type=float, default=None)
    csv_kml.add_argument("--point-step", type=int, default=50)
    csv_kml.set_defaults(func=_run_csv_to_kml)

    bag_kml = gnss_subparsers.add_parser(
        "bag-to-kml",
        help="ROS2 bag GNSS fix topic to KML",
    )
    bag_kml.add_argument("input", help="ROS2 bag directory path")
    bag_kml.add_argument("output", help="Output KML path")
    bag_kml.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help="Example: --topics /fix /gnss/fix",
    )
    bag_kml.add_argument("--min-status", type=int, default=0)
    bag_kml.add_argument("--max-cov-xy", type=float, default=None)
    bag_kml.add_argument("--point-step", type=int, default=50)
    _add_rosbag_backend_args(bag_kml)
    bag_kml.set_defaults(func=_run_bag_to_kml)

    plt_csv = gnss_subparsers.add_parser(
        "plt-to-csv",
        help="GeoLife PLT to GNSS fix CSV",
    )
    plt_csv.add_argument("input", help="Input .plt path")
    plt_csv.add_argument("output", help="Output CSV path")
    plt_csv.add_argument("--frame-id", default="geolife")
    plt_csv.add_argument("--skip-header-lines", type=int, default=6)
    plt_csv.set_defaults(func=_run_plt_to_csv)


def _add_rosbag_backend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "rosbags", "ros2"],
        help="bag reader backend. Windows 배포는 rosbags 권장.",
    )
    parser.add_argument(
        "--storage-id",
        default="auto",
        help="rosbag2 storage id: auto, sqlite3, mcap. ros2 backend에서 주로 사용.",
    )


def _run_bag_to_csv(args: argparse.Namespace) -> None:
    from data_parser.sensors.gnss.bag_to_csv import extract_rosbag_to_csv

    extract_rosbag_to_csv(
        bag_path=args.input,
        output_dir=args.output_dir,
        topics=args.topics,
        backend=args.backend,
        storage_id=args.storage_id,
    )


def _run_csv_to_kml(args: argparse.Namespace) -> None:
    from data_parser.sensors.gnss.csv_to_kml import fix_csv_to_kml

    fix_csv_to_kml(
        input_csv=args.input,
        output_kml=args.output,
        min_status=args.min_status,
        max_cov_xy=args.max_cov_xy,
        point_step=args.point_step,
    )


def _run_bag_to_kml(args: argparse.Namespace) -> None:
    from data_parser.sensors.gnss.bag_to_kml import convert_gnss_bag_to_kml

    output = Path(args.output)

    result = convert_gnss_bag_to_kml(
        bag_path=args.input,
        output_path=output.parent if str(output.parent) else Path("."),
        output_name=output.name,
        topics=args.topics,
        min_status=args.min_status,
        max_cov_xy=args.max_cov_xy,
        point_step=args.point_step,
        keep_csv=True,
        backend=args.backend,
        storage_id=args.storage_id,
    )

    print(f"[DONE] CSV: {result['csv_path']}")
    print(f"[DONE] KML: {result['kml_path']}")


def _run_plt_to_csv(args: argparse.Namespace) -> None:
    from data_parser.sensors.gnss.plt_to_csv import geolife_plt_to_fix_csv

    geolife_plt_to_fix_csv(
        input_plt=args.input,
        output_csv=args.output,
        frame_id=args.frame_id,
        skip_header_lines=args.skip_header_lines,
    )


def run_gnss_command(args: argparse.Namespace) -> bool:
    if getattr(args, "sensor", None) != "gnss":
        return False

    if not hasattr(args, "func"):
        raise ValueError("GNSS command parser did not set args.func")

    args.func(args)
    return True