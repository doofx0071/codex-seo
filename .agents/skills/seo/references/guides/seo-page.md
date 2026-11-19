# Single-page SEO review

1. Identify the requested URL, final URL if observable, page type, likely audience, and purpose. Record whether evidence came from raw HTML, the rendered page, a result preview, or user-supplied source.
2. Check the title, description, main heading, useful subheadings, body depth, internal links, canonical, robots directives, language and alternates where applicable. Compare the page's actual purpose to the expected intent. Review [quality gates](../topics/quality-gates.md) as heuristics.
3. Inspect visible content and JSON-LD separately using [schema](seo-schema.md), then review primary images and likely loading issues with [images](seo-images.md). Check source against rendered output when both are available.
4. Return evidence and priority for each issue. Report response-level checks or browser data as unavailable when the host only exposes page text. A source-level concern can justify a measurement recommendation without a measured result.
