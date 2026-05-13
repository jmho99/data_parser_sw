from __future__ import annotations

from data_parser.sensors.camera.bag_to_img import bag_to_img
from data_parser.sensors.camera.bag_to_video import bag_to_video
from data_parser.sensors.camera.video_to_img import video_to_img


def add_camera_subparser(subparsers) -> None:
    camera_parser = subparsers.add_parser(
        "camera",
        help="Camera 데이터 변환 기능",
    )

    camera_subparsers = camera_parser.add_subparsers(
        dest="camera_command",
        required=True,
    )

    _add_bag_to_img_parser(camera_subparsers)
    _add_bag_to_video_parser(camera_subparsers)
    _add_video_to_img_parser(camera_subparsers)


def _add_bag_to_img_parser(camera_subparsers) -> None:
    parser = camera_subparsers.add_parser(
        "bag-to-img",
        help="ROS2 bag의 Image/CompressedImage 토픽을 이미지 파일로 변환",
    )

    parser.add_argument(
        "bag_path",
        help="rosbag2 폴더 경로",
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="이미지 저장 폴더",
    )

    parser.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help=(
            "변환할 이미지 토픽. "
            "미입력 시 bag 안의 모든 Image/CompressedImage 토픽 자동 변환. "
            "예: --topics /camera/image_raw /camera/image_compressed"
        ),
    )

    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpg", "jpeg"],
        help="저장 이미지 형식",
    )

    parser.add_argument(
        "--every-n",
        type=int,
        default=1,
        help="N프레임마다 1장 저장. 기본값 1은 전체 저장",
    )

    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="전체 저장 최대 프레임 수. 미입력 시 제한 없음",
    )

    parser.set_defaults(func=handle_bag_to_img)


def _add_bag_to_video_parser(camera_subparsers) -> None:
    parser = camera_subparsers.add_parser(
        "bag-to-video",
        help="ROS2 bag의 Image/CompressedImage 토픽을 비디오 파일로 변환",
    )

    parser.add_argument(
        "bag_path",
        help="rosbag2 폴더 경로",
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="비디오 저장 폴더",
    )

    parser.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help=(
            "변환할 이미지 토픽. "
            "미입력 시 bag 안의 모든 Image/CompressedImage 토픽 자동 변환."
        ),
    )

    parser.add_argument(
        "--format",
        default="mp4",
        choices=["mp4", "avi", "webm", "mkv"],
        help="저장 비디오 형식",
    )

    parser.add_argument(
        "--fps",
        type=float,
        default=10.0,
        help="저장 비디오 FPS",
    )

    parser.add_argument(
        "--codec",
        default=None,
        help="FourCC codec. 미입력 시 format별 기본값 사용. 예: mp4v, MJPG, VP80",
    )

    parser.add_argument(
        "--every-n",
        type=int,
        default=1,
        help="N프레임마다 1장씩 비디오에 기록. 기본값 1은 전체 기록",
    )

    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="전체 저장 최대 프레임 수. 미입력 시 제한 없음",
    )

    parser.set_defaults(func=handle_bag_to_video)


def _add_video_to_img_parser(camera_subparsers) -> None:
    parser = camera_subparsers.add_parser(
        "video-to-img",
        help="비디오 파일을 이미지 시퀀스로 변환",
    )

    parser.add_argument(
        "video_path",
        help="비디오 파일 경로",
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="이미지 저장 폴더",
    )

    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpg", "jpeg"],
        help="저장 이미지 형식",
    )

    parser.add_argument(
        "--every-n",
        type=int,
        default=1,
        help="N프레임마다 1장 저장. 기본값 1은 전체 저장",
    )

    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="전체 저장 최대 프레임 수. 미입력 시 제한 없음",
    )

    parser.add_argument(
        "--start-time",
        type=float,
        default=0.0,
        help="변환 시작 시간. 단위: 초",
    )

    parser.add_argument(
        "--end-time",
        type=float,
        default=None,
        help="변환 종료 시간. 단위: 초. 미입력 시 끝까지 변환",
    )

    parser.set_defaults(func=handle_video_to_img)


def handle_bag_to_img(args) -> None:
    result = bag_to_img(
        bag_path=args.bag_path,
        output_dir=args.output,
        topics=args.topics,
        output_format=args.format,
        every_n=args.every_n,
        max_frames=args.max_frames,
    )

    print("[DONE] bag to img 변환 완료")
    print(f"[DONE] output: {result.output_dir}")
    print(f"[DONE] saved: {result.saved_count}")

    for topic_name, count in result.topic_saved_counts.items():
        print(f"[DONE] {topic_name}: {count}")


def handle_bag_to_video(args) -> None:
    result = bag_to_video(
        bag_path=args.bag_path,
        output_dir=args.output,
        topics=args.topics,
        output_format=args.format,
        fps=args.fps,
        codec=args.codec,
        every_n=args.every_n,
        max_frames=args.max_frames,
    )

    print("[DONE] bag to video 변환 완료")
    print(f"[DONE] output: {result.output_dir}")
    print(f"[DONE] saved frames: {result.saved_count}")

    for topic_name, path in result.video_paths.items():
        count = result.topic_saved_counts.get(topic_name, 0)
        print(f"[DONE] {topic_name}: {count} frames -> {path}")


def handle_video_to_img(args) -> None:
    result = video_to_img(
        video_path=args.video_path,
        output_dir=args.output,
        output_format=args.format,
        every_n=args.every_n,
        max_frames=args.max_frames,
        start_time_sec=args.start_time,
        end_time_sec=args.end_time,
    )

    print("[DONE] video to img 변환 완료")
    print(f"[DONE] output: {result.output_dir}")
    print(f"[DONE] saved: {result.saved_count}")