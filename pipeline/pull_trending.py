#!/usr/bin/env python3
"""Pull currently-trending YouTube videos (News & Politics) to inform sourcing.

Complementary to pull_youtube_stats.py, not a duplicate of it:
  - pull_youtube_stats.py -> how OUR OWN posted clips are performing
  - pull_trending.py (this file) -> what's trending on YouTube RIGHT NOW,
    independent of anything we've posted, to inform what to source next

Uses the same read-only YouTube Data API v3 key as pull_youtube_stats.py
(credentials/yt_data_api_key.txt) via videos.list?chart=mostPopular — a
public, read-only, OAuth-free endpoint (a plain API key is sufficient).

Usage: python3 pull_trending.py [--region US] [--category 25]
Run once daily (see the paired Hermes cron job) — zero LLM cost, pure API
pull, same "no-agent" pattern as pull_youtube_stats.py.

Category 25 = News & Politics (YouTube's fixed videoCategoryId), matches
this channel's niche. Full category list:
https://developers.google.com/youtube/v3/docs/videoCategories/list
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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "trending-latest.md")
API_URL = "https://www.googleapis.com/youtube/v3/videos"

DEFAULT_REGION = "US"
DEFAULT_CATEGORY = "25"  # News & Politics


def load_api_key() -> str:
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: {KEY_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    with open(KEY_FILE) as f:
        return f.read().strip()


def fetch_trending(api_key: str, region: str, category: str, max_results: int = 25) -> list:
    """Fetch up to max_results currently-trending videos for region+category.

    chart=mostPopular is YouTube's real, current trending endpoint (the old
    standalone /trending page is gone, but this API parameter is not
    deprecated — it's how YouTube's own trending page is built).
    """
    params = urllib.parse.urlencode({
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "videoCategoryId": category,
        "maxResults": max_results,
        "key": api_key,
    })
    url = f"{API_URL}?{params}"
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


def write_report(items: list, region: str, category: str) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)

    lines = [
        f"# YouTube Trending — {now.strftime('%Y-%m-%d %H:%M')} UTC",
        "",
        f"**Region:** {region}  **Category:** {category} (News & Politics)  "
        f"**Videos:** {len(items)}",
        f"**Generated:** {now.isoformat()}",
        "",
        "Auto-pulled daily via pull_trending.py (zero LLM cost, read-only "
        "YouTube Data API v3). This is what's trending RIGHT NOW on "
        "YouTube's own charts — a sourcing SIGNAL, not a source list. A "
        "topic trending here doesn't mean clip it verbatim; it means this "
        "is what audiences are currently paying attention to, which is "
        "useful context when weighing candidates against each other.",
        "",
        "---",
        "",
    ]

    if not items:
        lines.append("_No trending videos returned for this region/category._")
    else:
        for i, item in enumerate(items, 1):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            title = snippet.get("title", "?")
            channel = snippet.get("channelTitle", "?")
            published = snippet.get("publishedAt", "?")
            views = stats.get("viewCount", "?")
            video_id = item.get("id", "?")
            lines.append(f"### #{i} — {title}")
            lines.append(f"- **Channel:** {channel}")
            lines.append(f"- **Published:** {published}")
            lines.append(f"- **Views:** {views}")
            lines.append(f"- **URL:** https://www.youtube.com/watch?v={video_id}")
            lines.append("")

    tmp = OUTPUT_FILE + f".tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        f.write("\n".join(lines))
    os.replace(tmp, OUTPUT_FILE)  # atomic — a reader never sees a half-written file


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", default=DEFAULT_REGION, help=f"Region code (default {DEFAULT_REGION})")
    ap.add_argument("--category", default=DEFAULT_CATEGORY, help=f"Video category ID (default {DEFAULT_CATEGORY} = News & Politics)")
    ap.add_argument("--max-results", type=int, default=25, help="Max videos to fetch (default 25, API cap 50)")
    args = ap.parse_args()

    api_key = load_api_key()
    print(f"Fetching trending videos (region={args.region}, category={args.category})...")
    items = fetch_trending(api_key, args.region, args.category, args.max_results)
    print(f"Got {len(items)} trending videos.")

    write_report(items, args.region, args.category)
    print(f"Wrote {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
