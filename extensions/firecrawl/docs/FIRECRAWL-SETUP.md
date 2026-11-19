# Firecrawl Setup Guide

## 1. Get Your API Key

1. Go to [firecrawl.dev/app/sign-up](https://www.firecrawl.dev/signup)
2. Create a free account (500 credits/month included)
3. Navigate to **API Keys** in the dashboard
4. Copy your API key (starts with `fc-`)

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/firecrawl/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\firecrawl\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Install Node.js 20+ and set `FIRECRAWL_API_KEY` in your local environment.

## Configure MCP

Add this entry to your user `~/.codex/config.toml`. Set the named credentials in the environment that starts Codex. See [MCP and provider setup](../../../docs/MCP-INTEGRATION.md).

```toml
[mcp_servers.firecrawl-mcp]
command = "npx"
args = ["-y", "firecrawl-mcp@3.11.0"]
env_vars = ["FIRECRAWL_API_KEY"]
```

Verify registration with `codex mcp list`.

## Verify installation

Confirm the connection in Codex. Firecrawl operations can consume credits. Review the expected cost before running a live crawl.

## 5. Understanding Credits

| Operation | Credits Used |
|-----------|-------------|
| `crawl` | 1 per page crawled |
| `scrape` | 1 per page |
| `map` | 0.5 per URL discovered |
| `search` | 1 per result returned |

**Free tier**: 500 credits/month resets on your billing date.

**Tip**: Use `map` first (cheap) to see how many pages a site has, then decide how many to `crawl` (more expensive).
