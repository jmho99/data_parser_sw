"""GNSS CLI commands.

Use this from data_parser/cli/main_cli.py instead of changing configs/*.yaml or
templates/*.yaml.
"""

from __future__ import annotations

import argparse


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

    csv_kml = gnss_subparsers.add_parser(
        "csv-to-kml",
        help="GNSS fix CSV to KML",
    )
    csv_kml.add_argument("input", help="GNSS fix CSV path")
    csv_kml.add_argument("output", help="Output KML path")
    csv_kml.add_argument("--min-status", type=int, default=0)
    csv_kml.add_argument("--max-cov-xy", type=float, default=None)
    csv_kml.add_argument("--point-step", type=int, default=50)

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

    plt_csv = gnss_subparsers.add_parser(
        "plt-to-csv",
        help="GeoLife PLT to GNSS fix CSV",
    )
    plt_csv.add_argument("input", help="Input .plt path")
    plt_csv.add_argument("output", help="Output CSV path")
    plt_csv.add_argument("--frame-id", default="geolife")
    plt_csv.add_argument("--skip-header-lines", type=int, default=6)


def run_gnss_command(args: argparse.Namespace) -> bool:
    """Run GNSS command if args.sensor == 'gnss'. Return True if handled."""
    if getattr(args, "sensor", None) != "gnss":
        return False

    command = getattr(args, "command", None)

    if command == "bag-to-csv":
        from data_parser.sensors.gnss.bag_to_csv import extract_rosbag_to_csv

        extract_rosbag_to_csv(
            bag_path=args.input,
            output_dir=args.output_dir,
            topics=args.topics,
        )
        return True

    if command == "csv-to-kml":
        from data_parser.sensors.gnss.bag_to_kml import fix_csv_to_kml

        fix_csv_to_kml(
            input_csv=args.input,
            output_kml=args.output,
            min_status=args.min_status,
            max_cov_xy=args.max_cov_xy,
            point_step=args.point_step,
        )
        return True

    if command == "bag-to-kml":
        from data_parser.sensors.gnss.bag_to_kml import bag_to_kml

        bag_to_kml(
            bag_path=args.input,
            output_kml=args.output,
            topics=args.topics,
            min_status=args.min_status,
            max_cov_xy=args.max_cov_xy,
            point_step=args.point_step,
        )
        return True

    if command == "plt-to-csv":
        from data_parser.sensors.gnss.plt_to_csv import geolife_plt_to_fix_csv

        geolife_plt_to_fix_csv(
            input_plt=args.input,
            output_csv=args.output,
            frame_id=args.frame_id,
            skip_header_lines=args.skip_header_lines,
        )
        return True

    raise ValueError(f"Unsupported GNSS command: {command}")
