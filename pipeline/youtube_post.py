#!/usr/bin/env python3
"""
ByteVerdict YouTube Poster — posts 9:16 Shorts to the ByteVerdict YouTube channel
via the YouTube Data API v3 (videos.insert, resumable MediaFileUpload).

Prerequisites (one-time):
  1. Create a Google Cloud project at https://console.cloud.google.com/
  2. Enable the YouTube Data API v3
  3. OAuth consent screen (External, youtube.upload scope, add your account as test user)
  4. Credentials → OAuth client ID → Desktop app → download JSON
  5. Save as client_secrets.json next to this script

First run: browser opens for OAuth consent; after authorize, saves token.json.
All future runs use the refresh token — no re-consent.

Usage:
  python3 youtube_post.py <video_path> <title> <description> --clip-id CLIP_ID [tags] [--privacy {public,unlisted,private}] [--category CATEGORY]

Example:
  python3 youtube_post.py \\
    platform-exports/tb001_c3_energy_leverage_ytshorts_9x16.mp4 \\
    "The US runs a trade deficit with Canada" \\
    "Reuters via ByteVerdict..." \\
    --clip-id tb001-c3 \\
    "trade,tariffs,canada,reuters,economy" \\
    --privacy public

--clip-id is REQUIRED (2026-08-28, Leo's directive) and is not just for
logging: this script refuses to post if the same clip_id already has a
recorded successful YouTube post (see post_dedup.py). This is a code-level
guard, independent of whatever the calling agent checked in a markdown log.
"""

import argparse
import http.client
import json
import os
import socket
import ssl
import sys
import time
from pathlib import Path
from typing import Any, Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import post_dedup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "credentials")
CLIENT_SECRETS_FILE = os.path.join(CREDENTIALS_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "token.json")
MAX_RETRIES = 5
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
# Non-HttpError transient failures worth retrying during a long chunked upload
# (a multi-minute upload in 256KB chunks means many round trips — a brief
# connection reset or timeout partway through used to kill the whole upload
# with no retry, unlike the equivalent retry logic in ig_post.py). This
# mirrors what Google's own resumable-upload sample recommends catching.
RETRIABLE_EXCEPTIONS = (
    socket.timeout,
    ConnectionError,
    ssl.SSLError,
    http.client.IncompleteRead,
    http.client.BadStatusLine,
    TimeoutError,
)
CHUNK_SIZE = 1024 * 256  # 256 KB chunks for resumable upload
DEFAULT_CATEGORY = "28"  # Science & Technology

# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------


