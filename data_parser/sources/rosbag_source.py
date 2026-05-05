from __future__ import annotations

from typing import Iterator, Any

from data_parser.sources.base_source import BaseSource


class RosbagSource(BaseSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self.reader = None

    def open(self) -> None:
        input_config = self.config.get("input", {})
        rosbag_config = self.config.get("rosbag", {})

        bag_path = input_config.get("path")
        storage_id = rosbag_config.get("storage_id", "auto")

        if bag_path is None:
            raise ValueError("input.path is required for rosbag source")

        # 실제 rosbag2_py reader 연결은 다음 단계에서 구현
        self.bag_path = bag_path
        self.storage_id = storage_id

    def close(self) -> None:
        self.reader = None

    def read(self) -> Iterator[Any]:
        """
        이후 rosbag2_py를 사용해서 아래 형태로 반환 예정.

        yield {
            "topic": topic,
            "msg": msg,
            "timestamp": timestamp,
            "msg_type": msg_type,
        }
        """
        raise NotImplementedError("RosbagSource.read() is not implemented yet")