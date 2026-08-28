#!/usr/bin/env python3
"""Shared Instagram Graph API helpers for ig_post.py and refresh_ig_token.py.

Consolidates what used to be two diverging copies of state load/save (different
schemas — one dropped the other's fields on write) and two different
lookup_ig_user_id implementations (one without retry logic). Also fixes a real
race: both callers used to write to the *same* "ig_state.json.tmp" path with no
unique suffix, so two overlapping writers (e.g. a manual refresh while a
scheduled post is mid-run) could stomp each other's temp file and crash one of
them with FileNotFoundError, or interleave a corrupt state file.
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "credentials")
STATE_FILE = os.path.join(CREDENTIALS_DIR, "ig_state.json")
API_VERSION = "v26.0"
GRAPH_HOST = f"https://graph.instagram.com/{API_VERSION}"

MAX_RETRIES = 5
RETRYABLE_STATUS_CODES = (500, 502, 503, 504, 507)


class ApiError(Exception):
    """Non-retryable API error."""
    pass


def _decode_response(raw: bytes) -> dict:
    """Parse JSON response; raise ApiError if it contains an 'error' key."""
    decoded = json.loads(raw.decode("utf-8"))
    if "error" in decoded:
        raise ApiError(decoded["error"].get("message", json.dumps(decoded["error"])))
    return decoded


def _request_with_retry(req: urllib.request.Request, timeout: int) -> dict:
    """Shared retry loop used by both api_get and api_post — retries on
    transient HTTP status codes and network/parse errors with exponential
    backoff, raises ApiError on non-retryable failures or exhausted retries."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return _decode_response(resp.read())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            if e.code in RETRYABLE_STATUS_CODES:
                last_exc = e
                print(f"  HTTP {e.code} (retriable). Retry {attempt}/{MAX_RETRIES} "
                      f"in {2**attempt}s...")
                time.sleep(2 ** attempt)
                continue
            raise ApiError(f"HTTP {e.code}: {body_text[:200]}")
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            last_exc = e
            print(f"  Network/parse error. Retry {attempt}/{MAX_RETRIES} "
                  f"in {2**attempt}s...")
            time.sleep(2 ** attempt)
            continue
    raise ApiError(f"Exhausted retries: {last_exc}")


def api_post(url: str, body: dict, token: str, timeout: int = 30) -> dict:
    """POST JSON to a Graph API endpoint with Bearer token. Retries on transient errors."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    return _request_with_retry(req, timeout)


def api_get(url: str, token: str, timeout: int = 30) -> dict:
    """GET a Graph API endpoint with Bearer token. Retries on transient errors
    (previously this did not retry at all, unlike api_post — a single
    transient 503 during e.g. container-status polling would abort an
    otherwise-successful post after the video had already fully uploaded)."""
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    return _request_with_retry(req, timeout)


# ---------------------------------------------------------------------------
# State / caching
# ---------------------------------------------------------------------------


def load_state() -> dict:
    """Load cached token + ig_user_id if available."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(token: str, ig_user_id: str, notes: str = "") -> None:
    """Persist token + IG user ID to ig_state.json.

    One schema, one writer — previously ig_post.py and refresh_ig_token.py each
    wrote a different set of fields via a full-file overwrite, so whichever
    script ran second silently dropped the other's fields (e.g. _notes/_expired).
    """
    state = {
        "token": token,
        "ig_user_id": ig_user_id,
        "cached_at": int(time.time()),
        "_notes": notes or "Token cached by clips-channel pipeline.",
        "_expired": False,
    }
    # Unique temp filename (pid + monotonic-ish timestamp) — avoids two
    # concurrent writers (e.g. a manual refresh racing a scheduled post)
    # colliding on the same "ig_state.json.tmp" path.
    tmp = f"{STATE_FILE}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)
    print(f"Cached token + IG user ID in {STATE_FILE}")


def lookup_ig_user_id(token: str, timeout: int = 30) -> str:
    """Look up the Instagram user ID (and print username/account type) for a
    token. Uses the shared retry-capable api_get instead of a raw one-shot
    urllib call, so a transient network blip doesn't abort a token refresh."""
    url = f"{GRAPH_HOST}/me?fields=id,username,account_type"
    print("Looking up IG User ID...")
    print(f"  GET {url}")
    data = api_get(url, token, timeout=timeout)
    ig_id = data.get("id")
    if not ig_id:
        raise ApiError(f"No id in response: {data}")
    print(f"  IG User ID: {ig_id}")
    print(f"  Username:   {data.get('username', '')}")
    print(f"  Account:    {data.get('account_type', '')}")
    return ig_id
