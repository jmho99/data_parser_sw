#!/usr/bin/env python3

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "gui":
        from data_parser.gui.app import main as gui_main

        gui_main()
        return

    from data_parser.cli.main_cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()