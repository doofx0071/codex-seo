"""Keep the runtime and its data available in the checkout."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_runtime_import_validation_requires_html_clean_split_package() -> None:
    runtime = _text("scripts/runtime.py")
    assert "import bs4, lxml, lxml_html_clean, playwright, requests, trafilatura" in runtime


def test_google_updates_data_exists_at_installed_relative_path() -> None:
    assert (ROOT / "data" / "google-updates.json").is_file()
    assert (ROOT / "scripts" / "seo_updates.py").is_file()
