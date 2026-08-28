# YouTube Poster — Post-Mortem

**Date:** 2026-08-25
**Channel:** ByteVerdict (3 subscribers)
**Scope:** youtube.upload (OAuth Desktop app)
**Client ID:** `587724207587-k4ravfbkj5rvkeage0ubcu7s1hrgc3v6`

Posted one Short (TB-001-C1, Iran war footage) as unlisted first; followed with two public posts (C2 Alibaba, C3 Canada trade). All three uploads succeeded. No API errors, no retries needed. **Later: C1 flipped to public.** Token refreshed (expired, scope mismatch resolved).

## What posted

| Clip | Title | Privacy | Video ID | URL |
|------|-------|---------|----------|-----|
| TB-001-C1 | ByteVerdict — Trump on Iran: "completely collapsing" | **public** (was unlisted) | `__dTM3fnN0I` | https://youtu.be/__dTM3fnN0I |
| TB-001-C2 | ByteVerdict — Alibaba Wan3.0 AI video model | public | `SSVwuybfsJc` | https://youtu.be/SSVwuybfsJc |
| TB-001-C3 | ByteVerdict — Trump threatens 50% tariffs on Canadian cars | public | `4FX9ymtfOAA` | https://youtu.be/4FX9ymtfOAA |

## What didn't

- **Instagram Reels:** skipped all three — no valid IG token at post time (expired 07:00 PDT). Manual posting needed.
- **TikTok:** skipped all three — no TikTok automation tool available. Manual posting needed.

## Token state

- `token.json`: valid, **refreshed** (was expired with wrong scope `youtube` → refreshed with correct scope). New expiry 2026-08-25T16:38:12Z. OAuth flow worked cleanly.
- `ig_state.json`: token expired 2026-08-25 07:00 PDT. `ig_user_id` still empty. IG automation blocked until new token.
- `ig_token.json`: token field empty — no long-lived IG token obtained yet. User provided new token but it failed to decrypt ("could not be decrypted").

## Corruption recovery

- `POST-MORTEM.md`: file was truncated mid-write at 235 bytes ("Posted one Shor..."). Reconstructed from TB-001 posting logs. Now 2,190 bytes, complete.
- `tb003_carney_9x16.mp4`: 0 bytes (corrupt/missing). Re-cut from source (CBC, 4:30–5:15) with correct vertical scaling (1080×1920), re-composited with `tb003_carney_overlay.png`. Master: 9.36 MB.
- `tb003_carney` platform exports: 0 bytes → regenerated (tiktok/ytshorts/igreels), all 9.20 MB, 1080×1920.
- `tb003_bbc_strike` platform exports: were 1280×720 landscape (exported from landscape cut). Regenerated from correct 1080×1920 master. All 13.65 MB.
- BBC ig reels export: `moov atom not found` (timeout during write) → regenerated.
- TB-001-C2 overlay: attribution said "Source: Reuters" but footage is Bloomberg Tech. Regenerated `tb001_c2_alibaba_wan3_overlay.png` with "Source: Bloomberg Tech".

## Issues flagged

1. **C1 flipped to public** — war content, highest sensitivity. Done. Monitor for Content ID / age-restriction.
2. **Attribution discrepancy on C2 — RESOLVED** — overlay now says "Source: Bloomberg Tech". Done.
3. **Reused-content signal** — C3 and C3b both from Reuters. Watch account-level reused-content pattern as more clips accumulate.
4. **IG gap** — no valid token. User provided new token but it failed to decrypt. Need proper OAuth flow.

## Network logo check

- **BBC strike (TB-003-c1):** Vision analysis of full timeline — no BBC logo/badge/bug found in any frame. Original landscape source (1280×720) → 9:16 vertical crop likely eliminated it. Logo blur: **not applicable**.
- **Carney (TB-003-c2):** Vision analysis of full timeline — no CBC/CBCNN logo/badge/bug found in any frame. Same crop elimination. Logo blur: **not applicable**.

## Status

- YouTube: 3/3 posted, all public. C1 flipped 2026-08-25.
- Instagram: 0/3 posted. Manual queue pending (no valid token).
- TikTok: 0/3 posted. Manual queue pending.
- Channel: 10 videos live on ByteVerdict (C1 + earlier uploads). Sub count: 3.

*Last updated: 2026-08-25*
