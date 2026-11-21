"""Codex role tool guidance and fail-closed regressions."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = (
    ROOT / "agents" / "seo-dataforseo.md",
    ROOT / "extensions" / "dataforseo" / "agents" / "seo-dataforseo.md",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_dataforseo_agent_mirrors_use_codex_config_not_markdown_tool_grants():
    for path in AGENTS:
        text = _text(path)
        frontmatter = text.split("---", 2)[1]
        assert not any(
            line.startswith(("model:", "maxTurns:", "tools:"))
            for line in frontmatter.splitlines()
        )
        assert "Use only the exact DataForSEO MCP tools exposed in this Codex session" in text
    config = tomllib.loads((ROOT / ".codex/agents/seo-dataforseo.toml").read_text(encoding="utf-8"))
    assert config["name"] == "seo-dataforseo"
    assert "agents/seo-dataforseo.md" in config["developer_instructions"]


def test_dataforseo_agent_mirrors_fail_closed_without_mcp():
    required = (
        "fail closed",
        "Never inspect credential or",
        "never bypass MCP with curl, raw HTTP, or another client",
    )
    for path in AGENTS:
        text = _text(path)
        for phrase in required:
            assert phrase in text


def test_dataforseo_agent_bodies_stay_mirrored():
    public_body = _text(AGENTS[0]).split("---", 2)[2]
    extension_body = _text(AGENTS[1]).split("---", 2)[2]
    assert public_body == extension_body


def test_dataforseo_setup_uses_matching_mcp_server_name():
    setup = _text(ROOT / "extensions/dataforseo/docs/DATAFORSEO-SETUP.md")
    assert "[mcp_servers.dataforseo]" in setup


def test_maps_agent_uses_only_data_passed_by_the_lead_for_paid_data():
    # Codex Markdown does not grant a per-agent tool set. Keep the paid-data
    # boundary in the role instructions instead of stale host-specific metadata.
    path = ROOT / "agents" / "seo-maps.md"
    text = _text(path)
    assert "Do not call DataForSEO tools yourself" in text
    assert "use DataForSEO maps data only when the lead explicitly passes it" in text
    assert "try `business_data_business_listings_search`" not in text
    assert "Never reach DataForSEO with curl, raw HTTP, or another client" in text
    assert "Capability tier used" in text


def test_hub_passes_paid_maps_data_to_the_maps_agent():
    hub = _text(ROOT / "skills" / "seo" / "SKILL.md")
    assert "through the seo-dataforseo agent or your own DataForSEO MCP tools" in hub
    assert "pass that data in the seo-maps prompt" in hub
    assert "must say which tier was used" in hub


def test_posthog_agent_is_read_only_and_names_both_tool_spellings():
    path = ROOT / "extensions" / "posthog" / "agents" / "seo-posthog.md"
    text = _text(path)
    assert "mcp__PostHog__exec" in text and "mcp__posthog__exec" in text
    assert "The extension installer registers only the checkout skill" in " ".join(text.split())
    assert "Read-only, with no exceptions." in text
    assert "never send a query that is not" in text
    # The setup guide registers the server in lowercase, so references accept
    # that spelling alongside the alternate casing exposed by some hosts.
    assert "codex mcp add posthog --url" in _text(ROOT / "extensions/posthog/docs/POSTHOG-SETUP.md")
    for rel in ("skills/seo/SKILL.md", "extensions/posthog/skills/seo-posthog/SKILL.md",
                "extensions/posthog/docs/POSTHOG-SETUP.md"):
        doc = _text(ROOT / rel)
        assert "mcp__posthog__exec" in doc and "mcp__PostHog__exec" in doc, rel


def test_posthog_docs_recommend_read_only_access():
    setup = _text(ROOT / "extensions/posthog/docs/POSTHOG-SETUP.md")
    skill = _text(ROOT / "extensions/posthog/skills/seo-posthog/SKILL.md")
    assert "Use read-only access." in setup
    security = skill.split("## Security", 1)[1]
    assert "read-only PostHog login or API key" in security
