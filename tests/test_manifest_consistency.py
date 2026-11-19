"""Keep the Codex checkout's version, role and source-guide metadata in sync."""

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _project() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_citation_matches_checkout_metadata():
    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "title: Codex SEO" in citation
    assert re.search(r"^version: (\S+)", citation, re.MULTILINE).group(1) == _project()["version"]
    assert f"repository-code: '{_project()['urls']['Repository']}'" in citation


def test_native_roles_match_the_source_agent_prompts():
    native = {p.stem for p in (REPO_ROOT / ".codex/agents").glob("seo-*.toml")}
    prompts = {p.stem for p in (REPO_ROOT / "agents").glob("seo-*.md")}
    assert native == prompts


def _extract_section(text: str, heading: str) -> str:
    """Return the body of a `## <heading>` section, up to the next H2 heading or EOF."""
    pattern = rf"^## {re.escape(heading)}\b.*?(?=^## |\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return m.group(0) if m else ""


def test_orchestrator_sub_skills_list_matches_disk():
    """skills/seo/SKILL.md Sub-Skills numbered list must equal set(skills/*) minus orchestrator itself.

    Background: v1.9.8 CI guard checks the top-level guides but not the orchestrator's
    own canonical-phrasing source. PR #92 surfaced that the orchestrator had stale "21
    specialized" claims and the list included seo-firecrawl (extension-only). This
    guard closes that gap.
    """
    text = (REPO_ROOT / "skills" / "seo" / "SKILL.md").read_text(encoding="utf-8")
    section = _extract_section(text, "Sub-Skills")
    listed_list = re.findall(r"^\d+\.\s+\*\*(seo-[a-z-]+)\*\*", section, re.MULTILINE)
    assert len(listed_list) == len(set(listed_list)), (
        f"Duplicate entries in Sub-Skills list: "
        f"{[n for n in listed_list if listed_list.count(n) > 1]}"
    )
    listed = set(listed_list)
    on_disk = {
        d.name for d in (REPO_ROOT / "skills").iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    }
    # The orchestrator (`seo`) does not list itself.
    # seo-firecrawl is documented separately in an Optional Extensions subsection
    # because it lives only in extensions/, not in skills/.
    expected = on_disk - {"seo"}
    assert listed == expected, (
        f"Sub-Skills list != skills/ dir. "
        f"Missing from list: {sorted(expected - listed)}. "
        f"Extra in list: {sorted(listed - expected)}."
    )


def test_orchestrator_subagents_list_matches_disk():
    """skills/seo/SKILL.md Subagents bullet list must equal set(agents/seo-*.md), no duplicates.

    Background: same drift pattern as Sub-Skills. Codex round 3 review surfaced that
    the Subagents list was missing seo-flow (file on disk) and included seo-firecrawl
    (no agent file on disk).
    """
    text = (REPO_ROOT / "skills" / "seo" / "SKILL.md").read_text(encoding="utf-8")
    section = _extract_section(text, "Subagents")
    listed_list = re.findall(r"^- `(seo-[a-z-]+)`", section, re.MULTILINE)
    assert len(listed_list) == len(set(listed_list)), (
        f"Duplicate entries in Subagents list: "
        f"{[n for n in listed_list if listed_list.count(n) > 1]}"
    )
    listed = set(listed_list)
    on_disk = {
        p.stem for p in (REPO_ROOT / "agents").iterdir()
        if p.is_file() and p.suffix == ".md" and p.name.startswith("seo-")
    }
    assert listed == on_disk, (
        f"Subagents list != agents/ dir. "
        f"Missing from list: {sorted(on_disk - listed)}. "
        f"Extra in list: {sorted(listed - on_disk)}."
    )


def _extract_frontmatter(text: str) -> str:
    """Return the YAML frontmatter block (between the first two `---` lines).

    Returns the body between the delimiters (exclusive), or empty string if no
    frontmatter present. Scoping the regex search to this block prevents a
    fenced code example or later doc snippet from satisfying a metadata check.
    """
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    return m.group(1) if m else ""


