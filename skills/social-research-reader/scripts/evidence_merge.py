#!/usr/bin/env python3
"""Social Research Reader: merge already-collected social evidence. Offline; no network or auth.

Usage:
  python evidence_merge.py --input export.json [--input export.jsonl] \
      --output evidence.json --brief brief.md

Accepts JSON list, one record/object with `items`, or JSONL with one record per line.
Only short summaries and source links are retained. Provider exports must be
reviewed for privacy/terms before this script is used.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

STATUSES = {"CONTENT_READ", "PARTIAL", "METADATA_ONLY", "ACCESS_BLOCKED"}
RETRIEVAL_ALIASES = {"CONTENT_VERIFIED": "CONTENT_READ"}  # Backward-compatible input only
CLAIMS = {"Verified", "Partially Verified", "Unverified", "Disputed"}
# Legacy input fields are accepted for old exports; these mappings
# preserve the *reported* classification, NOT independent factual validation.
LEGACY_CLAIMS = {
    "CONFIRMED_PRIMARY": "Verified",
    "CORROBORATED_SECONDARY": "Partially Verified",
    "UNVERIFIED_SOCIAL": "Unverified",
    "DISPROVEN": "Disputed",
    "NOT_ASSESSED": "Unverified",
}
STATUS_RANK = {"ACCESS_BLOCKED": 0, "METADATA_ONLY": 1, "PARTIAL": 2, "CONTENT_READ": 3}
SAFE_QUERY_KEYS = {"v", "list", "id", "story_fbid", "fbid", "comment"}
SENSITIVE_KEYS = {"token", "access_token", "api_key", "apikey", "key", "password", "secret", "session", "auth", "signature", "sig"}


def canonical_url(raw: str) -> str:
    """Deduplicate known equivalent public social URLs, without fetching them.

    Unrecognized URL paths are retained conservatively: never merge distinct
    posts just because their URLs look similar. Do not use this as an SSRF
    safety check for downloading content; the merge tool makes no requests.
    """
    if not isinstance(raw, str):
        raise ValueError("A record needs an original public/authorized URL")
    parts = urlsplit(raw.strip())
    if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("A record URL must be public-looking HTTP(S) without embedded credentials")
    host = parts.hostname.lower().rstrip(".")
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or host.endswith((".local", ".internal", ".localhost", ".test")):
        raise ValueError("Local/private URLs are not research evidence sources")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise ValueError("Private or reserved IP is not a public research URL")
    if not re.fullmatch(r"[a-z0-9.:-]+", host):
        raise ValueError("Invalid source hostname")
    if parts.port and parts.port not in {80, 443}:
        raise ValueError("Unexpected source URL port")
    query_parts = parse_qsl(parts.query, keep_blank_values=True)
    if any(k.lower() in SENSITIVE_KEYS for k, _ in query_parts):
        raise ValueError("Possible secret-bearing URL parameter; remove it first")

    # Strip common presentation subdomains; do not strip arbitrary prefixes.
    if host.startswith("www."):
        host = host[4:]
    if host in {"m.youtube.com", "music.youtube.com", "youtube-nocookie.com"}:
        host = "youtube.com"
    if host in {"m.reddit.com", "old.reddit.com", "new.reddit.com", "np.reddit.com"}:
        host = "reddit.com"
    if host in {"twitter.com", "mobile.twitter.com", "m.twitter.com", "mobile.x.com", "m.x.com"}:
        host = "x.com"
    if host == "m.instagram.com":
        host = "instagram.com"
    if host in {"m.facebook.com", "mobile.facebook.com"}:
        host = "facebook.com"

    path = parts.path.rstrip("/") or "/"
    query_values = dict(query_parts)
    video_id = None
    if host == "youtu.be":
        candidate = path.lstrip("/").split("/")[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{3,64}", candidate):
            video_id = candidate
        host = "youtube.com"
    elif host == "youtube.com":
        segments = path.strip("/").split("/")
        if path.lower() == "/watch":
            video_id = query_values.get("v")
        elif len(segments) >= 2 and segments[0].lower() in {"shorts", "live", "embed", "v"}:
            # /embed/videoseries?list=... is a playlist, not a video ID.
            if not (segments[0].lower() == "embed" and segments[1].lower() == "videoseries"):
                video_id = segments[1]
    if video_id and re.fullmatch(r"[A-Za-z0-9_-]{3,64}", video_id):
        return urlunsplit(("https", "youtube.com", "/watch", urlencode({"v": video_id}), ""))

    # Reddit links: a post and each comment are distinct evidence items.
    # Ignore mutable title slugs, but preserve the comment ID when present.
    if host == "reddit.com":
        for pattern, prefix in (
            (r"/r/([^/]+)/comments/([a-z0-9]+)(?:/([^/]+))?(?:/([a-z0-9_]+))?", "/r/"),
            (r"/comments/([a-z0-9]+)(?:/([^/]+))?(?:/([a-z0-9_]+))?", "/comments/"),
        ):
            match = re.fullmatch(pattern, path, re.I)
            if not match:
                continue
            if prefix == "/r/":
                sub, post_id, _, comment_id = match.groups()
                path = f"/r/{sub.lower()}/comments/{post_id.lower()}"
            else:
                post_id, _, comment_id = match.groups()
                path = f"/comments/{post_id.lower()}"
            # Reddit also uses ?comment=<id> on post URLs.
            comment_id = comment_id or query_values.get("comment")
            if comment_id and re.fullmatch(r"(?:t1_)?[a-z0-9]+", comment_id, re.I):
                path += "/_/" + comment_id.lower().removeprefix("t1_")
            query_parts = [(k, v) for k, v in query_parts if k.lower() != "comment"]
            break

    # IG /p/{shortcode}, /reel/{shortcode}, and /{username}/reel/{shortcode}
    # refer to the same media ID. Preserve unknown IG paths unchanged.
    if host == "instagram.com":
        match = re.fullmatch(r"/(?:[^/]+/)?(reel|p|tv)/([A-Za-z0-9_-]+)(?:/.*)?", path, re.I)
        if match:
            path = "/p/" + match.group(2)

    # X/Twitter status IDs are globally unique even if the handle changes.
    if host == "x.com":
        match = re.fullmatch(r"/(?:[^/]+/status|i/web/status)/([0-9]+)(?:/.*)?", path, re.I)
        if match:
            path = "/i/web/status/" + match.group(1)

    query = urlencode(sorted((k, v) for k, v in query_parts if k.lower() in SAFE_QUERY_KEYS))
    return urlunsplit(("https", host, path, query, ""))


def short_text(value, maximum: int) -> str:
    if not isinstance(value, str):
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    return text[:maximum]


def normalize_record(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Each record must be a JSON object")
    missing = [x for x in ("url", "platform", "provider", "status") if not data.get(x)]
    if missing:
        raise ValueError("Missing required field(s): " + ", ".join(missing))
    status = RETRIEVAL_ALIASES.get(str(data["status"]).upper(), str(data["status"]).upper())
    if status not in STATUSES:
        raise ValueError(f"Unknown retrieval status: {status}")
    input_claim = str(data.get("claim_status", "Unverified")).strip()
    claim = LEGACY_CLAIMS.get(input_claim.upper(), input_claim)
    if claim not in CLAIMS:
        raise ValueError(f"Unknown reported factual claim status: {claim}")
    declared_lead_only = data.get("lead_only", True)
    if not isinstance(declared_lead_only, bool):
        raise ValueError("lead_only must be a boolean")
    lead_only = declared_lead_only or claim in {"Unverified", "Disputed"}
    if input_claim.upper() in LEGACY_CLAIMS:
        lead_only = True  # Old labels have not undergone current verification.
    layers = data.get("layers") or {}
    if not isinstance(layers, dict):
        raise ValueError("layers must be a mapping")
    cleaned_layers = {}
    for layer, value in layers.items():
        if layer not in ("metadata", "transcript", "visuals", "comments"):
            raise ValueError(f"Unknown layer: {layer}")
        normalized = RETRIEVAL_ALIASES.get(str(value).upper(), str(value).upper())
        if normalized not in STATUSES:
            raise ValueError(f"Unknown layer status for {layer}: {normalized}")
        cleaned_layers[layer] = normalized
    return {
        "url": canonical_url(data["url"]),
        "platform": re.sub(r"[^a-z0-9_-]", "", short_text(str(data["platform"]).lower(), 40)) or "unknown",
        "providers": [short_text(str(data["provider"]), 70)],
        "published_at": short_text(data.get("published_at"), 48),
        "retrieved_at": short_text(data.get("retrieved_at"), 48),
        "title": short_text(data.get("title"), 160),
        "summary": short_text(data.get("summary"), 420),
        "status": status,
        "claim_status": claim,
        "lead_only": lead_only,
        "layers": cleaned_layers,
    }


def parse_source(path: Path) -> list:
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in content.splitlines() if line.strip()]
    obj = json.loads(content)
    if isinstance(obj, dict) and isinstance(obj.get("items"), list):
        return obj["items"]
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        return [obj]
    raise ValueError(f"Expected JSON records in {path}")


def merge_records(items: list) -> list[dict]:
    by_url = {}
    for raw in items:
        record = normalize_record(raw)
        url = record["url"]
        if url not in by_url:
            by_url[url] = record
            continue
        current = by_url[url]
        existing_providers = current["providers"]
        for provider in record["providers"]:
            if provider not in existing_providers:
                existing_providers.append(provider)
        new_is_better = STATUS_RANK[record["status"]] > STATUS_RANK[current["status"]]
        if new_is_better:
            for field in ("title", "summary", "status", "published_at", "retrieved_at"):
                if record.get(field):
                    current[field] = record[field]
        else:
            for field in ("title", "summary", "published_at", "retrieved_at"):
                if not current[field] and record.get(field):
                    current[field] = record[field]
        # Preserve explicit claim statuses only when reports do not conflict.
        # A better extraction status alone does not justify a better truth claim.
        if record["claim_status"] != current["claim_status"]:
            current["claim_status"] = "Unverified"
            current["lead_only"] = True
        else:
            # Multiple provider reports never independently verify a claim.
            current["lead_only"] = current["lead_only"] or record["lead_only"]
        # Preserve the strongest actually-observed status per layer, but do not
        # automatically upgrade factual truth from sources' unsupported labels.
        for key, layer_status in record["layers"].items():
            prev = current["layers"].get(key)
            if prev is None or STATUS_RANK[layer_status] > STATUS_RANK[prev]:
                current["layers"][key] = layer_status
    for v in by_url.values():
        v["providers"].sort()
    return sorted(by_url.values(), key=lambda item: (item["platform"], item["url"]))


def build_brief(records: list[dict]) -> str:
    counts = Counter(r["status"] for r in records)
    platforms = sorted({r["platform"] for r in records})
    lines = ["# AW Reach - offline evidence inventory", "",
             f"Items: {len(records)}; platforms: {', '.join(platforms) or 'none'}", "",
             "Extraction status: " + ", ".join(f"{s}={counts[s]}" for s in sorted(STATUSES)), "",
             "This inventory summarizes what was retrieved, not whether claims are true.", "",
             "| Source | Platform | Extraction | Reported verification state | Lead only | Available layers |",
             "| --- | --- | --- | --- | --- | --- |"]
    for row in records:
        layers = ", ".join(f"{k}:{v}" for k, v in sorted(row["layers"].items())) or "not recorded"
        url = row["url"].replace("|", "%7C")
        lines.append(f"| [Link]({url}) | {row['platform']} | {row['status']} | {row['claim_status']} | {str(row['lead_only']).lower()} | {layers} |")
    lines.extend(["", "Unverified sources need independent checks before publication or financial/product claims.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, required=True, help="JSON/JSONL research export; repeat to merge")
    parser.add_argument("--output", type=Path, required=True, help="Normalized JSON file")
    parser.add_argument("--brief", type=Path, help="Optional Markdown inventory")
    args = parser.parse_args()
    source_records = []
    for path in args.input:
        source_records.extend(parse_source(path))
    records = merge_records(source_records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"items": records, "count": len(records)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.brief:
        args.brief.parent.mkdir(parents=True, exist_ok=True)
        args.brief.write_text(build_brief(records), encoding="utf-8")
    print(f"Validated {len(source_records)} records; normalized {len(records)} unique social items; network calls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
