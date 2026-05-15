"""LiDAR CLI commands."""

from __future__ import annotations

import argparse


def add_lidar_subparser(sensor_subparsers) -> None:
    """Attach LiDAR commands to an existing top-level sensor subparser group."""
    lidar_parser = sensor_subparsers.add_parser("lidar", help="LiDAR converters")
    lidar_subparsers = lidar_parser.add_subparsers(dest="command", required=True)

    bag_pcd = lidar_subparsers.add_parser(
        "bag-to-pcd",
        help="ROS2 bag PointCloud2 topics to PCD files",
    )
    bag_pcd.add_argument("input", help="ROS2 bag directory path")
    bag_pcd.add_argument("-o", "--output-dir", default="lidar_output")
    bag_pcd.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help="Example: --topics /ouster/points /points_raw",
    )
    bag_pcd.add_argument(
        "--pcd-format",
        choices=["ascii", "binary", "binary_compressed"],
        default="ascii",
        help="PCD DATA format",
    )
    bag_pcd.add_argument(
        "--fields",
        default="xyz,intensity",
        help=(
            "Fields to save. Examples: xyz,intensity | "
            "xyz,intensity,ring,t | all"
        ),
    )
    bag_pcd.add_argument(
        "--every-n",
        type=int,
        default=1,
        help="Save every Nth point cloud frame",
    )
    bag_pcd.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Start saving from this matched frame index",
    )
    bag_pcd.add_argument(
        "--end-index",
        type=int,
        default=None,
        help="Stop saving after this matched frame index",
    )
    bag_pcd.add_argument(
        "--storage-id",
        default="auto",
        help="rosbag2 storage id: auto, sqlite3, mcap",
    )
    bag_pcd.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "rosbags", "ros2"],
        help="bag reader backend. Windows 배포는 rosbags 권장.",
    )
    bag_pcd.add_argument(
        "--skip-nans",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip points containing NaN values",
    )
    bag_pcd.add_argument(
        "--timestamp-filename",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use rosbag timestamp in output file name",
    )

    bag_pcd.set_defaults(func=run_lidar_command)


def _parse_fields(fields_text: str) -> list[str] | str:
    fields_text = fields_text.strip()

    if not fields_text or fields_text.lower() == "all":
        return "all"

    parsed: list[str] = []

    for item in fields_text.replace(" ", ",").split(","):
        item = item.strip()

        if not item:
            continue

        if item == "xyz":
            parsed.extend(["x", "y", "z"])
        else:
            parsed.append(item)

    return parsed


def run_lidar_command(args: argparse.Namespace) -> None:
    command = getattr(args, "command", None)

    if command != "bag-to-pcd":
        raise ValueError(f"Unsupported LiDAR command: {command}")

    from data_parser.sensors.lidar.bag_to_pcd import extract_lidar_bag_to_pcd

    result = extract_lidar_bag_to_pcd(
        bag_path=args.input,
        output_dir=args.output_dir,
        topics=args.topics,
        pcd_format=args.pcd_format,
        fields=_parse_fields(args.fields),
        every_n=args.every_n,
        start_index=args.start_index,
        end_index=args.end_index,
        storage_id=args.storage_id,
        backend=args.backend,
        skip_nans=args.skip_nans,
        use_timestamp_filename=args.timestamp_filename,
    )

    print(f"[DONE] saved_frames: {result['saved_frames']}")
    print(f"[DONE] output_dir: {result['output_dir']}")