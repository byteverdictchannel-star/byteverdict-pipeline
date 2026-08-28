# Clip Log Entry TB-001-C3

**Clip ID:** TB-001-C3
**Date produced:** 2026-08-24
**Date posted:** not yet posted

---

## Source

| Field | Value |
|-------|-------|
| Source URL | https://www.youtube.com/watch?v=c2Q-TKJr4hE |
| Outlet | Reuters |
| Tier | A (wire/reporter footage, attributable) |
| Capture date | 2026-08-24 (via yt-dlp 2026.08.19) |
| Capture method | yt-dlp 2026.08.19 (merged f398+251-20) |
| Source file (merged) | `captures/tb001_clip3_reuters_carney_retaliation_c2Q-TKJr4hE.mp4` |
| Source duration | 1:36 (96 seconds) |
| Source specs | AV1/Opus, 1280x720, 7.5 MB |

---

## Selection

| Field | Value |
|-------|-------|
| Selection method | Manual — first 60 seconds of the Reuters clip (Trump tariff threat + Carney retaliation). Full 96s clip is within short-form range — could use full length if retention holds. |
| Clip duration (portion used) | 60s (first 60 seconds of a 96s source, ~62.5% of source) |
| Trim point | 0–60s |

**Why this segment:** The first 60 seconds cover the Trump 50% tariff threat on Canadian cars and Carney's retaliation announcement on steel and dairy. This is the core development — self-contained, attributable, clear before/after.

**Note:** The full 96s clip is within short-form range. If retention holds on the 60s version, consider using the full clip. Re-export from source if needed.

**Related:** TB-001-C3b is a different angle from the same Reuters source (energy-leverage counter-narrative, produced via AI second pass). C3b is the one with platform exports ready. This entry covers the original C3 trade-angle clip.

---

## Overlay

| Field | Value |
|-------|-------|
| Overlay tier | A |
| Headline | "Trump threatens 50% tariffs on Canadian cars" |
| Context line 1 | "• Carney says Canada can't accept US terms and will retaliate on steel and dairy." |
| Context line 2 | "• New Canadian measures take effect September 8." |
| Context line 3 | "• The trade war is escalating — and affecting prices." |
| Timestamp | Aug 24, 2026 |
| Source attribution | "Source: Reuters — see source log" |
| Overlay file | `overlays/tb001_c3_trade_carney_overlay.png` |
| Overlay PNG review | Legible per verification summary — headline + 3 context lines + date + source attribution all readable |

**What the overlay does:** Leads with the tariff threat in the headline, adds Carney's retaliation response and the September 8 effective date that the raw clip states but doesn't structure, frames the escalation, attributes the source.

---

## Production

| Field | Value |
|-------|-------|
| Cut points | 0–60s (first 60 seconds, or full 96s — review to decide) |
| Aspect ratio | 9:16 vertical |
| Resolution | 1080×1920 |
| Video codec | H.264 High, CRF 20, preset fast |
| Audio codec | AAC 126kbps (re-encoded from source Opus) |
| Master file | `exports/tb001_c3_trade_9x16.mp4` |
| Master size | 12.9 MB (12.7 MB per closeout) |
| Production tools | ffmpeg 7.0.2 static + PIL overlay PNG |

**Pipeline:** Trim to first 60s (or full 96s) → composite overlay onto 9:16 with blurred background fill (gblur sigma=20) → H.264 High CRF 20 / AAC 126k → 1080×1920.

**Platform exports:** Not yet produced. Single 9:16 master serves all three platforms if needed, but dedicated platform-export variants (CRF 22, AAC 128k) are recommended per the distribution workflow.

---

## Platform Exports

| Platform | File | Notes |
|----------|------|-------|
| TikTok | (not yet produced) | Needs platform export pass from master |
| YouTube Shorts | (not yet produced) | Needs platform export pass from master |
| Instagram Reels | (not yet produced) | Needs platform export pass from master |

**Master specs already meet platform requirements** (9:16, 1080×1920, H.264, AAC). Platform-export variants would be a re-encode pass with CRF 22 for cleaner platform posture.

---

## Risk Assessment

