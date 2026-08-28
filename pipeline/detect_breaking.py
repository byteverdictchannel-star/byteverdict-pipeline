#!/usr/bin/env python3
"""Detect breaking news on YouTube via recent uploads — CNN-focused
(2026-08-28, per Leo: "cnn +++++", "focus on breaking news for now").

This is a DETECTION layer, not a capture layer — it never records or
downloads anything. It only tells the Content Agent "this outlet just
published something, at this time" so sourcing searches can be pointed at
it faster. The actual clip still gets sourced the normal way, from the
outlet's own published upload — same attribution, same Tier 1/2 vetting,
same sensitive-content screen as every other candidate.

**Recent uploads, not live-stream status (fixed 2026-08-28):**
eventType=live was tried first and rejected — CNN's 24/7 rolling headline
stream is permanently "live" regardless of whether real breaking news is
happening, making it useless as a signal. Switched to order=date +
publishedAfter (last BREAKING_WINDOW_HOURS) against each channel's recent
uploads instead — that's what actually changes when a real story breaks.

**Channel-weighted rotation, not a broad query (changed 2026-08-28):**
search.list costs 100 quota units per call regardless of whether it's a
broad text query or a channel-scoped one — so switching from a generic
query to per-channel checks costs nothing extra, as long as it's still ONE
call per run. Rotates through a weighted list so CNN gets checked ~4x more
often than each backup outlet, without increasing call volume or quota
cost at all:
  CNN, CNN, BBC News, CNN, Reuters, CNN, Associated Press  (repeats)
Channel IDs verified live against the YouTube Data API on 2026-08-28
(channels.list?forHandle=...), not guessed.

**Severity scoring (added 2026-08-28, per Leo: "the severity of importance
needs to be assessed. the most important news is highest priority"):**
Every item pulled each run is mechanically scored (keyword severity +
cross-outlet corroboration + view velocity — see assess_severity()). Items
crossing MAJOR_THRESHOLD are logged to major-breaking-alerts.md AND fire an
immediate Telegram alert via telegram_review.py, so a major story is acted
on the moment it's detected, not just prioritized at production time.

Usage: python3 detect_breaking.py [--max-results 10]
Run every 30 min via the paired Hermes cron job — zero LLM cost, same
single-call-per-run quota cost as before this change (~4,800 units/day),
plus ~1 quota unit per item for the velocity check on major-looking items.
"""

import argparse
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
OUTPUT_DIR = os.path.join(
    os.path.dirname(SCRIPT_DIR), "test-batch", "discovery-outputs"
)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "breaking-alerts-latest.md")
STATE_FILE = os.path.join(OUTPUT_DIR, ".detect_breaking_rotation.json")
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Verified 2026-08-28 via channels.list?forHandle=... — not guessed.
CHANNELS = {
    "CNN": "UCupvZG-5ko_eiXAupbDfxWw",
    "BBC News": "UC16niRr50-MSBwiO3YDb3RA",
    "Reuters": "UChqUTb7kYRX8-EiaN3XFrSQ",
    "Associated Press": "UC52X5wxOL_s5yw0dQk7NtgA",
}
# CNN weighted ~4x — "cnn +++++" per Leo, 2026-08-28.
ROTATION = ["CNN", "CNN", "BBC News", "CNN", "Reuters", "CNN", "Associated Press"]


def load_api_key() -> str:
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: {KEY_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    with open(KEY_FILE) as f:
        return f.read().strip()


def next_channel() -> str:
    idx = 0
    if os.path.exists(STATE_FILE):
        try:
            idx = json.load(open(STATE_FILE)).get("idx", 0)
        except (json.JSONDecodeError, OSError):
            idx = 0
    name = ROTATION[idx % len(ROTATION)]
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"idx": idx + 1}, f)
    return name


BREAKING_WINDOW_HOURS = 3  # confirmed with Leo 2026-08-28 (~2-3 hours)


