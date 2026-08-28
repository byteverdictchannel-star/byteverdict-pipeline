# Risk Register — Trending Clips Channel

**A running log of risk events and risk decisions.** Not a one-time assessment — a living document that tracks what actually happens to the channel and what build decisions raised or lowered which risks.

This register complements the Legal & Risk Landscape Report (`~/clips-channel/legal-report/00-index.md`), which is the upfront assessment. This register is the operational record — what the assessment predicted, what actually occurred, and what the build did about it.

---

## 1. How to Use This Register

- **Log risk events as they happen.** A flag, a claim, a removal, an age-gate, a throttling, a monetization ineligibility signal — log it.
- **Log risk decisions as you make them.** A sourcing choice, an overlay choice, a clip-length choice, a platform choice — log the risk implication.
- **Review periodically.** Not daily (unless something is happening), but at the test-batch review and at the 30/60/90 decision points.
- **Use it to spot patterns.** Which sources keep getting flagged? Which content types? Which platforms? Which overlay qualities? Patterns before they become problems.

---

## 2. Risk Categories

### Copyright / IP risk

- Claims, takedowns, Content ID matches, strikes.
- Source-tier risk — which sources carry more or less enforcement risk.
- Portion-used risk — how much of the source is in the clip.

### Platform policy risk (non-copyright)

- Reused-content / unoriginal-content signals and reach throttling.
- Sensitive / graphic content flags, age-gating, removal.
- Monetization eligibility denials or restrictions.
- Account-level risk from content patterns.

### Content sensitivity risk

- Graphic violence, gore, death, distressing imagery.
- Platform sensitivity enforcement independent of copyright.
- The fastest failure mode for war content.

### Brand / trust risk

- Misleading overlays or captions.
- Accuracy failures.
- Audience trust erosion.
- Sponsor / partner perception.

### Operational risk

- Workflow breakdowns — sourcing unreliability, production bottlenecks, unsustainable cadence.
- Account-compromise or access risk.
- Content loss or versioning problems.

### Monetization risk

- Eligibility denials.
- Delayed eligibility.
- Platform rule changes affecting eligibility.
- Over-reliance on a single monetization path.

---

## 3. Register Template

One entry per risk event or risk decision.

| Field | Notes |
|-------|-------|
| Date | When it happened or was decided |
| Type | Which risk category |
| Clip / source | Which clip, which source, which platform (if relevant) |
| Description | What happened or what was decided |
| Risk implication | What risk this raises, lowers, or reflects |
| Action taken / to take | What was done, or what should be done |
| Outcome / status | Resolved, ongoing, pending, observed |
| Notes | Anything else worth remembering |

---

## 4. Example Entries (Illustrative — not actual events)

### Example 1 — Sensitive-content flag (observed)

- **Date:** 2026-09-02
- **Type:** Content sensitivity
- **Clip / source:** War development clip, broadcast outlet, YouTube Shorts
- **Description:** Clip age-restricted on YouTube shortly after posting. No copyright claim.
- **Risk implication:** Confirms that platform sensitivity is a first-order risk for war content, independent of copyright. The clip's fair-use posture was moot for this outcome.
- **Action taken / to take:** Screen war candidates more strictly going forward; consider whether the same development can be conveyed with less flagged footage.
- **Outcome / status:** Observed. Clip remains live but restricted.
- **Notes:** Overlay was Tier A; the restriction was about the footage, not the overlay.

### Example 2 — Source tier decision (decision)

- **Date:** 2026-09-03
- **Type:** Copyright / IP (source tier)
- **Clip / source:** Tech product announcement, official company YouTube channel
- **Description:** Decided to use this source for a test clip. Tier 2 (established outlet, commercial rights-holder). Used a short selected segment with specific overlay context and source attribution.
- **Risk implication:** Tier 2 carries moderate risk. Chose short segment + strong overlay + attribution to modulate. Not zero risk.
- **Action taken / to take:** Log the decision; monitor for any claim or flag; prefer shorter, more contextualized use of this source type going forward.
- **Outcome / status:** Decision logged. No event yet.
- **Notes:** Tech source, lower sensitivity than war — different risk profile, but still not "safe."

