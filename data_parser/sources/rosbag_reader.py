from __future__ import annotations

import sqlite3
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


@dataclass(frozen=True)
class ResolvedBagPath:
    kind: str
    path: Path
    storage_id: str


def _as_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def resolve_bag_path(bag_path: str | Path) -> ResolvedBagPath:
    """
    사용자가 선택한 경로를 실제로 읽을 수 있는 bag 경로로 보정한다.

    지원:
    - metadata.yaml이 있는 rosbag2 폴더
    - 한 단계 아래에 metadata.yaml이 있는 경우 자동 탐색
    - metadata.yaml 없이 .db3 파일만 있는 폴더
    - metadata.yaml 없이 .mcap 파일만 있는 폴더
    - .db3 / .mcap 파일 직접 선택
    """
    path = _as_path(bag_path)

    if not path.exists():
        raise FileNotFoundError(f"ROS2 bag path does not exist: {path}")

    if path.is_file():
        suffix = path.suffix.lower()

        if suffix == ".db3":
            return ResolvedBagPath(kind="db3_direct", path=path, storage_id="sqlite3")

        if suffix == ".mcap":
            return ResolvedBagPath(kind="mcap_direct", path=path, storage_id="mcap")

        raise ValueError(f"지원하지 않는 bag 파일 형식입니다: {path}")

    metadata_path = path / "metadata.yaml"

    if metadata_path.exists():
        storage_id = _storage_id_from_metadata(metadata_path)

        if not storage_id:
            storage_id = _storage_id_from_files(path)

        return ResolvedBagPath(
            kind="rosbag2_dir",
            path=path,
            storage_id=storage_id,
        )

    child_metadata_paths = sorted(path.glob("*/metadata.yaml"))

    if len(child_metadata_paths) == 1:
        child_bag_dir = child_metadata_paths[0].parent
        storage_id = _storage_id_from_metadata(child_metadata_paths[0])

        if not storage_id:
            storage_id = _storage_id_from_files(child_bag_dir)

        return ResolvedBagPath(
            kind="rosbag2_dir",
            path=child_bag_dir,
            storage_id=storage_id,
        )

    if len(child_metadata_paths) > 1:
        candidates = "\n".join(f"  - {p.parent}" for p in child_metadata_paths)
        raise RuntimeError(
            "선택한 폴더 아래에 rosbag 폴더가 여러 개 있습니다. "
            "metadata.yaml이 있는 실제 bag 폴더를 직접 선택해주세요.\n"
            f"{candidates}"
        )

    db3_files = sorted(path.glob("*.db3"))
    mcap_files = sorted(path.glob("*.mcap"))

    if db3_files and mcap_files:
        raise RuntimeError(
            "metadata.yaml 없이 .db3와 .mcap 파일이 함께 있습니다. "
            "어떤 storage를 읽어야 할지 알 수 없으므로 실제 bag 폴더를 다시 선택해주세요."
        )

    if len(db3_files) == 1:
        return ResolvedBagPath(kind="db3_direct", path=db3_files[0], storage_id="sqlite3")

    if len(db3_files) > 1:
        return ResolvedBagPath(kind="db3_dir", path=path, storage_id="sqlite3")

    if len(mcap_files) == 1:
        return ResolvedBagPath(kind="mcap_direct", path=mcap_files[0], storage_id="mcap")

    if len(mcap_files) > 1:
        return ResolvedBagPath(kind="mcap_dir", path=path, storage_id="mcap")

    raise RuntimeError(
        "rosbag을 찾지 못했습니다.\n"
        f"선택 경로: {path}\n"
        "확인할 것:\n"
        "1. metadata.yaml이 있는 rosbag2 폴더인지\n"
        "2. 또는 폴더 안에 .db3 / .mcap 파일이 있는지\n"
        "3. 압축 해제 시 rosbag 폴더가 한 단계 더 안쪽에 들어가 있지는 않은지"
    )


def _storage_id_from_metadata(metadata_path: Path) -> str | None:
    try:
        with metadata_path.open("r", encoding="utf-8", errors="ignore") as f:
            metadata = yaml.safe_load(f) or {}
    except Exception:
        return None

    info = metadata.get("rosbag2_bagfile_information", {}) or {}

    storage_id = (
        info.get("storage_identifier")
        or info.get("storage_id")
        or metadata.get("storage_identifier")
        or metadata.get("storage_id")
    )

    if storage_id:
        return str(storage_id).strip().strip("\"'")

    return None


