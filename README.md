# Codex SEO

Audit websites and web projects in Codex or ChatGPT. Codex SEO covers crawlability, indexing, structured data, content quality, Core Web Vitals, AI search, local search, and ecommerce. It produces an evidence-backed report with prioritized fixes and identifies the checks it could not run.

| Use | Start here |
|---|---|
| Codex checkout with local scripts and specialist agents | [Installation](docs/INSTALLATION.md) |
| Portable skill for ChatGPT Desktop and Codex | [Plugin build and verification](docs/PHASE1-VERIFICATION.md) |
| Optional SEO and analytics providers | [Integrations](docs/MCP-INTEGRATION.md) |
| Examples and supported prompts | [Command reference](docs/COMMANDS.md) |

## Run from a Codex checkout

```bash
git clone --branch main https://github.com/doofx0071/codex-seo.git
cd codex-seo
```

This is the independent Codex SEO repository. Its canonical branch is `main`. The project was carried forward from an earlier fork and is independently maintained and derived from [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo); upstream attribution and history are preserved.

Open the checkout in Codex. Codex discovers the `$seo` skill under `.agents/skills/seo/` and the project-scoped specialist agents in `.codex/agents/`. Try these prompts:

```text
$seo audit https://example.com
$seo page https://example.com/pricing
$seo technical https://example.com
$seo geo https://example.com
```

For script-backed checks, use Bash and Python 3.11 to 3.14. On Windows, use Git Bash or WSL with Python installed in the same environment. Check readiness and explicitly set up the isolated runtime when needed:

```bash
./scripts/codex-seo doctor --json
./scripts/codex-seo setup
```

From another working directory, use the quoted absolute path to the checkout's launcher. Keep the audited project as the working directory so local inputs and audit files resolve there. Managed scripts provide guarded fetches, processing of raw HTML and browser measurements when Chromium is available. Search performance, traffic and provider metrics require access to the corresponding data source.

The project config allows four active specialist agents. The root session keeps your selected model. Adjust `.codex/config.toml` and the role files if a configured specialist model is unavailable.

## Use the portable plugin

Use the plugin on a ChatGPT or Codex surface with access to the built archive. It follows the same audit method using the browsing and document tools available in its host. For example, ask “Use Codex SEO to audit https://example.com and mark any unavailable measurements.” See [Phase 1 verification](docs/PHASE1-VERIFICATION.md) for package availability and desktop smoke checks.

See [migration notes](docs/MIGRATION-v1-to-v2.md) for an existing checkout and [community integrations](docs/COMMUNITY-INTEGRATIONS.md) for contributed tools.

## Credits and license

Codex SEO is an independently maintained project derived and adapted from [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo). See [CONTRIBUTORS.md](CONTRIBUTORS.md) for original-author and community attribution and [LICENSE](LICENSE) for the MIT copyright and permission notice.
