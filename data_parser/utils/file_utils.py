import json
import re
from pathlib import Path
from typing import Any, Union

from .path_utils import to_path, ensure_parent_dir


PathLike = Union[str, Path]


def read_text(file_path: PathLike, encoding: str = "utf-8") -> str:
    return to_path(file_path).read_text(encoding=encoding)


def write_text(file_path: PathLike, text: str, encoding: str = "utf-8") -> Path:
    path = to_path(file_path)
    ensure_parent_dir(path)
    path.write_text(text, encoding=encoding)
    return path


def read_json(file_path: PathLike, encoding: str = "utf-8") -> Any:
    with to_path(file_path).open("r", encoding=encoding) as f:
        return json.load(f)


def write_json(
    file_path: PathLike,
    data: Any,
    encoding: str = "utf-8",
    indent: int = 2,
) -> Path:
    path = to_path(file_path)
    ensure_parent_dir(path)

    with path.open("w", encoding=encoding) as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

    return path


def read_yaml(file_path: PathLike, encoding: str = "utf-8") -> Any:
    try:
        import yaml
    except ImportError as e:
        raise ImportError("PyYAML is required. Install with: pip install pyyaml") from e

    with to_path(file_path).open("r", encoding=encoding) as f:
        return yaml.safe_load(f)


def write_yaml(
    file_path: PathLike,
    data: Any,
    encoding: str = "utf-8",
) -> Path:
    try:
        import yaml
    except ImportError as e:
        raise ImportError("PyYAML is required. Install with: pip install pyyaml") from e

    path = to_path(file_path)
    ensure_parent_dir(path)

    with path.open("w", encoding=encoding) as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
        )

    return path


def safe_filename(name: str, replacement: str = "_") -> str:
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', replacement, name)
    name = re.sub(r"\s+", replacement, name)
    name = re.sub(f"{re.escape(replacement)}+", replacement, name)
    return name.strip(replacement)


def unique_path(file_path: PathLike) -> Path:
    path = to_path(file_path)

    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    index = 1

    while True:
        candidate = parent / f"{stem}_{index}{suffix}"

        if not candidate.exists():
            return candidate

        index += 1