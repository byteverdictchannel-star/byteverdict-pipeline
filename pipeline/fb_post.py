#!/usr/bin/env python3
"""
ByteVerdict Facebook Page Poster — posts 9:16 video to the ByteVerdict
Facebook Page via the Facebook Graph API (/{page_id}/videos).

Relationship to the other posters:
  - youtube_post.py  -> YouTube Data API v3 (Shorts)
  - ig_post.py       -> Instagram Graph API (Reels)
  - fb_post.py       -> Facebook Graph API (Page video post)   <-- this file
  - tiktok_post.py   -> TikTok (manual/SDK) — out of scope for this pass

A Facebook Page is REQUIRED. The Page is the thing that owns the Instagram
Business account already used by ig_post.py, so the same Meta app that issued
the IG token can issue a Page Access Token — but the two tokens are distinct.

Credentials come from ~/.hermes/facebook_page_creds.json, written by
facebook_setup.py after you complete the one-time OAuth. That file holds:
    { page_id, page_name, page_access_token, expires_at }

FB Graph video upload is a single multipart POST to /{page_id}/videos with
the video file + title + description. No resumable session needed for shorts.

Ported 2026-08-28 from archive/unused-integrations/fb_post.py (a working
implementation from before this pipeline split into one-script-per-platform,
called directly by the Posting Agent — that script was never rebuilt for the
current architecture, it just got left behind). Three real changes from that
version, not just the dedup guard:
  1. --clip-id is REQUIRED for any real post — the code-level duplicate-post
     guard (post_dedup.py), same pattern as youtube_post.py / ig_post.py.
  2. The original called check_creds() (a real network call) unconditionally,
     even under --test — meaning "dry run" still hit the live Graph API.
     Fixed: --test no longer touches the network at all.
  3. --title/--desc were `required=False` but used unconditionally — an
     omitted one would silently post as literal "None". Now required for any
     real post (still optional-in-appearance for --check, which doesn't post).

Usage:
  # Post a local file
  python3 fb_post.py VIDEO.mp4 --title "Headline" --desc "Caption + source" --clip-id tb005-c1

  # Post from a public URL (skip local upload)
  python3 fb_post.py --video-url "https://.../clip.mp4" --title "..." --desc "..." --clip-id tb005-c1

  # Dry run (print the request, don't send — no network call at all)
  python3 fb_post.py VIDEO.mp4 --title "..." --desc "..." --clip-id tb005-c1 --test

  # Check token validity without posting (no --clip-id needed, doesn't post)
  python3 fb_post.py --check
"""

import argparse
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import post_dedup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CRED_FILE = os.path.expanduser("~/.hermes/facebook_page_creds.json")
GRAPH = "https://graph.facebook.com/v26.0"
MAX_RETRIES = 5
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def load_creds(path: str) -> dict:
    if not os.path.exists(path):
        sys.exit(
            f"ERROR: Facebook creds not found at {path}\n"
            "Run facebook_setup.py once to complete OAuth and save the Page token.\n"
            "(Requires FB_APP_ID + FB_APP_SECRET from a Meta app that owns the Page.)"
        )
    try:
        return json.load(open(path))
    except Exception as e:
        sys.exit(f"ERROR: could not read {path}: {e}")


def check_creds(cred: dict) -> bool:
    """Validate the saved Page token against Graph. Returns True if usable.

    Makes a real network call — never call this from a --test path.
    """
    pid = cred.get("page_id")
    tok = cred.get("page_access_token")
    if not pid or not tok:
        print("ERROR: creds missing page_id or page_access_token")
        return False
    r = requests.get(
        f"{GRAPH}/{pid}",
        params={"access_token": tok, "fields": "name,id"},
        timeout=15,
    )
    d = r.json()
    if d.get("error"):
        print("TOKEN INVALID:", json.dumps(d["error"]))
        return False
    print(f"Token OK — Page: {d.get('name')} (id={d.get('id')})")
    exp = cred.get("expires_at")
    if exp:
        days = (exp - time.time()) / 86400
        print(f"Token expires in ~{days:.0f} days" if days > 0 else "Token EXPIRED")
    return True


