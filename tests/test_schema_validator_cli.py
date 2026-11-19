"""Standard-library coverage for the standalone schema validator CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_schema.py"


class TestSchemaValidatorCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.page = Path(self.temp_dir.name) / "page.html"

    def write_page(self, payload: dict) -> None:
        self.page.write_text(
            '<script type="application/ld+json">'
            + json.dumps(payload)
            + "</script>",
            encoding="utf-8",
        )

    def run_validator(self, *args: str, input: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *map(str, args)],
            input=input,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )

    def test_valid_markup_is_silent(self) -> None:
        self.write_page({"@context": "https://schema.org", "@type": "Product", "name": "Thing"})
        result = self.run_validator(str(self.page))
        self.assertEqual(result.returncode, 0)
        self.assertEqual((result.stdout, result.stderr), ("", ""))

    def test_warnings_are_readable_without_json_mode(self) -> None:
        self.write_page({"@type": "Product", "name": "Thing"})
        result = self.run_validator(str(self.page))
        self.assertEqual(result.returncode, 0)
        self.assertIn("Schema validation warnings", result.stdout)
        self.assertIn("Missing @context", result.stdout)

    def test_warnings_can_be_emitted_as_json(self) -> None:
        self.write_page({"@type": "Product", "name": "Thing"})
        result = self.run_validator(str(self.page), "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["file"], str(self.page))
        self.assertTrue(any("Missing @context" in warning for warning in payload["warnings"]))

    def test_critical_findings_keep_exit_two_and_support_json(self) -> None:
        self.write_page({
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "[Business Name]",
        })
        result = self.run_validator(str(self.page), "--json")
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stderr)
        self.assertTrue(any("[Business Name]" in error for error in payload["errors"]))

    def test_unsupported_extension_reports_validation_error(self) -> None:
        unsupported = Path(self.temp_dir.name) / "image.png"
        unsupported.write_bytes(b"not an HTML document")
        result = self.run_validator(str(unsupported), "--json")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stderr)
        self.assertEqual(payload["file"], str(unsupported))
        self.assertIn("unsupported file type", payload["error"])

    def test_oversized_file_reports_validation_error(self) -> None:
        oversized = Path(self.temp_dir.name) / "large.html"
        oversized.write_bytes(b" " * (10 * 1024 * 1024 + 1))
        result = self.run_validator(str(oversized))
        self.assertEqual(result.returncode, 1)
        self.assertIn("exceeds the 10485760-byte validation limit", result.stderr)

    def test_cli_requires_a_file_and_does_not_read_host_events_from_stdin(self) -> None:
        result = self.run_validator(
            input=json.dumps({"tool_input": {"file_path": str(self.page)}})
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
