import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import clear_sample  # noqa: E402
import wiki_lint  # noqa: E402


class ClearSample(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "copy"
        shutil.copytree(REPO, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))

    def run_main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return clear_sample.main(["--root", str(self.root), *args])

    def pages(self):
        return sorted(p.name for p in (self.root / "wiki").rglob("*.md"))

    def test_does_nothing_without_yes(self):
        before = self.pages()
        self.assertEqual(self.run_main(), 2)
        self.assertEqual(self.pages(), before)

    def test_leaves_an_empty_wiki_that_passes_lint(self):
        self.assertEqual(self.run_main("--yes"), 0)
        self.assertEqual(self.pages(), ["index.md", "log.md"])
        self.assertEqual(wiki_lint.lint(self.root), [])

    def test_empties_the_other_layers_but_keeps_the_folders(self):
        self.run_main("--yes")
        for top in ("inbox", "raw", "outputs"):
            files = [p for p in (self.root / top).rglob("*") if p.is_file()]
            self.assertTrue(files, top)
            self.assertEqual({p.name for p in files}, {".gitkeep"}, top)
        self.assertTrue((self.root / "wiki/entities").is_dir())

    def test_keeps_the_tooling(self):
        self.run_main("--yes")
        for path in ("CLAUDE.md", "scripts/wiki_lint.py", ".claude/skills/ingest/SKILL.md"):
            self.assertTrue((self.root / path).is_file(), path)

    def test_refuses_a_wiki_that_is_no_longer_the_sample(self):
        self.run_main("--yes")
        real = self.root / "raw/contracts/real-contract.md"
        real.write_text("a real document\n", encoding="utf-8")
        self.assertEqual(self.run_main("--yes"), 2)
        self.assertTrue(real.is_file())


if __name__ == "__main__":
    unittest.main()
