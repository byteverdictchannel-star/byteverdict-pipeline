# Editing Tooling & Workflow — Zero Budget

**Free tools only.** This is the production layer: cut a self-contained moment from the source, add the overlay, export at platform-native specs, and organize the output for distribution.

---

## 1. The Editing Job, Broken Down

For each clip, the editing job is:

1. **Source capture / import** — get the footage into the editing tool. This may mean downloading from a platform, capturing a stream, or importing from a local source. Each has its own technique and its own risk considerations (downloading someone else's uploaded clip is still using someone else's footage).
2. **Clip selection** — pick the self-contained moment. Shorter, selected segments are a stronger position than near-whole reuse.
3. **Overlay composition** — place headline, context lines, timestamps, source attribution per the overlay design file.
4. **Review** — check legibility, hierarchy, accuracy, and that nothing is overcrowding the frame.
5. **Export** — platform-native aspect ratio and length.
6. **Versioning / organization** — keep the output organized for distribution and for the clip log.

---

## 2. Free Tooling Options (Categories, Not Endorsements)

The exact tool should be the one you actually learn and can use reliably. The categories below are the productive free ends of the spectrum.

### Non-linear video editors (free)

- **Open-source desktop editors** — DaVinci Resolve (free tier), Shotcut, Kdenlive, Olive, OpenShot, and similar. These give you timeline-based editing, text/title layers, and export control.
- **Choose one and learn it.** The tool matters less than the workflow discipline. A channel built in one tool you know well beats a channel planned in three tools you've barely touched.

### Lightweight / quick-edit tools

- For very simple cut + text overlay, lighter tools can be faster than a full NLE. The tradeoff is less control and less repeatability at volume.
- If the test batch is small, a lightweight tool may be enough to start; if you scale, a timeline editor with templates is usually the better home.

### Text / title compositing

- The overlay is text-on-video. Whatever tool you use, the overlay needs to be:
  - Readable at platform viewing size
  - Hierarchical (headline prominent, context subordinate)
  - Consistent in position, font, color, and treatment across clips (branding + repeatability)
  - Accurate and not overcrowding the frame

---

## 3. Workflow Discipline

### Source handling

- **Work from a local copy you control**, not from a platform URL you re-open each time. This makes the workflow repeatable and lets you version and organize outputs.
- **Track provenance.** Every imported source should be logged with where it came from, when, and what tier it's in. The source log is the companion to the clip log.

### Clip selection

- **Pick a self-contained moment.** A clear event, statement, development, or announcement beats a long, meandering segment.
- **Prefer shorter selected clips** over near-whole reuse. This is both a quality decision and a risk posture decision.
- **If the source is long**, choose the segment that is most clip-able and most valuable to overlay — not the longest segment.

### Overlay placement

- **Consistent position.** Pick a headline position and a context position and reuse them. Consistency is branding and repeatability.
- **Readable contrast.** Text vs. background — make sure the overlay reads against the footage. If the footage is busy or light/dark varies, you may need a backdrop, stroke, shadow, or position choice to keep text legible.
- **Don't crowd the frame.** The footage is the product; the overlay is the value-add. Too much text competes with the footage and looks like noise.

### Review before export

- **Headline accuracy** — does it match what the clip shows and what the underlying event is?
- **Context accuracy** — are the context lines true and appropriately qualified where needed?
- **Source attribution** — is it present and correct?
- **Legibility** — can you read everything at the platform's typical size?
- **Hierarchy** — is the headline the most prominent element?
- **Sensitive content screen** — this should have happened before editing, but do a final check: does the exported clip carry graphic content that will trip platform flags?

---

## 4. Export Specs (Platform-Native)

Export per platform. Don't export one file and push it everywhere — resize/re-export per platform.

### Common starting points (verify against current platform specs)

| Platform | Aspect ratio | Typical length sweet spot | Notes |
|----------|-------------|--------------------------|-------|
| TikTok | 9:16 vertical | Short-form; test what length holds retention | Reused-content and sensitivity enforcement are aggressive |
| YouTube Shorts | 9:16 vertical | Under the Shorts length cap; test retention vs. length | YPP eligibility is the long-game; copyright claims most likely here |
| Instagram Reels | 9:16 vertical | Reels-length range; test what retains | Reach and account health focus; monetization secondary |

**The exact caps and sweet spots change over time.** Use current platform specs as the source of truth; this document captures the structural point — one source clip, re-exported per surface — not fixed numbers.

### Export hygiene

- **Clean export** — no stray watermarks from your editing tool, no unintended artifacts.
- **Consistent treatment** — same font, same colors, same headline position across clips where you want a recognizable channel look.
- **File naming** — predictable naming that ties the output back to the source log and clip log (e.g., a short ID, source hint, date).

---

## 5. Batch Production

For a small test batch, one-off editing is fine. As volume increases, batch discipline matters.

### Batch workflow

1. **Backlog of vetted candidates** — you're not hunting at the edit bench; you're pulling from a logged, tiered backlog.
2. **Overlay templates** — reusable headline/context/attribution structures per content type (see overlay design file).
3. **Consistent export presets** — one export preset per platform, reused.
4. **Clip log entry per finished clip** — source, tier, what you did, overlay tier, sensitive-content flag, export details, where the file lives.

### Where the time goes

- **Sourcing and vetting** — finding and logging candidates
- **Overlay writing** — writing specific, accurate, value-adding overlays (this is skilled work)
- **Editing** — cutting, overlaying, exporting
- **Review and screening** — accuracy check, sensitive-content check
- **Distribution prep** — organizing outputs for posting

At zero budget, the leverage points are: better hunting-ground lists, overlay templates, consistent export presets, and batch discipline. The per-clip labor is real; the goal is to make it repeatable and to see where subagent help can fit without outsourcing judgment calls.

---

## 6. Where Editing Meets the Rest of the Build

- **Sourcing (`01-sourcing.md`):** The source log feeds the edit bench. Tier assignment from sourcing carries into the edit.
- **Overlay design (`02-overlay-design.md`):** The overlay is composed in the edit. Overlay quality tiers (A/B/C/D) are an edit-time and post-edit judgment.
- **Distribution (`04-distribution-workflow.md`):** The exported files are the distribution inputs. Platform-native re-exports come from the edit bench.
- **Test batch (`05-first-test-batch.md`):** The test batch is produced here. Overlay-quality variation is an edit/design decision.
- **Risk register (`09-risk-register.md`):** Clip length, portion used, and overlay quality are edit/overlay decisions that map to copyright and platform risk.

---

## 7. Honest Limits

- **Free tools are enough to start.** They are not always the fastest at scale; the win is workflow discipline, not tool sophistication.
- **Downloading someone else's uploaded clip is still using someone else's footage.** The edit bench doesn't change the legal/platform picture; it's the production layer on top of sourcing.
- **Good tooling doesn't rescue a bad source or a thin overlay.** The editing layer amplifies what sourcing and overlay design give it.

---

*Last updated: 2026-08-24*