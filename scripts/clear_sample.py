#!/usr/bin/env python3
"""Remove the fictional sample so the repo can hold a real company.

Deletes only the files named in SAMPLE_FILES, then writes a blank index and log.
It refuses to run, and deletes nothing, unless all of these hold:

- wiki/index.md still carries the sample marker.
- inbox/ and raw/ hold nothing except the sample.
- The repo root is a git repo with nothing uncommitted, so whatever is deleted
  can still be recovered from git history.
"""

import argparse
import subprocess
import sys
from pathlib import Path

MARKER = "FICTIONAL SAMPLE"
LAYERS = ("inbox", "raw", "outputs", "wiki")
# Every sample file. Adding a sample document means adding it here too, and a test
# fails until you do.
SAMPLE_FILES = (
    "inbox/2026-10-29-hotel-volume-email.md",
    "outputs/2026-10-20-hotel-rate-letter-draft.md",
    "raw/contracts/2026-03-01-workshop-lease.md",
    "raw/contracts/2026-09-14-damp-harbor-hotel-agreement.md",
    "raw/correspondence/2026-10-02-canopy-spoke-price-email.md",
    "raw/invoices/2026-10-16-invoice-0042.md",
    "raw/sessions/2026-10-20-owners-meeting.md",
    "wiki/concepts/net-30-terms.md",
    "wiki/concepts/renewal-notice.md",
    "wiki/entities/bumblewick-umbrella-repair.md",
    "wiki/entities/canopy-and-spoke-supply.md",
    "wiki/entities/damp-harbor-hotel.md",
    "wiki/entities/marigold-bumblewick.md",
    "wiki/entities/puddlemere-property-trust.md",
    "wiki/entities/tobias-ferrule.md",
    "wiki/sources/2026-03-01-workshop-lease.md",
    "wiki/sources/2026-09-14-damp-harbor-hotel-agreement.md",
    "wiki/sources/2026-10-02-canopy-spoke-price-email.md",
    "wiki/sources/2026-10-16-invoice-0042.md",
    "wiki/sources/2026-10-20-owners-meeting.md",
    "wiki/topics/obligations.md",
    "wiki/topics/spoke-price-impact.md",
    "wiki/topics/status-board.md",
)
# Sample files that are replaced with a blank copy instead of deleted.
REWRITTEN = ("wiki/index.md", "wiki/log.md")
# Files that never count as content in a layer.
NOT_CONTENT = (".gitkeep", ".DS_Store")
# The layers where anything outside the sample stops the script.
GUARDED_LAYERS = ("inbox", "raw")

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


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
    )


def git_problem(root):
    """Why the git tree is not safe to delete from, or None if it is."""
    try:
        top = git(root, "rev-parse", "--show-toplevel")
        status = git(root, "status", "--porcelain")
    except OSError:
        return "git could not be run, so uncommitted work cannot be ruled out"
    if top.returncode != 0 or status.returncode != 0:
        return "this is not a git repo, so uncommitted work cannot be ruled out"
    if Path(top.stdout.strip()).resolve() != root.resolve():
        return f"{root} is not the root of its git repo"
    if status.stdout.strip():
        return "the git tree has uncommitted changes:\n" + status.stdout.rstrip()
    return None


def unexpected_files(root):
    """Everything in the guarded layers that is not part of the sample."""
    known = set(SAMPLE_FILES) | set(REWRITTEN)
    found = []
    for layer in GUARDED_LAYERS:
        for path in sorted((root / layer).rglob("*")):
            relative = path.relative_to(root).as_posix()
            is_entry = path.is_symlink() or not path.is_dir()
            if is_entry and relative not in known and path.name not in NOT_CONTENT:
                found.append(relative)
    return found


def clear(root):
    for relative in SAMPLE_FILES:
        (root / relative).unlink(missing_ok=True)
    for layer in LAYERS:
        folder = root / layer
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

    unexpected = unexpected_files(args.root)
    if unexpected:
        print("clear_sample: nothing deleted, because these are not sample files:", file=sys.stderr)
        for relative in unexpected:
            print(f"  {relative}", file=sys.stderr)
        print("Move them out of the repo. If they came from trying the sample, start from a fresh clone.", file=sys.stderr)
        return 2

    problem = git_problem(args.root)
    if problem:
        print(f"clear_sample: nothing deleted, because {problem}", file=sys.stderr)
        print("Commit or discard your changes first. If they came from trying the sample, start from a fresh clone.", file=sys.stderr)
        return 2

    clear(args.root)
    print("Sample removed. Now edit the company section of CLAUDE.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
