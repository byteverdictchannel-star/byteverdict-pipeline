#!/usr/bin/env python3
"""Exchange a short-lived Instagram token for a long-lived one (60 days), and
refresh an existing long-lived token before it expires.

Two operations:
  --exchange TOKEN   Turn a short-lived Graph API Explorer token into a
                      long-lived one and cache it via ig_common.save_state.
  --refresh           Refresh the currently cached long-lived token in place
                      (extends another ~60 days). Only works on a token that's
                      already long-lived and at least 24h old.

Requires META_APP_ID / META_APP_SECRET (or FB_APP_ID / FB_APP_SECRET) in
~/.hermes/.env — already present there as of 2026-08-26.

Usage:
  python3 ig_token_exchange.py --exchange "IGAA..."   # one-time, needs a
                                                        # fresh short-lived
                                                        # token from
                                                        # developers.facebook.com/tools/explorer/
  python3 ig_token_exchange.py --refresh               # run periodically
                                                        # (cron), no input needed
"""

import argparse
import os
import sys
import urllib.parse
import urllib.request

from ig_common import ApiError, _request_with_retry, load_state, save_state, lookup_ig_user_id

HERMES_ENV = os.path.expanduser("~/.hermes/.env")
FB_GRAPH_HOST = "https://graph.facebook.com/v21.0"
IG_GRAPH_HOST = "https://graph.instagram.com/v21.0"


def _oauth_get(url: str, timeout: int = 30) -> dict:
    """GET an OAuth endpoint where credentials are in the query string, not a
    Bearer header (unlike ig_common.api_get, which always sends one)."""
    req = urllib.request.Request(url)
    return _request_with_retry(req, timeout)


def _load_app_credentials() -> tuple[str, str]:
    """Read META_APP_ID/META_APP_SECRET (or FB_APP_ID/FB_APP_SECRET) from
    ~/.hermes/.env. Returns (app_id, app_secret)."""
    if not os.path.exists(HERMES_ENV):
        raise ApiError(f"{HERMES_ENV} not found — can't read app credentials.")
    app_id = app_secret = None
    with open(HERMES_ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith(("META_APP_ID=", "FB_APP_ID=")) and not app_id:
                app_id = line.split("=", 1)[1].strip()
            elif line.startswith(("META_APP_SECRET=", "FB_APP_SECRET=")) and not app_secret:
                app_secret = line.split("=", 1)[1].strip()
    if not app_id or not app_secret:
        raise ApiError(
            "META_APP_ID/META_APP_SECRET (or FB_APP_ID/FB_APP_SECRET) not found in "
            f"{HERMES_ENV} — required for the long-lived token exchange."
        )
    return app_id, app_secret


def exchange_for_long_lived(short_lived_token: str) -> str:
    """Exchange a short-lived token for a long-lived one (~60 days)."""
    app_id, app_secret = _load_app_credentials()
    params = urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token,
    })
    url = f"{FB_GRAPH_HOST}/oauth/access_token?{params}"
    print("Exchanging short-lived token for a long-lived one...")
    data = _oauth_get(url)
    long_token = data.get("access_token")
    if not long_token:
        raise ApiError(f"No access_token in exchange response: {data}")
    expires_in = data.get("expires_in")
    print(f"  Got long-lived token, expires_in={expires_in}s (~{(expires_in or 0)/86400:.0f} days)")
    return long_token


def refresh_long_lived(current_token: str) -> str:
    """Refresh an already-long-lived token in place (extends another ~60 days).
    Must be at least 24h old and not yet expired."""
    params = urllib.parse.urlencode({
        "grant_type": "ig_refresh_token",
        "access_token": current_token,
    })
    url = f"{IG_GRAPH_HOST}/refresh_access_token?{params}"
    print("Refreshing long-lived token...")
    data = _oauth_get(url)
    new_token = data.get("access_token")
    if not new_token:
        raise ApiError(f"No access_token in refresh response: {data}")
    expires_in = data.get("expires_in")
    print(f"  Refreshed, expires_in={expires_in}s (~{(expires_in or 0)/86400:.0f} days)")
    return new_token


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exchange", metavar="TOKEN", help="Short-lived token to exchange")
    parser.add_argument("--refresh", action="store_true", help="Refresh the cached long-lived token")
    args = parser.parse_args()

    if not args.exchange and not args.refresh:
        parser.error("pass --exchange TOKEN or --refresh")

    try:
        if args.exchange:
            long_token = exchange_for_long_lived(args.exchange)
        else:
            state = load_state()
            current = state.get("token")
            if not current:
                print("ERROR: no cached token to refresh. Run --exchange first.", file=sys.stderr)
                return 1
            long_token = refresh_long_lived(current)

        ig_user_id = lookup_ig_user_id(long_token)
        save_state(long_token, ig_user_id, notes="Long-lived token (fb_exchange_token / ig_refresh_token). "
                                                   "Auto-refreshed weekly by cron — see ig_token_exchange.py --refresh.")
        print("Done. Long-lived token cached.")
        return 0
    except ApiError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
