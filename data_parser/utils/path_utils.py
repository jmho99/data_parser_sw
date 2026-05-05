from pathlib import Path
from typing import Iterable, Optional, Union


PathLike = Union[str, Path]


def to_path(path: PathLike) -> Path:
    return path if isinstance(path, Path) else Path(path)


def ensure_dir(path: PathLike) -> Path:
    p = to_path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_parent_dir(file_path: PathLike) -> Path:
    p = to_path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p.parent


def resolve_path(path: PathLike, base_dir: Optional[PathLike] = None) -> Path:
    p = to_path(path)

    if p.is_absolute():
        return p.resolve()

    if base_dir is not None:
        return (to_path(base_dir) / p).resolve()

    return p.resolve()


def change_suffix(file_path: PathLike, suffix: str) -> Path:
    p = to_path(file_path)

    if not suffix.startswith("."):
        suffix = "." + suffix

    return p.with_suffix(suffix)


def make_output_path(
    output_dir: PathLike,
    filename: str,
    suffix: Optional[str] = None,
) -> Path:
    out_dir = ensure_dir(output_dir)
    path = out_dir / filename

    if suffix is not None:
        path = change_suffix(path, suffix)

    ensure_parent_dir(path)
    return path


def list_files(
    directory: PathLike,
    extensions: Optional[Iterable[str]] = None,
    recursive: bool = False,
) -> list[Path]:
    root = to_path(directory)

    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    if extensions is not None:
        extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
        }

    pattern = "**/*" if recursive else "*"
    files = []

    for path in root.glob(pattern):
        if not path.is_file():
            continue

        if extensions is not None and path.suffix.lower() not in extensions:
            continue

        files.append(path)

    return sorted(files)