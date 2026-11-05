---
name: compound
description: Save what a working session learned into the company wiki. Use when a session winds down, or when asked to compound, wrap up or capture this conversation. Offer it if a long session produced facts or decisions the wiki does not hold.
---

# Compound

Decisions and facts that are only spoken in a session disappear when it ends. This step moves them into the wiki. Read `docs/wiki-conventions.md` first.

## Steps

1. **Take stock of the whole conversation, from the first message.** List decisions (yours and the people's), new facts, drafts waiting on a person, promises, open questions, documents mentioned but not ingested, and uncommitted files.
2. **Sort each item.**
   - Already in the wiki: skip it.
   - Has a real document behind it: run the ingest skill on that document.
   - A correction to how this repo is described: fix the skill or doc that owns it now.
   - Exists only in this conversation: carry on to step 3.
3. **Write session notes.** Add a new file `raw/sessions/YYYY-MM-DD-slug.md` recording who said or decided what. Keep it factual and short. This becomes the raw source, so that session facts trace to something like everything else.
4. **Fold them in.** Write a source page in `wiki/sources/`, then follow ingest steps 4 to 7.
5. **Log it even when empty.** If nothing needed saving, still add a line: `- YYYY-MM-DD | compound | nothing to save | touched: none`. A silent session looks the same as a forgotten one.
6. **Commit** only the files this session touched, naming them explicitly. Unfamiliar changes in the working tree may belong to someone else, so leave them out and mention them.

## Then

If the session really showed that the workflow itself should change, propose one change with the evidence and leave it for a person to accept. If it did not, say nothing about it.
