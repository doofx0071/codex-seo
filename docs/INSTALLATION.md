# Install Codex SEO

## Codex checkout

1. Clone and open the checkout in Codex.

   ```bash
   git clone --branch codex-native-support https://github.com/helx0071/codex-seo.git
   cd codex-seo
   ```

2. Select `$seo` and ask `audit https://example.com`. Codex reads `.agents/skills/seo/SKILL.md` and discovers the specialist roles in `.codex/agents/` when the project config is loaded.
3. For script-backed checks, install Python 3.11 to 3.14 and Bash. On Windows use Git Bash or WSL and install a Python interpreter accessible from that shell.

   ```bash
   ./scripts/codex-seo doctor --json
   ./scripts/codex-seo setup
   ./scripts/codex-seo run seo_updates.py --limit 1 --json
   ```

Setup installs the Python dependencies and Playwright Chromium into managed storage. It requires network access or an environment with dependencies already provisioned. `./scripts/codex-seo setup --skip-browser` is available when local browser checks are unnecessary. Run `./scripts/codex-seo setup --help` for options. If the working directory is another project, invoke `"/absolute/path/to/codex-seo/scripts/codex-seo"` to keep the audited project's relative paths intact.

Optional integrations are documented in [MCP and provider setup](MCP-INTEGRATION.md). Add credentials only when you need the provider. For updates, pull the reviewed branch revision and rerun `doctor`. The checkout's local configuration and venv can be removed when you retire that checkout.

## ChatGPT Desktop and Codex portable plugin

Follow [Phase 1 verification](PHASE1-VERIFICATION.md) to build the plugin archive when the packaging files are available. Use the installed or privately shared plugin in a new ChatGPT or Codex session, then ask it to audit `https://example.com`. The portable skill uses the host capabilities available to it.
