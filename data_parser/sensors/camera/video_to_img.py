from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2


LogCallback = Callable[[str], None]


@dataclass(frozen=True)
class VideoToImgResult:
    output_dir: Path
    saved_count: int


def video_to_img(
    video_path: str | Path,
    output_dir: str | Path,
    output_format: str = "png",
    every_n: int = 1,
    max_frames: int | None = None,
    start_time_sec: float = 0.0,
    end_time_sec: float | None = None,
    log_callback: LogCallback | None = None,
) -> VideoToImgResult:
    """
    비디오 파일을 프레임 이미지로 저장한다.
    """

    video_path = Path(video_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()

    if not video_path.exists():
        raise FileNotFoundError(f"video 경로가 존재하지 않습니다: {video_path}")

    if not video_path.is_file():
        raise RuntimeError(f"video_path는 파일이어야 합니다: {video_path}")

    output_format = output_format.lower().lstrip(".")
    if output_format == "jpeg":
        output_format = "jpg"

    if output_format not in {"png", "jpg"}:
        raise ValueError("output_format은 png, jpg, jpeg 중 하나여야 합니다.")

    if every_n < 1:
        raise ValueError("every_n은 1 이상이어야 합니다.")

    if start_time_sec < 0:
        raise ValueError("start_time_sec는 0 이상이어야 합니다.")

    if end_time_sec is not None and end_time_sec <= start_time_sec:
        raise ValueError("end_time_sec는 start_time_sec보다 커야 합니다.")

    output_dir.mkdir(parents=True, exist_ok=True)

    _log(log_callback, "[INFO] Video to image 변환 시작")
    _log(log_callback, f"[INFO] video path: {video_path}")
    _log(log_callback, f"[INFO] output dir: {output_dir}")
    _log(log_callback, f"[INFO] image format: {output_format}")
    _log(log_callback, f"[INFO] every_n: {every_n}")

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"비디오 파일을 열지 못했습니다: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    _log(log_callback, f"[INFO] input fps: {fps}")
    _log(log_callback, f"[INFO] input frame count: {total_frame_count}")

    if start_time_sec > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time_sec * 1000.0)

    read_count = 0
    saved_count = 0

    try:
        while True:
            ok, frame = cap.read()

            if not ok:
                break

            current_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
            current_sec = current_msec / 1000.0

            if end_time_sec is not None and current_sec > end_time_sec:
                break

            current_frame_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

            if read_count % every_n != 0:
                read_count += 1
                continue

            saved_count += 1

            filename = f"frame_{saved_count:06d}_{current_frame_index:06d}.{output_format}"
            save_path = output_dir / filename

            _write_image(save_path, frame, output_format)

            if saved_count % 100 == 0:
                _log(log_callback, f"[INFO] saved {saved_count} images...")

            if max_frames is not None and saved_count >= max_frames:
                _log(log_callback, f"[INFO] max_frames 도달: {max_frames}")
                break

            read_count += 1

    finally:
        cap.release()

    _log(log_callback, "[INFO] 변환 완료")
    _log(log_callback, f"[INFO] saved images: {saved_count}")

    return VideoToImgResult(
        output_dir=output_dir,
        saved_count=saved_count,
    )


def _write_image(save_path: Path, frame, output_format: str) -> None:
    if output_format == "jpg":
        success = cv2.imwrite(
            str(save_path),
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 95],
        )
    else:
        success = cv2.imwrite(str(save_path), frame)

    if not success:
        raise RuntimeError(f"이미지 저장 실패: {save_path}")


def _log(callback: LogCallback | None, message: str) -> None:
    if callback is not None:
        callback(message)
    else:
        print(message)