def post_video(
    page_id: str,
    token: str,
    title: str,
    description: str,
    video_path: str = None,
    video_url: str = None,
    published: bool = True,
) -> dict:
    if not video_path and not video_url:
        sys.exit("ERROR: provide --video PATH or --video-url URL")

    endpoint = f"{GRAPH}/{page_id}/videos"
    params = {
        "access_token": token,
        "title": title,
        "description": description,
        "published": "true" if published else "false",
    }

    retry = 0
    while True:
        try:
            if video_url:
                # Server-side fetch by FB — simplest, no upload bandwidth
                params["file_url"] = video_url
                r = requests.post(endpoint, data=params, timeout=120)
            else:
                # Local file upload via multipart — file handle must be
                # reopened on each retry attempt, not reused across sends.
                with open(video_path, "rb") as f:
                    files = {"source": (os.path.basename(video_path), f, "video/mp4")}
                    r = requests.post(endpoint, data=params, files=files, timeout=300)

            if r.status_code in RETRYABLE_STATUS_CODES:
                raise requests.exceptions.RequestException(
                    f"HTTP {r.status_code}: {r.text[:300]}"
                )
            return r.json()

        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
            retry += 1
            if retry > MAX_RETRIES:
                sys.exit(f"ERROR: {MAX_RETRIES} retries exhausted: {e}")
            sleep_time = 2 ** retry
            print(f"  Retriable error ({e}). Retrying in {sleep_time}s...")
            time.sleep(sleep_time)


def main() -> int:
    ap = argparse.ArgumentParser(description="Post a 9:16 video to the ByteVerdict FB Page")
    ap.add_argument("video", nargs="?", help="Local video file path")
    ap.add_argument("--video-url", help="Public URL of the video (skips local upload)")
    ap.add_argument("--title", help="Post title (required for any real post)")
    ap.add_argument("--desc", help="Post description / caption (required for any real post)")
    ap.add_argument(
        "--clip-id",
        help="Clip ID (e.g. tb005-c1). REQUIRED unless --check — used for "
             "the code-level duplicate-post guard, not just logging. This "
             "script refuses to post if this clip_id already has a "
             "successful Facebook post recorded (see post_dedup.py).",
    )
    ap.add_argument("--cred-file", default=DEFAULT_CRED_FILE, help="Path to FB creds JSON")
    ap.add_argument(
        "--published",
        choices=["true", "false"],
        default="true",
        help="Publish now (true) or stage as draft (false)",
    )
    ap.add_argument("--test", action="store_true",
                     help="Dry run — print the request, make NO network call at all")
    ap.add_argument("--check", action="store_true", help="Validate token, don't post")
    args = ap.parse_args()

    if args.check:
        cred = load_creds(args.cred_file)
        return 0 if check_creds(cred) else 1

    if not args.clip_id:
        ap.error("--clip-id is required unless --check is given")
    if not args.title or not args.desc:
        ap.error("--title and --desc are required for a real post")

    # Code-level duplicate-post guard — refuses and exits non-zero if this
    # clip_id already has a successful Facebook post recorded. Runs before
    # loading creds or touching the network at all.
    post_dedup.check_not_already_posted(args.clip_id, "facebook")

    published = args.published == "true"

    if args.test:
        # No network call in --test mode at all — not even a creds check.
        print("[DRY RUN] Would POST to Facebook Graph (no network call made):")
        print(f"  endpoint: {GRAPH}/<page_id>/videos")
        print(f"  title:    {args.title}")
        print(f"  desc:     {args.desc[:80]}...")
        print(f"  source:   {args.video or args.video_url}")
        print(f"  published: {published}")
        print(f"  clip_id:  {args.clip_id}")
        return 0

    cred = load_creds(args.cred_file)
    if not check_creds(cred):
        sys.exit("ERROR: token invalid. Re-run facebook_setup.py to refresh.")

    print("Posting to Facebook Page...")
    resp = post_video(
        page_id=cred["page_id"],
        token=cred["page_access_token"],
        title=args.title,
        description=args.desc,
        video_path=args.video,
        video_url=args.video_url,
        published=published,
    )

    if resp.get("error"):
        print("POST FAILED:", json.dumps(resp["error"]))
        return 1

    post_id = resp.get("id")
    permalink = f"https://www.facebook.com/{cred['page_id']}/videos/{post_id}"
    print(f"Posted. Post ID: {post_id}")
    print(f"  Permalink: {permalink}")

    # Record success ONLY here, after the API has confirmed the post —
    # never speculatively. This is what the guard above checks on the next
    # attempt for this clip_id.
    post_dedup.record_posted(args.clip_id, "facebook", post_id, permalink)

    return 0


if __name__ == "__main__":
    sys.exit(main())
