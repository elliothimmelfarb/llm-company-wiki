# llm-company-wiki

This is a template for a company knowledge base that an AI agent maintains. You give the agent documents such as contracts, invoices and emails. It keeps the originals untouched and writes a linked set of markdown pages about the company, where every page traces back to a document. People read the wiki, and the agent keeps it up to date.

The repo ships with a small sample wiki for Bumblewick Umbrella Repair, a fictional shop in the fictional town of Drizzleton. All its people, companies and documents are invented.

## How it is organized

| Folder | What it holds | Who changes it |
| --- | --- | --- |
| `inbox/` | Documents that have arrived but are not processed yet | People |
| `raw/` | The original documents, kept unchanged | The agent adds files, and nobody edits them |
| `wiki/` | The company record, as linked markdown | The agent |
| `outputs/` | Generated drafts, such as letters waiting for a person to send | The agent |

The agent has four operations, each a skill in `.claude/skills/`:

- **Ingest** files a document in `raw/` and folds its facts into the wiki.
- **Query** answers a question from the wiki and cites its pages.
- **Lint** checks the wiki for broken structure, conflicts and stale claims.
- **Compound** saves the decisions and facts from a working session into the wiki.

`CLAUDE.md` is the agent's operating guide, and `AGENTS.md` points other coding agents at the same files. `docs/wiki-conventions.md` holds the page and citation rules.

## Try it on the sample in five minutes

You need Python 3.9 or later and a coding agent. Claude Code picks up the skills on its own. Other agents read `AGENTS.md`.

Clone the repo, open a terminal in it, and confirm the sample is healthy:

```sh
python3 scripts/wiki_lint.py
python3 -m unittest discover -s tests
```

The lint prints `clean` and the tests end with `OK`. Now start your agent in this folder and work through these four requests.

1. Ask: "What does Damp Harbor Hotel owe us, and when is it due?" The answer should be $720 by 2026-11-15, with links to the wiki pages behind it.
2. Ask: "Ingest what is in the inbox." The email in `inbox/` asks for 60 umbrellas and claims the rate is $16, but the signed agreement says up to 40 at $18. The agent should move the email into `raw/`, write a source page, record the rate as a conflict rather than choosing a side, and put a reply in `outputs/` as a draft without sending it. Whether to accept 60 umbrellas is the owner's decision, so the agent should report it as an open request.
3. Ask: "Lint the wiki." It should run the script and then read for problems the script cannot see.
4. Ask: "Compound this session." It should save anything you decided along the way.

Open `wiki/index.md` and `wiki/log.md` to see what changed. To see the lint catch a real problem, change a link in any wiki page to a page that does not exist and run the script again.

## Rails to set before real use

Rails are the things the agent must never do on its own. The defaults in `CLAUDE.md` are below. Keep them and add your own before you give the agent real documents.

- **Drafts only.** The agent writes emails and messages into `outputs/`, and a person sends them.
- **No money.** The agent never pays, transfers, buys or trades. It prepares the work and a person does the last step.
- **No filings.** The agent never submits government, tax or legal filings.
- **No publishing.** Nothing goes public without a person's approval.
- **No plaintext credentials.** Passwords and keys never go in this repo.

These rules are written instructions, so an agent could still break one by mistake. The real protection is access. Do not give the agent a mail account that can send, a banking login or a filing portal login. If it can only reach read and draft tools, a mistake stops at a draft.

Documents can also contain instructions aimed at the agent, so `CLAUDE.md` tells it to treat them as data. Keep that line when you edit the file.

## Using it for a real company

Remove the sample, then replace the company line in `CLAUDE.md`:

```sh
python3 scripts/clear_sample.py --yes
```

The script deletes everything in `inbox/`, `raw/`, `outputs/` and `wiki/`, then writes a blank index and log. It refuses to run once the sample index is gone, so it cannot wipe real content.

Keep the repo private, because it will hold contracts, client names and money. Put your first documents in `inbox/` and ask the agent to ingest them.

## The lint script

`scripts/wiki_lint.py` uses only the Python standard library. It reports dead links, pages with no sources, sources that do not exist, orphan pages that no other content page links to, and pages missing from the index. It exits with 0 when clean, 1 when it has findings, and 2 when it cannot run.

It checks structure only. It cannot tell whether a page is true, so conflicts and stale claims are left to the lint skill and to people.

## License

MIT. See `LICENSE`.
