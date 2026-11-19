"""Banana's local readiness check reports presence without displaying a key."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "extensions/banana/scripts/validate_setup.py"


def test_no_part_of_the_key_is_shown(monkeypatch):
    fake_key = "test-key-with-private-fragments"
    monkeypatch.setenv("GOOGLE_AI_API_KEY", fake_key)
    result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert "[PASS] GOOGLE_AI_API_KEY is set" in result.stdout
    assert fake_key not in result.stdout + result.stderr
    assert "private-fragments" not in result.stdout + result.stderr