def fetch_recent(api_key: str, channel_name: str, max_results: int = 10) -> list:
    """Recent uploads from this channel, not live-stream status (fixed
    2026-08-28 — CNN's 24/7 rolling headline stream is permanently "live",
    which made eventType=live useless for spotting an actual breaking
    event; a real breaking story shows up as a fresh upload, which this
    catches). Server-side filtered via publishedAfter to the last
    BREAKING_WINDOW_HOURS — no point paying for or returning older results
    this pipeline won't treat as breaking anyway.
    """
    published_after = (
        datetime.now(timezone.utc).replace(microsecond=0)
        - __import__("datetime").timedelta(hours=BREAKING_WINDOW_HOURS)
    ).isoformat().replace("+00:00", "Z")
    params = urllib.parse.urlencode({
        "part": "snippet",
        "channelId": CHANNELS[channel_name],
        "type": "video",
        "order": "date",
        "publishedAfter": published_after,
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


CHANNEL_STATE_FILE = os.path.join(OUTPUT_DIR, ".detect_breaking_channel_state.json")


def load_channel_state() -> dict:
    if os.path.exists(CHANNEL_STATE_FILE):
        try:
            return json.load(open(CHANNEL_STATE_FILE))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def write_report(items: list, channel_name: str) -> None:
    """Update only `channel_name`'s entry, then render ALL channels' most
    recently-known state. A single-file-overwrite design (checked one
    channel, wrote a report with only that channel) would silently lose
    visibility into the other 3 channels between their own rotation turns
    — fixed 2026-08-28, same day it was written, caught before it shipped
    to the live pipeline. Each channel's entry keeps its own last-checked
    timestamp so staleness is visible per channel, not just assumed.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)

    state = load_channel_state()
    state[channel_name] = {
        "items": items,
        "checked_at": now.isoformat(),
    }
    tmp_state = CHANNEL_STATE_FILE + f".tmp.{os.getpid()}"
    with open(tmp_state, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_state, CHANNEL_STATE_FILE)

    lines = [
        f"# Breaking News — Recent Uploads (last {BREAKING_WINDOW_HOURS}h) — {now.strftime('%Y-%m-%d %H:%M')} UTC",
        "",
        f"**Just checked:** {channel_name} ({len(items)} recent upload(s))",
        f"**Generated:** {now.isoformat()}",
        "",
        "Auto-pulled every 30 min via detect_breaking.py (zero LLM cost, "
        "read-only YouTube Data API v3, search.list — recent uploads, not "
        "live-stream status; CNN's 24/7 stream is always \"live\" so that "
        "signal was useless). "
        "CNN-focused rotation (2026-08-28) — checks CNN most runs, BBC "
        "News/Reuters/Associated Press occasionally, ONE channel per "
        "pull, but this report shows all 4 channels' most-recently-known "
        "state (each with its own \"checked\" timestamp — a channel not "
        "checked this run keeps its last known status, not blanked out). "
        "This is a DETECTION signal only — nothing here has been "
        "captured, downloaded, or vetted. It exists so sourcing can "
        "notice an unfolding story fast; the actual candidate still has "
        "to be found as a published VOD/upload from the outlet later, "
        "and goes through the normal Tier 1/2 + sensitive-content screen "
        "like everything else. Do not treat a listing here as a sourced "
        "candidate on its own.",
        "",
        "---",
        "",
    ]

    for name in CHANNELS:
        entry = state.get(name)
        lines.append(f"## {name}")
        if not entry:
            lines.append("_Not checked yet this session._")
            lines.append("")
            continue
        lines.append(f"*(checked {entry['checked_at']})*")
        lines.append("")
        ch_items = entry["items"]
        if not ch_items:
            lines.append("_No recent uploads in the last 3h window._")
        else:
            for i, item in enumerate(ch_items, 1):
                snippet = item.get("snippet", {})
                title = snippet.get("title", "?")
                published = snippet.get("publishedAt", "?")
                video_id = item.get("id", {}).get("videoId", "?")
                lines.append(f"{i}. **{title}** — published {published}")
                lines.append(f"   https://www.youtube.com/watch?v={video_id}")
        lines.append("")

    tmp = OUTPUT_FILE + f".tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        f.write("\n".join(lines))
    os.replace(tmp, OUTPUT_FILE)  # atomic — a reader never sees a half-written file


# ---------------------------------------------------------------------------
# Severity scoring (added 2026-08-28, per Leo: "the severity of importance
# needs to be assessed. the most important news is highest priority")
# ---------------------------------------------------------------------------

STATS_URL = "https://www.googleapis.com/youtube/v3/videos"
MAJOR_ALERTS_FILE = os.path.join(OUTPUT_DIR, "major-breaking-alerts.md")
MAJOR_ALERTED_FILE = os.path.join(OUTPUT_DIR, ".major_breaking_alerted.json")

# Deliberately blunt, high-precision keywords — the kind of words a wire
# editor reaches for on a genuinely major story, not routine news. Weighted
# higher than corroboration/velocity since a single outlet using these
# words is already a strong signal.
SEVERITY_KEYWORDS = {
    3: ["breaking", "urgent", "alert", "emergency"],
    4: ["dead", "killed", "died", "deaths", "casualties", "explosion",
        "attack", "shooting", "evacuate", "evacuation"],
    5: ["war declared", "assassinat", "coup", "nuclear", "state of emergency",
        "mass casualty", "terrorist attack"],
}

MAJOR_THRESHOLD = 6  # sum of all signals below this = not flagged as major


def keyword_score(title: str) -> int:
    t = title.lower()
    score = 0
    for weight, words in SEVERITY_KEYWORDS.items():
        for w in words:
            if w in t:
                score = max(score, weight)  # strongest single keyword hit, not additive across tiers
    return score


def _title_words(title: str) -> set:
    stop = {"the", "a", "an", "to", "in", "on", "of", "for", "and", "is",
            "at", "as", "by", "with", "after", "over", "amid"}
    return {w for w in re.findall(r"[a-z0-9]+", title.lower()) if w not in stop and len(w) > 2}


def corroboration_score(title: str, channel_name: str, state: dict) -> int:
    """+2 per OTHER channel whose most recent item shares significant
    title-word overlap with this one — multiple outlets independently
    covering the same story fresh is a real signal, not a coincidence."""
    my_words = _title_words(title)
    if not my_words:
        return 0
    hits = 0
    for other_name, entry in state.items():
        if other_name == channel_name or not entry.get("items"):
            continue
        for other_item in entry["items"]:
            other_title = other_item.get("snippet", {}).get("title", "")
            other_words = _title_words(other_title)
            if not other_words:
                continue
            overlap = my_words & other_words
            if len(overlap) >= 3:  # several shared substantive words, not just "the"/"and"
                hits += 1
                break
    return hits * 2


def velocity_score(api_key: str, video_id: str, published_at: str) -> int:
    """+2 if view count is unusually high for how little time has passed
    since publish — a real, cheap (1 quota unit, not 100) signal of an
    audience already reacting to something big."""
    try:
        params = urllib.parse.urlencode({"part": "statistics", "id": video_id, "key": api_key})
        with urllib.request.urlopen(f"{STATS_URL}?{params}", timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        items = data.get("items", [])
        if not items:
            return 0
        views = int(items[0].get("statistics", {}).get("viewCount", 0))
        pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        hours_elapsed = max((datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600, 0.1)
        views_per_hour = views / hours_elapsed
        return 2 if views_per_hour > 5000 else 0
    except Exception as e:
        print(f"WARNING: velocity check failed for {video_id}: {e}", file=sys.stderr)
        return 0


def assess_severity(items: list, channel_name: str, state: dict, api_key: str) -> list:
    """Score every item in this pull, return the ones that cross
    MAJOR_THRESHOLD with their score and score breakdown."""
    major = []
    for item in items:
        snippet = item.get("snippet", {})
        title = snippet.get("title", "?")
        video_id = item.get("id", {}).get("videoId", "?")
        published = snippet.get("publishedAt", "?")

        kw = keyword_score(title)
        corr = corroboration_score(title, channel_name, state)
        vel = velocity_score(api_key, video_id, published) if video_id != "?" else 0
        total = kw + corr + vel

        if total >= MAJOR_THRESHOLD:
            major.append({
                "title": title, "video_id": video_id, "channel": channel_name,
                "published": published, "score": total,
                "breakdown": {"keyword": kw, "corroboration": corr, "velocity": vel},
            })
    return major


def load_alerted() -> set:
    if os.path.exists(MAJOR_ALERTED_FILE):
        try:
            return set(json.load(open(MAJOR_ALERTED_FILE)))
        except (json.JSONDecodeError, OSError):
            pass
    return set()


def save_alerted(video_ids: set) -> None:
    # Cap growth — keep the most recent 200 alerted IDs
    with open(MAJOR_ALERTED_FILE, "w") as f:
        json.dump(list(video_ids)[-200:], f)


def handle_major(major_items: list) -> None:
    """Log every major-severity item durably, and Telegram-alert on any
    NOT already alerted (avoids re-pinging Leo every 15 min for the same
    still-fresh story). Also triggers the Content Agent immediately so
    breaking news bypasses the normal 30-minute schedule."""
    if not major_items:
        return
    alerted = load_alerted()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)

    with open(MAJOR_ALERTS_FILE, "a") as f:
        for m in major_items:
            f.write(json.dumps({**m, "logged_at": now.isoformat()}) + "\n")

    new_ones = [m for m in major_items if m["video_id"] not in alerted]
    if not new_ones:
        return

    import subprocess
    telegram_script = os.path.join(SCRIPT_DIR, "telegram_review.py")
    for m in new_ones:
        text = (
            f"🔴 MAJOR breaking story detected ({m['channel']}, score {m['score']}): "
            f"{m['title']}\nhttps://www.youtube.com/watch?v={m['video_id']}\n"
            f"Content Agent should prioritize this over other candidates this run."
        )
        subprocess.run(["python3", telegram_script, "alert", text], timeout=30)
        alerted.add(m["video_id"])

    save_alerted(alerted)

    # TRIGGER CONTENT AGENT IMMEDIATELY — breaking news bypasses 30-min cycle
    content_agent_job_id = "917dd3e81af8"
    hermes_bin = os.path.expanduser("~/.local/bin/hermes")
    print(f"Triggering Content Agent immediately for breaking news...")
    subprocess.run(
        [hermes_bin, "cron", "run", content_agent_job_id],
        timeout=30,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-results", type=int, default=10, help="Max recent uploads to fetch (default 10, API cap 50)")
    ap.add_argument("--channel", choices=list(CHANNELS), help="Override the rotation and check one specific channel")
    args = ap.parse_args()

    api_key = load_api_key()
    channel_name = args.channel or next_channel()
    print(f"Checking {channel_name} for recent uploads (last {BREAKING_WINDOW_HOURS}h)...")
    items = fetch_recent(api_key, channel_name, args.max_results)
    print(f"Found {len(items)} recent upload(s) on {channel_name} in the last {BREAKING_WINDOW_HOURS}h.")

    state = load_channel_state()  # pre-update state, for corroboration checks
    write_report(items, channel_name)
    print(f"Wrote {OUTPUT_FILE}")

    major = assess_severity(items, channel_name, state, api_key)
    if major:
        print(f"MAJOR severity: {len(major)} item(s) crossed threshold {MAJOR_THRESHOLD}")
        handle_major(major)
    return 0


if __name__ == "__main__":
    sys.exit(main())
