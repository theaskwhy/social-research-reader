# AW Reach research recipes

Use the smallest recipe that covers the user's outcome. These recipes are process guidance, not implementations of any provider API.

## 1. News leads (use the latest 48 hours when unspecified)

- Search current official and first-party sources, then selected Reddit/X/YouTube public conversations for leads.
- Capture exact links, posted timestamps, aircraft/program identifiers, original speaker, claim and corroborating source status.
- Use claim verification's `Verified`, `Partially Verified`, `Unverified` and `Disputed`, plus independent `lead_only`, for factual claims; distinguish this from **retrieval status** (`CONTENT_READ`, etc.). A social video can be fully read while its claim remains unverified.
- Deduplicate reshared rumors and media reuse. Do not translate 'lots of views' into truth.
- Return: **Lead | original URL | post/event dates | verification status | missing evidence | next check**.
- Use `claim-verification` and the appropriate editorial and rights-review steps for later editorial and rights verification. No automatic drafting, importing or publication just because a lead is interesting.

## 2. Comment mining and voice of customer

- Define posts, platforms, target community and sampling rule; collect bounded comment/reply sets where allowed.
- Retain thread context and parent comment, if provided. Remove obvious spam and duplicates without rewriting authentic language.
- Categorize questions, frustrations, objections, praise, confusion, feature ideas, buying-intent signals and jokes/memes.
- Show **theme | sample count | representative short quote | source URL | counterexamples | confidence**.
- Preserve useful original language but avoid exposing unneeded handles/PII, copying full threads or treating self-selected comments as a representative poll.
- Next actions may be FAQs, content ideas, feature hypotheses or tests, **not** a claim of proven market demand.

## 3. Cross-platform social listening

- Define aliases, search terms and time window. Search 2-3 relevant platforms rather than all platforms blindly.
- Cluster topics and tone; distinguish actual comment content from titles/metadata-only hits.
- Summarize each platform separately before cross-platform synthesis; platform audiences and moderation differ.
- Return: **top themes, sources by platform, notable examples, confidence/sampling limitations and recommended investigation**. Say how many items were actually read; don't claim exhaustive monitoring.

## 4. Video transcript and visual content

- Read post metadata and caption first. Retrieve native transcript/captions only if actually available. Label ASR vs source captions and uncertainty.
- For visual assertions, verify actual frames/OCR or a genuine video-observation tool was used. A transcript or model-generated video description cannot prove on-screen details.
- Extract opening hook, claim, supporting illustration, CTA, repeated formats, editing patterns only from the corresponding available evidence layers.
- Return **video URL | metadata | spoken claim | on-screen claim | viewer comments | missing layers**. Use timestamps when supported, otherwise omit.

## 5. Competitor research and content angles

- Choose relevant creators and time window; compare each creator against their own recent baseline rather than raw views alone.
- Record actual public view/engagement counts, dates, post formats, subject and evidence URL. Never fabricate growth, audience demographics or revenue.
- Output repeatable content patterns, promising but unproven hypotheses, and low-cost tests. Separate observation from interpretation.

## 6. Qualitative product-demand signals

- Search pain phrases, alternatives, workarounds, user questions, complaints and reported purchase intent from Reddit and public videos.
- Score themes with transparent count, recency and diversity of sources; expose contradictions and counterexamples.
- Label **directional qualitative evidence**. Do not turn sample size or commenter sentiment into TAM, conversion rate or financial recommendation.

## 7. Provider comparison (only with access already authorized)

Apply the same three sample requests: one public Instagram Reel's comments, one public Reddit thread's comments, one public YouTube video's transcript. For each provider record: account/login required; data layers actually returned; count; cost/credits consumed; terms/rate-limit issues; retries; observed runtime. Stop when the $0 cap or authorization is reached. Do not create accounts on behalf of the user or use browser cookies to complete a comparison.
