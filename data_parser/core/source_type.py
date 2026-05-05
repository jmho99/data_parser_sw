from enum import Enum


class SourceType(str, Enum):
    ROSBAG = "rosbag"
    VIDEO_FILE = "video_file"
    IMAGE_DIR = "image_dir"
    CSV_FILE = "csv_file"
    LIVE_DEVICE = "live_device"


def parse_source_type(value: str) -> SourceType:
    try:
        return SourceType(value)
    except ValueError:
        valid_values = ", ".join(item.value for item in SourceType)
        raise ValueError(
            f"Unsupported source_type: {value}. "
            f"Valid source_type values are: {valid_values}"
        )