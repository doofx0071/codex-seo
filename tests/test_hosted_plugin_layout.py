"""Layout and checkout invocation checks for the Codex SEO launcher."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "codex-seo"
CHECKOUT_LAUNCHER = "./scripts/codex-seo"
PLUGIN_ROOT_LAUNCHER = "${CODEX_SEO_PLUGIN_ROOT}/scripts/codex-seo"

# A bare invocation is ``codex-seo run`` with nothing in front of it. The
# repository-relative form ``./scripts/codex-seo run`` does not match.
BARE_INVOCATION = re.compile(r"(?<![A-Za-z0-9_/])codex-seo (?:run|setup|doctor)\b")

# CHANGELOG.md records the historical bare form in released entries and must
# keep reading as written.
DOC_EXCLUSIONS = {"CHANGELOG.md"}


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return out.splitlines()


def _instruction_docs() -> list[str]:
    docs = []
    for rel in _tracked():
        if not rel.endswith(".md") or rel in DOC_EXCLUSIONS:
            continue
        if rel.startswith(("research/", ".github/", "tests/")):
            continue
        if rel.startswith(("skills/", "agents/", "docs/", "extensions/")) or "/" not in rel:
            docs.append(rel)
    return docs


def test_no_top_level_bin_directory() -> None:
    assert not (ROOT / "bin").exists(), (
        "a top-level bin/ directory makes hosted marketplace sync fail with "
        "marketplace_sync_bin_directory_not_allowed"
    )
    assert not any(rel == "bin" or rel.startswith("bin/") for rel in _tracked())


def test_launcher_lives_in_scripts_and_is_executable() -> None:
    assert LAUNCHER.is_file()
    if os.name == "posix":
        # The executable bit is a POSIX mode bit; Windows checkouts have none.
        assert LAUNCHER.stat().st_mode & 0o111, "the launcher must stay executable"
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'runtime="${launcher_dir}/runtime.py"' in text, (
        "the launcher must resolve runtime.py as a sibling"
    )
    assert "/../scripts/" not in text


def test_no_instruction_file_keeps_a_bare_launcher_invocation() -> None:
    offenders = []
    for rel in _instruction_docs():
        for match in BARE_INVOCATION.finditer((ROOT / rel).read_text(encoding="utf-8")):
            offenders.append(f"{rel}: {match.group(0)}")
    assert not offenders, "bare launcher invocations found: " + "; ".join(offenders)


def test_instruction_files_use_the_checkout_launcher() -> None:
    docs = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in _instruction_docs()}
    carriers = [
        rel
        for rel, text in docs.items()
        if CHECKOUT_LAUNCHER in text
    ]
    assert len(carriers) > 30, "the checkout launcher form should be used repo-wide"
    assert "skills/seo/SKILL.md" in carriers
    assert "agents/seo-technical.md" in carriers
    assert not [rel for rel, text in docs.items() if PLUGIN_ROOT_LAUNCHER in text]


@pytest.mark.skipif(
    os.name != "posix",
    reason="the launcher requires Bash",
)
def test_launcher_runs_without_network_or_managed_runtime() -> None:
    """``doctor --help`` is handled by argparse before any venv is touched."""
    # Python 3.14 argparse colourises help whenever colour is forced in the
    # environment; disable it and strip any escapes so the assertion is stable.
    env = {**os.environ, "PYTHON_COLORS": "0", "NO_COLOR": "1"}
    env.pop("FORCE_COLOR", None)
    result = subprocess.run(
        ["bash", str(LAUNCHER), "doctor", "--help"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=env,
    )
    assert result.returncode == 0, result.stderr
    plain = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert "usage: codex-seo doctor" in plain
