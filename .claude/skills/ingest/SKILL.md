---
name: ingest
description: Fold one raw document into the company wiki. Use when someone adds a contract, invoice, email, scan or article, says "ingest this", or asks to work through the inbox.
---

# Ingest

Read `docs/wiki-conventions.md` first. Then read the whole source, because a fact on the last page counts as much as one on the first.

## Steps

1. **File the original.** Move it from `inbox/` to a folder in `raw/`, with a `YYYY-MM-DD-slug` name. From here on it is never edited.
2. **Check what exists.** Read `wiki/index.md` and the pages this source touches, so that you extend them instead of creating duplicates.
3. **Write one source page** in `wiki/sources/`, with its `sources:` pointing at the file in `raw/`.
4. **Update the pages it touches.** For each person, company or idea the source mentions, add the fact to the existing page with an inline citation, list the source page in `sources:`, and change `updated:`. Create a page only for something likely to come up again. A single passing mention goes on the nearest existing page.
5. **Handle disagreement.** If the source conflicts with the wiki, keep both claims under a `## Conflicts` heading, each with its source. Put that heading on the page that owns the fact, usually the entity, and link to it from other pages that repeat the fact. Do not rewrite those pages. Never pick a winner yourself. A person decides. A request that nobody has agreed to yet is not a conflict, so record it as an open request.
6. **Refresh the living views.** Change `wiki/topics/status-board.md` if a piece of work moved. Add a row to `wiki/topics/obligations.md` for every new duty that has a consequence, and close any row this source settles. If the source gives no due date, write `no date set` rather than inventing one. Create either page if it does not exist yet.
7. **Close the books.** Add new pages to `wiki/index.md`, add one line to `wiki/log.md`, and run `python3 scripts/wiki_lint.py`.

## Report

Say what the source is, the few facts that matter, which pages changed, and anything that needs a person: conflicts, deadlines, replies to write. If a reply is needed, put a draft in `outputs/`. Never send it. A draft that touches a conflict or an undecided request states what the documents say, and opens with a bracketed note listing what the person must decide before sending.

Ask before ingesting only if you cannot tell what the document is.
