from __future__ import annotations

from data_parser.core.source_type import SourceType, parse_source_type
from data_parser.sources.base_source import BaseSource
from data_parser.sources.rosbag_source import RosbagSource
from data_parser.sources.video_source import VideoSource
from data_parser.sources.image_dir_source import ImageDirSource


def create_source(config: dict) -> BaseSource:
    input_config = config.get("input", {})
    source_type_value = input_config.get("source_type")

    if source_type_value is None:
        raise ValueError("input.source_type is required")

    source_type = parse_source_type(source_type_value)

    if source_type == SourceType.ROSBAG:
        return RosbagSource(config)

    if source_type == SourceType.VIDEO_FILE:
        return VideoSource(config)

    if source_type == SourceType.IMAGE_DIR:
        return ImageDirSource(config)

    raise NotImplementedError(f"Source type is not implemented yet: {source_type.value}")