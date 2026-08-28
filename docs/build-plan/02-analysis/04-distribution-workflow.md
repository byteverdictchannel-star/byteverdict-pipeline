# Distribution Workflow — One Clip, Three Surfaces

**One source clip → one cut/overlay → three platform-native exports.** This is the distribution layer: re-purpose the same produced clip to TikTok, YouTube Shorts, and Instagram Reels, each in its own aspect ratio and format, with platform-specific awareness of the rules that apply.

---

## 1. The Distribution Model

The channel's distribution model is:

- **One produced clip** — cut + text overlay, exported as the master.
- **Three platform-native exports** — re-exported per platform from the same master, not one file pushed everywhere.
- **One clip log entry** — the source, tier, overlay, sensitive-content flag, and platform decisions are logged once, not three times.
- **Posting cadence** — tied to the empirical test batch first, then scaled by what performs and what the labor model supports.

The structural point: the production effort is per-clip, not per-platform. The platform work is export + post + monitor.

---

## 2. Platform-by-Platform

### TikTok

- **Format:** 9:16 vertical, short-form.
- **Role in the channel:** Primary test surface — fastest reach, largest short-form audience, lowest barrier.
- **Risk profile:** Aggressive reused-content and sensitivity enforcement. War footage especially sensitive; tech/trending less so but not zero.
- **What to watch:** Reach and retention, but also platform flags — removals, age-gating, reach throttling. A clip that performs on reach but gets flagged is a signal, not just a win.
- **Posting awareness:** Don't treat TikTok as "set and forget." Reused-content and compilation patterns are evaluated at the account level over time.

### YouTube Shorts

- **Format:** 9:16 vertical, within the Shorts length range.
- **Role in the channel:** Long-game monetization anchor (YPP). Different reused-content enforcement from TikTok.
- **Risk profile:** Most mature copyright enforcement infrastructure of the three surfaces (Content ID, takedown, strikes). A copyright claim is most likely to materialize here as a concrete, trackable event.
- **What to watch:** Copyright claims/blocks/strikes, age-restriction, advertiser-friendliness, YPP eligibility trajectory.
- **Channel-level awareness:** YPP eligibility is earned over time and subject to content-pattern review. The YouTube surface should be treated not just as another place to post, but as the surface whose monetization eligibility should drive some build decisions — e.g., working toward sufficient originality and pattern to support YPP eligibility, while recognizing that eligibility is earned, not automatic.

### Instagram Reels

- **Format:** 9:16 vertical, Reels-length range.
- **Role in the channel:** Distribution surface with a different audience.
- **Risk profile:** Often less about immediate takedown and more about reduced reach / account-level risk for reposting patterns. Monetization features have their own eligibility.
- **What to watch:** Reach, account standing, distribution health. Monetization is secondary on this surface per the brief.
- **Posting awareness:** Repurposed/unoriginal content can face reduced distribution and feature eligibility. The pattern still matters.

---

## 3. One Clip, Three Exports — Practical Flow

### Step 1 — Master export

From the edit bench, export the produced clip as the master — the clean, full-quality cut + overlay.

### Step 2 — Re-export per platform

Re-export from the master to each platform's native specs:
- TikTok export
- YouTube Shorts export
- Instagram Reels export

Do not post the same file to all three. Re-export so each surface gets its intended aspect ratio and format. This is also where you catch platform-specific legibility issues (overlay text density vs. viewing size, etc.).

### Step 3 — Post

Post each export to its platform. Caption, hashtags, and posting time are part of the distribution work — keep them consistent with the overlay's framing and accurate to the content. Don't use misleading captions to chase clicks; that's the same bad-decision pattern as a misleading overlay.

### Step 4 — Log

One clip log entry with:
- Source / tier
- Overlay used / overlay tier
- Sensitive-content flag
- Master file and per-platform exports
- Posting time / caption notes
- Any platform flags observed

### Step 5 — Monitor

After posting, watch for:
- Reach and retention
- Engagement
- Platform flags (removal, age-gate, reach throttling, claims)
- Any downstream effects (e.g., a claim on YouTube, a flag on TikTok)

---

## 4. Cross-Platform Rhythm

For a solo operator at zero budget, the posting rhythm should be sustainable and not let distribution become the bottleneck.

### Test-batch rhythm

- Post the test batch across the three surfaces over the 1–2 week window.
- Space posts so you can observe platform response without overwhelming your own monitoring.
- Treat the test batch as an experiment, not a publishing sprint.

### Scaling rhythm (only after the test tells you something)

- If a format/surface is working, scale the cadence that the labor model supports.
- If the labor model can't support a cadence, either improve the workflow (batch editing, overlay templates, subagent help where it fits) or accept a lower cadence. Don't commit to a cadence the channel hasn't earned and the operator can't sustain.

---

## 5. What Distribution Does and Doesn't Do

**Distribution does:**
- Get the produced clip onto three surfaces
- Let you test which surface responds to what
- Feed the monitoring loop (what performs, what gets flagged)
- Build account history and pattern over time (which matters for monetization eligibility and platform perception)

**Distribution doesn't:**
- Make a clip legal or safe
- Override platform sensitivity rules
- Guarantee monetization eligibility
- Rescue a bad clip or a thin overlay
- Remove the need for per-platform awareness

---

## 6. Where Distribution Meets the Rest of the Build

- **Sourcing (`01-sourcing.md`):** The source tier and provenance feed the clip log and the distribution decision (some sources are riskier on some platforms).
- **Overlay design (`02-overlay-design.md`):** The produced clip's overlay is what's being distributed. Overlay quality maps to platform reused-content perception.
- **Editing (`03-editing-tooling.md`):** The exports come from the edit bench. Platform-native re-exports are an edit-layer output.
- **Test batch (`05-first-test-batch.md`):** The distribution rhythm is set by the test batch first.
- **Monetization (`07-monetization-paths.md`):** Each surface's monetization eligibility is a distribution-adjacent concern — reach and presence don't equal eligibility.
- **Risk register (`09-risk-register.md`):** Per-platform flags and claims are risk events to log and learn from.

---

## 7. Honest Limits

- **Presence on all three surfaces is not the same as success on any of them.** A clip can be live on TikTok, Shorts, and Reels and still be throttled, age-gated, or excluded from monetization on each.
- **Re-purposing the same clip across three platforms is efficient, but it's also visible.** If the output reads as mass reposting of others' content, account-level patterns matter more than per-clip presence.
- **Platform rules change.** What works on a surface today may not tomorrow. Build with margin and revisit as the channel scales or the format changes.

---

*Last updated: 2026-08-24*