"""IMU CLI commands."""

from __future__ import annotations

import argparse


def add_imu_subparser(sensor_subparsers) -> None:
    """Attach IMU commands to an existing top-level sensor subparser group."""
    imu_parser = sensor_subparsers.add_parser("imu", help="IMU converters")
    imu_subparsers = imu_parser.add_subparsers(dest="command", required=True)

    bag_csv = imu_subparsers.add_parser(
        "bag-to-csv",
        help="ROS2 bag IMU topics to CSV",
    )
    bag_csv.add_argument("input", help="ROS2 bag directory path")
    bag_csv.add_argument("-o", "--output-dir", default="imu_csv_output")
    bag_csv.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help="Example: --topics /imu/data /imu/raw",
    )
    bag_csv.add_argument(
        "--include-covariance",
        action="store_true",
        help="Also save IMU covariance arrays.",
    )
    bag_csv.set_defaults(func=_run_bag_to_csv)


def _run_bag_to_csv(args: argparse.Namespace) -> None:
    from data_parser.sensors.imu.bag_to_csv import extract_imu_rosbag_to_csv

    extract_imu_rosbag_to_csv(
        bag_path=args.input,
        output_dir=args.output_dir,
        topics=args.topics,
        include_covariance=args.include_covariance,
    )