def _storage_id_from_files(bag_dir: Path) -> str:
    if any(bag_dir.glob("*.mcap")):
        return "mcap"

    if any(bag_dir.glob("*.db3")):
        return "sqlite3"

    return "auto"


def detect_storage_id(bag_path: str | Path) -> str:
    return resolve_bag_path(bag_path).storage_id


class _BaseOpenedReader:
    topic_type_map: dict[str, str]

    def open(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def messages(self, topics: Iterable[str] | None = None) -> Iterator[RosbagRecord]:
        raise NotImplementedError


class _RosbagsReader(_BaseOpenedReader):
    """
    metadata.yaml이 있는 일반 rosbag2 폴더용 reader.

    단, storage_id가 mcap 또는 sqlite3로 명확하면 아래 _make_pure_python_reader()에서
    이 reader보다 direct reader를 우선 사용한다.
    """

    def __init__(self, bag_dir: Path, typestore_name: str = "ROS2_HUMBLE") -> None:
        self.bag_dir = bag_dir
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

        metadata_path = self.bag_dir / "metadata.yaml"

        if not metadata_path.exists():
            raise FileNotFoundError(f"metadata.yaml이 없습니다: {metadata_path}")

        store_name = self.typestore_name.upper()
        store = getattr(Stores, store_name, None)

        if store is None:
            valid = ", ".join(name for name in dir(Stores) if name.startswith("ROS2_"))
            raise ValueError(f"Unsupported rosbags typestore: {store_name}. valid={valid}")

        typestore = get_typestore(store)

        try:
            self._reader = AnyReader([self.bag_dir], default_typestore=typestore)
        except TypeError:
            self._reader = AnyReader([self.bag_dir])

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


class _Sqlite3DirectReader(_BaseOpenedReader):
    """
    sqlite3/.db3 rosbag2를 ROS2 없이 직접 읽는 reader.

    .db3 내부:
    - topics 테이블에서 topic name / msg type 확인
    - messages 테이블에서 CDR serialized data 확인
    - rosbags typestore로 deserialize_cdr 수행
    """

    def __init__(
        self,
        db3_path_or_dir: Path,
        typestore_name: str = "ROS2_HUMBLE",
    ) -> None:
        self.db3_path_or_dir = db3_path_or_dir
        self.typestore_name = typestore_name
        self.db3_files: list[Path] = []
        self.topic_type_map: dict[str, str] = {}
        self._typestore = None

    def open(self) -> None:
        try:
            from rosbags.typesys import Stores, get_typestore
        except ImportError as exc:
            raise ImportError(
                "sqlite3 직접 reader를 사용하려면 rosbags가 필요합니다. "
                "설치: pip install rosbags"
            ) from exc

        if self.db3_path_or_dir.is_file():
            self.db3_files = [self.db3_path_or_dir]
        else:
            self.db3_files = sorted(self.db3_path_or_dir.glob("*.db3"))

        if not self.db3_files:
            raise FileNotFoundError(f".db3 파일을 찾지 못했습니다: {self.db3_path_or_dir}")

        store_name = self.typestore_name.upper()
        store = getattr(Stores, store_name, None)

        if store is None:
            valid = ", ".join(name for name in dir(Stores) if name.startswith("ROS2_"))
            raise ValueError(f"Unsupported rosbags typestore: {store_name}. valid={valid}")

        self._typestore = get_typestore(store)
        self.topic_type_map = self._read_topic_type_map()

    def close(self) -> None:
        self.db3_files = []
        self.topic_type_map = {}
        self._typestore = None

    def _read_topic_type_map(self) -> dict[str, str]:
        topic_type_map: dict[str, str] = {}

        for db3_file in self.db3_files:
            with sqlite3.connect(str(db3_file)) as conn:
                rows = conn.execute(
                    "SELECT name, type FROM topics ORDER BY id"
                ).fetchall()

            for topic_name, msg_type in rows:
                topic_type_map[str(topic_name)] = str(msg_type)

        return topic_type_map

    def messages(self, topics: Iterable[str] | None = None) -> Iterator[RosbagRecord]:
        if self._typestore is None:
            raise RuntimeError("SQLite3 direct reader is not opened")

        topic_set = set(topics) if topics else None

        for db3_file in self.db3_files:
            with sqlite3.connect(str(db3_file)) as conn:
                query = """
                    SELECT
                        messages.timestamp,
                        messages.data,
                        topics.name,
                        topics.type
                    FROM messages
                    JOIN topics ON messages.topic_id = topics.id
                    ORDER BY messages.timestamp
                """

                for timestamp, data, topic_name, msg_type in conn.execute(query):
                    topic_name = str(topic_name)
                    msg_type = str(msg_type)

                    if topic_set is not None and topic_name not in topic_set:
                        continue

                    rawdata = bytes(data)
                    msg = self._typestore.deserialize_cdr(rawdata, msg_type)

                    yield RosbagRecord(
                        topic=topic_name,
                        msg=msg,
                        timestamp=int(timestamp),
                        msg_type=msg_type,
                    )


class _McapDirectReader(_BaseOpenedReader):
    """
    .mcap 파일을 ROS2 없이 직접 읽는 reader.

    metadata.yaml이 있더라도 storage_id가 mcap이면
    rosbags.AnyReader 대신 이 reader를 사용한다.
    """

    def __init__(self, mcap_path_or_dir: Path) -> None:
        self.mcap_path_or_dir = mcap_path_or_dir
        self.mcap_files: list[Path] = []
        self.topic_type_map: dict[str, str] = {}

    def open(self) -> None:
        try:
            from mcap.reader import make_reader
        except ImportError as exc:
            raise ImportError(
                "MCAP 직접 reader를 사용하려면 mcap-ros2-support가 필요합니다. "
                "설치: pip install mcap-ros2-support"
            ) from exc

        if self.mcap_path_or_dir.is_file():
            self.mcap_files = [self.mcap_path_or_dir]
        else:
            self.mcap_files = sorted(self.mcap_path_or_dir.glob("*.mcap"))

        if not self.mcap_files:
            raise FileNotFoundError(f".mcap 파일을 찾지 못했습니다: {self.mcap_path_or_dir}")

        topic_type_map: dict[str, str] = {}

        for mcap_file in self.mcap_files:
            with mcap_file.open("rb") as f:
                reader = make_reader(f)
                summary = reader.get_summary()

                if summary is None:
                    continue

                channels = summary.channels or {}
                schemas = summary.schemas or {}

                for channel in channels.values():
                    schema = schemas.get(channel.schema_id)

                    if schema is None:
                        continue

                    topic_type_map[str(channel.topic)] = str(schema.name)

        self.topic_type_map = topic_type_map

    def close(self) -> None:
        self.mcap_files = []
        self.topic_type_map = {}

    def messages(self, topics: Iterable[str] | None = None) -> Iterator[RosbagRecord]:
        try:
            from mcap_ros2.reader import read_ros2_messages
        except ImportError as exc:
            raise ImportError(
                "MCAP ROS2 메시지를 읽으려면 mcap-ros2-support가 필요합니다. "
                "설치: pip install mcap-ros2-support"
            ) from exc

        topic_filter = list(topics) if topics else None

        for mcap_file in self.mcap_files:
            for mcap_msg in read_ros2_messages(
                str(mcap_file),
                topics=topic_filter,
                log_time_order=True,
            ):
                topic = str(mcap_msg.channel.topic)
                msg_type = str(mcap_msg.schema.name)
                timestamp = int(mcap_msg.log_time_ns)

                yield RosbagRecord(
                    topic=topic,
                    msg=mcap_msg.ros_msg,
                    timestamp=timestamp,
                    msg_type=msg_type,
                )


class _Rosbag2PyReader(_BaseOpenedReader):
    """
    ROS2가 설치된 환경용 fallback reader.
    Windows 배포용 기본 경로는 아님.
    """

    def __init__(self, bag_dir: Path, storage_id: str = "auto") -> None:
        self.bag_dir = bag_dir
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
                "ros2 backend를 사용하려면 ROS2 Python 패키지"
                "(rosbag2_py, rclpy)가 필요합니다."
            ) from exc

        storage_id = self.storage_id

        if storage_id == "auto":
            storage_id = detect_storage_id(self.bag_dir)

        storage_options = rosbag2_py.StorageOptions(
            uri=str(self.bag_dir),
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


def _make_pure_python_reader(
    resolved: ResolvedBagPath,
    typestore_name: str,
) -> _BaseOpenedReader:
    """
    pure-python reader 선택.

    중요:
    - mcap은 metadata.yaml이 있어도 rosbags.AnyReader를 우회한다.
      일부 bag에서 metadata.yaml의 storage plugin 값이 비어 있어
      AnyReaderError: Storage plugin '' not supported 가 발생할 수 있기 때문.
    - sqlite3도 metadata.yaml 여부와 관계없이 직접 읽을 수 있게 한다.
    """

    if resolved.storage_id == "mcap":
        return _McapDirectReader(mcap_path_or_dir=resolved.path)

    if resolved.storage_id == "sqlite3":
        return _Sqlite3DirectReader(
            db3_path_or_dir=resolved.path,
            typestore_name=typestore_name,
        )

    if resolved.kind == "rosbag2_dir":
        return _RosbagsReader(
            bag_dir=resolved.path,
            typestore_name=typestore_name,
        )

    if resolved.kind in {"db3_direct", "db3_dir"}:
        return _Sqlite3DirectReader(
            db3_path_or_dir=resolved.path,
            typestore_name=typestore_name,
        )

    if resolved.kind in {"mcap_direct", "mcap_dir"}:
        return _McapDirectReader(
            mcap_path_or_dir=resolved.path,
        )

    raise ValueError(f"지원하지 않는 resolved bag kind입니다: {resolved.kind}")


@contextmanager
def open_rosbag_reader(
    bag_path: str | Path,
    backend: str = "auto",
    storage_id: str = "auto",
    typestore_name: str = "ROS2_HUMBLE",
) -> Iterator[_BaseOpenedReader]:
    """
    ROS2 bag reader.

    backend:
        auto:
            pure-python reader를 먼저 사용하고, 실패하면 rosbag2_py를 시도한다.
        rosbags:
            ROS2 설치 없이 읽는다.
            metadata.yaml + .db3 -> sqlite3 direct reader
            metadata.yaml + .mcap -> mcap direct reader
            .db3 only        -> sqlite3 direct reader
            .mcap only       -> mcap direct reader
        ros2:
            ROS2 rosbag2_py reader 사용.
    """
    normalized_backend = backend.lower().strip()

    if normalized_backend in {"pure", "pure-python", "no-ros", "no_ros"}:
        normalized_backend = "rosbags"

    if normalized_backend not in {"auto", "rosbags", "ros2"}:
        raise ValueError("backend must be one of: auto, rosbags, ros2")

    resolved = resolve_bag_path(bag_path)

    if storage_id != "auto":
        resolved = ResolvedBagPath(
            kind=resolved.kind,
            path=resolved.path,
            storage_id=storage_id,
        )

    errors: list[Exception] = []

    if normalized_backend == "rosbags":
        candidates: list[_BaseOpenedReader] = [
            _make_pure_python_reader(resolved, typestore_name=typestore_name)
        ]
    elif normalized_backend == "ros2":
        if resolved.kind != "rosbag2_dir":
            raise RuntimeError(
                "ros2 backend는 metadata.yaml이 있는 rosbag2 폴더가 필요합니다. "
                f"현재 감지된 입력: kind={resolved.kind}, path={resolved.path}"
            )

        candidates = [
            _Rosbag2PyReader(
                bag_dir=resolved.path,
                storage_id=resolved.storage_id,
            )
        ]
    else:
        candidates = [
            _make_pure_python_reader(resolved, typestore_name=typestore_name),
        ]

        if resolved.kind == "rosbag2_dir":
            candidates.append(
                _Rosbag2PyReader(
                    bag_dir=resolved.path,
                    storage_id=resolved.storage_id,
                )
            )

    opened_reader: _BaseOpenedReader | None = None

    for candidate in candidates:
        try:
            candidate.open()
            opened_reader = candidate
            break
        except Exception as exc:
            errors.append(exc)

    if opened_reader is None:
        detail = "\n".join(f"- {type(exc).__name__}: {exc}" for exc in errors)
        raise RuntimeError(
            "ROS2 bag reader를 열지 못했습니다.\n"
            f"입력 경로: {Path(bag_path).expanduser()}\n"
            f"감지 결과: kind={resolved.kind}, path={resolved.path}, storage_id={resolved.storage_id}\n"
            f"{detail}"
        )

    try:
        yield opened_reader
    finally:
        opened_reader.close()