### Example 3 — Overlay quality decision (decision)

- **Date:** 2026-09-04
- **Type:** Brand / trust + copyright (transformation)
- **Clip / source:** Viral news clip, aggregator source
- **Description:** Deliberately used a Tier B overlay (adequate, thinner) instead of a Tier A overlay for this test clip, to see whether overlay quality correlated with performance.
- **Risk implication:** Thinner overlay = weaker transformative posture and weaker brand signal. Accepted as a deliberate test variable, not as a default.
- **Action taken / to take:** Compare performance against Tier A clips in the test-batch review. If Tier A consistently outperforms, lean into overlay craft; if not, investigate further.
- **Outcome / status:** Decision logged. Awaiting test-batch review.
- **Notes:** Clip was still accurate and not misleading — the variation was overlay depth, not truthfulness.

### Example 4 — Monetization eligibility signal (observed)

- **Date:** 2026-09-10
- **Type:** Monetization
- **Clip / source:** Channel-level, YouTube
- **Description:** Noticed that a performing Short is not generating monetization signals / is not clearly YPP-eligible at this stage.
- **Risk implication:** Confirms that reach ≠ monetization eligibility. Channel is building toward eligibility, not automatically monetizable.
- **Action taken / to take:** Continue building toward originality and content pattern; don't assume monetization is immediate; keep off-platform ownership layer in progress.
- **Outcome / status:** Observed. Expected at this stage.
- **Notes:** In line with the plan's honest framing of monetization timing.

---

## 5. What the Register Tracks (Habit)

For each clip, the register should eventually capture:

- **Source and tier** — what was used and at what risk level.
- **Portion used** — how much of the source is in the clip.
- **Overlay used and tier** — what transformation was added and how strong.
- **Sensitive-content flag** — was the clip screened, and did it carry flagged material.
- **Platform risk assessment** — per platform, what was the anticipated risk.
- **Actual platform outcomes** — what actually happened (live, throttled, age-gated, flagged, claimed, removed).
- **Monetization signals** — any eligibility observations.

This habit is cheap and surfaces patterns before they become problems. It also documents good faith.

---

## 6. Review Cadence

- **After the test batch (Day 14):** Full review of what happened. Which risks materialized? Which didn't? What did the test tell us about the assessment?
- **At Day 30:** Review the register for patterns. Are certain sources, content types, or platforms generating repeated risk events?
- **At Day 90:** Full review. How has the risk picture evolved from the test batch to the early channel?
- **Ad hoc:** Whenever a risk event happens, log it and review if it's part of a pattern.

---

## 7. Where the Register Meets the Rest of the Build

- **Legal report (`~/clips-channel/legal-report/00-index.md`):** The register tests the assessment against reality. Do the predicted risks materialize? Do the confidence levels hold up?
- **Sourcing (`01-sourcing.md`):** Source-tier decisions and outcomes are the core of the copyright/IP risk tracking.
- **Overlay design (`02-overlay-design.md`):** Overlay quality decisions and outcomes are tracked here — both copyright/transformation risk and brand/trust risk.
- **Distribution (`04-distribution-workflow.md`):** Per-platform outcomes are logged here.
- **Test batch (`05-first-test-batch.md`):** The test batch is the first major input to the register.
- **30/60/90 plan (`06-30-60-90-plan.md`):** The register feeds the decision points in the 90-day plan.
- **Monetization paths (`07-monetization-paths.md`):** Eligibility events are logged here.
- **Subagent delegation (`08-subagent-delegation.md`):** Subagent-produced content and decisions are tracked here where relevant.

---

## 8. Honest Limits

- **The register is a record, not a safety net.** It documents risk; it doesn't eliminate it.
- **The register can't predict everything.** Some risk events are unpredictable (platform rule changes, unexpected enforcement, viral behavior).
- **The register can't make a bad decision good.** If a clip was a bad decision, the register records it — it doesn't undo it.
- **The register is only useful if you keep it.** A register that isn't updated is worse than no register, because it creates the illusion of tracking without the substance.

---

*Last updated: 2026-08-24*