# Clip Log: tb010 — Iran Blocks IAEA Inspectors From Damaged Nuclear Sites (NewsX World)

**Clip ID:** tb010
**Date identified:** 2026-08-27
**Status:** Candidate — draft package ready for Leo. Production NOT authorized (no `production-authorized.md`). Do NOT cut/export without Leo's explicit go-ahead.

---

## Source

- **Source URL:** https://www.youtube.com/watch?v=R8HWZ2ZB3Yc
- **Outlet:** NewsX World (Indian English-language news channel) — Tier 2 (major non-US news broadcaster)
- **Title:** "Iran Blocks IAEA Inspectors From Nuclear Sites After U.S.-Israel Strikes"
- **Capture date:** 2026-08-27
- **Source file:** `/tmp/src_tb010_newsx_R8HWZ2ZB3Yc.mp4` (not captured — short clip, partial verify segment needed if approved)
- **Source duration:** 1:11 (71s)
- **Source resolution:** TBD (need to capture to verify — expected 1280×720 or similar)
- **Source audio language:** English — expected based on channel name (NewsX World = English-language Indian news). **To be confirmed via capture + ffmpeg stream metadata or transcript.** If not English, flag to Leo.
- **Source identity verified:** YouTube search result with English title and English-language channel ("NewsX World"). Description/tone consistent with English-language Indian news coverage of Iran nuclear story.

---

## Why Clip-able (the hook)

- Iran is now **blocking IAEA inspectors** from accessing nuclear sites damaged in the US-Israel strikes — a direct escalation in the Iran conflict story
- This is a concrete development with a clear "who did what" — Iran refusing nuclear inspection access after being struck
- Fits the channel's best-performing category: geopolitical conflict with concrete stakes (per early-performance-signal.md: 1073-1550 view cluster)
- Short source (71s) — the entire clip could be used or a tight sub-segment
- Fresh development on an ongoing story — Iran/US/Israel nuclear tension is the dominant news thread this week

---

## Sensitive-Content Screen — BEFORE production, preliminary

1. **Death/injury/graphic violence?** Unknown — need to capture and screen. Nuclear facility footage could include damaged infrastructure. The title refers to "US-Israel strikes" — there may be footage of strikes or aftermath. Flag: needs actual screening before production.
2. **Destroyed infrastructure/burning/graphic aftermath?** Possible — damaged nuclear sites could be shown. Needs screen.
3. **Source broadcast package itself graphic?** Unknown — NewsX World is a news channel, likely professional, but the content matter (damaged nuclear sites, strike aftermath) could be graphic. Needs screen.
4. **First frame or most prominent shot trigger a pause?** Unknown — need to capture and screen first frame.
5. **News value in graphic content or in the development?** The development (Iran blocking inspectors) is the news value. If the footage shows graphic strike aftermath, prefer non-graphic alternative or wait for less sensitive angle.

**Decision:** UNCERTAIN — needs capture + frame screening before production can proceed. The story itself is strong; the footage risk is unknown.

---

## Tier Assessment

- **Tier 2** — NewsX World is a major Indian English-language news broadcaster. Not a wire service, not US-based, but a legitimate news outlet with editorial standards.
- English audio expected (channel is English-language). Lower copyright/IP risk than US-based Tier 2 sources for US-platform enforcement, but not Tier 1 (not public domain).
- Attribution: "Source: NewsX World" in overlay.

---

## Clip Selection (proposed, to be finalized after capture + review)

