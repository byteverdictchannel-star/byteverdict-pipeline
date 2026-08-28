#!/usr/bin/env python3
"""Code-level duplicate-post guard, shared by youtube_post.py, ig_post.py, fb_post.py.

Why this exists (2026-08-28, Leo's directive): before this, the ONLY thing
preventing a clip from being posted twice to the same platform was the
Posting Agent's own prompt-level discipline — "check the posting-log before
calling the script." That's a soft guarantee: it depends on the agent
correctly reading a markdown file every single time, with no code-level
backstop if it doesn't. A misread, a retry after a partial failure, two
overlapping cron runs, or the agent just forgetting a step would all produce
a real duplicate post with no error at all.

This module makes each poster script refuse to post a second time on its
own, regardless of what the calling agent did or didn't check. State lives
in test-batch/clip-log/<clip_id>.post_state.json — one file per clip, one
key per platform, written ONLY by record_posted() via an advisory file lock
+ atomic rename, so two scripts posting different platforms for the same
clip at the same time can't stomp each other's write.

Fails CLOSED, not open: an unreadable/corrupt state file blocks posting
rather than silently proceeding, because the failure mode we're defending
against (an unnoticed duplicate post) is worse than the failure mode of
occasionally forcing a human to look at a bad state file.

This is a hard backstop, not a replacement for the existing prompt-level
posting-log check — keep doing that too. Two independent checks catch more
than one.
"""

import fcntl
import json
import os
import time
from pathlib import Path

CLIP_LOG_DIR = Path(__file__).resolve().parent.parent / "test-batch" / "clip-log"


class AlreadyPostedError(SystemExit):
    """Raised (as SystemExit, so a bare script exits non-zero) when a
    clip+platform already has a recorded successful post."""


class CorruptStateError(SystemExit):
    """Raised when the state file exists but can't be parsed — fail closed."""


def _state_path(clip_id: str) -> Path:
    if not clip_id or "/" in clip_id or ".." in clip_id:
        raise ValueError(f"invalid clip_id: {clip_id!r}")
    return CLIP_LOG_DIR / f"{clip_id}.post_state.json"


def _lock_path(clip_id: str) -> Path:
    return _state_path(clip_id).with_suffix(".json.lock")


def check_not_already_posted(clip_id: str, platform: str) -> None:
    """Raise if `clip_id` already has a successful post recorded for `platform`.

    Call this at the very start of a posting script's main(), before doing
    any upload work. No file present = never posted = proceed normally.
    """
    path = _state_path(clip_id)
    if not path.exists():
        return
    try:
        state = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise CorruptStateError(
            f"REFUSING TO POST: {path} exists but could not be read/parsed "
            f"({exc}). Failing closed rather than risking a duplicate post — "
            f"a human needs to look at this file before {clip_id} can be "
            f"posted to {platform}."
        )
    entry = state.get(platform)
    if isinstance(entry, dict) and entry.get("status") == "success":
        raise AlreadyPostedError(
            f"REFUSING TO POST: {clip_id} already posted to {platform} at "
            f"{entry.get('posted_at', 'unknown time')} "
            f"(post_id={entry.get('post_id')}, url={entry.get('url')}). "
            f"This is a code-level guard, not a prompt-level one. If this is "
            f"genuinely a legitimate re-post (e.g. confirmed platform-side "
            f"deletion, per SKILL.md's re-post-after-deletion flow), a human "
            f"must edit {path} directly — this script will not bypass its "
            f"own duplicate check."
        )


def record_posted(clip_id: str, platform: str, post_id, url) -> None:
    """Record a successful post. Locked read-modify-write, atomic on disk.

    Call this ONLY after the platform API has confirmed success — never
    speculatively, never before the upload actually completes.
    """
    path = _state_path(clip_id)
    lock_path = _lock_path(clip_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(lock_path, "w") as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX)
        try:
            if path.exists():
                try:
                    state = json.loads(path.read_text())
                except (json.JSONDecodeError, OSError):
                    # Under lock, with a write about to happen: don't silently
                    # discard whatever the corrupt file held. Preserve it
                    # under a dated key rather than losing prior platforms'
                    # records.
                    state = {"_recovered_corrupt_state_at_" + str(int(time.time())): path.read_text(errors="replace")}
            else:
                state = {}

            state[platform] = {
                "status": "success",
                "post_id": post_id,
                "url": url,
                "posted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
            tmp.write_text(json.dumps(state, indent=2))
            os.replace(tmp, path)  # atomic on the same filesystem
        finally:
            fcntl.flock(lockfile, fcntl.LOCK_UN)
