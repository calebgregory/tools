#!/usr/bin/env -S uv run python
from pathlib import Path

import mdformat


def main(file: Path) -> None:
    file.write_text(mdformat.text(file.read_text(), extensions=["twospace"]))
    print("done")


def cli() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()

    main(args.file)


if __name__ == "__main__":
    cli()
