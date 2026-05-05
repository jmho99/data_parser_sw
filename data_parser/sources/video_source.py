from __future__ import annotations

from typing import Iterator, Any

from data_parser.sources.base_source import BaseSource


class VideoSource(BaseSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self.cap = None

    def open(self) -> None:
        input_config = self.config.get("input", {})
        video_path = input_config.get("path")

        if video_path is None:
            raise ValueError("input.path is required for video_file source")

        self.video_path = video_path

        # 나중에 cv2.VideoCapture 연결
        # self.cap = cv2.VideoCapture(str(video_path))

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def read(self) -> Iterator[Any]:
        """
        이후 OpenCV를 사용해서 아래 형태로 반환 예정.

        yield {
            "frame_index": frame_index,
            "frame": frame,
            "timestamp": timestamp,
        }
        """
        raise NotImplementedError("VideoSource.read() is not implemented yet")