# DataForSEO Account Setup

Step-by-step guide to getting DataForSEO API credentials for the Codex SEO extension.

## 1. Create Account

1. Go to [app.dataforseo.com/register](https://app.dataforseo.com/register)
2. Sign up with your email address
3. Verify your email

New accounts include a free trial balance for testing.

## 2. Find API Credentials

1. Log in to [app.dataforseo.com](https://app.dataforseo.com)
2. Go to **API Access** in the left sidebar
3. Your credentials are:
   - **Username**: Your registered email address
   - **Password**: Your API password (set during registration)

Set these as `DATAFORSEO_USERNAME` and `DATAFORSEO_PASSWORD` in the environment that starts Codex.

## 3. Understanding Credits

DataForSEO uses a credit-based system:

- Each API call costs a small number of credits
- Different endpoints have different costs
- Credits are purchased in advance
- Monitor usage at [app.dataforseo.com/dashboard](https://app.dataforseo.com/dashboard)

**Typical costs per call, verified as of 2026-07-10:**

| Endpoint Type | Approximate Cost |
|--------------|-----------------|
| SERP (single query) | $0.001-0.003 |
| Keyword volume (per keyword) | $0.0005-0.002 |
| Backlink summary | $0.002-0.005 |
| Backlink list | $0.005-0.01 |
| On-page crawl (per page) | $0.01-0.05 |
| AI optimization (per call) | $0.05 |

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/dataforseo/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\dataforseo\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Install Node.js 20+ and use the credentials from your account. Set the field configuration path to the absolute path to `extensions/dataforseo/field-config.json` in your checkout.

Add this entry to your user `~/.codex/config.toml`. Set the named credentials in the environment that starts Codex. See [MCP and provider setup](../../../docs/MCP-INTEGRATION.md).

```toml
[mcp_servers.dataforseo]
command = "npx"
args = ["-y", "dataforseo-mcp-server@2.8.10"]
env_vars = ["DATAFORSEO_USERNAME", "DATAFORSEO_PASSWORD"]

[mcp_servers.dataforseo.env]
ENABLED_MODULES = "SERP,KEYWORDS_DATA,ONPAGE,DATAFORSEO_LABS,BACKLINKS,DOMAIN_ANALYTICS,BUSINESS_DATA,CONTENT_ANALYSIS,AI_OPTIMIZATION"
FIELD_CONFIG_PATH = "/absolute/path/to/codex-seo/extensions/dataforseo/field-config.json"
```

Verify registration with `codex mcp list`.

## Verify installation

Use `codex mcp list` and confirm the tools are available in a new Codex session. Check your usage limits before approving a live query.
