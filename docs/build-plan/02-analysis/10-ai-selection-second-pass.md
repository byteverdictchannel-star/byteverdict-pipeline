# AI Selection as a Second Pass — Workflow Addendum

**Status:** Proven in spot-check (2026-08-25). Pending formalization.
**Source:** AI-Youtube-Shorts-Generator (`Anil-matcha`) local mode, Gemini-3.6-flash highlight ranking.
**Proven on:** C3 Reuters trade clip — AI surfaced a stronger hook than the manual pass.

---

## What This Is

A selection-augmentation step that runs *after* you've picked a source and *before* you commit to a trim point. The LLM framework proposes ranked clips from a transcript; you compare them to your manual pick and accept, reject, or reconsider.

It does not replace your pipeline. It does not produce your branded output. It is a second opinion on *which moments to clip*.

---

## When It Applies

**Use it when:**
- The source has substantial speech (a transcript worth analyzing)
- The source is longer than a single tight moment — you're choosing *where* to trim, not just *whether* to clip
- You want a second look at a source you might otherwise trim from the opening

**Skip it when:**
- The source is short enough that the trim point is obvious (under ~2min, single event)
- The source has no detectable speech (promo videos, music, B-roll)
- You're doing a quick pass where the cost of an extra LLM call isn't justified

**The framework correctly flagged C2 (Alibaba promo) as `content=vlog, density=low`** — a ~54s promotional video with no speech. The AI did the right thing there: it couldn't find viral highlights because there were none to find. That's the framework working as a filter, not a failure.

---

## The Proven Workflow

### Step 1 — Get a transcript

Use the repo's local mode to transcribe the source. This is the one real dependency: faster-whisper on CPU, base model, cached as an SRT file. For a 17min source this took a few minutes on CPU — acceptable but not fast. For a 1-2min source it's near-instant.

**Alternative:** if you already have a transcript (YouTube auto-captions, a caption file from the source), you can skip the Whisper step and feed text directly to the LLM.

### Step 2 — Run highlight ranking

Feed the transcript to the LLM via the repo's `highlights.py` framework (Gemini-3.6-flash on this account). The framework returns ranked candidates with:
- `title` — a label for the clip
- `start_time` / `end_time` — the proposed clip boundaries
- `score` (0-100) — viral potential
- `hook_sentence` — the opening line
- `virality_reason` — one-line explanation

### Step 3 — Compare to your manual pick

For each source, lay the AI's top 3 next to what you would have clipped manually. Look for:

- **Overlap** — did the AI pick the same moment? If yes, you've validated your instinct.
- **New angles** — did the AI surface a moment you wouldn't have grabbed? This is the value.
- **Score signal** — is the AI's #1 significantly higher-scored than #2 or #3? A big gap suggests a clear standout.
- **Content-type sanity** — did the AI classify the source correctly? If it says "podcast, density=high" for a promo video, something's wrong.

### Step 4 — Decide

For each AI-proposed clip:
- **Accept** — use it as-is, with your overlay pipeline
- **Reject** — it's weak, off-angle, or duplicates your pick
- **Reconsider** — the AI surfaced a moment you hadn't thought of; look at the raw footage and decide

Don't treat the AI's picks as authoritative. Treat them as proposals. You're the editor.

---

## The C3 Case Study (Proven)

**Source:** Reuters trade clip (Carney retaliation, 95s of speech), same source used for TB-001-C3.

**Your manual pick:** "Trump threatens 50% tariffs on Canadian cars" — first 60s, Carney retaliation framing, headline leads with the tariff threat.

**AI's picks:**
| # | Score | Title | Time | Hook |
|---|-------|-------|------|------|
| 1 | 96 | The Energy Leverage Reality Check | 57.5s→93.0s | "Another prominent justification for US tariffs has been their claim that since the US runs a trade deficit with Canada, we were ripping them off…" |
| 2 | 92 | Dollar-for-Dollar Tariff Retaliation | 23.0s→57.5s | "We cannot accept what they've offered and we will not give what they've asked." |
| 3 | 84 | Partnership vs Short-Term Transactions | 0.0s→23.0s | "We've consistently proposed long-term partnerships, while America has often pursued short-term transactions." |

