# Provider selection and capability boundaries

Check tools connected to the **current** runtime before use. Advertised support is not proof of availability.

| Provider type | Best use | Access and limitations | Cost/security rule |
| --- | --- | --- | --- |
| Built-in web search and official APIs | Public posts, platform data, primary sources, discovery | May return metadata without full comments or transcripts; APIs have terms and scopes | Prefer existing free access; do not create credentials by default |
| Public-page extraction service | Reading public pages and targeted extracts | Social sites may block automated access; some pages require login | Check credits before use; no bulk crawl by default |
| Local research command-line tools | Captions, public discussion search, and local channels | Capabilities vary; optional channels may require a session; local tools are unavailable in hosted runtimes | No automatic installation, update, login, or browser-session copying |
| Hosted data collection service | Bounded public comment, page, or result retrieval | Third-party runtime, permissions, retention, and billing vary | Check the exact action cost and remaining allowance; no overage or upgrade |
| Structured social-data API | Public posts, transcripts, comments, and trends | Requires an API key; does not authorize private account access | Use only with explicit finite budget approval |
| Video analysis tool | Actual frames, OCR, and transcription of authorized media | Downloadability, licensing, dependencies, and retention vary | Review local security and network behavior; no cloud transcription by default |
| Owned-account analytics connector | Performance data for accounts the user controls | Not a general-purpose scraper for arbitrary posts or competitors | Respect account scope; analytics do not establish what a video showed |

## Routing order

1. Use public, official, or connected data already available in this session.
2. Use already-installed local tools for supported, login-free sources.
3. Use specialized services only when the task needs missing evidence and authorization, terms, and cost are verified.
4. If no safe route is available, return `METADATA_ONLY` or `ACCESS_BLOCKED`, with the source URL, reason, and safe alternative. Never infer content that was not retrieved.

## Provider checks

Before using any specialized tool, inspect its current help and documentation, exact input and output contract, permissions, cost, data retention, and terms. Never run an unreviewed installer or shell script. A local bridge may still invoke a hosted service.
