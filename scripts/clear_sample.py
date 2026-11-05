#!/usr/bin/env python3
"""Remove the fictional sample so the repo can hold a real company.

Deletes every file in inbox/, raw/, outputs/ and wiki/, then writes a blank
index and log. It refuses to run unless wiki/index.md still carries the sample
marker, so it cannot be run against real content by accident.
"""

import argparse
import sys
from pathlib import Path

MARKER = "FICTIONAL SAMPLE"
LAYERS = ("inbox", "raw", "outputs", "wiki")

BLANK_INDEX = """# Index

Every wiki page is listed here. Lookups start on this page.

## Sources

## Entities

## Concepts

## Topics
"""

BLANK_LOG = """# Log

One line per event, newest last: `- YYYY-MM-DD | operation | what | touched: pages`
"""


def clear(root):
    for layer in LAYERS:
        folder = root / layer
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                path.unlink()
        for path in [folder, *sorted(p for p in folder.rglob("*") if p.is_dir())]:
            (path / ".gitkeep").touch()
    (root / "wiki/index.md").write_text(BLANK_INDEX, encoding="utf-8")
    (root / "wiki/log.md").write_text(BLANK_LOG, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Remove the fictional sample.")
    parser.add_argument("--yes", action="store_true", help="really delete the sample")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repo root (default: this repo)",
    )
    args = parser.parse_args(argv)

    if not args.yes:
        print("clear_sample: nothing deleted. Pass --yes to delete the sample.", file=sys.stderr)
        return 2

    index = args.root / "wiki/index.md"
    if not index.is_file() or MARKER not in index.read_text(encoding="utf-8"):
        print("clear_sample: wiki/index.md is not the sample, so nothing was deleted.", file=sys.stderr)
        return 2

    clear(args.root)
    print("Sample removed. Now edit the company section of CLAUDE.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
