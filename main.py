#!/usr/bin/env python3

"""
Data Parser 실행 진입점.

사용 예:
    python main.py
    python main.py --config configs/default.yaml
    python main.py camera bag-to-img --input ./bags/sample --output ./output
"""

from data_parser.cli.main_cli import main


if __name__ == "__main__":
    main()