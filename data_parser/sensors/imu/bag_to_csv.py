"""Extract IMU ROS2 bag topics to CSV.

Supported message types:
- sensor_msgs/msg/Imu

This version can read bags without ROS2 by using the pure-python rosbags backend.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

from data_parser.sources.rosbag_reader import detect_storage_id, open_rosbag_reader


IMU_TYPE = "sensor_msgs/msg/Imu"
SUPPORTED_IMU_ROSBAG_TYPES = {
    IMU_TYPE,
}


BASE_IMU_CSV_FIELDNAMES = [
    "bag_time",
    "header_time",
    "timestamp_sec",
    "timestamp_nanosec",
    "frame_id",
    "orientation_x",
    "orientation_y",
    "orientation_z",
    "orientation_w",
    "angular_velocity_x",
    "angular_velocity_y",
    "angular_velocity_z",
    "linear_acceleration_x",
    "linear_acceleration_y",
    "linear_acceleration_z",
]


def sanitize_topic_name(topic_name: str) -> str:
    name = topic_name.strip("/").replace("/", "_")
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
    return name or "root"


def stamp_to_sec(stamp) -> float:
    return float(stamp.sec) + float(stamp.nanosec) * 1e-9


def bag_time_to_sec(t_nsec: int) -> float:
    return float(t_nsec) * 1e-9


def get_header_time_or_bag_time(msg, bag_time_nsec: int) -> float:
    if hasattr(msg, "header"):
        return stamp_to_sec(msg.header.stamp)
    return bag_time_to_sec(bag_time_nsec)


def covariance_fieldnames(prefix: str) -> list[str]:
    return [
        f"{prefix}_{row}{col}"
        for row in range(3)
        for col in range(3)
    ]


def get_fieldnames(include_covariance: bool = False) -> list[str]:
    fieldnames = list(BASE_IMU_CSV_FIELDNAMES)

    if include_covariance:
        fieldnames.extend(covariance_fieldnames("orientation_covariance"))
        fieldnames.extend(covariance_fieldnames("angular_velocity_covariance"))
        fieldnames.extend(covariance_fieldnames("linear_acceleration_covariance"))

    return fieldnames


def add_covariance_to_row(row: dict, prefix: str, values) -> None:
    cov = list(values)

    for index, value in enumerate(cov):
        r = index // 3
        c = index % 3
        row[f"{prefix}_{r}{c}"] = value


def imu_message_to_row(
    msg,
    bag_time_nsec: int,
    include_covariance: bool = False,
) -> dict:
    bag_time = bag_time_to_sec(bag_time_nsec)
    header_time = get_header_time_or_bag_time(msg, bag_time_nsec)

    row = {
        "bag_time": bag_time,
        "header_time": header_time,
        "timestamp_sec": msg.header.stamp.sec,
        "timestamp_nanosec": msg.header.stamp.nanosec,
        "frame_id": msg.header.frame_id,
        "orientation_x": msg.orientation.x,
        "orientation_y": msg.orientation.y,
        "orientation_z": msg.orientation.z,
        "orientation_w": msg.orientation.w,
        "angular_velocity_x": msg.angular_velocity.x,
        "angular_velocity_y": msg.angular_velocity.y,
        "angular_velocity_z": msg.angular_velocity.z,
        "linear_acceleration_x": msg.linear_acceleration.x,
        "linear_acceleration_y": msg.linear_acceleration.y,
        "linear_acceleration_z": msg.linear_acceleration.z,
    }

    if include_covariance:
        add_covariance_to_row(
            row,
            "orientation_covariance",
            msg.orientation_covariance,
        )
        add_covariance_to_row(
            row,
            "angular_velocity_covariance",
            msg.angular_velocity_covariance,
        )
        add_covariance_to_row(
            row,
            "linear_acceleration_covariance",
            msg.linear_acceleration_covariance,
        )

    return row


def extract_imu_rosbag_to_csv(
    bag_path: str | Path,
    output_dir: str | Path = "imu_csv_output",
    topics: Iterable[str] | None = None,
    include_covariance: bool = False,
    backend: str = "auto",
    storage_id: str = "auto",
) -> list[Path]:
    """Extract sensor_msgs/msg/Imu topics from a ROS2 bag to CSV files."""
    bag_path = Path(bag_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if storage_id == "auto":
        try:
            detected_storage_id = detect_storage_id(bag_path)
        except Exception:
            detected_storage_id = "auto"
    else:
        detected_storage_id = storage_id

    print(f"[INFO] backend: {backend}")
    print(f"[INFO] Detected storage_id: {detected_storage_id}")

    selected_topic_set = set(topics) if topics else None
    fieldnames = get_fieldnames(include_covariance=include_covariance)

    writers: dict[str, csv.DictWriter] = {}
    files = {}
    output_paths: list[Path] = []

    with open_rosbag_reader(
        bag_path=bag_path,
        backend=backend,
        storage_id=detected_storage_id,
    ) as reader:
        type_map = reader.topic_type_map

        print("[INFO] Topics in bag:")
        for topic, msg_type in type_map.items():
            mark = "SUPPORTED" if msg_type in SUPPORTED_IMU_ROSBAG_TYPES else "SKIP"
            print(f"  {topic:40s} {msg_type:35s} {mark}")

        target_topics = selected_topic_set if selected_topic_set else set(type_map.keys())

        try:
            for record in reader.messages(topics=target_topics):
                topic = record.topic
                msg_type = record.msg_type

                if msg_type not in SUPPORTED_IMU_ROSBAG_TYPES:
                    continue

                row = imu_message_to_row(
                    msg=record.msg,
                    bag_time_nsec=record.timestamp,
                    include_covariance=include_covariance,
                )

                if topic not in writers:
                    output_path = output_dir / f"{sanitize_topic_name(topic)}.csv"
                    f = output_path.open("w", newline="", encoding="utf-8")
                    files[topic] = f

                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writers[topic] = writer
                    output_paths.append(output_path)

                    print(f"[INFO] Writing {topic} -> {output_path}")

                writers[topic].writerow(row)

        finally:
            for f in files.values():
                f.close()

    if not output_paths:
        print("[WARN] No IMU CSV files were created.")
        print("[WARN] Check topic name and message type. Expected sensor_msgs/msg/Imu.")
    else:
        print("[DONE] IMU CSV extraction complete.")

    return output_paths


extract_rosbag_to_csv = extract_imu_rosbag_to_csv


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extract IMU ROS2 bag topics to CSV.")
    parser.add_argument("bag_path", help="ROS2 bag directory path")
    parser.add_argument("-o", "--output-dir", default="imu_csv_output")
    parser.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help="Optional topic list. Example: --topics /imu/data /imu/raw",
    )
    parser.add_argument(
        "--include-covariance",
        action="store_true",
        help="Also save orientation/angular_velocity/linear_acceleration covariance arrays.",
    )
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

    args = parser.parse_args()

    extract_imu_rosbag_to_csv(
        bag_path=args.bag_path,
        output_dir=args.output_dir,
        topics=args.topics,
        include_covariance=args.include_covariance,
        backend=args.backend,
        storage_id=args.storage_id,
    )


if __name__ == "__main__":
    main()