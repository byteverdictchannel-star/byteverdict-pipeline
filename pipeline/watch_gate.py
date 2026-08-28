#!/usr/bin/env python3
"""Code-level guard: has this exact video file actually been watched?

Why this exists (2026-08-28, Leo's directive): the Content Agent's cron
prompt marks a watch.py pass "MANDATORY — do not skip" before a clip reaches
Leo. On the first real cron run after that change, the agent skipped it
anyway and still reported the clip as passing the quality gate — proven
empirically, not assumed (checked the session's own logs: zero watch.py
invocations, despite the run's own report claiming the gate passed). A
prompt-level "MANDATORY" is not a hard guarantee, exactly the same lesson
that motivated post_dedup.py for posting. This module is the same fix
applied to the watch gate: a receipt the agent can't fake without actually
running the tool.

How it works: pipeline/tools/watch/scripts/watch.py calls
record_watch_receipt() after it has genuinely extracted and returned real
frames from a real video file — not on a transcript-only run, not on a
failed/empty extraction. The receipt is keyed by a content hash of the
video file, not its path or filename, so:
  - A stale receipt from watching an OLD version of a file (before a
    re-render) does NOT satisfy the gate for the NEW version — this
    pipeline has already had files silently re-rendered in place (see
    tb005-c1's history), so path-based keying alone would be unsafe.
  - The same file reachable by two different paths (e.g. a master and a
    platform export produced from identical source frames) would still
    need its own genuinely-watched pass, UNLESS the bytes are literally
    identical, in which case a single watch pass legitimately covers both.

check_watch_receipt() is the enforcement side — call it from a posting
script before posting. Deliberately NOT wired into youtube_post.py /
ig_post.py / fb_post.py yet (2026-08-28) — see the TODO at the bottom of
this file for why, and what still needs deciding before it is.
"""

import hashlib
import json
import os
import time
from pathlib import Path

RECEIPT_DIR = Path(__file__).resolve().parent.parent / "test-batch" / "clip-log" / ".watch_receipts"

# How long a receipt stays valid. Generous on purpose — the point is to
# prove a real look happened at some point in this clip's production
# lifecycle, not to force a re-watch every few hours. A clip's whole
# lifecycle from first sourced to posted is usually well under this.
RECEIPT_MAX_AGE_SECONDS = 14 * 24 * 3600  # 14 days


def _hash_video(video_path) -> str:
    """SHA-256 of the file's actual bytes — the receipt's real key.

    Full-file hash, not a fast fingerprint (size+mtime): these are short
    clips (single-digit MB), hashing costs well under a second, and a
    fingerprint that can be spoofed by touching mtime defeats the point of
    a guard meant to resist exactly that kind of accidental or careless
    bypass.
    """
    h = hashlib.sha256()
    with open(video_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _receipt_path(content_hash: str) -> Path:
    return RECEIPT_DIR / f"{content_hash}.json"


def record_watch_receipt(video_path, frame_count: int, detail: str) -> None:
    """Record that this exact video file's content was genuinely watched.

    Call ONLY after real frames were actually extracted and are being
    returned in the report — never speculatively, never for a
    transcript-only run (no frames means no visual verification happened,
    which is specifically what this gate exists to prove).
    """
    if frame_count <= 0:
        return  # nothing visual actually happened; don't record a false receipt
    video_path = Path(video_path)
    if not video_path.is_file():
        return  # defensive — shouldn't happen, but never hash a nonexistent path

    content_hash = _hash_video(video_path)
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = {
        "content_sha256": content_hash,
        "watched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frame_count": frame_count,
        "detail": detail,
        "source_path_at_watch_time": str(video_path),
    }
    path = _receipt_path(content_hash)
    tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(receipt, indent=2))
    os.replace(tmp, path)


def check_watch_receipt(video_path) -> None:
    """Raise SystemExit if this exact video file's content has no valid
    (unexpired) watch receipt. Call before posting, after the dedup guard.
    """
    video_path = Path(video_path)
    if not video_path.is_file():
        raise SystemExit(f"REFUSING TO POST: video file not found: {video_path}")

    content_hash = _hash_video(video_path)
    path = _receipt_path(content_hash)
    if not path.exists():
        raise SystemExit(
            f"REFUSING TO POST: no watch.py receipt found for {video_path} "
            f"(content hash {content_hash[:12]}...). A mandatory multi-frame "
            f"review (pipeline/tools/watch/) must run against this exact file "
            f"before it can be posted — see agents/content-agent-prompt.md "
            f"step 2b and posting-agent-prompt.md §3a step 4. If this file was "
            f"re-rendered since it was last watched, a stale receipt for the "
            f"old version would not satisfy this check either — a fresh watch "
            f"pass against the current file is required."
        )

    try:
        receipt = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(
            f"REFUSING TO POST: watch receipt for {video_path} exists but "
            f"could not be read/parsed ({exc}). Failing closed."
        )

    watched_at = receipt.get("watched_at", "")
    try:
        watched_ts = time.mktime(time.strptime(watched_at, "%Y-%m-%dT%H:%M:%SZ"))
        age = time.time() - watched_ts
    except (ValueError, TypeError):
        age = None

    if age is not None and age > RECEIPT_MAX_AGE_SECONDS:
        raise SystemExit(
            f"REFUSING TO POST: watch receipt for {video_path} is stale "
            f"(watched {watched_at}, {age / 86400:.0f} days ago, max age is "
            f"{RECEIPT_MAX_AGE_SECONDS / 86400:.0f} days). A fresh watch.py "
            f"pass is required before this clip can be posted."
        )
    # Valid receipt — proceed silently, no return value needed.


# TODO (2026-08-28, deliberately not done yet): wire check_watch_receipt()
# into youtube_post.py / ig_post.py / fb_post.py, same pattern as
# post_dedup.check_not_already_posted(). Held back on purpose, pending a
# real decision, not an oversight:
#
#   1. Which file gets hashed and checked — the platform-specific export
#      being posted (tiktok/ytshorts/igreels .mp4), or the pre-export
#      master? The prompt's step 2b/step 4 language talks about watching
#      "the source_or_export_path" ambiguously. If it's the master, a
#      receipt on the master should probably satisfy the gate for all
#      three platform exports derived from it (same visual content,
#      different encode settings) — but that requires the poster scripts
#      to know the master's path too, which they currently don't take as
#      an argument at all.
#   2. What happens on a genuine, correctly-flagged FAILURE — i.e. watch.py
#      was run, a real problem was found, the agent correctly decided not
#      to post. There's no negative/failure receipt today, so this refusal
#      would be indistinguishable from "nobody ever looked" vs. "somebody
#      looked and rightly said no." Worth a distinct receipt state before
#      this becomes a hard blocker on real posting, not just a warning.
#
# check_watch_receipt() itself is built, tested, and ready — this is a
# scoping decision, not a technical blocker.
