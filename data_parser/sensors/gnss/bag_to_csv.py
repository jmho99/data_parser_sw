"""Extract GNSS-related ROS2 bag topics to CSV.

Supported message types:
- sensor_msgs/msg/NavSatFix -> fix CSV schema
- nmea_msgs/msg/Sentence   -> NMEA sentence CSV schema

This version can read bags without ROS2 by using the pure-python rosbags backend.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

from data_parser.sensors.gnss.gnss_config import (
    FIX_CSV_FIELDNAMES,
    NAVSATFIX_TYPE,
    NMEA_CSV_FIELDNAMES,
    NMEA_SENTENCE_TYPE,
    SUPPORTED_GNSS_ROSBAG_TYPES,
)
from data_parser.sources.rosbag_reader import detect_storage_id, open_rosbag_reader


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
    backend: str = "auto",
    storage_id: str = "auto",
) -> list[Path]:
    """Extract supported GNSS topics from a ROS2 bag to CSV files."""
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
            mark = "SUPPORTED" if msg_type in SUPPORTED_GNSS_ROSBAG_TYPES else "SKIP"
            print(f"  {topic:40s} {msg_type:35s} {mark}")

        target_topics = selected_topic_set if selected_topic_set else set(type_map.keys())

        try:
            for record in reader.messages(topics=target_topics):
                topic = record.topic
                msg_type = record.msg_type

                if msg_type not in SUPPORTED_GNSS_ROSBAG_TYPES:
                    continue

                row = message_to_row(record.msg, msg_type, record.timestamp)
                if row is None:
                    continue

                if topic not in writers:
                    fieldnames = get_fieldnames(msg_type)
                    if fieldnames is None:
                        continue

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

    extract_rosbag_to_csv(
        bag_path=args.bag_path,
        output_dir=args.output_dir,
        topics=args.topics,
        backend=args.backend,
        storage_id=args.storage_id,
    )


if __name__ == "__main__":
    main()