from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data or {}


def deep_merge(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    result = dict(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def load_default_config(config_dir: str | Path = "configs") -> dict[str, Any]:
    config_dir = Path(config_dir)
    return load_yaml(config_dir / "default.yaml")


def load_sensor_config(
    sensor_name: str,
    config_dir: str | Path = "configs",
) -> dict[str, Any]:
    config_dir = Path(config_dir)
    return load_yaml(config_dir / f"{sensor_name}.yaml")


def load_template(template_path: str | Path) -> dict[str, Any]:
    return load_yaml(template_path)


def load_config_bundle(
    sensor_name: str,
    config_dir: str | Path = "configs",
) -> dict[str, Any]:
    """
    default.yaml + sensor yaml을 합쳐서 반환한다.

    예:
        load_config_bundle("gnss")
        load_config_bundle("imu")
        load_config_bundle("camera")
        load_config_bundle("lidar")
    """

    default_config = load_default_config(config_dir)
    sensor_config = load_sensor_config(sensor_name, config_dir)

    merged_config = deep_merge(default_config, sensor_config)

    return {
        "default": default_config,
        "sensor": sensor_config,
        "merged": merged_config,
    }


def get_by_path(data: Any, path: str, default: Any = None) -> Any:
    """
    YAML template의 source 값을 이용해 메시지 내부 값을 꺼낸다.

    예:
        header.stamp.sec
        orientation.x
        position_covariance.0
    """

    current = data

    for part in path.split("."):
        if current is None:
            return default

        if isinstance(current, dict):
            current = current.get(part, default)
            continue

        if isinstance(current, (list, tuple)) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return default
            current = current[index]
            continue

        if hasattr(current, part):
            current = getattr(current, part)
            continue

        return default

    return current


def extract_row_from_template(
    msg: Any,
    template: dict[str, Any],
) -> dict[str, Any]:
    """
    CSV template의 columns 정의에 따라 ROS msg에서 row dict를 생성한다.
    """

    row: dict[str, Any] = {}

    for column in template.get("columns", []):
        name = column["name"]
        source = column.get("source")
        default = column.get("default")

        if source is None:
            row[name] = default
        else:
            row[name] = get_by_path(msg, source, default)

    return row