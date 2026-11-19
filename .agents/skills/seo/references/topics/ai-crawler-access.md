# AI crawler access by purpose

Inspect actual `robots.txt` user-agent groups, longest matching path rules and sampled URLs. A robots directive is an observable instruction to cooperative crawlers. It does not establish what the crawler did, whether an invocation succeeds, or whether a page appears in generated answers.

| Published user-agent label | Purpose | robots.txt behavior to verify |
|---|---|---|
| GPTBot | OpenAI model training; not ChatGPT Search | Honors published rules |
| OAI-SearchBot | ChatGPT Search discovery and citability | Honors published rules |
| ChatGPT-User | User-initiated browsing and actions | OpenAI says robots.txt "may not apply" |
| ClaudeBot | Anthropic model training; not Claude search citability | Honors published rules |
| Claude-SearchBot | Claude search-result discovery and citability | Honors published rules |
| Claude-User | User-initiated fetches | Anthropic documents that it honors robots.txt |
| PerplexityBot | Perplexity search index; not foundation-model training | Honors published rules |
| Perplexity-User | Fetch for a user's question | Generally ignores robots.txt; verify current vendor guidance |
| Googlebot | Google Search crawling and indexing | Honors published rules; also supports Search AI features |
| Google-Extended | Control token for Gemini/Vertex training and grounding, and training of Search gen-AI models; not a crawler | Honors published rules; does not control Search inclusion or ranking |
| Google-Agent, Google-GeminiNotebook, Google Messages | User-triggered fetches | Generally cannot be blocked with robots.txt; use server-side access controls |
| Applebot | Apple crawling for Siri, Spotlight and Safari search surfaces | Honors published rules |
| Applebot-Extended | Apple Intelligence training opt-out label for content fetched by Applebot; not a crawler | Honors published rules; does not control Apple search surfaces |
| CCBot | Common Crawl dataset | Honors published rules |

In particular, do not treat `GPTBot` as evidence of ChatGPT Search visibility, `ClaudeBot` as evidence of Claude search visibility, `Google-Extended` as a Google Search control, or `Applebot-Extended` as the crawler for Apple search. Check the current [OpenAI crawler guidance](https://platform.openai.com/docs/bots), [Anthropic crawler guidance](https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Google crawler guidance](https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers) and [Applebot guidance](https://support.apple.com/en-us/119829) before making vendor-specific recommendations. Keep access rules, actual requests and citation visibility separate.
