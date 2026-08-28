#!/usr/bin/env python3
"""Drop clips that have sat unreviewed too long — news doesn't stay fresh.

Added 2026-08-28, per Leo: "I don't think the clips will stay relevant for
long" — a clip waiting 12+ hours for a Telegram tap is more likely stale
news than a clip worth posting late. Rather than let it sit indefinitely
(or post it once reviewed, days later, to a story nobody cares about
anymore), auto-expire it and free up the queue.

Checks every clip in test-batch/ready-to-post/ that has a
<clip_id>.review_sent_at.json marker (written by telegram_review.py notify)
but no <clip_id>.review_decision.json yet (never reviewed). If the sent_at
timestamp is older than EXPIRE_AFTER_HOURS, move its files to
test-batch/expired/ (same non-destructive move pattern as a rejection —
nothing is deleted, just moved out of the ready queue) and write a decision
file with decision="expired" so the rejection-audit's pattern-tracking and
the Content Agent's own history checks both see it consistently.

Usage: python3 expire_stale_clips.py
Run periodically (no-agent cron) — zero LLM cost, pure file-age check.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
CLIP_LOG_DIR = ROOT / "test-batch" / "clip-log"
READY_DIR = ROOT / "test-batch" / "ready-to-post"
EXPIRED_DIR = ROOT / "test-batch" / "expired"

EXPIRE_AFTER_HOURS = 8  # middle of Leo's confirmed 6-12h range


def find_clip_ids():
    """Every clip_id with a review_sent_at marker (i.e. actually sent for
    review at some point) is a candidate — derived from the marker
    filenames themselves, not from ready-to-post file naming, since a
    clip_id may have several files (master + platform exports) sharing a
    common prefix."""
    return {p.name.removesuffix(".review_sent_at.json") for p in CLIP_LOG_DIR.glob("*.review_sent_at.json")}


def expire_clip(clip_id, sent_at_iso):
    EXPIRED_DIR.mkdir(parents=True, exist_ok=True)
    moved = []
    if READY_DIR.exists():
        for f in READY_DIR.glob(f"{clip_id}*"):
            dest = EXPIRED_DIR / f.name
            f.rename(dest)
            moved.append(str(dest))

    decision_path = CLIP_LOG_DIR / f"{clip_id}.review_decision.json"
    decision_path.write_text(json.dumps({
        "clip_id": clip_id,
        "decision": "expired",
        "note": f"Auto-expired — sent for review at {sent_at_iso}, no response within {EXPIRE_AFTER_HOURS}h.",
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    return moved


def main() -> int:
    now = datetime.now(timezone.utc)
    expired_count = 0

    for clip_id in find_clip_ids():
        decision_path = CLIP_LOG_DIR / f"{clip_id}.review_decision.json"
        if decision_path.exists():
            continue  # already reviewed (approved/rejected/expired) — nothing to do

        sent_marker = CLIP_LOG_DIR / f"{clip_id}.review_sent_at.json"
        try:
            sent = json.loads(sent_marker.read_text())
            sent_at = datetime.fromisoformat(sent["sent_at"])
        except (json.JSONDecodeError, KeyError, ValueError):
            print(f"WARNING: unreadable sent_at marker for {clip_id}, skipping", file=sys.stderr)
            continue

        age_hours = (now - sent_at).total_seconds() / 3600
        if age_hours >= EXPIRE_AFTER_HOURS:
            moved = expire_clip(clip_id, sent["sent_at"])
            print(f"{clip_id}: expired after {age_hours:.1f}h unreviewed, moved {len(moved)} file(s)")
            expired_count += 1

    if expired_count == 0:
        print("No stale clips to expire.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
