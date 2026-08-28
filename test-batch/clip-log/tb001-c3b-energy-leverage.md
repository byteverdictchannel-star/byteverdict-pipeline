# Clips Channel — Clip Log Entry TB-001-C3b

**Clip ID:** TB-001-C3b
**Date produced:** 2026-08-25
**Related:** TB-001-C3 (same source, different angle)

---

## Source

| Field | Value |
|-------|-------|
| Source URL | https://www.youtube.com/watch?v=c2Q-TKJr4hE |
| Outlet | Reuters |
| Tier | A (wire/reporter footage, attributable) |
| Capture date | 2026-08-24 (via yt-dlp 2026.08.19) |
| Source file | `captures/tb001_clip3_reuters_carney_retaliation_c2Q-TKJr4hE.mp4` |
| Source duration | 96s |
| Clip duration (portion used) | 35.5s (57.5s→93.0s, ~37% of source) |

---

## Selection

| Field | Value |
|-------|-------|
| Selection method | AI second pass (`Anil-matcha/AI-Youtube-Shorts-Generator`, local mode, Gemini-3.6-flash) |
| AI rank | #1 of 3 candidates (score 96) |
| Manual comparison | Different angle from TB-001-C3 manual pick. Manual led with tariff headline; AI led with energy-leverage counter-narrative. |
| Why this angle | The US-Canada trade deficit the clip discusses only exists because the US buys so much energy from Canada — the deficit is an energy-choice artifact, not evidence the US is "ripping Canada off." Viral-worthy counter-narrative with hard stats (99% gas / 85% electricity / 60% crude). |

---

## Overlay

| Field | Value |
|-------|-------|
| Overlay tier | A |
| Headline | "The US runs a trade deficit with Canada — so it is 'ripping them off.'" |
| Context line 1 | "The deficit only exists because the US buys so much of its energy from Canada." |
| Context line 2 (bullets) | "• Canada supplies 99% of US natural gas imports" / "• 85% of US electricity imports" / "• 60% of US crude oil imports" |
| Footer | "So the deficit is an energy choice, not exploitation." |
| Timestamp | Aug 25, 2026 |
| Source attribution | "Source: Reuters" |
| Overlay file | `overlays/tb001_c3_energy_leverage_overlay.png` |

