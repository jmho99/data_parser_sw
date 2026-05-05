from datetime import datetime, timezone
from typing import Any, Optional


def sec_to_ns(sec: float) -> int:
    return int(sec * 1_000_000_000)


def ns_to_sec(ns: int) -> float:
    return ns / 1_000_000_000.0


def stamp_to_sec(stamp: Any) -> Optional[float]:
    """
    ROS stamp, dict, tuple, int, float 등을 초 단위 float으로 변환.

    지원 예:
        stamp.sec, stamp.nanosec
        {"sec": 123, "nanosec": 456}
        (sec, nanosec)
        float seconds
        int nanoseconds 또는 seconds
    """
    if stamp is None:
        return None

    if isinstance(stamp, float):
        return stamp

    if isinstance(stamp, int):
        # 너무 큰 int는 nanosecond timestamp로 판단
        if stamp > 10_000_000_000:
            return ns_to_sec(stamp)
        return float(stamp)

    if isinstance(stamp, dict):
        sec = stamp.get("sec", 0)
        nanosec = stamp.get("nanosec", stamp.get("nsec", 0))
        return float(sec) + float(nanosec) * 1e-9

    if isinstance(stamp, (tuple, list)) and len(stamp) >= 2:
        sec, nanosec = stamp[0], stamp[1]
        return float(sec) + float(nanosec) * 1e-9

    if hasattr(stamp, "sec") and hasattr(stamp, "nanosec"):
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9

    if hasattr(stamp, "secs") and hasattr(stamp, "nsecs"):
        return float(stamp.secs) + float(stamp.nsecs) * 1e-9

    raise TypeError(f"Unsupported timestamp type: {type(stamp)}")


def stamp_to_ns(stamp: Any) -> Optional[int]:
    sec = stamp_to_sec(stamp)

    if sec is None:
        return None

    return sec_to_ns(sec)


def format_timestamp(
    timestamp: Optional[float] = None,
    fmt: str = "%Y%m%d_%H%M%S_%f",
    use_utc: bool = False,
) -> str:
    if timestamp is None:
        timestamp = datetime.now().timestamp()

    tz = timezone.utc if use_utc else None
    dt = datetime.fromtimestamp(timestamp, tz=tz)

    return dt.strftime(fmt)


def make_time_filename(
    prefix: str,
    timestamp: Optional[float] = None,
    ext: str = "",
    index: Optional[int] = None,
    digits: int = 6,
) -> str:
    time_text = format_timestamp(timestamp)

    parts = [prefix, time_text]

    if index is not None:
        parts.append(f"{index:0{digits}d}")

    filename = "_".join(parts)

    if ext:
        if not ext.startswith("."):
            ext = "." + ext
        filename += ext

    return filename