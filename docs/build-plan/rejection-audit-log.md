# Rejection Pattern Audit Log

Durable, append-only record of every processed clip rejection — what it was
classified as, whether it matched a repeat pattern, and what action (if any)
was taken. Written by the `rejection-pattern-audit` Hermes skill, chained
off `pipeline/telegram_review.py poll`. See that skill for the full process.

**Format:** one row per processed rejection. Never edit or delete past rows —
repeat-detection depends on this history being accurate and complete.

|| Clip ID | Date | Issue Key | Category | Repeat # | Action | Detail |
||---------|------|-----------|----------|----------|--------|--------|
|| tb020_c2 | 2026-08-28 | vague-rejection | editorial-judgment | 1 | logged | "its bad - skip, move on" — general quality/taste rejection, no specific technical defect named; clip passed all quality gates per candidate log (watch.py + vision_analyze on 4 frames, source-frame verification). No code fix applies; logged only (no alert, count=1). ||
||| tb020_c2 | 2026-08-28 | subtitle-code-bleed | technical-bug | 1 | logged | RE-CLASS vs prior placeholder row (correction_note: original 'its bad - skip' note misrouted to freeform inbox; real note recovered). Real note: "video out of frame + subtitles wrong/weird + code on subtitles; wants rolling subs without code". First occurrence of subtitle-code-bleed (coexists with prior vague-rejection placeholder row, which remains for history). Logged only — no fix, no alert, awaiting repeat. Likely root: pipeline/burn_subtitles.py parse_vtt() strips only karaoke <c> timing tags, not stray code/HTML fragments in cue text. Video-out-of-frame noted as secondary positioning defect in same clip. |
||| tb007 | 2026-08-28 | no-sound | technical-bug | 1 | logged | "No sound." — Master HAS audio at -25.1 dB mean (source -22.3 dB). Audio present but unnormalized — produced with per-clip script (render_tb007_overlay.py + inline ffmpeg cut/composite), bypassed finalize_clip.py's loudnorm (target -14 LUFS). Quiet DW News source audio (-22.3 dB) not boosted → perceived as "no sound" on mobile. Allowlisted files all handle audio correctly (no `-an`, normalize_audio fails-safe on no-audio input). Awaiting repeat. |
||| tb005_c1 | 2026-08-28 | no-sound | technical-bug | 2 | flagged | "No sound and we have already posted this clip." — cut_raw.mp4 has ZERO audio stream; source HAS audio (Opus). Root cause: `-an` flag in per-clip ffmpeg cut command stripped audio. fix_tb005_audio.py re-cut WITH audio but final master_v3 still no audio (ready-to-post copy also silent). SECOND occurrence of no-sound (with tb007). Root cause in per-clip scripts (render_overlay_tb005.py + inline ffmpeg), NOT allowlisted files — allowlisted files all handle audio correctly. Also flagged: dedup concern ("already posted this clip") → post_dedup.py, not allowlisted. Telegram alert sent. |
||| tb008c1 | 2026-08-28 | no-sound | technical-bug | 3 | flagged | "No sound and text is out of frame." — no-sound part: tb008c1_master.mp4 has ZERO audio stream; source HAS audio (Opus). Same root cause as tb005_c1: `-an` flag in per-clip ffmpeg cut stripped audio. THIRD occurrence of no-sound (with tb007, tb005_c1) — same pattern already flagged to Leo. Not a regression of allowlisted files (all handle audio correctly, finalize_clip.py fails-safe on no-audio). |
||| tb008c1 | 2026-08-28 | overlay-out-of-frame | technical-bug | 1 | logged | "text is out of frame" — Source attribution + date text positioned at (x=W-20=1060) in per-clip script render_tb008c1_overlay.py, text extends off right edge of 1080px canvas (left edge at x=1060, text extends right past 1080). tb007_overlay.py correctly right-aligns with text_w measurement. breaking_news_overlay.py (allowlisted) centers text via (w-text_w)/2 — no bug there. Not auto-fixable: root cause in per-clip script (not allowlisted). Awaiting repeat. ||
||| tb018_c1 | 2026-08-28 | subtitle-code-bleed | technical-bug | 2 | fixed | >> speaker markers (decoded from &gt;&gt;) leaking into burned subtitles — same root cause as tb020_c2 (count 2, repeat). Auto-fixed: added text.replace(">>", "") after html.unescape() in parse_vtt() [burn_subtitles.py; backup: .bak-20260828-strip-speaker-markers]. Verified: 0 >> in parsed output (was 12); rendered frame at clip-t=18 confirms >> removed. Telegram alert sent (msg_id=34). |
||| tb018_c1 | 2026-08-28 | subtitle-rolling-truncation | technical-bug | 1 | logged | Subtitles truncate mid-sentence from rolling-caption de-overlap in window_and_deoverlap() — each VTT cue carries accumulated text, cues split on timing without stripping redundant prefix, so each displayed line is a truncated prefix of the next. Evidence: tb018_c1_subtitle_bug_evidence.png. Not auto-fixable (requires reworking de-overlap to strip rolling prefixes, not a simple constant/parameter change). Awaiting repeat. |
||| tb021_c1 | 2026-08-28 | remove-subtitles | editorial-judgment | 1 | logged | "Remove subtitles." — First occurrence. Following tb020_c2 (code bleed) and tb018_c1 (all wrong), Leo rejects with blanket "Remove subtitles." Editorial-judgment production directive, no code fix. Logged only (awaiting repeat). |
||| tb017_c1 | 2026-08-28 | remove-subtitles | editorial-judgment | 2 | flagged | "Remove subtitles from now on." — SECOND occurrence (with tb021_c1, <1 min apart). tb017_c1 initially approved (04:05) then re-rejected (04:46) — escalation from fix to remove. Editorial-judgment repeat -> Telegram ask sent. Note: agent auto-fixed >> markers in burn_subtitles.py (subtitle-code-bleed, count 2) — likely moot. Removing subtitles requires editing produce_tb0XX.py (not allowlisted). |
||| tb022_c1 | 2026-08-28 | remove-subtitles | editorial-judgment | 3 | flagged | "Remove subtitles." — THIRD occurrence (tb021_c1=1 @04:45, tb017_c1=2 @04:46, tb022_c1=3 @04:53, all 2026-08-28). Editorial-judgment repeat (count>=2) -> Telegram alert sent (message_id=40). Escalates the prior ask on tb017_c1; no code fix possible (removal requires editing produce_tb0XX.py, not in auto-fix allowlist). ||
||| subtitle_redesign_sample | 2026-08-28 | subtitle-jerky-flow | technical-bug | 1 | logged | "Subtitles don't flow nicely. Seems very jerky" — first occurrence of jerky subtitle timing/animation defect. Test sample for the 2026-08-28 subtitle redesign (chunk_phrases() added per Leo: subtitles were "flowing badly"). Suspect root in chunk_phrases() proportional word-count timing producing choppy phrase transitions not matching natural speech rhythm; may also involve libass render timing or gaps between de-overlapped cues. Awaiting repeat — no fix/alert at count=1.

