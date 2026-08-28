# ByteVerdict Config Audit — 2026-08-27 18:45 (+04)

Verified live by Hermes (CoS). Every claim below backed by tool output this session,
not by the previous session's handoff. Supersedes the unaudited checklist in the
interrupted HANDOFF_2026-08-27.md (that file was never actually written to disk).

## Verdict: paid tier IS live. Two new problems found.

## ✅ Persisted from previous session

| Item | State | Evidence |
|---|---|---|
| Content Agent cron pinned paid | LIVE | job 917dd3e81af8 → model `poolside/laguna-s-2.1`, provider `openrouter`, every 60m. Ran today 16:37→17:15 (38m, completed); currently running again since 18:25. |
| Posting Agent cron pinned paid | LIVE | job 7a8c16fd7b21 → same pin, every 180m. Ran today 15:37→15:47 (10m, completed). |
| OpenRouter paid tier | CONFIRMED | `/auth/key`: `is_free_tier: false`, usage $1.10, no limit. |
| Laguna latency | VERIFIED | Live probe of `poolside/laguna-s-2.1`: **0.6s** round-trip. Paid-tier latency is a non-issue; no clip latency test needed to validate the tier. |
| Cost plugin | LOADED + FIRING | `~/.hermes/plugins/byteverdict-cost/` on disk; two ALERT entries today in desktop.log flagging unpinned models; pricing.json has laguna-s/xs entries. |
| YouTube gate | HARDENED | posting-agent-prompt.md §3c: one gate for every platform, YouTube exemption withdrawn, "silence is never approval", no timeout auto-approval. No `posting-autonomous.md` marker exists → gate active. |

## ❌ Audit commands in the handoff were wrong

- `~/.hermes/jobs.json` does not exist — real cron state is `~/.hermes/cron/jobs.json`.
- Per-job logs are not in `~/.hermes/logs/<job-id>*` — run history lives in
  `~/.hermes/cron/executions.db` (sqlite, table `executions`).
- `$OPENROUTER_API_KEY` is not in the shell env — key is stored in `~/.hermes/auth.json`.

## 🚨 New problems (not in any handoff)

1. **Gateway is STOPPED.** `hermes status`: systemd user service installed but stopped;
   no gateway process running. ALL 11 cron jobs (Content, Posting, status-check every 15m,
   YT stats, IG token refresh) will NOT fire until it's started.
   Content Agent's next run 19:25 and Posting Agent's 18:47 are at risk right now.
2. **state.db is corrupted.** `PRAGMA quick_check` on `~/.hermes/state.db` fails
   (btreeInitPage error code 11, tree 50). desktop.log 14:37 shows the matching runtime
   error: `sqlite3.DatabaseError: database disk image is malformed` in
   `hermes_state.py:resolve_session_id`. Session-history reads can fail or return garbage.
3. **WhatsApp delivery broken (known, confirmed):** every job delivery errors
   `platform 'whatsapp' not configured/enabled`. bridge.js process IS running, but the
   gateway-side platform state was `retrying` (`whatsapp_bridge_exited`) at last state write.
   Restarting the gateway is the first diagnostic step for this too.
4. **vision_analyze 401** (from batch file, not re-tested): automated visual QA fell back
   to pixel analysis only for today's batch. Either fix the image-model auth or accept
   pixel-analysis + manual review.

## ⏳ Waiting on Leo (this is the gate working as designed)

`test-batch/daily-batch-2026-08-27.md` is PENDING approval — one clip:
- **tb007** — CIA Director's secret Moscow visit (DW News), 40.0s, TikTok/YT-Shorts/IG.
  Checklist passed except vision check (see #4). Approve by creating
  `test-batch/daily-batch-2026-08-27.approved`.

Also noted in the batch: tb006 IG retry pending (rupload.facebook.com was unreachable on 2026-08-26).

## Actions taken this session (verified)

- **WhatsApp root cause FOUND + FIXED:** `platforms.whatsapp.enabled: false` in config.yaml
  AND `WHATSAPP_ENABLED=false` in .env — flipped sometime after the Aug 25 backup.
  bridge.js was healthy the whole time (`/health` = connected, paired session intact).
  Re-enabled both (backups: `config.yaml.bak-20260827-pre-wa-reenable`, `.env.bak-…`).
  Gateway restarted → log shows `✓ whatsapp connected`, 1 platform, 1 channel target.
- **Gateway:** started; then STOPPED again deliberately for the state.db fix (see below).
  All 11 cron jobs dormant until it's back.
- **state.db:** corruption isolated to `messages_fts_trigram_data` (derived FTS5 search
  index, tree 50). Canonical data proven intact by `hermes sessions recover --inspect-only`
  (10,169 messages / 46 sessions, 0 warnings). Full pre-work backup at
  `~/.hermes/backups/manual/state.db.pre-fts-repair-20260827`.
  - `hermes doctor --fix` and `hermes sessions repair` both fail: PID 5828 (the desktop
    app's own `hermes serve` backend) holds the DB — can't be stopped without closing
    the app. This also caused the Posting Agent's 18:49 run to fail (14s, no cost).
  - Offline recovery to a new DB produced a PARTIAL copy (source mutated mid-copy by the
    live writer) — deleted; do not use partial copies.
  - **FIX REQUIRES A 2-MINUTE WINDOW WITH HERMES DESKTOP CLOSED** — procedure handed to
    Leo (see chat 2026-08-27 ~19:10): close desktop → `hermes sessions repair && hermes
    gateway start` → reopen desktop. Hermes verifies afterwards.

## Recommended order of operations (updated)

1. Leo: run the state.db swap window (procedure above). ~2 min.
2. Hermes verifies: integrity clean, WhatsApp delivering, cron firing.
3. Leo: approve/reject today's batch (tb007 CIA/Moscow) — `test-batch/daily-batch-2026-08-27.approved`.
4. Then resume the priority queue: Alienware SSH worker integration (machine is headless,
   NVENC verified, per docs/alienware-headless-handoff.md 18:30 today).