**What the AI found that you didn't:** The energy-leverage counter-narrative (AI #1, score 96). The US-Canada trade deficit, the AI's analysis shows, only exists because the US buys so much energy from Canada — 99% of gas imports, 85% of electricity, 60% of crude. The "rip them off" framing is an energy-choice artifact, not evidence of exploitation. That's a viral-worthy counter-narrative with hard stats and a subtle threat about cutting off critical energy supplies.

**The output:** A 35.5s clip (57.5s→93.0s) with a Tier A overlay, written to `exports/tb001_c3_energy_leverage_9x16.mp4`. Side by side with the existing TB-001-C3, this gives you two different angles on the same source — the headline tariff story and the energy-leverage counter-narrative. Both are valid; they're different editorial choices.

---

## Integration Points

### Where it sits in the workflow

```
Source hunting → Tier + log → [Transcript] → [AI selection pass] → Manual pick / reconsider → Overlay → Cut → Export → Distribute
```

The AI pass is optional and sits between sourcing and editing. It doesn't change any downstream step. Your overlay design, cut, export, and distribution workflow is unchanged.

### Costs

- **Transcription:** faster-whisper on CPU, base model. A few minutes for a 10-20min source. Cacheable — the SRT is reused on re-runs.
- **LLM call:** Gemini-3.6-flash, one call per source for ranking + one for content-type classification. Near-instant.
- **Setup:** Python venv + `requirements-local.txt` (yt-dlp, faster-whisper, openai, google-genai, opencv-python). Already installed in `/home/leo/ai-youtube-shorts-gen/venv`.

### What it doesn't do

- It doesn't produce your branded output. The repo's local clipper (OpenCV face tracking) is incompatible with OpenCV 5.x on this system and even when it works, it produces raw center-cropped clips with no overlays. You keep your ffmpeg + PIL pipeline for production.
- It doesn't select sources. It selects moments *within* a source you've already chosen.
- It doesn't screen for sensitive content. That stays as a prior step — run it before the AI pass or after, but don't skip it.
- It doesn't write overlays. The AI gives you a hook sentence and a virality reason; you write the actual overlay text.

---

## Reliability Notes

### Gemini model

`gemini-2.5-flash` is no longer available to new users — the API returns a 404. The current model is `gemini-3.6-flash`, confirmed callable on this account. The `.env` and `config.py` are patched to it. If you re-run, it'll just work.

### OpenCV 5.x

The repo's local clipper calls `cv2.CascadeClassifier(...)` which doesn't exist in OpenCV 5.x (the wheel installed here is 5.0.0.93). The clipper has been patched to fall back to center-crop when face tracking isn't available. The selection layer (transcription + LLM) is unaffected — only the crop step is impacted.

The center-crop fallback produces clean 9:16 output but loses the face-tracking feature. For most news/talking-head sources this is acceptable. If face tracking matters for a specific source, that's a separate fix (install OpenCV 4.x alongside 5.x, or find the correct import path for 5.x).

### Transcription quality

faster-whisper base model on CPU is adequate for English-language news/podcast content. For sources with heavy accent, background music, or non-English speech, results may be weaker. The framework has a `--language` flag to force a specific language code.

### Chunking for long sources

The framework chunks sources over 30min into 20min overlapping segments, runs ranking per chunk, then deduplicates. This means the AI pass works on long-form content (podcasts, livestreams) without a separate setup step. The C1 BBC source (17min) wouldn't have triggered chunking — it's under the 30min threshold.

---

## Decision Rule

**Run the AI pass when you have a source with substantial speech and you're unsure about the best clip point.** The cost is a few minutes of CPU time and one LLM call. The benefit is a second opinion that may surface a stronger hook than your manual instinct.

**Skip it when the trim point is obvious or the source is thin.** A 90s clip with one clear event doesn't need an AI second pass. A promo video with no speech correctly returns "density=low" and nothing useful — don't run it.

**The signal from this spot-check:** the AI framework is worth keeping in the toolkit as a second pass, not as a replacement for manual selection. The C3 case is the proof — it found a better hook than the manual pass on the same source.

---

*Last updated: 2026-08-25 (proven on C3 Reuters trade clip; OpenCV 5.x fallback + Gemini-3.6-flash confirmed working)*