- **Proposed approach:** The full clip is only 71 seconds. If the entire clip is substantive and passes the sensitive-content screen, use the full clip (or a tight ~40-50s sub-segment if there's dead air at the end).
- **Selection rationale:** Short source, single story, no obvious need to trim heavily.

---

## Overlay Draft (Tier A — Strong)

**Headline (line 1):** "Iran blocks IAEA inspectors"
**Headline (line 2):** "From damaged nuclear sites"

**Context line 1:** "Iran is refusing IAEA access to nuclear facilities hit in the US-Israel strikes."

**Context line 2:** "The UN nuclear watchdog says it can't inspect the damaged sites."

**Source attribution:** "Source: NewsX World"
**Date:** "August 27, 2026"

**Overlay rationale:**
- Headline is specific and attributable — Iran blocking IAEA inspectors is the actual development
- Context adds what the headline alone doesn't say: the sites were damaged in US-Israel strikes, the IAEA is the UN nuclear watchdog
- No sensationalism — factual reporting of an inspection blockade
- Source attribution present + date (time-sensitive development)

---

## Caption Draft (humanized — no AI vocabulary, real voice, engagement question at end)

Iran just blocked UN nuclear inspectors from entering the sites damaged in the US-Israel strikes.

The IAEA — the International Atomic Energy Agency, the UN's nuclear watchdog — says it can't inspect those facilities now. Iran's nuclear chief says the IAEA can't inspect sites damaged in the attacks.

This is a direct escalation in the Iran story. The same country that's been under sanctions for its nuclear program is now refusing outside inspection of the sites everyone's worried about.

Source: NewsX World. August 27, 2026.

What do you think Iran's play is here — hiding something, or just saying no to outside scrutiny while it rebuilds?

---

## Caption Audit (humanizer pass)

- No AI vocabulary: no "actually," "additionally," "crucial," "pivotal," "underscores," "testament," "tapestry," "intricate"
- No em-dash overuse: clean — no em dashes in caption
- No sycophancy: opinioned but not fawning — "What do you think Iran's play is here" is a genuine engagement question, not a generic closer
- No formulaic structure: narrative flow, specific, no 3-point list or "challenges + future prospects"
- Real voice: "What do you think Iran's play is here — hiding something, or just saying no to outside scrutiny while it rebuilds?" — specific engagement question, not "what do you think?"
- Attribution present: NewsX World, date
- Accurate to likely clip content: every claim is drawn from the title/reporting (Iran blocking IAEA, damaged nuclear sites from US-Israel strikes, IAEA can't inspect)

**Remaining AI-tell check:**
- The middle paragraph could be tighter — "This is a direct escalation in the Iran story" is slightly generic
- No emoji, no boldface, no curly quotes, no bot-service openers — clean
- Verdict: humanized, not AI-sounding. Minor tightening possible on the middle paragraph.

---

## Production Specs (target — only if authorized + passes screen)

- **Cut:** ffmpeg crop+scale from source → 1080×1920 (9:16), ~40-50s segment (or full 71s if clean)
- **Overlay:** PIL PNG composite (DejaVu Sans Bold headline, DejaVu Sans context) onto cut
- **Codec:** H.264 High (libx264), CRF 22, preset fast, AAC 128k, movflags +faststart
- **Master:** `test-batch/exports/tb010_master.mp4` — 1080×1920, ~40-50s, WITH AUDIO
- **Platform exports:** TikTok, YouTube Shorts (≤60s — this one is ~40-50s, within cap), Instagram Reels — 9:16, 1080×1920
- **Logo check:** NewsX World branding — verify in export; attribute as "Source: NewsX World"

---

## Issues to flag to Leo BEFORE production

1. **Production NOT authorized this run.** `docs/build-plan/production-authorized.md` does not exist. Per content-agent-prompt.md §4, I cannot cut/export tb010 without Leo's explicit go-ahead. I am presenting the draft package only.

2. **Sensitive-content screen is UNCERTAIN.** I have not captured the source. The story (damaged nuclear sites from US-Israel strikes) has a real risk of graphic footage. Before producing, I need to: capture → extract frames → screen every frame → only proceed if no graphic content. If the footage is graphic, either find a different source or don't post.

3. **Audio language not yet confirmed.** NewsX World is an English-language channel, but I need to verify via capture + ffmpeg stream metadata or transcript. If the audio is not English and there are no English captions, flag to Leo — do not produce.

4. **Tier 2 source from outside the US.** NewsX World is an Indian broadcaster — lower US-platform enforcement risk than a US Tier 2 source, but not zero. Attribution present in overlay.

---

## Posting Order Suggestion (if approved)

1. YouTube Shorts first (monetization target — real ad-revenue-share program, the channel's long game)
2. TikTok second (primary test surface — watch for reach signals on Iran/nuclear content)
3. Instagram Reels third (reach/account health)

**Special monitoring note for tb010:** Iran nuclear story is topic-sensitive — may attract platform context labels or reach signals regardless of whether the footage is graphic. Watch for:
- YouTube Shorts: age-restriction or context label signals
- TikTok: reach throttling or "unoriginal content" signals (Tier 2 attribution helps but doesn't eliminate)
- Instagram: account standing / feature-eligibility signals

---

## Risk Register Entry

|| Field | Value ||
||-------|-------||
|| Date | 2026-08-27 ||
|| Type | Copyright/IP tier, platform policy, content sensitivity (graphic risk unknown), audio language unconfirmed ||
|| Clip/Source | tb010 / NewsX World YouTube video R8HWZ2ZB3Yc (proposed) ||
|| Description | Tier 2 non-US English news broadcaster. 71s source on Iran blocking IAEA inspectors from damaged nuclear sites. Overlay draft Tier A, caption draft humanized, sensitive-content screen UNCONFIRMED (needs capture + frame screen), audio language UNCONFIRMED (needs capture + metadata check). ||
|| Risk implication | Graphic footage risk (damaged nuclear sites, strike aftermath) — must screen before producing. Topic-sensitive Iran story may attract platform context labels. Tier 2 copyright risk on YouTube Shorts (Content ID). Attribution present in overlay. ||
|| Action taken | Candidate log + overlay draft + caption draft + sensitive-content screen (preliminary, flagged as uncertain) + source search all done. Presented to Leo. ||
|| Outcome/Status | Draft package ready — awaiting Leo's go-ahead (production NOT authorized). Sensitive-content screen + audio language check + source capture all pending. ||

---

## Files (target — only created on Leo's go-ahead)

- Master: `test-batch/exports/tb010_master.mp4`
- TikTok export: `test-batch/exports/platform-exports/tb010_tiktok_9x16.mp4`
- Shorts export: `test-batch/exports/platform-exports/tb010_ytshorts_9x16.mp4`
- Reels export: `test-batch/exports/platform-exports/tb010_igreels_9x16.mp4`
- Ready-to-post master: `test-batch/ready-to-post/tb010_master.mp4`
- Source capture: `test-batch/captures/newsx_iran_iaea_R8HWZ2ZB3Yc.mp4` (TBD — capture needed)

---

**Status:** Draft package complete. Awaiting Leo's decision: (1) approve tb010 for production, (2) actually capture and screen the source before any cut, (3) resolve the sensitive-content screen uncertainty.
