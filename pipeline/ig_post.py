#!/usr/bin/env python3
"""
ByteVerdict Instagram Reels Poster — posts 9:16 Reels to @byteverdict
via the Instagram Graph API (Content Publishing flow).

Flow (3 steps):
  1. Create media container  POST /{ig_user_id}/media  (media_type=REELS)
     - If video is on a public URL: pass video_url, container auto-processes
     - If video is local: pass upload_type=resumable, then upload separately
  2. Upload video (local only)  POST rupload.facebook.com/ig-api-upload/{version}/{container_id}
  3. Publish                   POST /{ig_user_id}/media_publish  (creation_id=container_id)

Prerequisites (one-time):
  1. Meta Developer account  https://developers.facebook.com/
  2. Create a Developer App, add "Instagram Graph API" product
  3. Obtain an Instagram User Access Token with:
       - instagram_business_basic
       - instagram_business_content_publish
     (Graph API Explorer for quick test; proper OAuth flow for automation)
  4. Get the Instagram User ID (numeric) for @byteverdict:
       GET https://graph.instagram.com/me?fields=id&access_token=<TOKEN>

Usage:
  # Quick test with token + IG ID on CLI:
  python3 ig_post.py \
    --token "IGAA..." \
    --ig-user-id 28370417429249464 \
    --video platform-exports/tb001_c3_energy_leverage_igreels_9x16.mp4 \
    --caption "Crisp verdict on energy leverage..."

  # Or with video already on a public URL (skips local upload):
  python3 ig_post.py \
    --token "IGAA..." \
    --ig-user-id 28370417429249464 \
    --video-url "https://example.com/video.mp4" \
    --caption "..."

  # Cache token + IG ID for reuse (writes ig_state.json):
  python3 ig_post.py --token "IGAA..." --ig-user-id 28370417429249464 --cache --video ... --caption "..."

  # Then subsequent runs without --token / --ig-user-id:
  python3 ig_post.py --video platform-exports/... --caption "..."

  # Dry run (print API calls without executing):
  python3 ig_post.py --token "IGAA..." --ig-user-id 28370417429249464 --video ... --caption "..." --test

--clip-id is REQUIRED for any real post (2026-08-28, Leo's directive) — not
required for --lookup-id, which doesn't post anything. This script refuses
to post if the same clip_id already has a recorded successful Instagram
post (see post_dedup.py) — a code-level guard, independent of whatever the
calling agent checked in a markdown log.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

from ig_common import (
    ApiError,
    api_get,
    api_post,
    load_state,
    save_state,
    lookup_ig_user_id as _shared_lookup_ig_user_id,
    STATE_FILE,
    GRAPH_HOST,
    MAX_RETRIES,
    RETRYABLE_STATUS_CODES,
)
import post_dedup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

UPLOAD_HOST = f"https://rupload.facebook.com/ig-api-upload/{GRAPH_HOST.rsplit('/', 1)[-1]}"
CONTAINER_POLL_INTERVAL = 5  # seconds
CONTAINER_POLL_MAX_ATTEMPTS = 36  # ~3 minutes max
REELS_MEDIA_TYPE = "REELS"


# ---------------------------------------------------------------------------
# Step 1 — Create media container
# ---------------------------------------------------------------------------


def create_container(
    ig_user_id: str,
    token: str,
    video_url: Optional[str] = None,
    is_resumable: bool = False,
    caption: str = "",
    file_path: Optional[str] = None,
) -> str:
    """Create a media container for a Reels video.
    Returns the container (creation) ID as a string."""
    body: dict = {
        "media_type": REELS_MEDIA_TYPE,
        "caption": caption,
    }
    # video_url is REQUIRED by the API even for resumable uploads
    # (used as a session identifier). For local files we pass a placeholder.
    if video_url:
        body["video_url"] = video_url
    else:
        fname = os.path.basename(file_path) if file_path else "upload.mp4"
        body["video_url"] = f"https://byteverdict.upload/{fname}"
    if is_resumable:
        body["upload_type"] = "resumable"

    url = f"{GRAPH_HOST}/{ig_user_id}/media"
    print(f"Creating media container (media_type={REELS_MEDIA_TYPE}, "
          f"{'video_url' if video_url else 'resumable'})...")
    print(f"  POST {url}")
    print(f"  Body: {json.dumps(body, indent=2)}")
    response = api_post(url, body, token)
    container_id = response.get("id")
    if not container_id:
        raise ApiError(f"Container creation failed, no id in response: {response}")
    print(f"  Container ID: {container_id}")
    return container_id


# ---------------------------------------------------------------------------
# Step 2 — Upload video (resumable local upload)
# ---------------------------------------------------------------------------


def upload_video_resumable(container_id: str, token: str, file_path: str) -> None:
    """Upload a local video file to Meta's resumable upload endpoint."""
    file_size = os.path.getsize(file_path)
    url = f"{UPLOAD_HOST}/{container_id}"
    print(f"Uploading {os.path.basename(file_path)} ({file_size / 1024 / 1024:.1f} MB) "
          f"to {UPLOAD_HOST}...")

    with open(file_path, "rb") as f:
        file_data = f.read()

    req = urllib.request.Request(
        url,
        data=file_data,
        headers={
            "Authorization": f"Bearer {token}",
            "offset": "0",
            "file_size": str(file_size),
            "Content-Type": "application/octet-stream",
        },
        method="POST",
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
                decoded = _decode_response(raw)
                # The upload endpoint returns {"success": true, "message": "..."}
                if not decoded.get("success"):
                    raise ApiError(f"Upload rejected: {decoded.get('message', str(decoded))}")
                print("  Upload successful.")
                return
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            if e.code in RETRYABLE_STATUS_CODES:
                print(f"  HTTP {e.code} (retriable). Retry {attempt}/{MAX_RETRIES}...")
                time.sleep(2 ** attempt)
                continue
            raise ApiError(f"Upload HTTP {e.code}: {body_text[:200]}")
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            print(f"  Upload error. Retry {attempt}/{MAX_RETRIES}...")
            time.sleep(2 ** attempt)
            continue
    raise ApiError("Upload exhausted retries")


# ---------------------------------------------------------------------------
# Step 2b — Poll container status
# ---------------------------------------------------------------------------


def poll_container_status(container_id: str, token: str) -> str:
    """Poll the container until FINISHED/PUBLISHED/ERROR/EXPIRED.
    Returns the final status string."""
    url = f"{GRAPH_HOST}/{container_id}?fields=status_code"
    print(f"Polling container {container_id} status "
          f"(max {CONTAINER_POLL_MAX_ATTEMPTS} attempts, "
          f"{CONTAINER_POLL_INTERVAL}s interval)...")
    last_status = "UNKNOWN"
    for attempt in range(1, CONTAINER_POLL_MAX_ATTEMPTS + 1):
        try:
            decoded = api_get(url, token)
            status = decoded.get("status_code", "UNKNOWN")
            last_status = status
            print(f"  [{attempt}/{CONTAINER_POLL_MAX_ATTEMPTS}] status_code={status}")
            if status in ("FINISHED", "PUBLISHED"):
                print(f"  Container ready ({status}).")
                return status
            if status in ("ERROR", "EXPIRED"):
                raise ApiError(f"Container ended with status={status}")
        except ApiError:
            raise
        except Exception as e:
            print(f"  Poll error: {e}. Retrying...")
        time.sleep(CONTAINER_POLL_INTERVAL)
    raise ApiError(
        f"Container did not finish within "
        f"{CONTAINER_POLL_MAX_ATTEMPTS * CONTAINER_POLL_INTERVAL}s. "
        f"Last status: {last_status}"
    )


# ---------------------------------------------------------------------------
# Step 3 — Publish container
# ---------------------------------------------------------------------------


def publish_container(ig_user_id: str, token: str, container_id: str) -> str:
    """Publish a media container. Returns the published media ID (IG Media ID)."""
    url = f"{GRAPH_HOST}/{ig_user_id}/media_publish"
    body = {"creation_id": container_id}
    print(f"Publishing container {container_id}...")
    print(f"  POST {url}")
    response = api_post(url, body, token)
    media_id = response.get("id")
    if not media_id:
        raise ApiError(f"Publish failed, no id in response: {response}")
    print(f"  Media ID: {media_id}")
    return media_id


# ---------------------------------------------------------------------------
# Look up IG user ID from token
# ---------------------------------------------------------------------------


# lookup_ig_user_id: use the shared implementation in ig_common (also used by
# refresh_ig_token.py) rather than a second, slightly different copy here.
lookup_ig_user_id = _shared_lookup_ig_user_id


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Post a 9:16 Reel to the ByteVerdict Instagram account "
                    "via the Instagram Graph API."
    )
    parser.add_argument("--token", help="Instagram User Access Token "
                                      "(or use cached in ig_state.json).")
    parser.add_argument("--ig-user-id", help="Instagram User ID (numeric) "
                                             "(or use cached).")
    parser.add_argument("--cache", action="store_true",
                        help="Cache token + IG user ID to ig_state.json for reuse.")
    video_group = parser.add_argument_group("video source")
    video_group.add_argument("--video", help="Local MP4 file path (resumable upload).")
    video_group.add_argument("--video-url", help="Public URL of the video "
                                                 "(skips local upload).")
    parser.add_argument("--caption", help="Reel caption text "
                                          "(include source attribution). Required unless --lookup-id.")
    parser.add_argument("--test", action="store_true",
                        help="Dry-run mode: print API calls without executing.")
    parser.add_argument("--lookup-id", action="store_true",
                        help="Look up IG user ID from token and cache it, then exit.")
    parser.add_argument(
        "--clip-id",
        help="Clip ID (e.g. tb005-c1). REQUIRED unless --lookup-id — used "
             "for the code-level duplicate-post guard, not just logging. "
             "This script refuses to post if this clip_id already has a "
             "successful Instagram post recorded (see post_dedup.py).",
    )
    args = parser.parse_args()

    if not args.lookup_id and not args.caption:
        parser.error("--caption is required unless --lookup-id is given")
    if not args.lookup_id and not args.clip_id:
        parser.error("--clip-id is required unless --lookup-id is given")

    # -------------------------------------------------------------------
    # Resolve token + IG user ID
    # -------------------------------------------------------------------
    token: Optional[str] = args.token
    ig_user_id: Optional[str] = args.ig_user_id

    state = load_state()
    if not token and "token" in state:
        token = state["token"]
        print("Using cached token.")
    if not ig_user_id and "ig_user_id" in state:
        ig_user_id = state["ig_user_id"]
        print("Using cached IG user ID.")

    if args.lookup_id:
        if not token:
            print("ERROR: --lookup-id requires --token.")
            return 1
        try:
            ig_user_id = lookup_ig_user_id(token)
            save_state(token, ig_user_id)
            print("Done. Now run the poster without --lookup-id.")
            return 0
        except ApiError as e:
            print(f"ERROR: {e}")
            return 1

    # Code-level duplicate-post guard — refuses and exits non-zero if this
    # clip_id already has a successful Instagram post recorded. Runs before
    # touching the video file or making any upload-related API call. Not
    # gated on --test: even a "dry run" caller should see the same refusal
    # a real run would give, so testing doesn't hide a real problem.
    post_dedup.check_not_already_posted(args.clip_id, "instagram")

    if not token:
        print("ERROR: No access token provided (-> --token) and none cached.")
        print("Get one from: https://developers.facebook.com/tools/explorer/")
        print("Select your Instagram app, then 'Generate Access Token'.")
        print("Required scopes: instagram_business_basic, instagram_business_content_publish")
        return 1

    if not ig_user_id:
        print("ERROR: No Instagram User ID provided (-> --ig-user-id) and none cached.")
        print("Get it via: GET https://graph.instagram.com/me?fields=id&access_token=<TOKEN>")
        print("Or pass --lookup-id to do this automatically.")
        return 1

    # -------------------------------------------------------------------
    # Cache if requested or if not yet cached
    # -------------------------------------------------------------------
    if args.cache:
        save_state(token, ig_user_id)
    elif not os.path.exists(STATE_FILE):
        # Auto-cache on first successful run with explicit token + id
        save_state(token, ig_user_id)

    # -------------------------------------------------------------------
    # Validate video source
    # -------------------------------------------------------------------
    if args.video and args.video_url:
        print("ERROR: Pass either --video or --video-url, not both.")
        return 1

    if args.test:
        print("=== TEST MODE — no API calls will be made ===")
        if args.video:
            file_path = args.video
            if not os.path.isfile(file_path):
                print(f"ERROR: File not found: {file_path}")
                return 1
            print(f"Video file: {file_path} ({os.path.getsize(file_path) / 1024 / 1024:.1f} MB)")
        elif args.video_url:
            print(f"Video URL: {args.video_url}")
        else:
            print("ERROR: Pass --video or --video-url.")
            return 1
        print(f"Caption: {args.caption}")
        print(f"IG User ID: {ig_user_id}")
        print(f"Token: {'*' * 10}…{token[-4:] if token else 'NONE'}")
        print()
        print("Planned API calls:")
        if args.video:
            print(f"  1. POST {GRAPH_HOST}/{ig_user_id}/media")
            print(f"     body: {{media_type='{REELS_MEDIA_TYPE}', "
                  f"upload_type='resumable', caption=<encoded>}}")
            print(f"  2. POST {UPLOAD_HOST}/{{CONTAINER_ID}}")
            print(f"     (resumable upload of {args.video})")
        else:
            print(f"  1. POST {GRAPH_HOST}/{ig_user_id}/media")
            print(f"     body: {{media_type='{REELS_MEDIA_TYPE}', "
                  f"video_url='{args.video_url}', caption=<encoded>}}")
        print(f"  2. GET {GRAPH_HOST}/{{CONTAINER_ID}}?fields=status_code")
        print(f"     (poll until FINISHED/PUBLISHED)")
        print(f"  3. POST {GRAPH_HOST}/{ig_user_id}/media_publish")
        print(f"     body: {{creation_id=<CONTAINER_ID>}}")
        return 0

    # Resolve video handling mode
    if args.video:
        file_path = args.video
        if not os.path.isfile(file_path):
            print(f"ERROR: File not found: {file_path}")
            return 1
        is_resumable = True
        video_url = None
    elif args.video_url:
        video_url = args.video_url
        is_resumable = False
        file_path = None
    else:
        print("ERROR: Pass --video or --video-url.")
        return 1

    # -------------------------------------------------------------------
    # Run the publish flow
    # -------------------------------------------------------------------
    print(f"\nPublishing Reel to @byteverdict...")
    print(f"  Video: {'local ' + file_path if file_path else video_url}")
    print(f"  Caption: {args.caption[:80]}{'...' if len(args.caption) > 80 else ''}")

    try:
        # Step 1: Create container
        container_id = create_container(
            ig_user_id=ig_user_id,
            token=token,
            video_url=video_url,
            is_resumable=is_resumable,
            caption=args.caption,
            file_path=file_path,
        )

        # Step 2: Upload (if local/resumable)
        if is_resumable:
            print()
            upload_video_resumable(container_id, token, file_path)

        # Step 3: Poll status
        print()
        final_status = poll_container_status(container_id, token)

        # Step 4: Publish
        print()
        media_id = publish_container(ig_user_id, token, container_id)

        # -------------------------------------------------------------------
        # Result
        # -------------------------------------------------------------------
        print()
        print("=" * 60)
        print("PUBLISHED")
        print("=" * 60)
        print(f"  Reel URL:    https://www.instagram.com/reel/{media_id}/")
        print(f"  Media ID:    {media_id}")
        print(f"  Container:   {container_id}")
        print(f"  Status:      {final_status}")
        print(f"  Profile:     https://www.instagram.com/byteverdict/")

        # Record success ONLY here, after the API has confirmed publish —
        # never speculatively. This is what the guard above checks on the
        # next attempt for this clip_id.
        post_dedup.record_posted(
            args.clip_id, "instagram", media_id,
            f"https://www.instagram.com/reel/{media_id}/",
        )
        return 0

    except ApiError as e:
        print(f"\nFAILED: {e}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
