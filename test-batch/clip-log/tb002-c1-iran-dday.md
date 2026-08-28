# Clip Log Entry TB-002-C1

**Clip ID:** TB-002-C1
**Date produced:** 2026-08-25
**Date posted:** 2026-08-25

---

## Source

| Field | Value |
|-------|-------|
| Source URL | BBC News coverage of Israel-Gaza escalation / Iran missile response (YouTube) |
| Outlet | BBC News |
| Tier | B (major broadcaster) |
| Capture date | 2026-08-25 (via yt-dlp) |
| Source file | `captures/iran_bbc_nleE37zPSNpw.f398+251.mp4` |
| Source duration | ~96s (source merged from two segments) |

---

## Selection

| Field | Value |
|-------|-------|
| Selection method | Manual — Iran D-Day escalation is the most clip-able moment in the source; the development (Iran firing missiles at Israel, Israel's defense chief signaling a direct strike on Iran) is a self-contained news event |
| Trim point | Iran D-Day escalation segment |
| Clip duration (portion used) | ~30s (portion of source) |

**Rationale:** The escalation from Gaza ground incursion to Iran-Israel direct fire is the clearest single development in the source. It's a standalone news moment with a clear before/after.

---

## Overlay

| Field | Value |
|-------|-------|
| Overlay tier | A |
| Headline | "Israel's next target: Iran itself" |
| Context line 1 | "Iran fired missiles at Israel after the Gaza ground incursion." |
| Context line 2 | "Israel's defense chief says the next step is a direct strike on Iran." |
| Context line 3 | "When two regional powers exchange fire, the whole map gets redrawn." |
| Timestamp | Aug 25, 2026 |
| Source attribution | "Source: BBC News" |
| Overlay file | `overlays/tb002_clip1_iran_dday_overlay.png` (or equivalent) |

**What the overlay does:** Leads with the development in the headline, adds the Iran-Israel causal chain that the raw clip implies but doesn't state as a sequence, attributes the source.

---

## Production

| Field | Value |
|-------|-------|
| Cut points | Iran D-Day segment of source |
| Aspect ratio | 9:16 vertical |
| Resolution | 1080×1920 |
| Video codec | H.264 High, CRF 22 |
| Audio codec | AAC 128kbps |
| Master file | `exports/tb002_clip1_iran_dday_9x16.mp4` |
| Master size | 7.4 MB |
| Platform exports | TikTok, YouTube Shorts, IG Reels (in `platform-exports/`) |

**Production tools:** ffmpeg 7.0.2 static + PIL overlay PNG.

---

## Platform Exports

| Platform | File | Notes |
|----------|------|-------|
| TikTok | `platform-exports/tb002_clip1_iran_dday_tiktok_9x16.mp4` | Master copied |
| YouTube Shorts | `platform-exports/tb002_clip1_iran_dday_ytshorts_9x16.mp4` | Re-encoded for clean YPP posture |
| Instagram Reels | `platform-exports/tb002_clip1_iran_dday_igreels_9x16.mp4` | Re-encoded, 9:16 Reels format |

---

## Risk Assessment

### Copyright / IP
- **Source tier:** B (BBC — major broadcaster, active rights-holder)
- **Portion used:** Partial segment of source. Not near-whole reuse.
- **Overlay quality:** Tier A, adds context and sequencing beyond the raw clip.
- **Attribution:** Present (BBC News).
- **Overall posture:** Same baseline as channel model. Plausible fair-use argument, not a clear safe harbor.

### Platform policy (non-copyright)
- **YouTube Shorts:** Most mature copyright enforcement. A claim is most likely to materialize here. Posted as private initially, flipped to public after review.
- **TikTok:** Aggressive reused-content and sensitivity enforcement. War content is high-sensitivity — flagged at account level over time.
- **Instagram Reels:** Distribution surface. Risk is more about reduced reach than immediate takedown.

### Content sensitivity
- **Graphic content:** War footage — Iran D-Day is a known high-sensitivity topic. Sensitive-content screen reviewed before posting.
- **Sensitive-content screen:** Reviewed. Clip cleared with eyes open. YouTube posted as private first, then flipped to public.
- **Framing check:** Headline is accurate to the development. Context lines grounded in the clip's own events. No sensationalist framing.

### Brand / trust
- Accurate to the clip. No misrepresentation.

---

## Pre-Post Checklist

- [x] Sensitive-content screen (war footage — reviewed, cleared with eyes open)
- [x] Source logged (BBC News, segment of source, overlay, attribution)
- [x] Overlay accurate (headline + context lines verified against source events)
- [x] Platform exports ready (9:16, three platforms)
- [x] Clip log entry complete (this file)
- [x] Description written (`tb002_clip1_iran_dday_description.txt`)

---

## Posting

| Field | Value |
|-------|-------|
| Posting decision | Post with eyes open — war content, check sensitivity before public |
| YouTube | Posted private → flipped to public after review |
| YouTube video ID | `pHCYzoNXFRw` — https://youtu.be/pHCYzoNXFRw |
| YouTube privacy | public |
| Instagram Reels | Manual post needed (no IG token) |
| TikTok | Manual post needed (no TikTok tool) |

**Caption used:**
> Lead with the development: Israel's ground incursion into Gaza has triggered a cascade across the Middle East — Iran launched missiles at Israel, and Israel's defense chief says the next step is a direct strike on Iran itself.
>
> The escalation is no longer about Gaza. Iran fired missiles. Israel's leadership is now talking about hitting Iran directly. When two regional powers start exchanging fire, the whole map gets redrawn.
>
> Source: BBC News. What's your read — is this the opening of a wider regional war, or posturing before a negotiated off-ramp?

---

## Monitoring

- **YouTube:** Reach, any copyright claim/Content ID match/block/strike, age-restriction, advertiser-friendliness.
- **TikTok:** Once posted manually — reach, retention, any flags/age-gating/removal.
- **Instagram Reels:** Once posted manually — reach, account standing, any removal/deprioritization.

Log actual outcomes in the risk register.

---

## Risk Register Entry

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Type | Copyright / IP + platform policy + content sensitivity |
| Clip / source | TB-002-C1 / BBC News |
| Description | Iran D-Day escalation clip. Tier B source, Tier A overlay, war content. Posted to YouTube (private → public). IG + TikTok pending manual post. |
| Risk implication | War content is the highest-sensitivity lane in the batch. YouTube copyright enforcement is the most likely claim surface. TikTok sensitivity enforcement is the most likely flag surface. |
| Action taken | Pre-post checklist complete. Platform exports produced. Clip log entry written. YouTube posted (private, flipped to public). |
| Outcome / status | YouTube live (public). IG + TikTok: pending manual post. Monitor all three. |
| Notes | |

*Last updated: 2026-08-25*
