import contextlib
import io
import shutil
import subprocess
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
        self.git("init", "-q")
        self.commit()

    def git(self, *args):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
        )

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "snapshot")

    def add_file(self, relative, text="a real document\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

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

    def assert_refused_with_nothing_deleted(self):
        before = self.pages()
        sample = self.root / "raw/contracts/2026-03-01-workshop-lease.md"
        self.assertEqual(self.run_main("--yes"), 2)
        self.assertEqual(self.pages(), before)
        self.assertTrue(sample.is_file())

    def test_refuses_a_committed_real_file_in_raw_while_the_marker_is_still_there(self):
        real = self.add_file("raw/contracts/real-contract.md")
        self.commit()
        self.assert_refused_with_nothing_deleted()
        self.assertTrue(real.is_file())

    def test_refuses_a_real_file_in_inbox(self):
        real = self.add_file("inbox/real-invoice.pdf")
        self.commit()
        self.assert_refused_with_nothing_deleted()
        self.assertTrue(real.is_file())

    def test_refuses_a_gitignored_real_file_in_raw(self):
        real = self.add_file("raw/contracts/.env")
        self.assert_refused_with_nothing_deleted()
        self.assertTrue(real.is_file())

    def test_refuses_uncommitted_changes_anywhere_in_the_tree(self):
        self.add_file("notes.txt")
        self.assert_refused_with_nothing_deleted()

    def test_refuses_an_edited_sample_file(self):
        path = self.root / "wiki/topics/status-board.md"
        path.write_text("edited\n", encoding="utf-8")
        self.assert_refused_with_nothing_deleted()

    def test_refuses_when_it_cannot_check_git(self):
        shutil.rmtree(self.root / ".git")
        self.assert_refused_with_nothing_deleted()

    def test_refuses_a_root_that_is_only_inside_another_repo(self):
        parent = self.root.parent
        subprocess.run(["git", "init", "-q"], cwd=parent, check=True)
        shutil.rmtree(self.root / ".git")
        self.assert_refused_with_nothing_deleted()

    def test_leaves_files_it_does_not_list_in_wiki_and_outputs(self):
        page = self.add_file("wiki/topics/real-page.md")
        draft = self.add_file("outputs/real-draft.md")
        self.commit()
        self.assertEqual(self.run_main("--yes"), 0)
        self.assertTrue(page.is_file())
        self.assertTrue(draft.is_file())

    def test_the_list_matches_the_sample_in_the_repo(self):
        found = {
            p.relative_to(REPO).as_posix()
            for layer in clear_sample.LAYERS
            for p in (REPO / layer).rglob("*")
            if p.is_file() and p.name not in clear_sample.NOT_CONTENT
        }
        self.assertEqual(found, set(clear_sample.SAMPLE_FILES) | set(clear_sample.REWRITTEN))


if __name__ == "__main__":
    unittest.main()
