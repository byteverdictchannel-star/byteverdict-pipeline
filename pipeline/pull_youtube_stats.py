#!/usr/bin/env python3
"""Pull real YouTube view/like/comment stats for every posted clip and append
a timestamped ## Performance entry to each clip's posting-log.

Uses a read-only YouTube Data API v3 key (credentials/yt_data_api_key.txt) —
separate from the OAuth upload credentials in client_secrets.json/token.json.
This closes the feedback-loop gap: content-agent-prompt.md §2b reads these
Performance sections back in when planning future sourcing.

Usage: python3 pull_youtube_stats.py
Run periodically (see the paired Hermes cron job) — zero LLM cost, pure API pulls.
"""

import glob
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "credentials")
KEY_FILE = os.path.join(CREDENTIALS_DIR, "yt_data_api_key.txt")
CLIP_LOG_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "test-batch", "clip-log")

VIDEO_ID_RE = re.compile(r"Video ID:.{0,10}?([A-Za-z0-9_-]{11})")
API_URL = "https://www.googleapis.com/youtube/v3/videos"


def load_api_key() -> str:
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: {KEY_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    with open(KEY_FILE) as f:
        return f.read().strip()


def find_video_ids() -> dict:
    """Map video_id -> posting-log file path, scanning all posting-logs."""
    mapping = {}
    for path in glob.glob(os.path.join(CLIP_LOG_DIR, "*posting-log.md")):
        with open(path) as f:
            content = f.read()
        for match in VIDEO_ID_RE.finditer(content):
            mapping[match.group(1)] = path
    return mapping


def fetch_stats(video_ids: list, api_key: str) -> dict:
    """Batch-fetch stats for up to 50 video IDs at once (API limit)."""
    results = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        params = urllib.parse.urlencode({
            "part": "statistics,status",
            "id": ",".join(batch),
            "key": api_key,
        })
        url = f"{API_URL}?{params}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if "error" in data:
            print(f"API ERROR: {data['error'].get('message')}", file=sys.stderr)
            continue
        for item in data.get("items", []):
            results[item["id"]] = item["statistics"]
    return results


def append_performance(path: str, video_id: str, stats: dict) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    views = stats.get("viewCount", "?")
    likes = stats.get("likeCount", "?")
    comments = stats.get("commentCount", "?")
    entry = (f"\n## Performance ({today})\n"
             f"- YouTube Shorts ({video_id}): views={views}, likes={likes}, comments={comments} "
             f"(auto-pulled via YouTube Data API v3)\n")
    with open(path, "a") as f:
        f.write(entry)


def main() -> int:
    api_key = load_api_key()
    id_to_file = find_video_ids()
    if not id_to_file:
        print("No video IDs found in any posting-log.")
        return 0

    print(f"Found {len(id_to_file)} video IDs across posting-logs. Fetching stats...")
    stats_by_id = fetch_stats(list(id_to_file.keys()), api_key)

    updated, unavailable = 0, []
    for video_id, path in id_to_file.items():
        if video_id in stats_by_id:
            append_performance(path, video_id, stats_by_id[video_id])
            updated += 1
        else:
            unavailable.append(video_id)

    print(f"Updated {updated} posting-log(s) with fresh performance data.")
    if unavailable:
        print(f"Unavailable (deleted/private, no data returned): {', '.join(unavailable)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
