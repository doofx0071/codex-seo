"""Core and extension copies expose consistent SEO guidance."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from extension_install import _entry, manage_skill  # noqa: E402

# Mirrored role prompts must be byte-identical. Model assignment lives in
# native `.codex/agents/*.toml`; tools follow the parent session's permissions.
AGENT_MIRRORS = [
    ("agents/seo-dataforseo.md", "extensions/dataforseo/agents/seo-dataforseo.md"),
    ("agents/seo-image-gen.md", "extensions/banana/agents/seo-image-gen.md"),
    ("agents/seo-posthog.md", "extensions/posthog/agents/seo-posthog.md"),
]

# The DataForSEO skill has no install-specific content, so the whole folder
# (SKILL.md and references) must match.
DATAFORSEO_CORE = ROOT / "skills/seo-dataforseo"
DATAFORSEO_EXT = ROOT / "extensions/dataforseo/skills/seo-dataforseo"

# The Bing, Shopify and PostHog guides share the same text in both trees.
IDENTICAL_SKILL_MIRRORS = [
    ("skills/seo-bing", "extensions/bing-webmaster/skills/seo-bing"),
    ("skills/seo-shopify", "extensions/shopify/skills/seo-shopify"),
    ("skills/seo-posthog", "extensions/posthog/skills/seo-posthog"),
]

# The image-gen skill differs on purpose: the core copy has no scripts and
# points at the installed Banana MCP, while the extension copy ships
# presets.py, cost_tracker.py and generate.py and resolves them through
# the extension runtime. These files may differ; every other reference must not.
IMAGE_GEN_CORE_REFS = ROOT / "skills/seo-image-gen/references"
IMAGE_GEN_EXT_REFS = ROOT / "extensions/banana/references"
IMAGE_GEN_ALLOWED_DIFFERENCES = {
    "cost-tracking.md",
    "gemini-models.md",
    "mcp-tools.md",
    "prompt-engineering.md",
    "seo-image-presets.md",
}


@pytest.mark.parametrize("core, ext", AGENT_MIRRORS)
def test_agent_mirrors_are_identical(core, ext):
    assert (ROOT / core).read_bytes() == (ROOT / ext).read_bytes(), (
        f"{ext} has drifted from {core}; edit both together"
    )


def _files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_dataforseo_skill_mirror_is_identical():
    core, ext = _files(DATAFORSEO_CORE), _files(DATAFORSEO_EXT)
    assert core == ext, f"file sets differ: {sorted(core ^ ext)}"
    drifted = [
        name
        for name in sorted(core)
        if (DATAFORSEO_CORE / name).read_bytes() != (DATAFORSEO_EXT / name).read_bytes()
    ]
    assert not drifted, f"seo-dataforseo copies have drifted: {drifted}"


@pytest.mark.parametrize("core, ext", IDENTICAL_SKILL_MIRRORS)
def test_skill_mirror_folders_are_identical(core, ext):
    core_dir, ext_dir = ROOT / core, ROOT / ext
    assert (core_dir / "SKILL.md").is_file(), f"{core}/SKILL.md missing"
    core_files, ext_files = _files(core_dir), _files(ext_dir)
    assert core_files == ext_files, f"file sets differ: {sorted(core_files ^ ext_files)}"
    drifted = [
        name
        for name in sorted(core_files)
        if (core_dir / name).read_bytes() != (ext_dir / name).read_bytes()
    ]
    assert not drifted, f"{ext} has drifted from {core}; edit both together: {drifted}"


def test_image_gen_references_differ_only_where_documented():
    core, ext = _files(IMAGE_GEN_CORE_REFS), _files(IMAGE_GEN_EXT_REFS)
    assert core == ext, f"reference file sets differ: {sorted(core ^ ext)}"
    drifted = {
        name
        for name in core
        if (IMAGE_GEN_CORE_REFS / name).read_bytes() != (IMAGE_GEN_EXT_REFS / name).read_bytes()
    }
    unexpected = drifted - IMAGE_GEN_ALLOWED_DIFFERENCES
    assert not unexpected, f"undocumented image-gen reference drift: {sorted(unexpected)}"


def _make_checkout(tmp_path, extension):
    checkout = tmp_path / "checkout with spaces"
    guide = next((ROOT / "extensions" / extension / "skills").glob("seo-*/SKILL.md"))
    target = checkout / guide.relative_to(ROOT)
    target.parent.mkdir(parents=True)
    target.write_bytes(guide.read_bytes())
    return checkout, guide.parent.name


def test_extension_install_and_uninstall_are_scoped_to_the_checkout(tmp_path):
    checkout, name = _make_checkout(tmp_path, "shopify")
    skill = checkout / ".agents/skills" / name / "SKILL.md"
    manage_skill(checkout, "shopify", "install")
    original = skill.read_text(encoding="utf-8")
    relative_guide = "../../../extensions/shopify/skills/seo-shopify/SKILL.md"
    assert checkout.as_posix() not in original
    assert relative_guide in original
    checkout = checkout.rename(tmp_path / "renamed checkout")
    skill = checkout / ".agents/skills" / name / "SKILL.md"
    assert (skill.parent / relative_guide).is_file()
    manage_skill(checkout, "shopify", "install")
    assert skill.read_text(encoding="utf-8") == original

    user_file = skill.with_name("notes.md")
    user_file.write_text("private notes", encoding="utf-8")
    manage_skill(checkout, "shopify", "uninstall")
    assert not skill.exists()
    assert user_file.read_text(encoding="utf-8") == "private notes"


def test_extension_installer_preserves_existing_skill(tmp_path):
    checkout, name = _make_checkout(tmp_path, "posthog")
    skill = checkout / ".agents/skills" / name / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("local guidance", encoding="utf-8")
    for action in ("install", "uninstall"):
        with pytest.raises(ValueError, match="left in place"):
            manage_skill(checkout, "posthog", action)
        assert skill.read_text(encoding="utf-8") == "local guidance"


@pytest.mark.parametrize("action", ["install", "uninstall"])
def test_moved_legacy_registration_only_changes_if_unedited(tmp_path, action):
    checkout, name = _make_checkout(tmp_path, "posthog")
    guide = checkout / f"extensions/posthog/skills/{name}/SKILL.md"
    skill = checkout / ".agents/skills" / name / "SKILL.md"
    skill.parent.mkdir(parents=True)
    previous = _entry(checkout, guide, legacy_root=(tmp_path / "old checkout").as_posix())
    edited = previous + b"Local notes\n"
    skill.write_bytes(edited)
    with pytest.raises(ValueError, match="left in place"):
        manage_skill(checkout, "posthog", action)
    assert skill.read_bytes() == edited

    skill.write_bytes(previous)
    manage_skill(checkout, "posthog", action)
    if action == "install":
        assert b"../../../extensions/posthog/skills/seo-posthog/SKILL.md" in skill.read_bytes()
        assert b"old checkout" not in skill.read_bytes()
    else:
        assert not skill.exists()
