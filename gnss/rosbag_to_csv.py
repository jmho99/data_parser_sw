#!/usr/bin/env python3

import os
import csv
import math
import argparse
import re
import yaml
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

def detect_storage_id(bag_path: str) -> str:
    metadata_path = os.path.join(bag_path, "metadata.yaml")

    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = yaml.safe_load(f)

        storage_id = metadata.get("rosbag2_bagfile_information", {}).get("storage_identifier")
        if storage_id:
            return storage_id

    # metadata.yaml에서 못 찾으면 파일 확장자로 추정
    files = os.listdir(bag_path)

    if any(name.endswith(".mcap") for name in files):
        return "mcap"

    if any(name.endswith(".db3") for name in files):
        return "sqlite3"

    raise RuntimeError(
        f"Cannot detect rosbag storage type in: {bag_path}\n"
        "Expected .mcap or .db3 file, or metadata.yaml with storage_identifier."
    )
    
def sanitize_topic_name(topic_name: str) -> str:
    name = topic_name.strip("/")
    name = name.replace("/", "_")
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
    if not name:
        name = "root"
    return name


def stamp_to_sec(stamp) -> float:
    return float(stamp.sec) + float(stamp.nanosec) * 1e-9


def bag_time_to_sec(t_nsec: int) -> float:
    return float(t_nsec) * 1e-9


def get_header_time_or_bag_time(msg, bag_time_nsec: int) -> float:
    if hasattr(msg, "header"):
        return stamp_to_sec(msg.header.stamp)
    return bag_time_to_sec(bag_time_nsec)


def get_fieldnames(msg_type: str):
    if msg_type == "sensor_msgs/msg/NavSatFix":
        return [
            "bag_time",
            "header_time",
            "frame_id",
            "latitude",
            "longitude",
            "altitude",
            "status",
            "service",
            "cov_xx",
            "cov_yy",
            "cov_zz",
            "cov_xy",
            "cov_xz",
            "cov_yz",
            "position_covariance_type",
        ]

    if msg_type == "nav_msgs/msg/Odometry":
        return [
            "bag_time",
            "header_time",
            "frame_id",
            "child_frame_id",
            "x",
            "y",
            "z",
            "qx",
            "qy",
            "qz",
            "qw",
            "vx",
            "vy",
            "vz",
            "wx",
            "wy",
            "wz",
        ]

    if msg_type == "geometry_msgs/msg/PoseStamped":
        return [
            "bag_time",
            "header_time",
            "frame_id",
            "x",
            "y",
            "z",
            "qx",
            "qy",
            "qz",
            "qw",
        ]

    if msg_type == "geometry_msgs/msg/TwistStamped":
        return [
            "bag_time",
            "header_time",
            "frame_id",
            "linear_x",
            "linear_y",
            "linear_z",
            "angular_x",
            "angular_y",
            "angular_z",
        ]

    if msg_type == "sensor_msgs/msg/Imu":
        return [
            "bag_time",
            "header_time",
            "frame_id",
            "ori_x",
            "ori_y",
            "ori_z",
            "ori_w",
            "ang_vel_x",
            "ang_vel_y",
            "ang_vel_z",
            "lin_acc_x",
            "lin_acc_y",
            "lin_acc_z",
        ]

    if msg_type == "nmea_msgs/msg/Sentence":
        return [
            "bag_time",
            "header_time",
            "frame_id",
            "sentence",
        ]

    return None


