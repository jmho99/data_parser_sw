from __future__ import annotations

import argparse

from data_parser.cli.gnss_cli import add_gnss_subparser
from data_parser.cli.camera_cli import add_camera_subparser
from data_parser.cli.imu_cli import add_imu_subparser
from data_parser.cli.lidar_cli import add_lidar_subparser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data_parser",
        description="Sensor data parser CLI",
    )

    subparsers = parser.add_subparsers(
        dest="sensor",
        required=True,
    )

    add_gnss_subparser(subparsers)
    add_camera_subparser(subparsers)
    add_lidar_subparser(subparsers)
    add_imu_subparser(subparsers)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
        return

    parser.print_help()


if __name__ == "__main__":
    main()