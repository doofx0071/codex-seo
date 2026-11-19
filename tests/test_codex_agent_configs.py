"""Codex-native agent configuration and durable audit output regressions."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SKILL = ROOT / "skills" / "seo-audit" / "SKILL.md"
CODEX_AGENTS_DIR = ROOT / ".codex" / "agents"
EXTENSION_AGENTS_GLOB = "extensions/*/agents"

EARLY_WRITE_SENTENCE = (
    "write a partial findings\nfile after the first analysis pass and overwrite it with the complete findings\n"
    "before finishing, so a turn-budget stop never loses completed work"
)


def _discover_audit_agents() -> set[str]:
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    names = set(re.findall(r"`(seo-[a-z-]+)`", text))
    # Matomo is applied inline after its credential probe; it is not a Codex
    # subagent and therefore has no `.codex/agents/seo-matomo.toml` file.
    names.discard("seo-matomo")
    return names


def _role_prompt(name: str) -> Path:
    """Resolve the role Markdown used by a Codex config, core tree first."""
    core = ROOT / "agents" / f"{name}.md"
    if core.is_file():
        return core
    matches = sorted(ROOT.glob(f"{EXTENSION_AGENTS_GLOB}/{name}.md"))
    return matches[0] if matches else core


def _config(name: str) -> dict:
    path = CODEX_AGENTS_DIR / f"{name}.toml"
    assert path.is_file(), f"missing Codex agent config for {name}"
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_audit_skill_still_names_the_known_subagent_set():
    assert _discover_audit_agents() == {
        "seo-technical", "seo-content", "seo-schema", "seo-sitemap",
        "seo-performance", "seo-visual", "seo-geo", "seo-local", "seo-maps",
        "seo-google", "seo-backlinks", "seo-cluster", "seo-sxo", "seo-drift",
        "seo-ecommerce", "seo-dataforseo", "seo-agentic",
    }


def test_every_audit_agent_has_a_codex_toml_and_role_prompt():
    for path in sorted(CODEX_AGENTS_DIR.glob("*.toml")):
        name = path.stem
        config = _config(name)
        assert config["name"] == name
        assert config.get("description")
        instructions = config.get("developer_instructions", "")
        role = _role_prompt(name)
        assert role.is_file(), f"missing role prompt for {name}"
        assert role.relative_to(ROOT).as_posix() in instructions
    assert _discover_audit_agents() <= {path.stem for path in CODEX_AGENTS_DIR.glob("*.toml")}


def test_model_defaults_live_in_codex_configuration():
    root_config = tomllib.loads((ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
    assert root_config["agents"]["default_subagent_model"] == "gpt-6-luna"
    technical = _config("seo-technical")
    assert technical["model"] == "gpt-6.2-sol"
    assert technical["model_reasoning_effort"] == "high"


def test_role_markdown_does_not_carry_legacy_host_controls():
    paths = sorted((ROOT / "agents").glob("*.md"))
    paths += sorted(ROOT.glob("extensions/*/agents/*.md"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        frontmatter = text.split("---", 2)[1]
        assert not re.search(r"^(?:model|maxTurns|tools):", frontmatter, re.MULTILINE), path


def test_every_audit_agent_has_the_early_write_instruction():
    missing = []
    for name in sorted(_discover_audit_agents()):
        text = _role_prompt(name).read_text(encoding="utf-8")
        if EARLY_WRITE_SENTENCE not in text:
            missing.append(name)
    assert not missing, f"agents missing the early-write instruction: {missing}"


def test_dataforseo_extension_mirror_also_has_the_early_write_instruction():
    mirror = ROOT / "extensions" / "dataforseo" / "agents" / "seo-dataforseo.md"
    text = mirror.read_text(encoding="utf-8")
    assert EARLY_WRITE_SENTENCE in text
