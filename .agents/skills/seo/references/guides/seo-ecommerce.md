# Ecommerce SEO

For a store-level review, follow relevant public internal links from the homepage, navigation, collections, and categories to find product pages. Check observed sitemap URLs for additional candidates and state the checked scope. A sitemap without product URLs does not establish that products do not exist or are not indexed.

Adapt the sample to the public evidence: with zero product pages found, report only that none were found in the checked scope and ask whether the store is prelaunch before recommending catalog changes; with one, review it in depth and do not generalize to other templates; with multiple, select a small sample across available types, variants, or categories and state its limits. Check publicly linked shipping, returns/refunds, privacy, terms, and contact details; report what was found, not found in scope, or unavailable.

Label page-source, response-header, and indexing findings as **observed**, **measured**, **inferred**, or **unavailable**, with the reason and evidence needed to verify unavailable items. Source or rendered content does not prove response headers or indexing. A raw HTTP response can verify headers, browser rendering can verify rendered behavior, and URL Inspection or a relevant Search Console export can verify indexing status. Do not infer product existence or indexation from sitemap membership or omission, HTML, or a search snippet.

For the selected product, collection, and category templates, compare titles and merchandising content, product variants, canonical strategy, faceted navigation, product images, internal links, indexability indicators, and breadcrumbs. Match Product or ProductGroup, Offer, and variant IDs to published page facts. Check price, currency, availability, seller, and review data against the visible page.

The checkout-only `ecommerce_page_check.py` can compare visible HTML evidence with Product/Offer JSON-LD without network access. It uses explicit microdata and a bounded text fallback for one visible Offer scope. Currency symbols alone are ambiguous, and source inspection cannot determine computed CSS or JavaScript-driven visibility; confirm those cases in a browser.

Review any user-provided merchant or marketplace export independently. Do not estimate rankings, sellers, visibility, or feed health from a product page. A publicly supplied commerce profile may be examined passively when relevant. Apply [product evidence checks](../topics/product-evidence.md).
