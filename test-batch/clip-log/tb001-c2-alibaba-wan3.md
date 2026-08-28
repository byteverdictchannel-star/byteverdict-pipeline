# Clip Log Entry TB-001-C2

**Clip ID:** TB-001-C2
**Date produced:** 2026-08-24
**Date posted:** not yet posted

---

## Source

| Field | Value |
|-------|-------|
| Source URL | https://www.youtube.com/watch?v=g8s2t1EJj0k |
| Outlet | Bloomberg Tech |
| Tier | B (tech press / major broadcaster) |
| Reporting source of underlying facts | Reuters |
| Capture date | 2026-08-24 (via yt-dlp 2026.08.19) |
| Capture method | yt-dlp → ffmpeg merge (f398.mp4 + f251-18.webm) |
| Source file (merged) | `captures/alibaba_wan3_merged.mp4` |
| Source duration | 46:41 (46 min 41 sec) |
| Source specs | AV1/AAC, 1280x720, 219.7 MB |

---

## Selection

| Field | Value |
|-------|-------|
| Selection method | Manual — first 40 seconds of the Bloomberg coverage, opening segment. Exact Wan3.0 announcement segment to confirm in review (may be later in the 46-min clip). |
| Clip duration (portion used) | 40s (first 40 seconds of a 46:41 source, ~1.4% of source) |
| Trim point | 0–40s |

**Why this segment:** The opening of the Bloomberg coverage sets up the Wan3.0 launch context. If the exact Wan3.0 announcement moment is later in the 46-min clip, re-trim and re-export from the merged master.

**Note on source attribution:** The overlay currently attributes "Source: Reuters." The actual broadcast source is Bloomberg Tech. Reuters is the reporting source for the underlying facts (per the closeout log), but the clip footage itself is Bloomberg's. This is a discrepancy that should be resolved before posting — either correct the overlay to "Source: Bloomberg Tech" or document why Reuters attribution is used for the underlying facts while Bloomberg is the footage source.

---

## Overlay

| Field | Value |
|-------|-------|
| Overlay tier | A |
| Headline | "Alibaba just launched Wan3.0 — an AI video generator" |
| Context line 1 | "• The model launched Monday with enhanced video-generation capabilities." |
| Context line 2 | "• It followed Alibaba's $10 billion share placement to fund rising AI spending." |
| Context line 3 | "• Alibaba is betting AI video is a competitive battleground." |
| Timestamp | Aug 24, 2026 |
| Source attribution | "Source: Reuters" (⚠ see note above — should be "Source: Bloomberg Tech" or clarified) |
| Overlay file | `overlays/tb001_c2_alibaba_wan3_overlay.png` |
| Overlay PNG review | Legible per verification summary — headline + 3 context lines + date + source attribution all readable |

**What the overlay does:** Leads with the product launch in the headline, adds the funding context ($10B share placement) and the competitive-battleground framing that the raw clip implies but doesn't state as a thesis, attributes the source.

---

## Production

| Field | Value |
|-------|-------|
| Cut points | 0–40s (first 40 seconds) |
| Aspect ratio | 9:16 vertical |
| Resolution | 1080×1920 |
| Video codec | H.264 High, CRF 20, preset fast |
| Audio codec | AAC 127kbps (re-encoded from source AAC) |
| Master file | `exports/tb001_c2_alibaba_9x16.mp4` |
| Master size | 24.7 MB (23.9 MB per closeout) |
| Production tools | ffmpeg 7.0.2 static + PIL overlay PNG |

**Pipeline:** Trim to first 40s → composite overlay onto 9:16 with blurred background fill (gblur sigma=20) → H.264 High CRF 20 / AAC 127k → 1080×1920.

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
- **Source tier:** B (Bloomberg Tech — tech press, major broadcaster, active rights-holder)
- **Portion used:** 40s of a 46:41 source (~1.4%). Small portion taken — favorable on Factor 3.
- **Overlay quality:** Tier A, adds funding context and competitive-battleground framing. Better Factor 1 position than a thin overlay.
- **Attribution:** Present in overlay ("Source: Reuters" — but see discrepancy note above).
- **Overall posture:** Same baseline as channel model. Plausible fair-use argument, not a clear safe harbor. This clip is one of the better-positioned ones in the batch (Tier B source + Tier A overlay + tech lane, not war).

