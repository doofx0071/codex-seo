# Banana Extension Setup Guide

## Google AI API Key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API key"
4. Store the key securely for the environment that launches Codex

**Free tier limits:**
- Check current limits in Google AI Studio before batch work

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/banana/install.sh
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Install Node.js 20+ and set `GOOGLE_AI_API_KEY` from your Google AI account. Add this entry to your user `~/.codex/config.toml`. Set the named credentials in the environment that starts Codex. See [MCP and provider setup](../../../docs/MCP-INTEGRATION.md).

```toml
[mcp_servers.nanobanana-mcp]
command = "npx"
args = ["-y", "@ycse/nanobanana-mcp@1.1.1"]
env_vars = ["GOOGLE_AI_API_KEY", "NANOBANANA_MODEL"]
```

Verify registration with `codex mcp list`.

## Verifying Installation

```bash
./scripts/codex-seo run --extension banana validate_setup.py
```

Confirm `nanobanana-mcp` is connected in Codex. Both checks can run without generating images. Ask for an estimate before approving generation.

## Common Issues

### "MCP tools not available"
- Restart Codex after installing the extension
- Verify your API key is valid at [aistudio.google.com](https://aistudio.google.com)
- Check `codex mcp list` shows the nanobanana-mcp entry

### "Rate limited (429)"
- Check current free-tier limits in Google AI Studio
- Wait 60 seconds and retry
- For batch operations, add delays between requests

### "IMAGE_SAFETY" error
- The safety filter flagged your prompt (often a false positive)
- Codex will suggest rephrased alternatives automatically
- Common triggers: certain color descriptions, implied scenarios
- See `references/prompt-adaptation-safety.md` (Safety Filter Rephrase Strategies)

### "Node.js version too old"
- Requires Node.js 20+
- Update via nvm: `nvm install 20 && nvm use 20`
- Or download from [nodejs.org](https://nodejs.org/)

### Generated images not appearing
- Default output directory: `~/Documents/nanobanana_generated/`
- Check the path returned by Codex after generation
- Verify disk space is available

## ImageMagick (Optional)

For post-processing (WebP conversion, cropping, background removal):

```bash
# Ubuntu/Pop!_OS
sudo apt install imagemagick

# Verify
magick --version
```

If `magick` (v7) is not available, the scripts fall back to `convert` (v6).
