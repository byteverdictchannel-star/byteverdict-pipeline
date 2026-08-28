#!/usr/bin/env python3
"""ByteVerdict IG token refresh utility.

Takes a new token from Meta Graph API Explorer and caches it to credentials/ig_state.json.
Usage: python3 refresh_ig_token.py --token "IGAA..."
"""

import sys

from ig_common import ApiError, lookup_ig_user_id, save_state, STATE_FILE  # noqa: F401  (STATE_FILE kept for callers that import it from here)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Refresh IG token for @byteverdict and cache it."
    )
    parser.add_argument("--token", help="New IG access token from Meta Graph API Explorer")
    args = parser.parse_args()

    token = args.token
    if not token:
        print("Usage: python3 refresh_ig_token.py --token \"IGAA...\"")
        print("Get a token from: https://developers.facebook.com/tools/explorer/")
        print("Select your Instagram app -> Generate Access Token")
        print("Required scopes: instagram_business_basic, instagram_business_content_publish")
        return 1

    try:
        ig_user_id = lookup_ig_user_id(token)
    except ApiError as e:
        print(f"ERROR: {e}")
        return 1

    save_state(token, ig_user_id, notes="Token from Meta Graph API Explorer. Short-lived — refresh before expiry.")
    print("\nDone. Token cached. Now test with:")
    print("  python3 ig_post.py --lookup-id  # should succeed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
