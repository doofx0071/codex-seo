# PostHog extension setup

This extension lets codex-seo use the PostHog MCP server as an analytics source,
the same way the Matomo extension uses the Matomo Reporting API. It stores no
credentials: authentication belongs to the MCP server.

> **Use read-only access.** The PostHog MCP `exec` tool can read data and also
> create, update and delete PostHog objects (insights, dashboards, feature
> flags and more). codex-seo only ever needs to read, and its read-only rule is
> an instruction to the agent, not a technical limit. Authenticate the MCP
> server with a read-only scoped personal API key, or sign in as a member whose
> access to the project is read-only, so a write cannot succeed.

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/posthog/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\posthog\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

## Connect the MCP server

```bash
codex mcp add posthog --url https://mcp.posthog.com/mcp
codex mcp login posthog
codex mcp list
```

Use a read-only account or equivalent scoped access. If you self-host, use your instance's MCP URL. Check the PostHog documentation for the authentication and permissions supported by your instance. Tools can be exposed as `mcp__posthog__exec` or `mcp__PostHog__exec`, depending on the server name.

## 3. Use

```
$seo posthog check
$seo posthog organic
$seo posthog referrers
```

During `$seo audit`, the agent is spawned when PostHog MCP tools are available.

## Limits

- Organic search uses `session.$channel_type = 'Organic Search'` (fallback:
  `$referring_domain`), so numbers will not match GA4 or Matomo exactly
- No organic keyword data (use Search Console via `seo-google`)
- Requires `$pageview` events with referrer properties captured
- Queries run as HogQL via `execute-sql`. Sub-tool names can change between
  PostHog MCP versions, so the agent runs `info` before each new tool

## Uninstall

Run `./extensions/posthog/uninstall.sh` to remove the checkout skill entry. Remove your server registration with `codex mcp remove posthog`.
