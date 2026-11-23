# Integration boundaries

This skill contains no remote credentials or provider clients. It uses tools exposed by the current host. Connecting accounts, signing up for services, or installing local software are separate user-controlled actions.

- Check actual tool availability at run time. Do not infer access from documentation or another environment.
- Analytics products for owned accounts are not general-purpose scrapers for arbitrary posts or comments.
- A local command-line tool is not accessible merely because this skill is loaded in a hosted assistant.
- Inspect a tool's help and documented capabilities before use. Use only configured, permitted channels; prefer public sources that require no login.
- Never run an upstream installer, enable optional channels, or copy browser sessions without a separate explicit approval and security review. Pin and inspect source/version before any approved installation.
- Hosted connectors are separate account connections and can be unavailable even when their documentation is public.
- For every optional provider, confirm the exact input contract, output fields, cost, retention, and terms before execution. A local bridge can still invoke remote services.
- Avoid hosted transcription and unauthorized media downloads. Use transcripts, frames, and OCR only when obtained from permitted media.
