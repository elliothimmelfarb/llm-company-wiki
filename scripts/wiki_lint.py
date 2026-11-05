#!/usr/bin/env python3
"""Mechanical health check for wiki/. Standard library only.

Checks:
  dead-link     a wikilink or relative markdown link points at nothing
  no-sources    a page has no frontmatter, or an empty sources list
  bad-source    a sources entry is missing, or is outside raw/ and wiki/sources/
  orphan        no other content page links here (index and log do not count)
  not-in-index  the page is missing from wiki/index.md

Exit codes: 0 clean, 1 findings, 2 could not run.
Judgment calls such as contradictions and stale claims belong to the lint skill.
"""

import argparse
import posixpath
import re
import sys
from collections import namedtuple
from pathlib import Path
from urllib.parse import unquote

Finding = namedtuple("Finding", "page check detail")

CATALOG_PAGES = {"index", "log"}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+).+?\1")
WIKILINK = re.compile(r"\[\[([^\[\]]+)\]\]")
MARKDOWN_LINK = re.compile(r"\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:|^//")


def split_frontmatter(text):
    """Return (frontmatter lines, body). No frontmatter gives ([], text)."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for number, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return lines[1:number], "\n".join(lines[number + 1 :])
    return [], text


def parse_sources(frontmatter):
    """Read the sources field, in either flow or block list form."""
    clean = lambda value: value.strip().strip("'\"")
    for number, line in enumerate(frontmatter):
        key, colon, value = line.partition(":")
        if key != "sources" or not colon:
            continue
        value = value.strip()
        if value.startswith("["):
            inner = value[1:].split("]", 1)[0]
            return [clean(item) for item in inner.split(",") if clean(item)]
        if value and not value.startswith("#"):
            return [clean(value)]
        items = []
        for following in frontmatter[number + 1 :]:
            match = re.match(r"\s*-\s+(.+)", following)
            if not match:
                break
            items.append(clean(match.group(1)))
        return items
    return []


def strip_code(body):
    """Drop fenced blocks and inline code, where a link is only an example."""
    kept = []
    fence = None
    for line in body.splitlines():
        match = FENCE.match(line)
        if fence:
            closes = (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
                and line.strip() == match.group(1)
            )
            if closes:
                fence = None
            continue
        if match:
            fence = match.group(1)
            continue
        kept.append(INLINE_CODE.sub("", line))
    return "\n".join(kept)


def wikilink_target(raw):
    """Reduce [[target#heading|alias]] to target. Tables escape the pipe."""
    target = re.split(r"\\?\|", raw, maxsplit=1)[0]
    target = target.split("#", 1)[0].strip()
    return target[:-3] if target.endswith(".md") else target


def collect_files(root):
    """Every file under root as an exact-case relative path, skipping dot folders."""
    found = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if path.is_file() and not any(part.startswith(".") for part in relative.parts[:-1]):
            found.add(relative.as_posix())
    return found


def check_sources(key, rel, entries, files):
    if not entries:
        return [Finding(rel, "no-sources", "frontmatter lists no sources")]
    found = []
    for entry in entries:
        if not entry.startswith(("raw/", "wiki/sources/")):
            found.append(Finding(rel, "bad-source", f"{entry} is outside raw/ and wiki/sources/"))
        elif entry not in files:
            found.append(Finding(rel, "bad-source", f"{entry} does not exist"))
    if key.startswith("sources/") and not any(e.startswith("raw/") for e in entries):
        found.append(Finding(rel, "bad-source", "a source page must cite a file in raw/"))
    return found


def lint(root):
    """Return a sorted list of Findings for the repo at root."""
    root = Path(root)
    if not (root / "wiki").is_dir():
        raise FileNotFoundError(f"no wiki/ folder under {root}")

    files = collect_files(root)
    pages = {
        rel[len("wiki/") : -len(".md")]: rel
        for rel in files
        if rel.startswith("wiki/") and rel.endswith(".md")
    }

    findings = []
    outlinks = {}
    for key, rel in pages.items():
        text = (root / rel).read_text(encoding="utf-8-sig", errors="replace")
        frontmatter, body = split_frontmatter(text)
        prose = strip_code(body)
        outlinks[key] = set()

        for raw in WIKILINK.findall(prose):
            target = wikilink_target(raw)
            if not target:
                continue
            if target in pages:
                outlinks[key].add(target)
            else:
                findings.append(Finding(rel, "dead-link", f"[[{target}]]"))

        for raw in MARKDOWN_LINK.findall(prose):
            if URL_SCHEME.match(raw) or raw.startswith("#"):
                continue
            target = unquote(re.split(r"[#?]", raw, maxsplit=1)[0])
            path = posixpath.normpath(posixpath.join(posixpath.dirname(rel), target))
            if path not in files:
                findings.append(Finding(rel, "dead-link", raw))
            elif path.startswith("wiki/") and path.endswith(".md"):
                outlinks[key].add(path[len("wiki/") : -len(".md")])

        if key not in CATALOG_PAGES:
            findings += check_sources(key, rel, parse_sources(frontmatter), files)

    content = [key for key in pages if key not in CATALOG_PAGES]
    for key in content:
        if not any(key in outlinks[other] for other in content if other != key):
            findings.append(Finding(pages[key], "orphan", "no inbound link from a content page"))

    if "index" in pages:
        for key in content:
            if key not in outlinks["index"]:
                findings.append(Finding(pages[key], "not-in-index", f"add [[{key}]] to the index"))
    else:
        findings.append(Finding("wiki/index.md", "not-in-index", "the index page is missing"))

    return sorted(findings)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check wiki/ for broken structure.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repo root holding wiki/ and raw/ (default: this repo)",
    )
    args = parser.parse_args(argv)

    try:
        findings = lint(args.root)
    except FileNotFoundError as error:
        print(f"wiki_lint: {error}", file=sys.stderr)
        return 2

    for finding in findings:
        print(f"{finding.page}: {finding.check}: {finding.detail}")
    print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