def message_to_row(msg, msg_type: str, bag_time_nsec: int):
    bag_time = bag_time_to_sec(bag_time_nsec)
    header_time = get_header_time_or_bag_time(msg, bag_time_nsec)

    if msg_type == "sensor_msgs/msg/NavSatFix":
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

    if msg_type == "nav_msgs/msg/Odometry":
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        v = msg.twist.twist.linear
        w = msg.twist.twist.angular

        return {
            "bag_time": bag_time,
            "header_time": header_time,
            "frame_id": msg.header.frame_id,
            "child_frame_id": msg.child_frame_id,
            "x": p.x,
            "y": p.y,
            "z": p.z,
            "qx": q.x,
            "qy": q.y,
            "qz": q.z,
            "qw": q.w,
            "vx": v.x,
            "vy": v.y,
            "vz": v.z,
            "wx": w.x,
            "wy": w.y,
            "wz": w.z,
        }

    if msg_type == "geometry_msgs/msg/PoseStamped":
        p = msg.pose.position
        q = msg.pose.orientation

        return {
            "bag_time": bag_time,
            "header_time": header_time,
            "frame_id": msg.header.frame_id,
            "x": p.x,
            "y": p.y,
            "z": p.z,
            "qx": q.x,
            "qy": q.y,
            "qz": q.z,
            "qw": q.w,
        }

    if msg_type == "geometry_msgs/msg/TwistStamped":
        v = msg.twist.linear
        w = msg.twist.angular

        return {
            "bag_time": bag_time,
            "header_time": header_time,
            "frame_id": msg.header.frame_id,
            "linear_x": v.x,
            "linear_y": v.y,
            "linear_z": v.z,
            "angular_x": w.x,
            "angular_y": w.y,
            "angular_z": w.z,
        }

    if msg_type == "sensor_msgs/msg/Imu":
        q = msg.orientation
        w = msg.angular_velocity
        a = msg.linear_acceleration

        return {
            "bag_time": bag_time,
            "header_time": header_time,
            "frame_id": msg.header.frame_id,
            "ori_x": q.x,
            "ori_y": q.y,
            "ori_z": q.z,
            "ori_w": q.w,
            "ang_vel_x": w.x,
            "ang_vel_y": w.y,
            "ang_vel_z": w.z,
            "lin_acc_x": a.x,
            "lin_acc_y": a.y,
            "lin_acc_z": a.z,
        }

    if msg_type == "nmea_msgs/msg/Sentence":
        return {
            "bag_time": bag_time,
            "header_time": header_time,
            "frame_id": msg.header.frame_id,
            "sentence": msg.sentence,
        }

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bag_path", help="ROS2 bag directory path")
    parser.add_argument("-o", "--output_dir", default="csv_output")
    parser.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help="Optional topic list. Example: --topics /fix /gps/fix /odom",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    storage_id = detect_storage_id(args.bag_path)
    print(f"[INFO] Detected storage_id: {storage_id}")

    storage_options = rosbag2_py.StorageOptions(
        uri=args.bag_path,
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

    selected_topics = set(args.topics) if args.topics else set(type_map.keys())

    supported_types = {
        "sensor_msgs/msg/NavSatFix",
        "nav_msgs/msg/Odometry",
        "geometry_msgs/msg/PoseStamped",
        "geometry_msgs/msg/TwistStamped",
        "sensor_msgs/msg/Imu",
        "nmea_msgs/msg/Sentence",
        "gnss/fix",
        "gps/fix",
    }

    writers = {}
    files = {}
    msg_classes = {}

    print("[INFO] Topics in bag:")
    for topic, msg_type in type_map.items():
        mark = "SUPPORTED" if msg_type in supported_types else "SKIP"
        print(f"  {topic:40s} {msg_type:35s} {mark}")

    while reader.has_next():
        topic, data, t_nsec = reader.read_next()

        if topic not in selected_topics:
            continue

        msg_type = type_map.get(topic)
        if msg_type not in supported_types:
            continue

        if topic not in msg_classes:
            msg_classes[topic] = get_message(msg_type)

        msg = deserialize_message(data, msg_classes[topic])
        row = message_to_row(msg, msg_type, t_nsec)

        if row is None:
            continue

        if topic not in writers:
            filename = sanitize_topic_name(topic) + ".csv"
            path = os.path.join(args.output_dir, filename)

            f = open(path, "w", newline="")
            files[topic] = f

            fieldnames = get_fieldnames(msg_type)
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            writers[topic] = writer
            print(f"[INFO] Writing {topic} -> {path}")

        writers[topic].writerow(row)

    for f in files.values():
        f.close()

    print("[DONE] CSV extraction complete.")


if __name__ == "__main__":
    main()
