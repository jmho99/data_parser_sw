from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

from data_parser.utils.path_utils import ensure_dir, ensure_parent_dir, to_path


PathLike = Union[str, Path]


def export_image(image, output_path: PathLike) -> Path:
    """
    이미지 1장을 저장.

    지원:
        - numpy ndarray
        - PIL Image

    OpenCV가 있으면 cv2.imwrite 사용.
    OpenCV가 없고 PIL이 있으면 PIL로 저장.
    """
    path = to_path(output_path)
    ensure_parent_dir(path)

    if hasattr(image, "save") and callable(image.save):
        image.save(path)
        return path

    try:
        import cv2
    except ImportError:
        cv2 = None

    if cv2 is not None:
        success = cv2.imwrite(str(path), image)

        if not success:
            raise RuntimeError(f"Failed to write image: {path}")

        return path

    try:
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "Image export requires either opencv-python or pillow"
        ) from e

    pil_image = Image.fromarray(image)
    pil_image.save(path)

    return path


def export_images(
    images: Iterable,
    output_dir: PathLike,
    prefix: str = "frame",
    ext: str = "png",
    start_index: int = 0,
    digits: int = 6,
    filenames: Optional[Sequence[str]] = None,
) -> list[Path]:
    """
    여러 이미지를 순차 저장.

    예:
        export_images(frames, "./output/images")

    저장 결과:
        frame_000000.png
        frame_000001.png
        ...
    """
    out_dir = ensure_dir(output_dir)
    saved_paths = []

    if not ext.startswith("."):
        ext = "." + ext

    for offset, image in enumerate(images):
        index = start_index + offset

        if filenames is not None:
            filename = filenames[offset]
        else:
            filename = f"{prefix}_{index:0{digits}d}{ext}"

        output_path = out_dir / filename
        saved_paths.append(export_image(image, output_path))

    return saved_paths