# Profound extension setup

Profound (https://tryprofound.com) tracks brand mentions across LLMs as
a time-series: the complement to SE Ranking's on-demand sampling.

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/profound/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\profound\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Set `PROFOUND_API_KEY` in your Codex launch environment. Use a provider account with read-only access for audits.

## Verify

```
$seo profound citations "Codex SEO"
```

## Uninstall

Run `./extensions/profound/uninstall.sh` to remove the checkout skill entry. Remove `PROFOUND_API_KEY` from the environment you configured.

## When to use Profound vs. SE Ranking

| Use Profound | Use SE Ranking |
|---|---|
| Trend analysis (week-over-week brand mention drift) | Single-shot SoV measurement |
| ChatGPT + Perplexity deep coverage | All 5 platforms in one call |
| Alerts on citation rate change | Competitor-keyword gap analysis |

The two are complementary, not redundant. Install both for full AI
visibility coverage; install one if budget-constrained.
