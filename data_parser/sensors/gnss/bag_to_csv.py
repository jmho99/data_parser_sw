"""Extract GNSS-related ROS2 bag topics to CSV.

Supported message types:
- sensor_msgs/msg/NavSatFix -> fix CSV schema
- nmea_msgs/msg/Sentence   -> NMEA sentence CSV schema

ROS2 packages are imported lazily inside extract_rosbag_to_csv(), so this module
can still be imported on a non-ROS machine for help/tests that do not read bags.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

import yaml

from data_parser.sensors.gnss.gnss_config import (
    FIX_CSV_FIELDNAMES,
    NAVSATFIX_TYPE,
    NMEA_CSV_FIELDNAMES,
    NMEA_SENTENCE_TYPE,
    SUPPORTED_GNSS_ROSBAG_TYPES,
)


def detect_storage_id(bag_path: str | Path) -> str:
    """Detect ROS2 bag storage type from metadata.yaml or bag file extension."""
    bag_path = Path(bag_path)
    metadata_path = bag_path / "metadata.yaml"

    if metadata_path.exists():
        with metadata_path.open("r") as f:
            metadata = yaml.safe_load(f) or {}

        storage_id = (
            metadata.get("rosbag2_bagfile_information", {})
            .get("storage_identifier")
        )
        if storage_id:
            return str(storage_id)

    if not bag_path.exists():
        raise FileNotFoundError(f"ROS2 bag path does not exist: {bag_path}")

    names = [p.name for p in bag_path.iterdir()]

    if any(name.endswith(".mcap") for name in names):
        return "mcap"

    if any(name.endswith(".db3") for name in names):
        return "sqlite3"

    raise RuntimeError(
        f"Cannot detect rosbag storage type in: {bag_path}\n"
        "Expected .mcap or .db3 file, or metadata.yaml with storage_identifier."
    )


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


def get_fieldnames(msg_type: str) -> list[str] | None:
    if msg_type == NAVSATFIX_TYPE:
        return FIX_CSV_FIELDNAMES

    if msg_type == NMEA_SENTENCE_TYPE:
        return NMEA_CSV_FIELDNAMES

    return None


def message_to_row(msg, msg_type: str, bag_time_nsec: int) -> dict | None:
    bag_time = bag_time_to_sec(bag_time_nsec)
    header_time = get_header_time_or_bag_time(msg, bag_time_nsec)

    if msg_type == NAVSATFIX_TYPE:
        cov = list(msg.position_covariance)
        return {
            "bag_time": bag_time,
            "header_time": header_time,
            "frame_id": msg.header.frame_id,
            "latitude": msg.latitude,
            "longitude": msg.longitude,
            "altitude": msg.altitude,
            "status": msg.status.status,
            "service": msg.status.service,
            "cov_xx": cov[0],
            "cov_yy": cov[4],
            "cov_zz": cov[8],
            "cov_xy": cov[1],
            "cov_xz": cov[2],
            "cov_yz": cov[5],
            "position_covariance_type": msg.position_covariance_type,
        }

    if msg_type == NMEA_SENTENCE_TYPE:
        return {
            "bag_time": bag_time,
            "header_time": header_time,
            "frame_id": msg.header.frame_id,
            "sentence": msg.sentence,
        }

    return None


def extract_rosbag_to_csv(
    bag_path: str | Path,
    output_dir: str | Path = "csv_output",
    topics: Iterable[str] | None = None,
) -> list[Path]:
    """Extract supported GNSS topics from a ROS2 bag to CSV files."""
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    bag_path = Path(bag_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    storage_id = detect_storage_id(bag_path)
    print(f"[INFO] Detected storage_id: {storage_id}")

    storage_options = rosbag2_py.StorageOptions(
        uri=str(bag_path),
        storage_id=storage_id,
    )
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )

    reader = rosbag2_py.SequentialReader()
    reader.open(storage_options, converter_options)

    topic_types = reader.get_all_topics_and_types()
    type_map = {t.name: t.type for t in topic_types}
    selected_topics = set(topics) if topics else set(type_map.keys())

    print("[INFO] Topics in bag:")
    for topic, msg_type in type_map.items():
        mark = "SUPPORTED" if msg_type in SUPPORTED_GNSS_ROSBAG_TYPES else "SKIP"
        print(f"  {topic:40s} {msg_type:35s} {mark}")

    writers: dict[str, csv.DictWriter] = {}
    files = {}
    msg_classes = {}
    output_paths: list[Path] = []

    try:
        while reader.has_next():
            topic, data, t_nsec = reader.read_next()

            if topic not in selected_topics:
                continue

            msg_type = type_map.get(topic)
            if msg_type not in SUPPORTED_GNSS_ROSBAG_TYPES:
                continue

            if topic not in msg_classes:
                msg_classes[topic] = get_message(msg_type)

            msg = deserialize_message(data, msg_classes[topic])
            row = message_to_row(msg, msg_type, t_nsec)
            if row is None:
                continue

            if topic not in writers:
                fieldnames = get_fieldnames(msg_type)
                if fieldnames is None:
                    continue

                output_path = output_dir / f"{sanitize_topic_name(topic)}.csv"
                f = output_path.open("w", newline="")
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

    print("[DONE] GNSS CSV extraction complete.")
    return output_paths


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extract GNSS ROS2 bag topics to CSV.")
    parser.add_argument("bag_path", help="ROS2 bag directory path")
    parser.add_argument("-o", "--output-dir", default="csv_output")
    parser.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help="Optional topic list. Example: --topics /fix /gnss/fix /nmea",
    )
    args = parser.parse_args()

    extract_rosbag_to_csv(
        bag_path=args.bag_path,
        output_dir=args.output_dir,
        topics=args.topics,
    )


if __name__ == "__main__":
    main()
