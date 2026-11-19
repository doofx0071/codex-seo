"""Checkout extension wrappers forward safe arguments to the managed runtime."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("source", sorted((ROOT / "extensions").glob("*/*install.sh")))
@pytest.mark.skipif(os.name != "posix" or not shutil.which("bash"), reason="requires POSIX Bash")
def test_extension_wrapper_forwards_arguments_without_shell_expansion(tmp_path, source):
    checkout = tmp_path / "checkout with spaces"
    installer = checkout / source.relative_to(ROOT)
    installer.parent.mkdir(parents=True)
    shutil.copy2(source, installer)
    launcher = checkout / "scripts/codex-seo"
    launcher.parent.mkdir()
    launcher.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\npwd\n", encoding="utf-8")
    launcher.chmod(0o700)

    audit_dir = tmp_path / "audited project"
    audit_dir.mkdir()
    argument = "$(touch unexpected)"
    result = subprocess.run(
        ["bash", str(installer), argument], cwd=audit_dir, check=True,
        capture_output=True, text=True,
    )
    assert result.stdout.splitlines() == [
        "run", "extension_install.py", installer.stem, installer.parent.name,
        argument, str(audit_dir.resolve()),
    ]
    assert not (audit_dir / "unexpected").exists()


@pytest.mark.parametrize("source", sorted((ROOT / "extensions").glob("*/*install.ps1")))
def test_powershell_wrapper_uses_the_checkout_launcher(source):
    text = source.read_text(encoding="utf-8")
    assert 'Join-Path $PSScriptRoot "../../scripts/codex-seo"' in text
    assert f"run extension_install.py {source.stem} $Extension @args" in text
    assert "Invoke-Expression" not in text
