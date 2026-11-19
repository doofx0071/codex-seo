# Codex SEO

A Codex-first SEO workspace based on [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo). The upstream project supplies 29 SEO skill guides, 20 specialist prompts, and the local Python toolkit. This fork adds Codex-native skill discovery and custom agent roles while preserving the upstream code and MIT license.

## Use it in Codex

This Codex adaptation is currently on the `codex-native-support` branch.

1. Clone this branch and open the folder in Codex:

~~~bash
git clone --branch codex-native-support https://github.com/helx0071/codex-seo.git
~~~

2. Let Codex load the project instructions and skills. The project skill is under `.agents/skills/seo/`; the specialist roles are under `.codex/agents/`.
3. Ask Codex to use the `$seo` skill:

~~~text
$seo audit https://example.com
$seo page https://example.com/pricing
$seo technical https://example.com
$seo geo https://example.com
~~~

The skill routes requests to the existing specialist guides under `skills/`, then uses the existing `agents/` prompts for delegated analysis. It keeps the work in Codex's native skill and agent formats instead of requiring Claude Code or Claude-only plugin commands.

## Runtime

For script-backed checks, the skill uses the repository's managed launcher:

~~~bash
./scripts/claude-seo doctor --json
./scripts/claude-seo run render_page.py https://example.com --mode auto --json
~~~

The launcher requires Bash and Python 3.11–3.14. On Windows, run it from WSL or Git Bash. The isolated runtime setup changes the local environment, so request setup explicitly before running:

~~~bash
./scripts/claude-seo setup
~~~

Some integrations need their own credentials or MCP connection. They are optional; a basic audit can still report which checks could not be measured. Do not treat estimates from source inspection as measured Core Web Vitals.

## Model and parallelism

The project config uses `gpt-6-luna` with high reasoning for ordinary SEO specialists, caps active subagents at four, and assigns `seo-technical` to `gpt-6.2-sol` for more demanding technical and security checks. The root Codex session remains on the model you select. Edit `.codex/config.toml` and the relevant agent TOML if those models are unavailable or you prefer different usage.

## Upstream and license

This is a fork of [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo). The upstream project already includes cross-agent guidance for Codex; this branch adds a Codex-discoverable entry point and native custom-agent configurations. The original code and guides remain attributed to their authors under the MIT License in [LICENSE](LICENSE). For the upstream Claude Code installation and extension documentation, see the original repository.

