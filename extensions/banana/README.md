# Banana extension for Codex SEO

Generate SEO image assets with the Gemini-backed Banana integration.

Follow the [setup guide](docs/BANANA-SETUP.md) to register the checkout skill, configure Codex access, and check prerequisites. Use the extension skill guide for supported prompts, provider behavior, and cost details.

## Commands

| Command | What it does |
|---------|-------------|
| `$seo image-gen og <description>` | OG/social preview image (1200x630 feel) |
| `$seo image-gen hero <description>` | Blog hero image (widescreen, dramatic) |
| `$seo image-gen product <description>` | Product photography (clean, white BG) |
| `$seo image-gen infographic <description>` | Infographic visual (vertical, data-heavy) |
| `$seo image-gen custom <description>` | Custom with full Creative Director pipeline |
| `$seo image-gen batch <description> [N]` | Generate N variations (default: 3) |

CSV batch planning helper:
```bash
./scripts/codex-seo run --extension banana batch.py --csv requests.csv --model "$NANOBANANA_MODEL"
```
