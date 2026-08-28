#!/bin/bash
# Phase 4 of the ByteVerdict Hermes -> Alienware migration.
# *** DO NOT RUN THIS UNTIL PHASE 3 HAS BEEN VERIFIED AND YOU'VE ***
# *** CONFIRMED WITH CLAUDE THAT IT'S SAFE TO PROCEED.            ***
#
# This is the actual cutover. It:
#   1. Pauses all 12 ByteVerdict jobs on the LAPTOP.
#   2. Resumes the matching 12 jobs on the ALIENWARE.
# In that order, so there is never a moment where both machines are
# running the same jobs at once (the double-post/double-source risk
# the migration plan explicitly called out).
#
# "ByteVerdict Weekly Organization Review" is deliberately left running
# on the laptop — it shells out to the `claude` CLI, not installed on
# the Alienware. Not part of this cutover; separate decision.

set -euo pipefail
REMOTE="leo@100.99.62.20"
HERMES='~/.local/bin/hermes'

LAPTOP_JOB_IDS=(
  917dd3e81af8   # Content Agent
  7a8c16fd7b21   # Posting Agent
  a7f0a84adfbf   # Status Check
  11f3e0088914   # ByteVerdict Organization Check
  bdb7be778d7b   # ByteVerdict IG Token Refresh
  447219b09ea0   # ByteVerdict YouTube Stats Pull
  cfd7324492be   # ByteVerdict YouTube Trending Pull
  1ea69afb1d87   # ByteVerdict Breaking News Detect
  e2cedeb337be   # ByteVerdict Telegram Review Poll
  adfe3f9d5cfd   # ByteVerdict Rejection Pattern Audit
  13bb45b1200d   # ByteVerdict Telegram Brain
  669de17b3699   # ByteVerdict Stale Clip Expiry
)

JOB_NAMES=(
  "Content Agent"
  "Posting Agent"
  "Status Check"
  "ByteVerdict Organization Check"
  "ByteVerdict IG Token Refresh"
  "ByteVerdict YouTube Stats Pull"
  "ByteVerdict YouTube Trending Pull"
  "ByteVerdict Breaking News Detect"
  "ByteVerdict Telegram Review Poll"
  "ByteVerdict Rejection Pattern Audit"
  "ByteVerdict Telegram Brain"
  "ByteVerdict Stale Clip Expiry"
)

echo "== Step 1: pausing all 12 ByteVerdict jobs on the LAPTOP =="
for jid in "${LAPTOP_JOB_IDS[@]}"; do
  echo "  pausing $jid (laptop)"
  hermes cron pause "$jid"
done

echo
echo "== Confirming laptop jobs are paused =="
hermes cron list | grep -B2 -A1 -E "$(IFS='|'; echo "${JOB_NAMES[*]}")" | grep -E 'Name:|\[paused\]|\[active\]'

echo
echo "== Step 2: resuming the matching 12 jobs on the ALIENWARE =="
for name in "${JOB_NAMES[@]}"; do
  jid=$(ssh "$REMOTE" "$HERMES cron list" | grep -B1 "$name" | grep -oE '[a-f0-9]{12}' | head -1)
  if [ -z "$jid" ]; then
    echo "  WARNING: could not find '$name' on the Alienware — skipping, investigate manually" >&2
    continue
  fi
  echo "  resuming $jid ($name, alienware)"
  ssh "$REMOTE" "$HERMES cron resume $jid"
done

echo
echo "== Cutover complete. Verify: =="
echo "  Laptop:    hermes cron list   (12 ByteVerdict jobs should show [paused])"
echo "  Alienware: ssh $REMOTE '$HERMES cron list'   (12 jobs should show [active])"
echo
echo "Watch the next few ticks closely — especially the Posting Agent's"
echo "next run — to confirm nothing double-fires."
