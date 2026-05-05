"""GNSS parser defaults.

This is a Python code-level default module, not configs/gnss.yaml.
Keep YAML config/template files unchanged.
"""

FIX_CSV_FIELDNAMES = [
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

NMEA_CSV_FIELDNAMES = [
    "bag_time",
    "header_time",
    "frame_id",
    "sentence",
]

SUPPORTED_GNSS_ROSBAG_TYPES = {
    "sensor_msgs/msg/NavSatFix",
    "nmea_msgs/msg/Sentence",
}

NAVSATFIX_TYPE = "sensor_msgs/msg/NavSatFix"
NMEA_SENTENCE_TYPE = "nmea_msgs/msg/Sentence"

DEFAULT_GNSS_TOPICS = [
    "/fix",
    "/gnss/fix",
    "/gps/fix",
    "/nmea",
    "/gnss/nmea",
]
