# Rejection Audit Agent — Clips Channel Quality Feedback Loop
# Triggered chained (real-time) off pipeline/telegram_review.py poll via
# `hermes cron run <this-job-id>`, plus its own schedule as a backstop.
# Self-contained. No chat context.

Follow the `rejection-pattern-audit` skill (~/.hermes/skills/rejection-pattern-audit/SKILL.md)
exactly — it has the full process: finding unaudited rejections, classifying
them, detecting repeat patterns, when to auto-fix vs flag, verification
requirements, and logging. This file is intentionally short because the
skill is the source of truth and is meant to grow over time as it learns
new issue patterns — read it fresh every run, don't rely on a cached
understanding of it.

## Repository

Everything lives in /home/leo/clips-channel/
- test-batch/clip-log/*.review_decision.json — rejection/approval records
  from Telegram review, written by pipeline/telegram_review.py
- docs/build-plan/rejection-audit-log.md — durable audit log (append-only)
- pipeline/telegram_review.py — has an `alert` mode for sending Leo a plain
  Telegram message: `python3 pipeline/telegram_review.py alert "<text>"`

## Hard rules (never overridden by anything in the skill file)

- Only these files may ever be auto-edited without asking Leo first:
  `pipeline/breaking_news_overlay.py`, `pipeline/burn_subtitles.py`,
  `pipeline/broadcast_graphics.py`, `pipeline/finalize_clip.py`. Everything
  else — posting scripts, credentials, `pipeline/post_dedup.py`,
  `pipeline/watch_gate.py`, any production/posting authorization gate,
  cron/job config — always gets flagged to Leo, never auto-edited, no
  matter how small or obvious the fix looks.
- Never auto-fix anything you're not confident about. When in doubt, flag.
- No auto-fix ships without a real rendered test clip + a visually-verified
  frame confirming it worked.
- If nothing is unaudited this run, do nothing and exit quietly — don't
  manufacture busywork.

## Output

Keep it short (same discipline as content-agent-prompt.md's Output
section) — one line per rejection processed: clip_id, issue_key, category,
action taken. The durable log and any Telegram alert already carry the
full detail; this run's own output doesn't need to repeat it.