def get_authenticated_service() -> Any:
    """Return an authorized YouTube v3 service, running OAuth if needed.

    Only usable interactively: run_local_server() opens a browser and blocks
    until the OAuth redirect completes, with no timeout. This must never be
    reached from the unattended cron Posting Agent (runs every ~3h with no
    human present) — if it is, that means token.json is missing/invalid and
    needs a human to re-authorize first. Fail fast instead of hanging.
    """
    if not sys.stdin.isatty():
        sys.exit(
            "ERROR: no cached/valid token.json and no interactive terminal available "
            "to complete OAuth consent. This must be run once interactively by a human "
            "to (re)authorize before the cron Posting Agent can use it — refusing to "
            "start an interactive OAuth flow that would hang forever unattended."
        )

    if not os.path.exists(CLIENT_SECRETS_FILE):
        sys.exit(
            f"ERROR: {CLIENT_SECRETS_FILE} not found.\n"
            "Create it at https://console.cloud.google.com/ :\n"
            "  1. Create a project\n"
            "  2. Enable YouTube Data API v3\n"
            "  3. OAuth consent screen (External, scope: youtube.upload)\n"
            "  4. Credentials -> OAuth client ID -> Desktop app\n"
            "  5. Download JSON, save as client_secrets.json next to this script\n"
        )

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def load_existing_token() -> Optional[Any]:
    """Try to load a cached token.json and refresh if expired."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            return creds
        return creds
    except Exception as e:
        # Any failure here (corrupt file, revoked token, or just a transient
        # network blip during refresh) used to be swallowed identically —
        # print it so a transient error is at least distinguishable in logs
        # from "no token file at all", which callers otherwise can't tell apart.
        print(f"  Warning: failed to load/refresh cached token: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


def upload_video(
    youtube: Any,
    file_path: str,
    title: str,
    description: str,
    tags: Optional[list[str]] = None,
    privacy_status: str = "private",
    category_id: str = DEFAULT_CATEGORY,
) -> dict:
    """Upload a video via resumable MediaFileUpload. Returns the video resource."""
    if not os.path.isfile(file_path):
        sys.exit(f"ERROR: file not found: {file_path}")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True, chunksize=CHUNK_SIZE)
    insert_request = youtube.videos().insert(
        part=", ".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    retry = 0
    file_size = os.path.getsize(file_path)

    print(f"Uploading {os.path.basename(file_path)} ({file_size / 1024 / 1024:.1f} MB)...")

    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if status:
                pct = round(status.progress() * 100)
                print(f"\r  {pct}%", end="", flush=True)
            if response and "id" in response:
                print()  # newline after progress
                return response
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                retry += 1
                if retry > MAX_RETRIES:
                    sys.exit(f"ERROR: {MAX_RETRIES} retries exhausted: {e}")
                sleep_time = 2 ** retry
                print(f"\n  Retriable error {e.resp.status}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            retry += 1
            if retry > MAX_RETRIES:
                sys.exit(f"ERROR: {MAX_RETRIES} retries exhausted: {e}")
            sleep_time = 2 ** retry
            print(f"\n  Retriable network error ({type(e).__name__}: {e}). Retrying in {sleep_time}s...")
            time.sleep(sleep_time)

    return response


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Post a 9:16 Short to the ByteVerdict YouTube channel"
    )
    parser.add_argument("video_path", help="Path to the MP4 to upload")
    parser.add_argument("title", help="Video title")
    parser.add_argument("description", help="Video description (include source attribution)")
    parser.add_argument(
        "--clip-id",
        required=True,
        help="Clip ID (e.g. tb005-c1). REQUIRED — used for the code-level "
             "duplicate-post guard, not just logging. This script refuses "
             "to post if this clip_id already has a successful YouTube post "
             "recorded (see post_dedup.py).",
    )
    parser.add_argument(
        "tags",
        nargs="?",
        default="",
        help="Comma-separated tags (optional)",
    )
    parser.add_argument(
        "--privacy",
        choices=["public", "unlisted", "private"],
        default="private",
        help="Privacy status (default: private — callers should still pass this explicitly, never rely on the default)",
    )
    parser.add_argument(
        "--category",
        default=DEFAULT_CATEGORY,
        help=f"YouTube category ID (default: {DEFAULT_CATEGORY} = Science & Technology)",
    )
    args = parser.parse_args()

    # Code-level duplicate-post guard — refuses and exits non-zero if this
    # clip_id already has a successful YouTube post recorded. Runs before
    # any network call, before OAuth, before touching the video file.
    post_dedup.check_not_already_posted(args.clip_id, "youtube")

    # Try cached token first; fall back to fresh OAuth
    creds = load_existing_token()
    if creds is None:
        print("No cached token. Starting OAuth flow — your browser will open.")
        youtube = get_authenticated_service()
    else:
        print("Using cached credentials.")
        youtube = build("youtube", "v3", credentials=creds)

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    result = upload_video(
        youtube=youtube,
        file_path=args.video_path,
        title=args.title,
        description=args.description,
        tags=tags,
        privacy_status=args.privacy,
        category_id=args.category,
    )

    video_id = result.get("id")
    print(f"\nUpload complete.")
    print(f"  Video ID: {video_id}")
    print(f"  URL:      https://www.youtube.com/watch?v={video_id}")
    print(f"  Short URL: https://youtu.be/{video_id}")
    print(f"  Privacy:  {args.privacy}")

    # Record success ONLY here, after the API has confirmed the upload —
    # never speculatively. This is what the guard above checks on the next
    # attempt for this clip_id.
    post_dedup.record_posted(
        args.clip_id, "youtube", video_id, f"https://youtu.be/{video_id}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
