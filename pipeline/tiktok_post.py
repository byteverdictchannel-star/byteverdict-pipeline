#!/usr/bin/env python3
"""
TikTok posting wrapper for the clips-channel Posting Agent.
Uses TiktokAutoUploader (cli.py) under the hood — session cookies already active for @byteverdict.
"""

import json
import os
import subprocess
import sys

TIKTOK_AUTO_UPLOADER = "/home/leo/TiktokAutoUploader"
CLI = os.path.join(TIKTOK_AUTO_UPLOADER, "cli.py")
VENV_PYTHON = os.path.join(TIKTOK_AUTO_UPLOADER, ".venv", "bin", "python")

CLIPPINGS_CHANNEL = "/home/leo/clips-channel"
READY_TO_POST = os.path.join(CLIPPINGS_CHANNEL, "test-batch", "ready-to-post")
POSTING_LOG_DIR = os.path.join(CLIPPINGS_CHANNEL, "test-batch", "clip-log")


def post_tiktok(video_path: str, title: str, cookie_name: str = "tiktok_session-byteverdict") -> dict:
    """
    Upload a video to TikTok via TiktokAutoUploader CLI.
    Returns dict with status, video_id (always None — see note below), error (if failed).

    Note: the underlying CLI has no --cookie flag; it resolves the session purely from
    -u/--users, which the cookie_store looks up by username. cookie_name is expected in
    the form "tiktok_session-<username>" (matching the .cookie filename convention) and
    the username is derived from it here so this parameter actually controls which
    account's session gets used, instead of being silently ignored.

    Note: TikTok's CLI never prints a video ID or URL on success (confirmed in
    tiktok_uploader/tiktok.py — it exists internally as upload_node["Vid"] but the CLI
    only prints "Published successfully"). video_id is therefore always None here. Callers
    that need duplicate-post protection for TikTok must rely on a logged success status,
    not a URL/ID, since none is available.
    """
    # HARD BLOCK (added 2026-08-28) — Leo has repeatedly, explicitly said to
    # leave TikTok out ("leave tik tok out for the time being"). A real,
    # unauthorized TikTok post happened this same day because that rule
    # only lived in a prompt, and the prompt got skipped. This mirrors the
    # exact lesson this whole pipeline was built around: prompt-only
    # "MANDATORY" instructions get skipped; code-level guards don't. Remove
    # this block ONLY when Leo explicitly says TikTok is back in scope —
    # not on an agent's own judgment that it "seems fine now."
    raise RuntimeError(
        "TikTok posting is hard-blocked at the code level. Leo has explicitly "
        "said to leave TikTok out of scope. This function will not run until "
        "that restriction is deliberately removed by a human, on Leo's explicit "
        "instruction — not inferred from context."
    )

    video = os.path.abspath(video_path)
    if not os.path.exists(video):
        return {"status": "error", "error": f"Video not found: {video}"}

    username = cookie_name.removeprefix("tiktok_session-") or "byteverdict"

    cmd = [
        VENV_PYTHON, CLI, "upload",
        "-u", username,
        "-v", video,
        "-t", title,
    ]
    print(f"Running: {' '.join(cmd)}", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            cwd=TIKTOK_AUTO_UPLOADER,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min per upload
        )
        stdout = result.stdout
        stderr = result.stderr
        combined = stdout + "\n" + stderr

        print(combined, file=sys.stderr)

        if result.returncode == 0 and "Published successfully" in combined:
            # No video ID/URL is extractable — the CLI never prints one, see docstring.
            return {"status": "success", "video_id": None, "output": combined[:500]}
        elif result.returncode == 0:
            return {"status": "success", "output": combined[:500]}
        else:
            return {"status": "error", "error": stderr or stdout or f"exit code {result.returncode}", "output": combined[:500]}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Upload timed out after 5 minutes"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    """CLI entry point for the Posting Agent."""
    import argparse
    parser = argparse.ArgumentParser(description="Post a clip to TikTok")
    parser.add_argument("--video", required=True, help="Path to video file (master or TikTok export)")
    parser.add_argument("--title", required=True, help="Video title/caption")
    parser.add_argument("--cookie", default="tiktok_session-byteverdict", help="Cookie file name in CookiesDir")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without posting")
    args = parser.parse_args()

    if args.dry_run:
        print(f"[DRY RUN] Would post: {args.video} with title: {args.title}")
        return

    # Verify cookie exists
    cookie_path = os.path.join(TIKTOK_AUTO_UPLOADER, "CookiesDir", f"{args.cookie}.cookie")
    if not os.path.exists(cookie_path):
        print(f"ERROR: Cookie file not found: {cookie_path}", file=sys.stderr)
        sys.exit(1)

    result = post_tiktok(args.video, args.title, args.cookie)
    print(json.dumps(result, indent=2))

    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
