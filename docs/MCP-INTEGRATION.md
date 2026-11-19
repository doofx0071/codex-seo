# MCP and provider setup

The checkout can use configured Codex MCP servers and the provider-specific tools under `scripts/`. The portable plugin uses the tools available in its host. A provider connection is optional for general audits. Report unavailable metrics when a connection or credential is missing.

## Connect a provider in a Codex checkout

1. Follow the relevant setup guide below. For optional checkout skill discovery, run the extension's `install.sh` or its `install.ps1` where provided. These scripts register the skill under `.agents/skills/` in the checkout.
2. Configure MCP servers in the user `~/.codex/config.toml`, or use Codex MCP settings where available. For stdio servers, `env_vars` forwards named variables from the Codex process environment. Supply their values outside the checkout and avoid putting tokens in config examples, logs, or shell history.
3. Use `codex mcp list` to check registration. Open a new session after changing local configuration. For supported remote OAuth connections, authorize the server using `codex mcp login <server-name>` or the host's connection settings. See [Codex MCP documentation](https://developers.openai.com/codex/mcp).

If Codex is already running, restart it from an environment that has the required variables. If the desktop app cannot inherit them, use the Codex CLI from the configured shell.

| Integration | Setup guide |
|---|---|
| Ahrefs | [Ahrefs](../extensions/ahrefs/docs/AHREFS-SETUP.md) |
| Banana | [Banana](../extensions/banana/docs/BANANA-SETUP.md) |
| DataForSEO | [DataForSEO](../extensions/dataforseo/docs/DATAFORSEO-SETUP.md) |
| Firecrawl | [Firecrawl](../extensions/firecrawl/docs/FIRECRAWL-SETUP.md) |
| PostHog | [PostHog](../extensions/posthog/docs/POSTHOG-SETUP.md) |
| Bing and IndexNow | [Bing Webmaster](../extensions/bing-webmaster/docs/BING-WEBMASTER-SETUP.md) |
| Google | [Google credentials](../skills/seo-google/references/auth-setup.md) |
| Matomo | [Matomo](../extensions/matomo/docs/MATOMO-SETUP.md) |
| Profound | [Profound](../extensions/profound/docs/PROFOUND-SETUP.md) |
| SE Ranking | [SE Ranking](../extensions/seranking/docs/SERANKING-SETUP.md) |
| Shopify | [Shopify](../extensions/shopify/docs/SHOPIFY-SETUP.md) |
| Unlighthouse | [Unlighthouse](../extensions/unlighthouse/docs/UNLIGHTHOUSE-SETUP.md) |

## Run a checkout integration

```bash
./scripts/codex-seo run google_auth.py --check
./scripts/codex-seo run pagespeed_check.py https://example.com --json
```

The Google setup guide covers API key and OAuth tiers. Search Console and Analytics reports require a verified property or appropriate permissions. PageSpeed Insights delivers lab results, while CrUX delivers field measurements where the data is available. Treat unmeasured checks as unavailable.

Use the least privilege the provider supports. Ask before spending credits, generating paid assets, writing to a provider, or submitting URLs for indexing. An extension's uninstall script removes its checkout skill entry. Remove its MCP entry separately with `codex mcp remove <server-name>` and clear any environment variables or tokens you configured.
