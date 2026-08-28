#!/bin/bash
# Phase 2 of the ByteVerdict Hermes -> Alienware migration.
# Run this ON THE LAPTOP. Requires Phase 1 to have completed first.
#
# Creates all 12 ByteVerdict cron jobs on the Alienware, exactly matching
# the laptop's current definitions — then immediately pauses every job
# it creates. Nothing goes active. The laptop's jobs are untouched.
#
# NOT included: "ByteVerdict Weekly Organization Review" — shells out to
# the `claude` CLI, which is not installed on the Alienware. Left on the
# laptop pending Leo's decision.
#
# Design note: the 4 agent-job prompts (some containing backticks, single
# quotes, etc.) are NOT interpolated into the SSH command string locally
# — that risks the local/remote shell misparsing special characters.
# Instead each prompt is copied to the Alienware as a plain file first,
# and the remote shell reads it back with $(cat ...) itself, so quoting
# only has to survive being written to disk, not a shell round-trip.

set -euo pipefail
REMOTE="leo@100.99.62.20"
HERMES='~/.local/bin/hermes'
LOCAL_PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/prompts" && pwd)"

echo "== Copying prompt files to the Alienware =="
ssh "$REMOTE" 'mkdir -p /tmp/bv-cron-prompts'
scp -q "$LOCAL_PROMPTS_DIR"/*.txt "$REMOTE:/tmp/bv-cron-prompts/"
ssh "$REMOTE" 'ls /tmp/bv-cron-prompts/'

echo
echo "== Recording which job IDs exist on the Alienware before we start =="
ssh "$REMOTE" "$HERMES cron list" | grep -oE '^  [a-f0-9]{12}' | tr -d ' ' > /tmp/alienware_jobs_before.txt || true
echo "Existing jobs before: $(wc -l < /tmp/alienware_jobs_before.txt)"

echo
echo "== 1/12: Content Agent =="
ssh "$REMOTE" bash -s <<'REMOTE'
set -euo pipefail
~/.local/bin/hermes cron create '*/25 * * * *' \
  --name 'Content Agent — clips channel sourcing + production' \
  --provider openrouter --model poolside/laguna-s-2.1 \
  --workdir /home/leo/clips-channel --deliver origin \
  --skill clips-channel-production --skill humanizer \
  --skill short-form-video-production --skill youtube-full \
  "$(cat /tmp/bv-cron-prompts/content-agent.txt)"
REMOTE

echo
echo "== 2/12: Posting Agent =="
ssh "$REMOTE" bash -s <<'REMOTE'
set -euo pipefail
~/.local/bin/hermes cron create '*/20 * * * *' \
  --name 'Posting Agent — clips channel auto-publish' \
  --provider openrouter --model poolside/laguna-s-2.1 \
  --workdir /home/leo/clips-channel --deliver origin \
  --skill clips-channel-production --skill ig-auto-post-setup \
  "$(cat /tmp/bv-cron-prompts/posting-agent.txt)"
REMOTE

echo
echo "== 3/12: Status Check (no-agent) =="
ssh "$REMOTE" "$HERMES cron create 'every 15m' \
  --name 'Status Check (no-agent)' \
  --no-agent --script status-check.sh --deliver origin"

echo
echo "== 4/12: ByteVerdict Organization Check (no-agent) =="
ssh "$REMOTE" "$HERMES cron create 'every 1440m' \
  --name 'ByteVerdict Organization Check (no-agent)' \
  --no-agent --script repo-organization-check.sh --deliver origin"

echo
echo "== 5/12: ByteVerdict IG Token Refresh (no-agent) =="
ssh "$REMOTE" "$HERMES cron create '0 4 * * 1' \
  --name 'ByteVerdict IG Token Refresh (no-agent)' \
  --no-agent --script ig-token-refresh.sh --deliver origin"

echo
echo "== 6/12: ByteVerdict YouTube Stats Pull (no-agent) — SAFE TEST JOB =="
ssh "$REMOTE" "$HERMES cron create '0 5 * * *' \
  --name 'ByteVerdict YouTube Stats Pull (no-agent)' \
  --no-agent --script youtube-stats-pull.sh --deliver origin"

echo
echo "== 7/12: ByteVerdict YouTube Trending Pull (no-agent) =="
ssh "$REMOTE" "$HERMES cron create '0 5 * * *' \
  --name 'ByteVerdict YouTube Trending Pull (no-agent)' \
  --no-agent --script youtube-trending-pull.sh --deliver local"

echo
echo "== 8/12: ByteVerdict Breaking News Detect (no-agent) =="
ssh "$REMOTE" "$HERMES cron create '*/30 * * * *' \
  --name 'ByteVerdict Breaking News Detect (no-agent)' \
  --no-agent --script youtube-breaking-detect.sh --deliver local"

echo
echo "== 9/12: ByteVerdict Telegram Review Poll (no-agent) =="
ssh "$REMOTE" "$HERMES cron create '* * * * *' \
  --name 'ByteVerdict Telegram Review Poll (no-agent)' \
  --no-agent --script telegram-review-poll.sh --deliver local"

echo
echo "== 10/12: ByteVerdict Rejection Pattern Audit =="
ssh "$REMOTE" bash -s <<'REMOTE'
set -euo pipefail
~/.local/bin/hermes cron create '*/30 * * * *' \
  --name 'ByteVerdict Rejection Pattern Audit' \
  --provider openrouter --model poolside/laguna-s-2.1 \
  --workdir /home/leo/clips-channel --deliver local \
  "$(cat /tmp/bv-cron-prompts/rejection-audit.txt)"
REMOTE

echo
echo "== 11/12: ByteVerdict Telegram Brain =="
ssh "$REMOTE" bash -s <<'REMOTE'
set -euo pipefail
~/.local/bin/hermes cron create '*/10 * * * *' \
  --name 'ByteVerdict Telegram Brain' \
  --provider openrouter --model poolside/laguna-s-2.1 \
  --workdir /home/leo/clips-channel --deliver local \
  "$(cat /tmp/bv-cron-prompts/telegram-brain.txt)"
REMOTE

echo
echo "== 12/12: ByteVerdict Stale Clip Expiry (no-agent) =="
ssh "$REMOTE" "$HERMES cron create '*/30 * * * *' \
  --name 'ByteVerdict Stale Clip Expiry (no-agent)' \
  --no-agent --script expire-stale-clips.sh --deliver local"

echo
echo "== Cleaning up prompt files from the Alienware's /tmp =="
ssh "$REMOTE" 'rm -rf /tmp/bv-cron-prompts'

echo
echo "== Pausing every job just created (nothing goes active) =="
ssh "$REMOTE" "$HERMES cron list" | grep -oE '^  [a-f0-9]{12}' | tr -d ' ' > /tmp/alienware_jobs_after.txt
NEW_JOBS=$(comm -13 <(sort /tmp/alienware_jobs_before.txt) <(sort /tmp/alienware_jobs_after.txt))
for jid in $NEW_JOBS; do
  echo "  pausing $jid"
  ssh "$REMOTE" "$HERMES cron pause $jid"
done

echo
echo "== Phase 2 complete. Verify everything is paused: =="
echo "  ssh $REMOTE '$HERMES cron list'"
echo "All 12 new jobs should show [paused], not [active]."