### Copyright / IP
- **Source tier:** A (Reuters — wire/reporter footage, attributable)
- **Portion used:** 60s of a 96s source (~62.5%). Substantial portion — not strongly favorable on Factor 3. The full 96s clip would be a near-whole reuse.
- **Overlay quality:** Tier A, adds retaliation timeline and escalation framing. Better Factor 1 position than a thin overlay, but still text-overlay-only (no voiceover, no commentary). The channel's format sits on the thinner end of the transformative-use spectrum.
- **Attribution:** Present in overlay ("Source: Reuters — see source log"). Good practice, not a defense.
- **Overall posture:** Same baseline as channel model — plausible fair-use argument in some configurations, not a clear safe harbor. This clip is in the moderate-risk lane (Tier A source + Tier A overlay + trade/economics not war), but the 62.5% portion used is the weakest factor. Consider using a shorter trim if the first 60s has dead air or if a tighter segment surfaces.

### Platform policy (non-copyright)
- **TikTok:** Trade/economics is lower sensitivity than war but not zero. Reused-content pattern matters at account level over time.
- **YouTube Shorts:** Most mature copyright enforcement. A claim is most likely to materialize here. YPP eligibility is earned, not automatic.
- **Instagram Reels:** Distribution surface. Risk is more about reduced reach than immediate takedown.

### Content sensitivity
- **Graphic content:** None expected. Trade/economics, not conflict footage.
- **Sensitive-content screen:** Not required (trade lane, expected clean). Standard accuracy check on overlay passed.
- **Framing check:** Headline is attributable (Trump's 50% tariff threat from the clip). Context lines are grounded in the clip's own stated facts (Carney retaliation, steel/dairy, September 8 effective date, escalating trade war). No misleading or sensationalist framing.

### Brand / trust
- Headline and context are accurate to the clip. No misrepresentation.

---

## Pre-Post Checklist

- [x] Sensitive-content screen (trade lane — expected clean, no war-content screen required)
- [x] Source logged (Reuters, 60s of 96s, overlay, attribution)
- [x] Overlay accurate (headline attributable — Trump's 50% tariff threat, context lines grounded in clip's own facts)
- [ ] Platform exports ready (not yet — needs export pass)
- [x] Clip log entry complete (this file — being written now)
- [ ] Description written (not yet — write before posting)

---

## Posting

| Field | Value |
|-------|-------|
| Posting decision | Pending — not yet posted |
| Suggested order | Secondary clean lane — not graphic, economically charged. Could go after C2 (tech) but before C1 (war). Or post alongside C3b (energy-leverage angle from same source). |
| YouTube | Not yet posted |
| Instagram Reels | Not yet posted |
| TikTok | Not yet posted |

**Caption (suggested):**
> Trump is threatening 50% tariffs on Canadian cars — and Canada's prime minister Carney says he won't accept the terms.
>
> Canada is retaliating on steel and dairy, with new measures taking effect September 8. The trade war is escalating, and it's starting to affect prices on both sides of the border.
>
> Source: Reuters. Is 50% on cars a negotiating tactic or the real target — and what happens to Canadian steel and dairy if the tariffs land?

**Caption accuracy check:** Caption is accurate to the clip and overlay. No misleading framing.

**Caption tone:** Informative, trade-focused. The click comes from the tariff number (50%) and the retaliation timeline (September 8), not from hype.

---

## Monitoring

- **TikTok:** Reach and retention. Any flags, age-gating, reach throttling, or removal. Trade/economics is lower sensitivity than war.
- **YouTube Shorts:** Reach. Any copyright claim, Content ID match, block, or strike. Age-restriction. Advertiser-friendliness. YPP eligibility signals.
- **Instagram Reels:** Reach and account standing. Any removal or deprioritization. Feature-eligibility signals.

Log actual outcomes in the risk register.

---

## Risk Register Entry

| Field | Value |
|-------|-------|
| Date | 2026-08-24 (produced) / pending (posting) |
| Type | Copyright / IP + platform policy |
| Clip / source | TB-001-C3 / Reuters (c2Q-TKJr4hE) |
| Description | US-Canada trade war clip — Trump 50% tariff threat + Carney retaliation. Tier A source, Tier A overlay, trade/economics lane. 60s of 96s source (~62.5%). Not yet posted. |
| Risk implication | Moderate risk lane. Tier A source improves posture, but 62.5% portion used is the weakest factor. Trade/economics content is lower sensitivity than war. Consider shorter trim if a tighter segment surfaces. Same source as C3b (energy-leverage angle) — two clips from one source increases the reused-content signal at account level. |
| Action taken | Production complete (trim + overlay + export). Clip log entry being written. Platform exports pending. |
| Outcome / status | Pending — write clip log, produce platform exports, write description, post. |
| Notes | Two clips from the same Reuters source (C3 + C3b) — watch the reused-content signal at account level. Trim point (first 60s) is a starting guess — full 96s is within short-form range; use full if retention holds. |

*Last updated: 2026-08-25 (clip log entry written)*
