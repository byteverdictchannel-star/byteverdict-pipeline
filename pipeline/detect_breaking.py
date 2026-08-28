#!/usr/bin/env python3
"""Detect currently-live breaking-news broadcasts on YouTube.

This is a DETECTION layer, not a capture layer — it never records or
downloads a live stream. It only tells the Content Agent "something is
breaking right now, on this channel, since this time" so sourcing searches
can be pointed at it faster. The actual clip still gets sourced the normal
way, from the outlet's own published VOD/upload once one exists — same
attribution, same Tier 1/2 vetting, same sensitive-content screen as every
other candidate. Recording a live broadcast directly was considered and
rejected: an unpublished live feed has had zero editorial/legal review by
anyone, including us, and that's a materially worse copyright posture than
clipping something the outlet already chose to publish. See conversation
2026-08-28 for the full reasoning.

Uses search.list?eventType=live, the YouTube Data API v3's live-broadcast
finder. Costs 100 quota units per call (vs 1 unit for videos.list) — a
10,000/day default quota affords roughly 96 calls/day with headroom left
for the cheap stats/trending pulls, so this runs every 30 minutes (48
calls/day), not more often.

Usage: python3 detect_breaking.py [--max-results 10]
Run every 30 min via the paired Hermes cron job — zero LLM cost.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "credentials")
KEY_FILE = os.path.join(CREDENTIALS_DIR, "yt_data_api_key.txt")
OUTPUT_DIR = os.path.join(
    os.path.dirname(SCRIPT_DIR), "test-batch", "discovery-outputs"
)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "breaking-alerts-latest.md")
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Broad query rather than a per-channel allowlist — per-channel search.list
# calls also cost 100 units EACH, so one broad query stays within quota
# while still surfacing whichever major outlet has something live right now.
QUERY = "breaking news"


def load_api_key() -> str:
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: {KEY_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    with open(KEY_FILE) as f:
        return f.read().strip()


def fetch_live(api_key: str, max_results: int = 10) -> list:
    params = urllib.parse.urlencode({
        "part": "snippet",
        "q": QUERY,
        "type": "video",
        "eventType": "live",
        "order": "relevance",
        "maxResults": max_results,
        "key": api_key,
    })
    url = f"{SEARCH_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"ERROR: request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in data:
        print(f"API ERROR: {data['error'].get('message')}", file=sys.stderr)
        sys.exit(1)

    return data.get("items", [])


def write_report(items: list) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)

    lines = [
        f"# Breaking News — Live Right Now — {now.strftime('%Y-%m-%d %H:%M')} UTC",
        "",
        f"**Live broadcasts found:** {len(items)}",
        f"**Generated:** {now.isoformat()}",
        "",
        "Auto-pulled every 30 min via detect_breaking.py (zero LLM cost, "
        "read-only YouTube Data API v3, search.list eventType=live). This "
        "is a DETECTION signal only — nothing here has been captured, "
        "downloaded, or vetted. It exists so sourcing can notice an "
        "unfolding story fast; the actual candidate still has to be found "
        "as a published VOD/upload from the outlet later, and goes through "
        "the normal Tier 1/2 + sensitive-content screen like everything "
        "else. Do not treat a listing here as a sourced candidate on its "
        "own.",
        "",
        "---",
        "",
    ]

    if not items:
        lines.append("_No live breaking-news broadcasts found this pull._")
    else:
        for i, item in enumerate(items, 1):
            snippet = item.get("snippet", {})
            title = snippet.get("title", "?")
            channel = snippet.get("channelTitle", "?")
            published = snippet.get("publishedAt", "?")
            video_id = item.get("id", {}).get("videoId", "?")
            lines.append(f"### #{i} — {title}")
            lines.append(f"- **Channel:** {channel}")
            lines.append(f"- **Live since:** {published}")
            lines.append(f"- **URL:** https://www.youtube.com/watch?v={video_id}")
            lines.append("")

    tmp = OUTPUT_FILE + f".tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        f.write("\n".join(lines))
    os.replace(tmp, OUTPUT_FILE)  # atomic — a reader never sees a half-written file


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-results", type=int, default=10, help="Max live broadcasts to fetch (default 10, API cap 50)")
    args = ap.parse_args()

    api_key = load_api_key()
    print("Checking for live breaking-news broadcasts...")
    items = fetch_live(api_key, args.max_results)
    print(f"Found {len(items)} live right now.")

    write_report(items)
    print(f"Wrote {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