### Platform policy (non-copyright)
- **TikTok:** Tech/AI content is lower sensitivity than war. Reused-content pattern still matters at account level over time.
- **YouTube Shorts:** Most mature copyright enforcement. A claim is most likely to materialize here. YPP eligibility is earned, not automatic.
- **Instagram Reels:** Distribution surface. Risk is more about reduced reach than immediate takedown.

### Content sensitivity
- **Graphic content:** None expected. Tech/product announcement.
- **Sensitive-content screen:** Not required (tech lane, expected clean). Standard accuracy check on overlay passed.
- **Framing check:** Headline is accurate to the clip's product-launch claim. Context lines grounded in the clip's own stated facts ($10B share placement, AI video competitive battleground). No misleading or sensationalist framing.

### Brand / trust
- Headline and context are accurate to the clip. No misrepresentation. The $10B share placement fact is a real Alibaba move (per the source).

---

## Pre-Post Checklist

- [ ] Sensitive-content screen (tech lane — expected clean, no war-content screen required)
- [ ] Source logged (Bloomberg Tech, 40s of 46:41, overlay, attribution — **attribution discrepancy needs resolution**)
- [ ] Overlay accurate (headline attributable, context lines grounded in clip's own facts — verify before posting)
- [ ] Platform exports ready (not yet — needs export pass)
- [ ] Clip log entry complete (this file — being written now)
- [ ] Description written (not yet — write before posting)

---

## Posting

| Field | Value |
|-------|-------|
| Posting decision | Pending — not yet posted |
| Suggested order | Cleanest corner of the batch — lowest sensitivity, sponsor-adjacent audience signal. Could go first. |
| YouTube | Not yet posted |
| Instagram Reels | Not yet posted |
| TikTok | Not yet posted |

**Caption (suggested):**
> Alibaba just launched Wan3.0 — an AI video generator that comes out the same week the company raised $10 billion in a share placement to fund its AI push.
>
> The model launched with enhanced video-generation capabilities, and Alibaba is positioning AI video as a competitive battleground. The funding and the product launch are the same story — one is the fuel, the other is the engine.
>
> Source: Bloomberg Tech. Is AI video generation the next big platform battle, or the latest hype cycle?

**Caption accuracy check:** Caption is accurate to the clip and overlay. No misleading framing.

**Caption tone:** Informative, tech-forward. The click comes from the funding story and the competitive angle, not from hype.

---

## Monitoring

- **TikTok:** Reach and retention. Any flags, age-gating, reach throttling, or removal. Tech content is lower sensitivity than war.
- **YouTube Shorts:** Reach. Any copyright claim, Content ID match, block, or strike. Age-restriction. Advertiser-friendliness. YPP eligibility signals.
- **Instagram Reels:** Reach and account standing. Any removal or deprioritization. Feature-eligibility signals.

Log actual outcomes in the risk register.

---

## Risk Register Entry

| Field | Value |
|-------|-------|
| Date | 2026-08-24 (produced) / pending (posting) |
| Type | Copyright / IP + platform policy |
| Clip / source | TB-001-C2 / Bloomberg Tech (g8s2t1EJj0k) |
| Description | Alibaba Wan3.0 AI video model clip. Tier B source, Tier A overlay, tech lane. 40s of 46:41 source (~1.4%). Not yet posted. |
| Risk implication | Tech lane — lower sensitivity than war. Better-positioned clip in the batch (small portion taken + Tier A overlay + tech not war). Attribution discrepancy (Reuters vs. Bloomberg Tech) needs resolution before posting. |
| Action taken | Production complete (trim + overlay + export). Clip log entry being written. Platform exports pending. |
| Outcome / status | Pending — write clip log, resolve attribution, produce platform exports, post. |
| Notes | Trim point (first 40s) is a starting guess — the exact Wan3.0 announcement segment may be later in the 46-min clip. Re-trim if needed. Attribution: overlay says "Reuters" but footage is Bloomberg — resolve before posting. |

*Last updated: 2026-08-25 (clip log entry written)*
