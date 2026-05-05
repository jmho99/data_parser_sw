from __future__ import annotations

from pathlib import Path
from typing import Iterator, Any

from data_parser.sources.base_source import BaseSource


class ImageDirSource(BaseSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self.image_paths: list[Path] = []

    def open(self) -> None:
        input_config = self.config.get("input", {})
        image_dir_config = self.config.get("image_dir", {})

        image_dir = input_config.get("path")

        if image_dir is None:
            raise ValueError("input.path is required for image_dir source")

        image_dir = Path(image_dir)

        if not image_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {image_dir}")

        extensions = image_dir_config.get(
            "supported_extensions",
            [".jpg", ".jpeg", ".png", ".webp", ".bmp"],
        )

        recursive = image_dir_config.get("recursive", False)

        pattern = "**/*" if recursive else "*"

        self.image_paths = sorted(
            path
            for path in image_dir.glob(pattern)
            if path.suffix.lower() in extensions
        )

    def close(self) -> None:
        self.image_paths = []

    def read(self) -> Iterator[Any]:
        """
        이후 cv2.imread 또는 PIL로 실제 이미지 로드.

        yield {
            "frame_index": index,
            "path": image_path,
            "frame": frame,
        }
        """
        for index, image_path in enumerate(self.image_paths):
            yield {
                "frame_index": index,
                "path": image_path,
            }