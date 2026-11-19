"""Static launcher checks that do not mutate a real home."""

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    os.name != "posix", reason="the executable bit is a POSIX mode bit; Windows has none"
)
def test_launcher_is_executable() -> None:
    assert (ROOT / "scripts/codex-seo").stat().st_mode & 0o100


def test_launcher_uses_safe_exec() -> None:
    text = (ROOT / "scripts/codex-seo").read_text(encoding="utf-8")
    assert 'exec "${CODEX_SEO_PYTHON}" "${runtime}" "$@"' in text
    assert 'exec "$@" "${runtime}" "${script_args[@]+"${script_args[@]}"}"' in text
    assert "eval " not in text
