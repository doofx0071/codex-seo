# Technical SEO

- Crawlability and indexability. Sample robots.txt rules by the relevant user agent and path, then compare sitemap inclusion, response code, redirects, robots meta or response headers, canonical targets, and internal discovery. Report a declaration as observed and indexed status only when separately evidenced.
- Site structure. Look for duplicate parameter paths, loops, broken internal links and inconsistent preferred hosts. Check the reasoning against the actual final URL. Mark sitewide prevalence and unsampled pages as unavailable.
- Rendering and mobile. Compare source with a rendered view for primary text, links, metadata, and structured data. Inspect the tested viewport and state if layout, input, or screenshot checks were unavailable.
- Delivery. Observe HTTPS and returned headers if exposed. Review image payload, resource priority, and script hints as potential contributors. Use [Core Web Vitals measurement guidance](../topics/cwv-thresholds.md) for measured performance.
- AI access and structured data. Use [crawler-purpose guidance](../topics/ai-crawler-access.md) before attributing effects to a rule. Use [schema](seo-schema.md) for linked entity checks and [sitemap](seo-sitemap.md) for URL scope.
