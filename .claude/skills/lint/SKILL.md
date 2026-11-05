---
name: lint
description: Health check the company wiki. Use when asked to lint, check or audit the wiki, after a large batch of ingests, or about once a month.
---

# Lint

Read `docs/wiki-conventions.md` first. The check has two parts, one mechanical and one that needs reading.

## Mechanical

Run `python3 scripts/wiki_lint.py`. It reports dead links, pages with no sources, sources that do not exist, orphans and pages missing from the index. Exit code 1 means findings. Fix these directly, unless a fix would mean inventing a source. In that case mark the claim `[unverified]` and report it.

## Reading

The script cannot do these, so go through the wiki and look for:

- **Conflicts:** two pages that disagree on a date, an amount, a name or a status.
- **Staleness:** a page whose `updated:` date is older than the `created:` date of a source page that lists it under what it changed, or a status block older than a related log line.
- **Obligations drift:** a duty with a stated consequence and no row in `topics/obligations.md`, or a row whose matter is closed.
- **Overclaims:** a sentence that says more than the source it cites.
- **Unlinked names:** a name mentioned in plain text that already has its own page.
- **Missing pages:** a term that keeps appearing with no concept page.
- **Coverage gaps:** company activity that no source documents.
- **Inbox backlog:** anything in `inbox/` more than two days old.

## Fix or report

Fix without asking: dead links with an obvious target, index omissions, missing links, `updated:` dates, rows for facts that are unambiguous.

Report and leave alone: conflicts, stale claims that need a new source, new concept pages, and which documents to go and find.

## Output

Write `wiki/topics/health-check-YYYY-MM-DD.md` with `sources:` listing the source pages behind its findings. Give a one-line verdict, then findings grouped by the bold labels above, each naming the page and a proposed fix. Link it from `topics/status-board.md`, replacing any link to an earlier report, add it to the index, and add a line to the log. If nothing is wrong, skip the page and add only the log line.
