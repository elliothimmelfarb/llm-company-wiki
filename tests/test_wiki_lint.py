import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import wiki_lint  # noqa: E402


def page(body="", sources="[wiki/sources/lease.md]"):
    return f"---\ntitle: A page\nsources: {sources}\n---\n\n# A page\n\n{body}\n"


class WikiCase(unittest.TestCase):
    """Each test starts from a small clean repo and breaks one thing."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.write("raw/lease.md", "the original\n")
        self.write(
            "wiki/index.md",
            "# Index\n\n[[sources/lease]] [[entities/shop]] [[topics/rent]]\n",
        )
        self.write("wiki/log.md", "# Log\n")
        self.write(
            "wiki/sources/lease.md",
            page("See [[entities/shop]].", "[raw/lease.md]"),
        )
        self.write("wiki/entities/shop.md", page("From [[sources/lease]], see [[topics/rent]]."))
        self.write("wiki/topics/rent.md", page("Paid by [[entities/shop]]."))

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def findings(self, check=None):
        found = wiki_lint.lint(self.root)
        return [f for f in found if check is None or f.check == check]

    def pages_flagged(self, check):
        return [f.page for f in self.findings(check)]


class CleanWiki(WikiCase):
    def test_clean_wiki_has_no_findings(self):
        self.assertEqual(self.findings(), [])


class DeadLinks(WikiCase):
    def test_wikilink_to_missing_page(self):
        self.write("wiki/topics/rent.md", page("[[entities/shop]] and [[entities/nobody]]"))
        self.assertEqual(self.pages_flagged("dead-link"), ["wiki/topics/rent.md"])

    def test_alias_heading_and_table_pipe_forms_resolve(self):
        body = "[[entities/shop|the shop]] [[entities/shop#Rent]] | [[entities/shop\\|shop]] |"
        self.write("wiki/topics/rent.md", page(body))
        self.assertEqual(self.findings("dead-link"), [])

    def test_alias_does_not_hide_a_dead_target(self):
        self.write("wiki/topics/rent.md", page("[[entities/shop]] [[entities/gone|the shop]]"))
        self.assertEqual(len(self.findings("dead-link")), 1)

    def test_case_mismatch_is_dead_even_on_case_insensitive_disks(self):
        self.write("wiki/topics/rent.md", page("[[entities/shop]] [[Entities/Shop]]"))
        self.assertEqual(len(self.findings("dead-link")), 1)

    def test_links_inside_code_are_examples_not_links(self):
        body = "[[entities/shop]] `[[entities/a]]`\n\n```text\n[[entities/b]]\n```\n"
        self.write("wiki/topics/rent.md", page(body))
        self.assertEqual(self.findings("dead-link"), [])

    def test_link_after_a_closed_fence_is_still_checked(self):
        body = "[[entities/shop]]\n\n```\ncode\n```\n\n[[entities/gone]]\n"
        self.write("wiki/topics/rent.md", page(body))
        self.assertEqual(len(self.findings("dead-link")), 1)

    def test_relative_markdown_link_to_missing_file(self):
        body = "[[entities/shop]] [lease](../../raw/gone.md)"
        self.write("wiki/topics/rent.md", page(body))
        self.assertEqual(self.pages_flagged("dead-link"), ["wiki/topics/rent.md"])

    def test_relative_markdown_link_resolves_from_the_page_folder(self):
        body = "[[entities/shop]] [lease](../../raw/lease.md#page-2)"
        self.write("wiki/topics/rent.md", page(body))
        self.assertEqual(self.findings("dead-link"), [])

    def test_external_links_are_left_alone(self):
        body = "[[entities/shop]] [site](https://example.test/x) [mail](mailto:a@example.test)"
        self.write("wiki/topics/rent.md", page(body))
        self.assertEqual(self.findings("dead-link"), [])


class Sources(WikiCase):
    def test_empty_list(self):
        self.write("wiki/topics/rent.md", page("[[entities/shop]]", "[]"))
        self.assertEqual(self.pages_flagged("no-sources"), ["wiki/topics/rent.md"])

    def test_missing_field(self):
        self.write("wiki/topics/rent.md", "---\ntitle: Rent\n---\n\n[[entities/shop]]\n")
        self.assertEqual(self.pages_flagged("no-sources"), ["wiki/topics/rent.md"])

    def test_no_frontmatter(self):
        self.write("wiki/topics/rent.md", "# Rent\n\nsources: [raw/lease.md]\n[[entities/shop]]\n")
        self.assertEqual(self.pages_flagged("no-sources"), ["wiki/topics/rent.md"])

    def test_block_list_is_understood(self):
        block = "\n  - wiki/sources/lease.md\n  - 'raw/lease.md'"
        self.write("wiki/topics/rent.md", page("[[entities/shop]]", block))
        self.assertEqual(self.findings(), [])

    def test_field_with_crlf_line_endings(self):
        text = "---\r\ntitle: Rent\r\nsources: [raw/lease.md]\r\n---\r\n\r\n[[entities/shop]]\r\n"
        (self.root / "wiki/topics/rent.md").write_bytes(text.encode())
        self.assertEqual(self.findings(), [])

    def test_source_that_does_not_exist(self):
        self.write("wiki/topics/rent.md", page("[[entities/shop]]", "[raw/invented.md]"))
        self.assertEqual(self.pages_flagged("bad-source"), ["wiki/topics/rent.md"])

    def test_one_bad_source_among_good_ones_is_caught(self):
        sources = "[raw/lease.md, raw/invented.md]"
        self.write("wiki/topics/rent.md", page("[[entities/shop]]", sources))
        self.assertEqual(self.pages_flagged("bad-source"), ["wiki/topics/rent.md"])

    def test_source_cannot_escape_the_source_layers(self):
        self.write("README.md", "not a source\n")
        self.write("wiki/topics/rent.md", page("[[entities/shop]]", "[raw/../README.md]"))
        self.assertEqual(self.pages_flagged("bad-source"), ["wiki/topics/rent.md"])

    def test_source_page_must_reach_a_raw_file(self):
        self.write(
            "wiki/sources/lease.md",
            page("See [[entities/shop]].", "[wiki/sources/lease.md]"),
        )
        self.assertEqual(self.pages_flagged("bad-source"), ["wiki/sources/lease.md"])

    def test_index_and_log_need_no_sources(self):
        self.assertEqual(self.findings("no-sources"), [])


class Orphans(WikiCase):
    def test_page_linked_only_by_the_index_is_an_orphan(self):
        self.write("wiki/topics/spare.md", page())
        self.write("wiki/index.md", (self.root / "wiki/index.md").read_text() + "[[topics/spare]]\n")
        self.assertEqual(self.pages_flagged("orphan"), ["wiki/topics/spare.md"])

    def test_page_linked_only_by_the_log_is_an_orphan(self):
        self.write("wiki/topics/spare.md", page())
        self.write("wiki/log.md", "# Log\n\n[[topics/spare]]\n")
        self.assertIn("wiki/topics/spare.md", self.pages_flagged("orphan"))

    def test_link_to_itself_does_not_count(self):
        self.write("wiki/topics/spare.md", page("[[topics/spare]]"))
        self.assertIn("wiki/topics/spare.md", self.pages_flagged("orphan"))

    def test_markdown_style_link_counts_as_inbound(self):
        self.write("wiki/topics/spare.md", page())
        self.write("wiki/topics/rent.md", page("[[entities/shop]] [spare](spare.md)"))
        self.assertNotIn("wiki/topics/spare.md", self.pages_flagged("orphan"))

    def test_link_in_a_code_block_does_not_rescue_a_page(self):
        self.write("wiki/topics/spare.md", page())
        self.write("wiki/topics/rent.md", page("[[entities/shop]] `[[topics/spare]]`"))
        self.assertIn("wiki/topics/spare.md", self.pages_flagged("orphan"))


class IndexCoverage(WikiCase):
    def test_page_missing_from_the_index(self):
        self.write("wiki/topics/new.md", page())
        self.write("wiki/topics/rent.md", page("[[entities/shop]] [[topics/new]]"))
        self.assertEqual(self.pages_flagged("not-in-index"), ["wiki/topics/new.md"])

    def test_missing_index_is_one_finding_not_one_per_page(self):
        (self.root / "wiki/index.md").unlink()
        self.assertEqual(self.pages_flagged("not-in-index"), ["wiki/index.md"])


class Scope(WikiCase):
    def test_hidden_folders_and_non_markdown_are_skipped(self):
        self.write("wiki/.obsidian/notes.md", "no frontmatter\n")
        self.write("wiki/topics/chart.png", "not a page\n")
        self.assertEqual(self.findings(), [])


class CommandLine(WikiCase):
    def run_main(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = wiki_lint.main(list(args))
        return code, out.getvalue()

    def test_exit_zero_when_clean(self):
        self.assertEqual(self.run_main("--root", str(self.root))[0], 0)

    def test_exit_one_and_names_the_page_when_broken(self):
        self.write("wiki/topics/rent.md", page("[[entities/shop]] [[entities/gone]]"))
        code, output = self.run_main("--root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("wiki/topics/rent.md", output)
        self.assertIn("entities/gone", output)

    def test_wrong_root_is_an_error_not_a_clean_pass(self):
        code, _ = self.run_main("--root", str(self.root / "nowhere"))
        self.assertEqual(code, 2)


class ShippedSample(unittest.TestCase):
    def test_the_sample_in_this_repo_is_clean(self):
        self.assertEqual(wiki_lint.lint(REPO), [])


if __name__ == "__main__":
    unittest.main()
