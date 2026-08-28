# Posting Log: TB-002-C3 (Wrong-Way Crash)

**Date:** 2026-08-26 (TikTok retry; YouTube originally posted 2026-08-25)

## Platforms Attempted

### YouTube Shorts
- **Status:** ALREADY POSTED (2026-08-25)
- **Video ID:** 6es-NS73oiA
- **URL:** https://youtu.be/6es-NS73oiA
- **Privacy:** public

### TikTok
- **Status:** FAILED (both attempts)
- **Error:** Publish failed — TikTok API returned status_code=5, status_msg="Invalid parameters"
- **Details:** Upload completed but publish step rejected on both attempts (2026-08-25 and 2026-08-26).
- **Timestamp:** 2026-08-26 (retry)

### Instagram Reels
- **Status:** SKIPPED
- **Reason:** IG access token expired (401 Unauthorized). No IG user ID cached. Was already pending manual post from prior session.
- **Action needed:** Leo to re-authorize IG OAuth in a real browser, then cache token + IG user ID.

### X/Twitter
- **Status:** SKIPPED
- **Reason:** xurl not installed.

## Description Used
A driver went the wrong way on a highway and triggered a chain-reaction crash — and the footage shows exactly how fast a single mistake turns into a multi-car pileup.

Wrong-way entries are rare and catastrophic. Most happen at night on divided highways, where drivers have seconds, not minutes, to react. The video doesn't need a voiceover — the sequence speaks for itself.

Source: Sky News. Have you ever seen a wrong-way driver on the road? What did you do?

## Errors
- TikTok: publish step failed with "Invalid parameters" (status_code=5) on both attempts. Video uploaded but not published.

## Next Actions
- TikTok: retry posting — may be a transient API issue or title/caption parameter issue. If it fails again, post manually.
- IG Reels: manual post needed until OAuth re-authorized
- Monitor YouTube (already live)
