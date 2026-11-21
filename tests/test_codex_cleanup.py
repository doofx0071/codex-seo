"""Working-tree scanner path containment checks."""

from __future__ import annotations

import os
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_codex_cleanup  # noqa: E402
from check_codex_cleanup import _is_scannable_file  # noqa: E402


class TestCodexCleanupScanner(unittest.TestCase):
    def test_allows_specific_provenance_but_rejects_unrelated_claude_code(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "checkout"
            phase1 = root / "docs" / "PHASE1-VERIFICATION.md"
            workflow = root / "docs" / "WORKFLOW-public-private.md"
            unrelated = root / "docs" / "other.md"
            phase1.parent.mkdir(parents=True)
            phase1.write_text(
                "Historical " + "Claude" + "-SEO behavior. Fork: " + "AgriciDaniel/" + "claude" + "-seo.\n",
                encoding="utf-8",
            )
            workflow.write_text("Upstream: [" + "AgriciDaniel/" + "claude" + "-seo]\n", encoding="utf-8")
            unrelated.write_text("Claude" + " Code integration still remains.\n", encoding="utf-8")
            paths = (
                "docs/PHASE1-VERIFICATION.md\0"
                "docs/WORKFLOW-public-private.md\0"
                "docs/other.md\0\0"
            ).encode()
            output = io.StringIO()

            with mock.patch.object(check_codex_cleanup, "ROOT", root), \
                    mock.patch.object(check_codex_cleanup, "CRAWLER_FILES", ()), \
                    mock.patch.object(check_codex_cleanup.subprocess, "check_output", return_value=paths), \
                    contextlib.redirect_stdout(output):
                status = check_codex_cleanup.main()

            self.assertEqual(status, 1)
            self.assertEqual(output.getvalue(), "docs/other.md:1: " + "Claude" + " Code integration still remains.\n")

    def test_regular_checkout_file_is_scannable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "checkout"
            root.mkdir()
            path = root / "file.md"
            path.write_text("in checkout", encoding="utf-8")
            self.assertTrue(_is_scannable_file(path, root))

    def test_external_symlink_is_not_scannable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "checkout"
            root.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside checkout", encoding="utf-8")
            link = root / "linked.txt"
            try:
                os.symlink(outside, link)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assertFalse(_is_scannable_file(link, root))

    def test_file_under_symlinked_directory_is_not_scannable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "checkout"
            root.mkdir()
            outside = base / "outside"
            outside.mkdir()
            target = outside / "file.txt"
            target.write_text("outside checkout", encoding="utf-8")
            try:
                os.symlink(outside, root / "linked-dir", target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory symlink creation unavailable: {exc}")
            self.assertFalse(_is_scannable_file(root / "linked-dir" / "file.txt", root))

    def test_main_fails_when_required_crawler_file_is_an_external_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "checkout"
            root.mkdir()
            outside = base / "outside.md"
            outside.write_text("ClaudeBot Claude-SearchBot Claude-User", encoding="utf-8")
            required = root / "references" / "ai-crawler-access.md"
            required.parent.mkdir()
            try:
                os.symlink(outside, required)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)

            output = io.StringIO()
            with mock.patch.object(check_codex_cleanup, "ROOT", root), \
                    mock.patch.object(check_codex_cleanup, "CRAWLER_FILES", ("references/ai-crawler-access.md",)), \
                    contextlib.redirect_stdout(output):
                status = check_codex_cleanup.main()

            self.assertEqual(status, 1)
            self.assertIn("Required crawler guidance missing or unsafe", output.getvalue())


if __name__ == "__main__":
    unittest.main()
