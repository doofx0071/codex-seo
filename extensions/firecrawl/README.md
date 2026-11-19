# Firecrawl extension for Codex SEO

Use Firecrawl for deeper page extraction, URL discovery, and bounded site crawls.

Follow the [setup guide](docs/FIRECRAWL-SETUP.md) to register the checkout skill, configure Codex access, and check prerequisites. Use the extension skill guide for supported prompts, provider behavior, and cost details.

## Commands

| Command | Purpose | Credits |
|---------|---------|---------|
| `$seo firecrawl crawl <url>` | Full-site crawl with content extraction | 1 per page |
| `$seo firecrawl map <url>` | Discover site structure (URLs only) | 0.5 per URL |
| `$seo firecrawl scrape <url>` | Single-page deep scrape with JS rendering | 1 |
| `$seo firecrawl search <query> <url>` | Search within a site | 1 per result |

## Cost

| Plan | Credits/month | Price |
|------|--------------|-------|
| Free | 500 | $0 |
| Hobby | 3,000 | $16/mo |
| Standard | 100,000 | $83/mo |
| Growth | 500,000 | $333/mo |

1 credit = 1 page crawled or scraped. Map operations use 0.5 credits per URL.