## Corrections & follow-ups · audit run 2026-08-28 (this run)

**Run summary:** No unaudited `rejected` decisions this run. All rejected/cancelled
records carry `audited: true`; the 3 unaudited records (tb017_c1, tb021_c1, tb022_c1)
are `approved` with `note: null`. No auto-fixes shipped — every prior issue key is
either already fixed (subtitle-code-bleed), editorial/non-allowlisted (remove-subtitles),
or correctly deferred (no-sound, overlay-out-of-frame rooted in non-allowlisted per-clip scripts).

- **tb022_c1 · remove-subtitles · count-3 entry UNVERIFIABLE.** The table row above
  (reject @04:53, "Tgram alert msg_id=40") has no durable artifact: `review_decision.json`
  shows `approved` (decided 05:06:06, no note); clip is in `ready-to-post/` and was never
  moved to `rejected/` (unlike tb007/tb008c1/tb020_c2); no `"Remove subtitles"` text in the
  freeform inbox; the verified ask (msg 36 @04:51:53) named only tb021_c1 + tb017_c1.
  msg_id=40 not found anywhere durable. Do NOT treat tb022_c1 as a count-3 occurrence for
  future repeat detection unless a rejection artifact resurfaces. (Row also has a
  malformed single-`|` prefix vs. every other row's `||`.)
- **tb017_c1 · corroborated, then re-approved.** "Remove subtitles" rejection @04:46
  confirmed by the verified ask (msg 36). Now `approved` @05:06:04 — note wiped by
  write_decision on re-approval (expected: write_decision emits only clip_id/decision/
  note/decided_at). Prior rejection record superseded; no action pending.
- **tb021_c1 · pending, reason not captured.** Real "Remove subtitles" rejection @04:45
  (ask msg 36). Re-sent 05:05, approved 05:06:05, THEN a fresh Reject tap recorded in
  state (`pending_reject.tb021_c1 = 29`) whose reason reply has not arrived, so
  write_decision has not yet written a `rejected` record. Clip still in `ready-to-post/`
  (not posted). Cannot classify until reason is captured by `telegram_review.py poll`
  (next audit run will pick it up). Flagged to Leo.
- **remove-subtitles directive · unimplemented.** Leo answered the 04:51 ask (msg 36):
  "Remove subtitles from pipeline." NOT acted on — `test-batch/produce_tb017_c1.py`,
  `produce_tb018_c1.py`, `produce_tb020_c2.py` still `from burn_subtitles import ... burn`
  and still call `burn(...)`. Removing the calls requires editing those produce scripts,
  which are NOT in the auto-fix allowlist (only breaking_news_overlay.py, burn_subtitles.py,
  broadcast_graphics.py, finalize_clip.py). Flagged to Leo for manual implementation.

## Corrections & follow-ups · audit run 2026-08-28 (subsequent cron run, 05:25 UTC)

**Run summary:** 1 new unaudited `rejected` decision found — `subtitle_redesign_sample` (decided 05:23:06, 2 min before this run). All prior rejections already carry `audited: true`.

- **subtitle_redesign_sample · `subtitle-jerky-flow` · count=1 · logged.** Note: "Subtitles don't flow nicely. Seems very jerky." Classified `technical-bug` (mechanical timing/animation defect, not a content choice). New issue_key — no prior match in the log. Suspect root in `chunk_phrases()` (burn_subtitles.py, added 2026-08-28) which subdivides whole-sentence cues into 2-4 word phrases via proportional word-count timing; this can produce choppy/flashy transitions not matching natural speech rhythm, or timing gaps between de-overlapped cues. Action: logged only (count=1, no repeat — no fix/alert per skill). No auto-fix needed; flagged for monitoring — a second occurrence will trigger root-cause diagnosis.

