import argparse

from data_parser.cli.gnss_cli import add_gnss_subparser, run_gnss_command


def main():
    parser = argparse.ArgumentParser(
        prog="data_parser",
        description="Sensor data parser CLI",
    )

    subparsers = parser.add_subparsers(
        dest="sensor",
        required=True,
    )

    # GNSS 명령어 등록
    add_gnss_subparser(subparsers)

    args = parser.parse_args()

    # GNSS 명령어 실행
    if run_gnss_command(args):
        return

    parser.print_help()