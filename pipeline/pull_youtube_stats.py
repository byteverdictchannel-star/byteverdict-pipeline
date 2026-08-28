#!/usr/bin/env python3
"""Pull real YouTube view/like/comment stats for every posted clip and append
a timestamped ## Performance entry to each clip's posting-log.

Uses a read-only YouTube Data API v3 key (credentials/yt_data_api_key.txt) —
separate from the OAuth upload credentials in client_secrets.json/token.json.
This closes the feedback-loop gap: content-agent-prompt.md §2b reads these
Performance sections back in when planning future sourcing.

Enhanced 2026-08-28: also generates performance-summary.json for the Content
Agent's analytics feedback loop, with subscriber correlation and topic weighting.

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
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "credentials")
KEY_FILE = os.path.join(CREDENTIALS_DIR, "yt_data_api_key.txt")
CLIP_LOG_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "test-batch", "clip-log")
DISCOVERY_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "test-batch", "discovery-outputs")
SUMMARY_FILE = os.path.join(DISCOVERY_DIR, "performance-summary.json")

VIDEO_ID_RE = re.compile(r"Video ID:.{0,10}?([A-Za-z0-9_-]{11})")
API_URL = "https://www.googleapis.com/youtube/v3/videos"
CHANNEL_API_URL = "https://www.googleapis.com/youtube/v3/channels"


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
            "part": "statistics,status,snippet,topicDetails",
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
            results[item["id"]] = item
    return results


def fetch_channel_subscribers(api_key: str) -> int:
    """Fetch current channel subscriber count."""
    # Get channel ID from credentials or use 'mine' parameter
    params = urllib.parse.urlencode({
        "part": "statistics",
        "mine": "true",
        "key": api_key,
    })
    url = f"{CHANNEL_API_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("items"):
            return int(data["items"][0]["statistics"].get("subscriberCount", 0))
    except Exception as e:
        print(f"Warning: could not fetch channel subscribers: {e}", file=sys.stderr)
    return 0


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


def extract_topic_tags(snippet: dict) -> list:
    """Extract topic keywords from video title/description/tags."""
    text = " ".join([
        snippet.get("title", ""),
        snippet.get("description", ""),
    ]).lower()
    # Common news topics to track
    topics = []
    topic_keywords = {
        "iran": ["iran", "iranian", "tehran", "persian"],
        "trump": ["trump", "donald trump"],
        "canada": ["canada", "canadian", "trudeau", "carney"],
        "tariffs": ["tariff", "tariffs", "trade war", "trade"],
        "ukraine": ["ukraine", "ukrainian", "zelensky", "kyiv"],
        "israel": ["israel", "israeli", "gaza", "hamas"],
        "china": ["china", "chinese", "beijing", "xi"],
        "russia": ["russia", "russian", "putin", "moscow"],
        "economy": ["economy", "inflation", "recession", "gdp", "jobs"],
        "military": ["military", "army", "navy", "air force", "defense"],
        "climate": ["climate", "weather", "hurricane", "flood", "wildfire"],
        "health": ["health", "covid", "vaccine", "disease", "who"],
    }
    for topic, keywords in topic_keywords.items():
        if any(kw in text for kw in keywords):
            topics.append(topic)
    return topics if topics else ["other"]


def generate_summary(stats_by_id: dict, id_to_file: dict, subscribers: int) -> None:
    """Generate performance-summary.json for the Content Agent's feedback loop."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Aggregate by topic
    topic_performance = defaultdict(lambda: {"views": 0, "likes": 0, "comments": 0, "count": 0})
    video_data = []
    
    for video_id, item in stats_by_id.items():
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        
        topics = extract_topic_tags(snippet)
        for topic in topics:
            topic_performance[topic]["views"] += views
            topic_performance[topic]["likes"] += likes
            topic_performance[topic]["comments"] += comments
            topic_performance[topic]["count"] += 1
        
        video_data.append({
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "views": views,
            "likes": likes,
            "comments": comments,
            "topics": topics,
        })
    
    # Sort topics by total views (descending)
    sorted_topics = sorted(
        topic_performance.items(),
        key=lambda x: x[1]["views"],
        reverse=True
    )
    
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel_subscribers": subscribers,
        "total_videos_tracked": len(stats_by_id),
        "topic_ranking": [
            {"topic": t[0], **t[1], "avg_views": t[1]["views"] // max(t[1]["count"], 1)}
            for t in sorted_topics
        ],
        "top_performing_videos": sorted(video_data, key=lambda x: x["views"], reverse=True)[:5],
        "recommendation": "Weight sourcing toward top-performing topics while maintaining diversity",
    }
    
    os.makedirs(DISCOVERY_DIR, exist_ok=True)
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Performance summary written to {SUMMARY_FILE}")


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
            append_performance(path, video_id, stats_by_id[video_id]["statistics"])
            updated += 1
        else:
            unavailable.append(video_id)

    print(f"Updated {updated} posting-log(s) with fresh performance data.")
    if unavailable:
        print(f"Unavailable (deleted/private, no data returned): {', '.join(unavailable)}")

    # Generate performance summary for Content Agent feedback loop
    subscribers = fetch_channel_subscribers(api_key)
    generate_summary(stats_by_id, id_to_file, subscribers)

    return 0


if __name__ == "__main__":
    sys.exit(main())
