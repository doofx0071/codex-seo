# SE Ranking extension setup

SE Ranking's API exposes traditional SEO data (SERP, backlinks,
competitors) plus AI Share-of-Voice across 5 AI platforms.

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/seranking/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\seranking\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Set `SERANKING_API_KEY` in the environment that starts Codex. Confirm any plan charges before invoking a provider query.

## Get an API key

https://seranking.com/api.html: pricing is unit-based; the AI visibility
endpoint costs ~5 units per query (1 per platform).

## Verify

```
$seo seranking ai-visibility "Codex SEO"
```

Expected output: percentages per platform (ChatGPT, Gemini, Perplexity,
AI Overviews, AI Mode) with sample-size confidence notes.

## Rotate key

Replace `SERANKING_API_KEY` in the environment that launches Codex, then open a new session.

## Uninstall

Run `./extensions/seranking/uninstall.sh` to remove the checkout skill entry. Remove `SERANKING_API_KEY` from the environment you configured.