def test_skill_metadata_versions_match_checkout():
    """Source SKILL.md metadata.version must equal the checkout version (with community allowlist).

    Covers in-tree skills/*/SKILL.md and extension-mirror copies under
    extensions/*/skills/*/SKILL.md. Community contributions can be allowlisted
    to keep their own version cadence.

    Implementation note: parses the YAML frontmatter block specifically so that
    a fenced code example or later doc snippet showing `version: "x"` cannot
    satisfy the assertion after metadata.version has been removed from frontmatter.
    """
    # Community-contributed skills that maintain their own version cadence.
    # Each entry: skill name -> expected literal version string.
    COMMUNITY_OVERRIDES = {"seo-content-brief": "1.0.0"}

    expected_default = _project()["version"]
    errors = []

    candidates = list((REPO_ROOT / "skills").glob("*/SKILL.md")) + list(
        (REPO_ROOT / "extensions").glob("*/skills/*/SKILL.md")
    )
    for skill_md in candidates:
        skill_name = skill_md.parent.name
        rel = skill_md.relative_to(REPO_ROOT)
        text = skill_md.read_text(encoding="utf-8")
        frontmatter = _extract_frontmatter(text)
        if not frontmatter:
            errors.append(f"{rel} has no YAML frontmatter block")
            continue
        # metadata.version is nested under `metadata:` and indented by 2 spaces
        match = re.search(
            r'^  version:\s*"([^"]+)"', frontmatter, re.MULTILINE
        )
        if not match:
            errors.append(f"{rel} has no metadata.version in frontmatter")
            continue
        actual = match.group(1)
        expected = COMMUNITY_OVERRIDES.get(skill_name, expected_default)
        if actual != expected:
            errors.append(f"{rel}: version is {actual}, expected {expected}")

    assert not errors, "Skill metadata.version drift:\n  " + "\n  ".join(errors)


def test_reference_files_have_at_least_one_link():
    """Every skills/*/references/*.md file must be cited somewhere in the repo.

    Guards against orphan reference files, docs on disk that no SKILL.md,
    agent, top-level doc, or other reference file actually links to. Catches
    drift like the v2.0.0-era incident where llmstxt-evidence.md landed in
    references/ but was reachable only through a sibling cross-link, not
    through its parent SKILL.md.

    Cross-skill references are legitimate (e.g. skills/seo/references/
    backlink-quality.md is cited from seo-backlinks/SKILL.md) so the search
    is repo-wide rather than per-parent-skill.

    Searches the full filename (`name.md`) and the Obsidian-style wikilink
    form (`[[name]]`) across: every SKILL.md, every agent .md, every doc/*.md,
    top-level README/CHANGELOG/AGENTS/CONTRIBUTING, and every other
    reference file. Each reference is excluded from its own search.
    """
    ref_files = list((REPO_ROOT / "skills").glob("*/references/*.md"))
    if not ref_files:
        return  # no references at all

    search_paths: list[Path] = []
    search_paths += list((REPO_ROOT / "skills").glob("*/SKILL.md"))
    search_paths += list((REPO_ROOT / "agents").glob("*.md"))
    search_paths += list((REPO_ROOT / "docs").glob("*.md"))
    for doc in ("README.md", "CHANGELOG.md",
                "AGENTS.md", "CONTRIBUTING.md"):
        candidate = REPO_ROOT / doc
        if candidate.exists():
            search_paths.append(candidate)
    # Reference files can cite each other (e.g. via [[wikilink]]).
    search_paths += ref_files

    text_by_path = {p: p.read_text(encoding="utf-8") for p in search_paths}

    orphans = []
    for ref in ref_files:
        slug = ref.stem  # 'llmstxt-evidence'
        filename = ref.name  # 'llmstxt-evidence.md'
        wikilink = f"[[{slug}]]"
        found = False
        for other_path, text in text_by_path.items():
            if other_path == ref:
                continue
            if filename in text or wikilink in text:
                found = True
                break
        if not found:
            orphans.append(str(ref.relative_to(REPO_ROOT)))

    assert not orphans, (
        "Orphan reference files (on disk, not cited anywhere repo-wide):\n  "
        + "\n  ".join(orphans)
        + "\n\nFix: link the file from its parent SKILL.md, a related "
          "reference doc, or a top-level doc, or delete it if obsolete."
    )
