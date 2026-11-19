# Unlighthouse extension setup

[Unlighthouse](https://unlighthouse.dev) is an MIT-licensed multi-page
Lighthouse runner that produces a single aggregate report. No API
quota, no credentials, no network egress beyond crawling the target.

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/unlighthouse/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\unlighthouse\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Install Node.js 18+ and make `npx` available. Set up Playwright Chromium through the checkout launcher. The audit runs `unlighthouse@0.13.5` with the checkout's browser egress guard. It may download the package on first use.

## Verify

```
$seo unlighthouse https://example.com --max-routes 5
```

## When to use Unlighthouse vs. PageSpeed Insights

| Use Unlighthouse | Use PSI |
|---|---|
| Site has 100s of pages and you want every one audited | Single-URL focused audit |
| Offline / restricted environment | Field data from real Chrome users (CrUX) |
| CI-driven regression check post-deploy | Quick CLI/web-form check |
| Free / no quota concern | PSI quota OK for small sites |

PSI uses CrUX field data when available (real users); Unlighthouse
runs Lighthouse lab tests locally. For trustworthy CWV measurement
on production traffic, prefer PSI / CrUX.

## Uninstall

Run `./extensions/unlighthouse/uninstall.sh` to remove the checkout skill entry.
