# Wiki conventions

These rules bind every page in `wiki/` and all four skills.

## Folders

| Folder | Holds |
| --- | --- |
| `wiki/index.md` | A list of every page. Lookups start here. |
| `wiki/log.md` | One line per event, added at the end, never rewritten. |
| `wiki/sources/` | One page per raw document. |
| `wiki/entities/` | People, companies and other actors. |
| `wiki/concepts/` | Terms, rules and processes that are not actors. |
| `wiki/topics/` | Analysis across sources, plus the living views. |

## Page shape

Each page starts with this frontmatter and one H1 that matches `title`.

```yaml
---
type: entity            # source, entity, concept or topic
title: Damp Harbor Hotel
created: 2026-10-20
updated: 2026-10-20
sources: [wiki/sources/2026-09-14-damp-harbor-hotel-agreement.md]
tags: [client]
---
```

Paths in `sources:` start at the repo root. A page in `wiki/sources/` cites at least one file in `raw/`. Every other page cites pages in `wiki/sources/`, or a raw file directly. The lint script checks that each one exists. `index.md` and `log.md` are the only pages without sources.

Source pages hold, in order: a one-line reason it matters, key facts with a clause, page or message reference, the pages it changed, and a relative link to the original.

## Links

- Between wiki pages use wikilinks relative to `wiki/`: `[[entities/damp-harbor-hotel]]`. Do not add `.md`.
- To raw files use relative markdown links, never wikilinks.
- Cite in the body, not only in frontmatter. A page counts as an orphan until another content page links to it. Links from the index and the log do not count.
- Refer to files in `outputs/` as an inline code path, because drafts come and go.
- `wiki/log.md` names pages in plain text, because an append-only file cannot be repaired if a page later moves.

## Filenames

Lowercase ASCII with hyphens. Prefix anything tied to an event with `YYYY-MM-DD-`. A source page uses the same name as its raw file.

## Claims

- Each fact has a source. Anything else is marked `[inferred]`, meaning worked out from sources, or `[unverified]`, meaning stated without one.
- When sources disagree, keep both under `## Conflicts` and let a person decide.
- Store dates, not distances. "2026-11-15" stays true, and "in ten days" does not.
- A search that finds nothing proves nothing about the world, so say what was searched.
- If sources arrive in another language, keep the original in `raw/`, write the wiki in one agreed language, and add a translation file beside the original for documents people will reread.

## Living views

- `topics/status-board.md` says where each piece of work stands. Blocks are edited in place, and each one states the date it was last checked.
- `topics/obligations.md` lists duties, soonest first. A row needs an owner, a due date or `no date set`, and a consequence. Open research questions do not belong there.

## Log format

```text
- 2026-10-20 | ingest | hotel agreement | touched: sources/x, entities/y
```

## Style

Plain sentences. No em dashes.
