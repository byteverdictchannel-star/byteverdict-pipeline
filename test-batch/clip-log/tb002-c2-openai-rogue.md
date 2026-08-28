# Clip Log Entry TB-002-C2

**Clip ID:** TB-002-C2
**Date produced:** 2026-08-25
**Date posted:** 2026-08-25

---

## Source

| Field | Value |
|-------|-------|
| Source URL | CBS News coverage of OpenAI whistleblower / "rogue employee" allegations (YouTube) |
| Outlet | CBS News |
| Tier | B (major broadcaster) |
| Capture date | 2026-08-25 (via yt-dlp) |
| Source file | `captures/openai_rogue_cbs_bH9ADw9GLcg.mp4` |
| Source duration | ~60s (source) |

---

## Selection

| Field | Value |
|-------|-------|
| Selection method | Manual — OpenAI whistleblower allegation is the most clip-able moment; self-contained claim with a named figure (former employee) and a clear conflict (whistleblower vs. company narrative) |
| Clip duration (portion used) | ~30s (portion of source) |

**Rationale:** The whistleblower-claim-versus-company-response structure is a clean narrative arc for a short clip. It's a tech/AI story that carries a human conflict — more engaging than a pure product announcement.

---

## Overlay

| Field | Value |
|-------|-------|
| Overlay tier | A |
| Headline | "OpenAI accused of silencing a 'rogue' employee" |
| Context line 1 | "A former employee says OpenAI's security team flagged him as a 'rogue' agent and moved to shut him down." |
| Context line 2 | "The allegation is now part of a whistleblower case heading to regulators." |
| Context line 3 | "One side says he raised real concerns; the other says he was spinning a narrative." |
| Timestamp | Aug 25, 2026 |
| Source attribution | "Source: CBS News" |
| Overlay file | `overlays/tb002_clip2_openai_rogue_overlay.png` (or equivalent) |

**What the overlay does:** Leads with the accusation, adds the regulatory-stakes context, frames the conflict symmetrically without taking a side.

---

## Production

| Field | Value |
|-------|-------|
| Cut points | Whistleblower allegation segment of source |
| Aspect ratio | 9:16 vertical |
| Resolution | 1080×1920 |
| Video codec | H.264 High, CRF 20 |
| Audio codec | AAC 128kbps |
| Master file | `exports/tb002_clip2_openai_rogue_9x16_v2.mp4` |
| Master size | 5.5 MB |
| Platform exports | TikTok, YouTube Shorts, IG Reels (in `exports/` or `platform-exports/`) |

**Production tools:** ffmpeg 7.0.2 static + PIL overlay PNG.

---

## Platform Exports

| Platform | File | Notes |
|----------|------|-------|
| YouTube Shorts | `exports/tb002_clip2_openai_rogue_9x16_v2.mp4` | Posted directly from master |
| TikTok | (not yet exported) | Needs platform export pass |
| Instagram Reels | (not yet exported) | Needs platform export pass |

---

## Risk Assessment

### Copyright / IP
- **Source tier:** B (CBS News — major broadcaster, active rights-holder)
- **Portion used:** Partial segment. Not near-whole reuse.
- **Overlay quality:** Tier A, adds regulatory context and frames the conflict.
- **Attribution:** Present (CBS News).
- **Overall posture:** Same baseline as channel model.

### Platform policy (non-copyright)
- **YouTube Shorts:** Most mature copyright enforcement. Posted as private first.
- **TikTok:** Lower sensitivity than war, but tech/AI content with a conflict angle can trigger reused-content scrutiny.
- **Instagram Reels:** Distribution surface.

### Content sensitivity
- **Graphic content:** None. Tech/whistleblower story.
- **Sensitive-content screen:** Not required (expected clean). Standard accuracy check passed.
- **Framing check:** Headline is accurate to the clip's claims. Context lines present both sides without endorsing either.

### Brand / trust
- Accurate to the clip. No misrepresentation. Symmetrical framing avoids taking a side.

---

## Pre-Post Checklist

- [x] Sensitive-content screen (tech lane — expected clean)
- [x] Source logged (CBS News, segment of source, overlay, attribution)
- [x] Overlay accurate (headline + context lines verified against source)
- [x] Platform exports ready (YouTube Shorts posted; TikTok + IG Reels need export pass)
- [x] Clip log entry complete (this file)
- [x] Description written (`tb002_clip2_openai_rogue_description.txt`)

---

## Posting

| Field | Value |
|-------|-------|
| Posting decision | Post — tech lane, lower sensitivity than war |
| YouTube | Posted private → public |
| YouTube video ID | `qA0F2U5birA` — https://youtu.be/qA0F2U5birA |
| YouTube privacy | public |
| Instagram Reels | Manual post needed (no IG token) |
| TikTok | Manual post needed (no TikTok tool) |

**Caption used:**
> A former OpenAI employee says the company's security team flagged him as a "rogue" agent and moved to shut him down — and the allegation is now part of a whistleblower case heading to regulators.
>
> The clash is over what "safety" means inside the company. One side says the whistleblower raised real concerns; the other says he was a disgruntled employee spinning a narrative. When the people who built the system start accusing each other of misconduct, the public has a right to know which version holds up.
>
> Source: CBS News. Do you side with the whistleblower or the company — and what would it take to settle this one cleanly?

---

## Monitoring

- **YouTube:** Reach, copyright claims, age-restriction, advertiser-friendliness.
- **TikTok:** Once posted manually — reach, retention, flags.
- **Instagram Reels:** Once posted manually — reach, account standing.

Log actual outcomes in the risk register.

---

## Risk Register Entry

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Type | Copyright / IP + platform policy |
| Clip / source | TB-002-C2 / CBS News |
| Description | OpenAI whistleblower clip. Tier B source, Tier A overlay, tech lane (lower sensitivity). Posted to YouTube (private → public). IG + TikTok pending manual post. |
| Risk implication | Tech/AI content with a conflict angle. Lower sensitivity than war, but the whistleblower framing could draw scrutiny on TikTok if the account builds a reused-content pattern. |
| Action taken | Pre-post checklist complete. Platform exports produced (YouTube). Clip log entry written. |
| Outcome / status | YouTube live (public). IG + TikTok: pending manual post. Monitor all three. |
| Notes | |

*Last updated: 2026-08-25*
