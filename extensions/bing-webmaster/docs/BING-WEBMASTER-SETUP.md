# Bing Webmaster Tools + IndexNow extension setup

## What this gives you

1. **Bing Webmaster Tools API**: inbound links, crawl stats, search
   keywords, and competitor link comparison via
   `./scripts/codex-seo run bing_webmaster.py` (already shipped with codex-seo).
2. **IndexNow URL submission** for Amazon, Bing, Naver, Seznam.cz,
   Yandex, and Yep via `./scripts/codex-seo run indexnow_submit.py`.
3. A unified `seo-bing` skill that routes the right command at the
   right script.

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/bing-webmaster/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\bing-webmaster\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Set `BING_WEBMASTER_API_KEY` in the local runtime environment for Bing queries. For IndexNow, use `INDEXNOW_KEY` and `INDEXNOW_KEY_LOCATION` for the host you administer. Each service can be configured independently. Keep the values out of the repository and shell history.

## IndexNow setup checklist

1. Generate a key: `openssl rand -hex 32`
2. Save the key to a file at the **root** of your site, named `<key>.txt`,
   served at `https://example.com/<key>.txt`. The file body is the key.
3. Run:
   ```
   $seo bing verify-indexnow
   ```
   The verifier fetches your keyLocation URL and confirms the body
   matches the key, the #1 onboarding mistake.

## Microsoft Copilot citation

Microsoft Copilot pulls citations from the Bing index. Pages that
aren't in Bing aren't citable. IndexNow notifies participating
engines about changed URLs and can speed discovery, but it does not
guarantee indexing speed.

## Uninstall

Run `./extensions/bing-webmaster/uninstall.sh` to remove the checkout skill entry. Remove `BING_WEBMASTER_API_KEY`, `INDEXNOW_KEY`, and `INDEXNOW_KEY_LOCATION` from the environment you configured.
