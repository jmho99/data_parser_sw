from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Literal

import yaml


RosbagBackend = Literal["auto", "rosbags", "ros2"]


@dataclass(frozen=True)
class RosbagRecord:
    topic: str
    msg: Any
    timestamp: int
    msg_type: str


def detect_storage_id(bag_path: str | Path) -> str:
    """Detect rosbag2 storage type from metadata.yaml or bag file extension."""
    path = Path(bag_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"ROS2 bag path does not exist: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"ROS2 bag path must be a directory: {path}")

    metadata_path = path / "metadata.yaml"
    if metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8", errors="ignore") as f:
            metadata = yaml.safe_load(f) or {}

        info = metadata.get("rosbag2_bagfile_information", {}) or {}
        storage_id = info.get("storage_identifier") or info.get("storage_id")
        if storage_id:
            return str(storage_id)

    if any(path.glob("*.mcap")):
        return "mcap"

    if any(path.glob("*.db3")):
        return "sqlite3"

    raise RuntimeError(
        f"Cannot detect rosbag storage type in: {path}\n"
        "Expected .mcap or .db3 file, or metadata.yaml with storage_identifier."
    )


class _BaseOpenedReader:
    topic_type_map: dict[str, str]

    def open(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def messages(self, topics: Iterable[str] | None = None) -> Iterator[RosbagRecord]:
        raise NotImplementedError


class _RosbagsReader(_BaseOpenedReader):
    def __init__(self, bag_path: str | Path, typestore_name: str = "ROS2_HUMBLE") -> None:
        self.bag_path = Path(bag_path).expanduser().resolve()
        self.typestore_name = typestore_name
        self._reader = None
        self.topic_type_map: dict[str, str] = {}

    def open(self) -> None:
        try:
            from rosbags.highlevel import AnyReader
            from rosbags.typesys import Stores, get_typestore
        except ImportError as exc:
            raise ImportError(
                "rosbags backend를 사용하려면 rosbags가 필요합니다. "
                "설치: pip install rosbags"
            ) from exc

        store_name = self.typestore_name.upper()
        store = getattr(Stores, store_name, None)
        if store is None:
            valid = ", ".join(name for name in dir(Stores) if name.startswith("ROS2_"))
            raise ValueError(f"Unsupported rosbags typestore: {store_name}. valid={valid}")

        typestore = get_typestore(store)

        try:
            self._reader = AnyReader([self.bag_path], default_typestore=typestore)
        except TypeError:
            self._reader = AnyReader([self.bag_path])

        self._reader.open()
        self.topic_type_map = {
            connection.topic: connection.msgtype
            for connection in self._reader.connections
        }

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
            self._reader = None

    def messages(self, topics: Iterable[str] | None = None) -> Iterator[RosbagRecord]:
        if self._reader is None:
            raise RuntimeError("Rosbags reader is not opened")

        topic_set = set(topics) if topics else None
        connections = [
            connection
            for connection in self._reader.connections
            if topic_set is None or connection.topic in topic_set
        ]

        for connection, timestamp, rawdata in self._reader.messages(connections=connections):
            msg = self._reader.deserialize(rawdata, connection.msgtype)
            yield RosbagRecord(
                topic=connection.topic,
                msg=msg,
                timestamp=int(timestamp),
                msg_type=connection.msgtype,
            )


class _Rosbag2PyReader(_BaseOpenedReader):
    def __init__(self, bag_path: str | Path, storage_id: str = "auto") -> None:
        self.bag_path = Path(bag_path).expanduser().resolve()
        self.storage_id = storage_id
        self._reader = None
        self._msg_classes: dict[str, Any] = {}
        self._deserialize_message = None
        self._get_message = None
        self.topic_type_map: dict[str, str] = {}

    def open(self) -> None:
        try:
            import rosbag2_py
            from rclpy.serialization import deserialize_message
            from rosidl_runtime_py.utilities import get_message
        except ImportError as exc:
            raise ImportError(
                "ros2 backend를 사용하려면 ROS2 Python 패키지(rosbag2_py, rclpy)가 필요합니다."
            ) from exc

        storage_id = detect_storage_id(self.bag_path) if self.storage_id == "auto" else self.storage_id

        storage_options = rosbag2_py.StorageOptions(
            uri=str(self.bag_path),
            storage_id=storage_id,
        )
        converter_options = rosbag2_py.ConverterOptions(
            input_serialization_format="cdr",
            output_serialization_format="cdr",
        )

        self._reader = rosbag2_py.SequentialReader()
        self._reader.open(storage_options, converter_options)
        self._deserialize_message = deserialize_message
        self._get_message = get_message

        self.topic_type_map = {
            topic_metadata.name: topic_metadata.type
            for topic_metadata in self._reader.get_all_topics_and_types()
        }

    def close(self) -> None:
        self._reader = None
        self._msg_classes.clear()

    def messages(self, topics: Iterable[str] | None = None) -> Iterator[RosbagRecord]:
        if self._reader is None or self._deserialize_message is None or self._get_message is None:
            raise RuntimeError("rosbag2_py reader is not opened")

        topic_set = set(topics) if topics else None

        while self._reader.has_next():
            topic, rawdata, timestamp = self._reader.read_next()

            if topic_set is not None and topic not in topic_set:
                continue

            msg_type = self.topic_type_map.get(topic)
            if msg_type is None:
                continue

            if topic not in self._msg_classes:
                self._msg_classes[topic] = self._get_message(msg_type)

            msg = self._deserialize_message(rawdata, self._msg_classes[topic])
            yield RosbagRecord(
                topic=topic,
                msg=msg,
                timestamp=int(timestamp),
                msg_type=msg_type,
            )


@contextmanager
def open_rosbag_reader(
    bag_path: str | Path,
    backend: str = "auto",
    storage_id: str = "auto",
    typestore_name: str = "ROS2_HUMBLE",
) -> Iterator[_BaseOpenedReader]:
    """
    Open a ROS2 bag with either pure-python rosbags or ROS2 rosbag2_py.

    backend:
        - "rosbags": pure Python reader. Recommended for Windows distribution.
        - "ros2": ROS2 rosbag2_py reader.
        - "auto": try rosbags first, then ros2 fallback.
    """
    normalized_backend = backend.lower().strip()

    if normalized_backend in {"pure", "pure-python", "no-ros", "no_ros"}:
        normalized_backend = "rosbags"

    if normalized_backend not in {"auto", "rosbags", "ros2"}:
        raise ValueError("backend must be one of: auto, rosbags, ros2")

    errors: list[Exception] = []
    candidates: list[_BaseOpenedReader]

    if normalized_backend == "rosbags":
        candidates = [_RosbagsReader(bag_path, typestore_name=typestore_name)]
    elif normalized_backend == "ros2":
        candidates = [_Rosbag2PyReader(bag_path, storage_id=storage_id)]
    else:
        candidates = [
            _RosbagsReader(bag_path, typestore_name=typestore_name),
            _Rosbag2PyReader(bag_path, storage_id=storage_id),
        ]

    reader: _BaseOpenedReader | None = None

    for candidate in candidates:
        try:
            candidate.open()
            reader = candidate
            break
        except Exception as exc:
            errors.append(exc)

    if reader is None:
        detail = "\n".join(f"- {type(exc).__name__}: {exc}" for exc in errors)
        raise RuntimeError(f"ROS2 bag reader를 열지 못했습니다.\n{detail}")

    try:
        yield reader
    finally:
        reader.close()