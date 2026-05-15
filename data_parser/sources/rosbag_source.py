from __future__ import annotations

from typing import Any, Iterator

from data_parser.sources.base_source import BaseSource
from data_parser.sources.rosbag_reader import open_rosbag_reader


class RosbagSource(BaseSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self._context = None
        self._reader = None

    def open(self) -> None:
        input_config = self.config.get("input", {})
        rosbag_config = self.config.get("rosbag", {})

        bag_path = input_config.get("path")
        storage_id = rosbag_config.get("storage_id", "auto")
        backend = rosbag_config.get("backend", "auto")

        if bag_path is None:
            raise ValueError("input.path is required for rosbag source")

        self._context = open_rosbag_reader(
            bag_path=bag_path,
            backend=backend,
            storage_id=storage_id,
        )
        self._reader = self._context.__enter__()

    def close(self) -> None:
        if self._context is not None:
            self._context.__exit__(None, None, None)
        self._context = None
        self._reader = None

    def read(self) -> Iterator[Any]:
        """
        Yield records in a dict shape compatible with the older planned source API.
        """
        if self._reader is None:
            raise RuntimeError("RosbagSource is not opened")

        for record in self._reader.messages():
            yield {
                "topic": record.topic,
                "msg": record.msg,
                "timestamp": record.timestamp,
                "msg_type": record.msg_type,
            }