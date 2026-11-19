# Ahrefs extension setup

Wires the official [`@ahrefs/mcp@0.0.11`](https://www.npmjs.com/package/@ahrefs/mcp)
server into your Codex session so the `seo-ahrefs` skill can call
live Ahrefs data.

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/ahrefs/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\ahrefs\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Install Node.js 18+ and obtain an Ahrefs API token. Add this entry to your user `~/.codex/config.toml`. Set the named credentials in the environment that starts Codex. See [MCP and provider setup](../../../docs/MCP-INTEGRATION.md).

```toml
[mcp_servers.ahrefs]
command = "npx"
args = ["--yes", "--package=@ahrefs/mcp@0.0.11", "mcp"]
env_vars = ["AHREFS_API_TOKEN"]
```

Verify registration with `codex mcp list`.

## Verify

Open a new Codex session and ask:

```
$seo ahrefs metrics https://example.com
```

If Ahrefs MCP is unavailable, check `codex mcp list` and confirm Codex inherited `AHREFS_API_TOKEN`. Make sure Node.js and `npx` are available in that environment. The first server start may need network access to download the pinned package.

## Rotate token

Replace `AHREFS_API_TOKEN` in your local environment and start a new Codex session.

## Uninstall

Run `./extensions/ahrefs/uninstall.sh` to remove the checkout skill entry. Remove your server registration with `codex mcp remove ahrefs`. Remove `AHREFS_API_TOKEN` from the environment you configured.

## Cost model

Ahrefs charges per "unit". A unit covers most read endpoints (domain
metrics, backlink data) at 1 unit each; bulk endpoints cost more. The
`./scripts/codex-seo run dataforseo_costs.py` cost tracker shipped with codex-seo
generalises across vendors; see the DataForSEO extension's
`references/cost-tiers.md` for the budget-preset pattern to mirror when
wiring Ahrefs accounting.

## Troubleshooting

Check `codex mcp list`, the server package and Node version, and whether the Codex process inherited `AHREFS_API_TOKEN`. If a request returns 401, check the token and permissions in your Ahrefs account.
