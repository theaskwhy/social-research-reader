# Evidence and offline merge format

Keep **retrieval confidence** separate from the **truth of content claims**. `CONTENT_READ` means the requested content layer was actually read, NOT that its factual assertions are verified. A claim's `claim_status` is a *reported* classification, not certified by the offline merge script. AW Reach uses `Verified`, `Partially Verified`, `Unverified`, `Disputed` from the claim-verification workflow and a separate `lead_only` flag. Social-only reports default to `Unverified` + `lead_only=true`. Historical `CONTENT_VERIFIED` inputs map to `CONTENT_READ`; old `CONFIRMED_PRIMARY`/`CORROBORATED_SECONDARY`/`UNVERIFIED_SOCIAL`/`DISPROVEN`/`NOT_ASSESSED` map to the four standard labels, with `lead_only=true`, never as newly verified findings.

## Four content layers

- `metadata`: original post URL, author/creator if relevant and public, caption/title, published timestamp, platform and public engagement if supported.
- `transcript`: speech/captions, transcript origin (creator subtitles, platform captions or ASR) and approximate timing when available.
- `visuals`: real viewed frames, OCR or video observations; note frame sampling limitations.
- `comments`: actual text/replies and sample size with original post context.

For each layer set one of `CONTENT_READ`, `PARTIAL`, `METADATA_ONLY`, `ACCESS_BLOCKED` as warranted. Unrequested layers may be omitted. A missing layer cannot be inferred from another.

## Normalized JSON record

Pass an array of records or JSONL to `scripts/evidence_merge.py` when deterministic deduplication is needed. Each record is one source item. For Reddit comment mining, **each comment must have its own permalink or comment ID in its source URL**; a shared thread URL is not sufficient to distinguish comments. If only a thread URL is available, represent the thread as one aggregated record and preserve the separate comments in approved source evidence rather than pretending they are individual deduplicated records. Minimal example (no private identifiers):

```json
[
  {
    "url": "https://www.reddit.com/r/sample/comments/example/a_discussion/",
    "platform": "reddit",
    "provider": "public_web",
    "published_at": "2026-11-08T14:00:00-06:00",
    "retrieved_at": "2026-11-08T16:00:00-06:00",
    "title": "Discussion of a public announcement",
    "status": "PARTIAL",
    "layers": {"metadata": "CONTENT_READ", "comments": "PARTIAL"},
    "summary": "A small sample discusses a reported change, without primary confirmation",
    "claim_status": "Unverified",
    "lead_only": true
  }
]
```

Output statuses: `CONTENT_READ`, `PARTIAL`, `METADATA_ONLY`, `ACCESS_BLOCKED`. Reported claim statuses (from the claim-verification workflow): `Verified`, `Partially Verified`, `Unverified`, `Disputed`; `lead_only` is a separate boolean flag. Historical v1 claim labels are only migrated as reported labels and remain `lead_only=true`, not independently accepted evidence.

Required for a source record: public/authorized original `url`, `platform`, `provider`, `status`. All other fields optional and should remain unknown if not observed. The offline script never logs in or scrapes; it validates, deduplicates equivalent YouTube, Reddit, X/Twitter, Instagram and www-host URL forms **without collapsing different Reddit comments into the parent thread**, and emits a small JSON and Markdown summary. Preserve the original provider exports separately when needed for audits; don't assume the merge tool can recover dropped raw fields.

## Output brief

1. Scope and source platforms, date range, number actually read and access gaps.
2. Key findings with direct per-finding source links and precise observed fields.
3. Where video is involved, what was seen (`metadata`, `transcript`, `visuals`, `comments`), not just 'watched'.
4. Contradictory examples and sampling limits.
5. Follow-up evidence or editorial gates, with `NOT_RUN` for absent checks.

Avoid broad profiling or aggregating sensitive personal information. Do not include credentials, cookies or long copyrighted excerpts.
