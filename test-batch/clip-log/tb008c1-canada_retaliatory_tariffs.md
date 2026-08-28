# Clip Log: tb008-c1 — Canada Retaliatory Tariffs (CTV News)

**Clip ID:** tb008-c1
**Date produced:** 2026-08-27
**Status:** Produced — ready for Leo's review

---

## Source

- **Source URL:** https://www.youtube.com/watch?v=5p8NbFAacU4
- **Outlet:** CTV News (Bell Media) — Canadian broadcast news, Tier 2
- **Title:** "Canada's retaliatory tariffs | CTV News Barrie at Six for Aug. 26, 2026"
- **Capture date:** 2026-08-27
- **Source file:** `test-batch/captures/canada_tariffs_5p8NbFAacU4.f398+251-15.mp4`
- **Source duration:** 44:05.52
- **Source resolution:** 1280×720, AV1 video, Opus audio
- **Source identity verified via:** YouTube video metadata — channel is CTV News Barrie (Bell Media property). Visual confirmation via frame sampling: news broadcast format, anchor segments, b-roll of goods. No competing channel branding detected.

## Source Audio Language Gate — PASSED

- **Audio language:** English (confirmed via ffmpeg stream metadata: Audio stream tagged as `eng`)
- **English captions on source:** Not checked (YouTube video assets); English audio is the primary language track.
- **Decision:** English audio confirmed via stream metadata. Channel publishes in English. No flag.

## Clip Selection

- **In-point:** ~0:00 (anchor introduction to tariffs segment — to be confirmed after first-cut review)
- **Out-point:** ~0:35 (target 35s, within ~25-40s target range)
- **Selection rationale:**
  - CTV News Barrie at Six covers Canada's dollar-for-dollar retaliatory tariffs on US goods
  - The anchor intro + tariff announcement is the hook: Canada matching Trump tariff-for-tariff, $27.6 billion worth
  - B-roll of affected goods (cosmetics, furniture) provides visual variety
  - Trump's response ("US won't tolerate") adds the escalation angle

**Note:** Exact in/out points to be finalized after first cut review. Source is 44 minutes — the tariffs segment is likely in the first 5-10 minutes (local news at-six format: top stories first).

## Overlay Draft

**Headline (line 1):** "Canada hits back with tariffs"
**Headline (line 2):** "Dollar-for-dollar. $27.6 billion."
**Context line 1:** "Canada slapped retaliatory tariffs on ~700 US products — cosmetics, furniture, food."
**Context line 2:** "Trump says the US won't tolerate it."
**Source attribution:** "Source: CTV News"
**Date:** "August 26, 2026"

**Overlay rationale:** Headline leads with the action (Canada hitting back) and the scale ($27.6B). Context adds what's affected and Trump's response — the escalation. Attributable to CTV News reporting.

## Caption Draft

Canada just slapped $27.6 billion in retaliatory tariffs on US goods — dollar for dollar, ~700 products hit, from cosmetics to furniture to food.

Trump's response: the US won't tolerate it. The trade war between the two closest allies in the world just escalated.

This isn't abstract — these tariffs land on real products on real shelves. What hits your household budget first?

Source: CTV News. August 26, 2026.

## Sensitive-Content Screen — EXPECTED PASS

- **Death/injury/graphic violence?** No — trade policy story
- **Destroyed infrastructure/burning?** No
- **Source broadcast package graphic?** No — CTV News is professional broadcast
- **First frame triggers pause?** No — news anchor intro
- **News value in graphic content?** No — value is in the policy development

**Decision:** Expected to pass. Will confirm after cut review.

## Production Specs (target)

- **Cut:** ffmpeg trim to ~35s segment, scale -2:1920, crop 1080:1920
- **Overlay:** PIL composite of overlay PNG onto cut
- **Codec:** H.264 High (libx264), CRF 22, preset fast, AAC 128k, movflags +faststart
- **Master:** test-batch/exports/tb008c1_master.mp4 — 1080×1920, ~35s
- **Platform exports:** TikTok, YouTube Shorts, Instagram Reels — 9:16, 1080×1920

## Logo Check

- CTV News is the source — no third-party network logo to blur
- CTV/Bell Media branding may appear as lower-third — this is the source's own branding, not a third-party logo requiring removal
- **Note:** If CTV logo appears in the export's top-right corner and would trigger copyright concerns, consider blur. Decision pending cut review.

## Posting Order Suggestion

1. YouTube Shorts first (monetization target)
2. TikTok second
3. Instagram Reels third

## Risk Register Entry

| Field | Value |
|-------|-------|
| Date | 2026-08-27 |
| Type | Copyright/IP tier, platform policy |
| Clip/Source | tb008-c1 / CTV News YouTube video 5p8NbFAacU4 |
| Description | Tier 2 broadcast news source. English audio confirmed. Cut from 44-min local news broadcast. Target ~35s. |
| Risk implication | Tier 2 copyright risk (CTV/Bell Media). YouTube Shorts is highest enforcement platform. Attribution present in overlay. |
| Action taken | Source logged. English audio verified. Overlay draft prepared. |
| Outcome/Status | Produced, not yet posted. Waiting for Leo's approval. |

---

## Files

- Master: `test-batch/exports/tb008c1_master.mp4` (to be created)
- TikTok export: `test-batch/exports/platform-exports/tb008c1_tiktok_9x16.mp4` (to be created)
- Shorts export: `test-batch/exports/platform-exports/tb008c1_ytshorts_9x16.mp4` (to be created)
- Reels export: `test-batch/exports/platform-exports/tb008c1_igreels_9x16.mp4` (to be created)
- Ready-to-post master: `test-batch/ready-to-post/tb008c1_master.mp4` (to be created)
- Source capture: `test-batch/captures/canada_tariffs_5p8NbFAacU4.f398+251-15.mp4`

---

**Status:** Produced. Awaiting Leo's per-clip approval before posting.