**What the overlay does:** Leads with an attributable claim from the clip itself (Carney's "ripping them off" framing), adds the "why the deficit exists" context that the raw clip doesn't state on its own, attributes the source. The clip-plus-overlay is arguably a different work than the raw clip — the overlay adds analysis, not just restatement.

---

## Production

| Field | Value |
|-------|-------|
| Cut points | 57.5s→93.0s |
| Aspect ratio | 9:16 vertical |
| Resolution | 1080×1920 |
| Video codec | H.264 High, CRF 20, preset fast |
| Audio codec | AAC 128kbps (re-encoded from source Opus) |
| Master file | `exports/tb001_c3_energy_leverage_9x16.mp4` (19.6MB, 35.5s) |
| Production tools | ffmpeg 7.0.2 static + PIL overlay PNG, same stack as TB-001 |

---

## Platform Exports

| Platform | File | Notes |
|----------|------|-------|
| TikTok | `platform-exports/tb001_c3_energy_leverage_tiktok_9x16.mp4` | Master, copied. 35.5s within short-form range. |
| YouTube Shorts | `platform-exports/tb001_c3_energy_leverage_ytshorts_9x16.mp4` | Re-encoded (CRF 22, AAC 128k) for clean YPP posture. Under Shorts cap. |
| Instagram Reels | `platform-exports/tb001_c3_energy_leverage_igreels_9x16.mp4` | Re-encoded (CRF 22, AAC 128k). 9:16 Reels format. |

One source file → three platform-native exports, per distribution workflow.

---

## Risk Assessment

### Copyright / IP
- **Source tier:** A (Reuters, wire). Moderate risk. Reuters is an active rights-holder with known enforcement posture.
- **Portion used:** 37% of a 96s source. Not a near-whole reuse, but substantial enough that Factor 3 (amount taken) isn't strongly favorable.
- **Overlay quality:** Tier A, adds real context/analysis. Better Factor 1 position than a thin overlay, but still text-overlay-only (no voiceover, no commentary). The channel's format sits on the thinner end of the transformative-use spectrum per the legal report.
- **Attribution:** Present ("Source: Reuters"). Good practice, not a defense. Per the attribution-myth doc: not a fair-use factor, not a license, not a platform shield.
- **Overall copyright posture:** Same baseline as the channel model — plausible fair-use argument in some configurations, not a clear safe harbor. This clip is one of the better-positioned ones in the batch (Tier A source + Tier A overlay + trade/economics not war + attributable headline), but there is no guarantee.

### Platform policy (non-copyright)
- **TikTok:** Aggressive reused-content and sensitivity enforcement. Trade/economics is lower sensitivity than war but not zero. Reused-content pattern matters at account level over time.
- **YouTube Shorts:** Most mature copyright enforcement (Content ID, takedown, strikes). A claim is most likely to materialize here. YPP eligibility is earned, not automatic — this format is in the zone YPP scrutinizes.
- **Instagram Reels:** Distribution surface, different audience. Risk is often more about reduced reach/feature eligibility than immediate takedown. Repurposed/unoriginal content can face reduced distribution.
- **All three:** Presence on all three surfaces ≠ success on any of them. A clip can be live everywhere and still be throttled, age-gated, or excluded from monetization on each.

### Content sensitivity
- **Graphic content:** None expected. Trade/economics, not conflict footage.
- **Sensitive-content screen:** Not required (trade lane, expected clean). Standard accuracy check on overlay passed.
- **Framing check:** Headline is attributable (Carney's own framing from the clip). Context lines are grounded in the clip's own stated stats. No misleading or sensationalist framing.

### Brand / trust
- Headline and context are accurate to the clip. No misrepresentation. The energy-leverage angle is a real editorial find, not invented.

---

## Pre-Post Checklist

- [x] Sensitive-content screen (trade lane, expected clean — no war-content screen required)
- [x] Source logged (Reuters, 35.5s of 96s, overlay, attribution)
- [x] Overlay accurate (headline attributable, context lines grounded in clip's own stats)
- [x] Platform exports ready (9:16, 35.5s, 1080×1920, per platform)
- [x] Clip log entry complete (this file)

---

## Posting

| Field | Value |
|-------|-------|
| Posting decision | Operator decision — post with eyes open |
| Suggested order | Not the highest-sensitivity clip in the batch (trade, not war). Could go before or after C2 (tech). |
| Caption (suggested) | Lead with the hook: the US runs a trade deficit with Canada — but the deficit only exists because the US buys so much energy from Canada. 99% of gas imports, 85% of electricity, 60% of crude. The deficit is an energy choice, not exploitation. |
| Caption accuracy check | Caption is accurate to the clip and overlay. No misleading framing. |
| Caption tone | Informative, not sensational. The click comes from the real economic stakes and the counter-narrative, not from hype. |

---

## Monitoring

After posting, watch for:

- **TikTok:** Reach and retention. Any flags, age-gating, reach throttling, or removal. A flagged clip on TikTok is a signal about the sensitivity/reused-content boundary, not just a loss.
- **YouTube Shorts:** Reach. Any copyright claim, Content ID match, block, or strike. Age-restriction. Advertiser-friendliness. Any YPP eligibility signal (not expected this early, but note it).
- **Instagram Reels:** Reach and account standing. Any removal or deprioritization. Any feature-eligibility signal.

Log actual outcomes in the risk register.

---

## Risk Register Entry (log this)

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Type | Copyright / IP + platform policy |
| Clip / source | TB-001-C3b / Reuters (c2Q-TKJr4hE) |
| Description | Posted energy-leverage angle from same Reuters source as TB-001-C3. Tier A source, Tier A overlay, trade/economics content, 37% of source used. |
| Risk implication | Same baseline risk as channel model. Better-positioned clip in the batch (Tier A + Tier A overlay + trade not war), but no guarantee. Watch for platform flags/claims, especially YouTube. |
| Action taken | Pre-post checklist complete. Platform exports produced. Clip log entry written. |
| Outcome / status | Pending — post, then monitor and log actual outcomes. |
| Notes | AI second pass surfaced this angle; manual pass did not. Case study for the second-pass framework. |

---

*Last updated: 2026-08-25 (TB-001-C3b produced, ready to post)*
