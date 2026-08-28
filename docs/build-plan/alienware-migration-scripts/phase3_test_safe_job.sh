#!/bin/bash
# Phase 3 of the ByteVerdict Hermes -> Alienware migration.
# Run this ON THE LAPTOP. Requires Phase 1 and Phase 2 to have completed
# first, with `hermes cron list` on the Alienware showing all 12 new
# jobs as [paused].
#
# Tests exactly ONE job before trusting the Alienware with anything
# live: "ByteVerdict YouTube Stats Pull (no-agent)" — read-only (pulls
# view/like/comment counts via the YouTube Data API), zero posting side
# effects, zero cost. This is the safe canary the migration plan called
# for before letting the Posting Agent anywhere near this machine.
#
# It manually triggers that ONE job, prints its output for you to check,
# then re-pauses it. It does NOT touch the Posting Agent, Content Agent,
# or anything that can post/source. It does NOT resume any other job.

set -euo pipefail
REMOTE="leo@100.99.62.20"
HERMES='~/.local/bin/hermes'

echo "== Finding the YouTube Stats Pull job's ID on the Alienware =="
JOB_ID=$(ssh "$REMOTE" "$HERMES cron list" | grep -B1 'ByteVerdict YouTube Stats Pull' | grep -oE '[a-f0-9]{12}' | head -1)
if [ -z "$JOB_ID" ]; then
  echo "ERROR: could not find the job — did Phase 2 run successfully?" >&2
  exit 1
fi
echo "Job ID: $JOB_ID"

echo
echo "== Confirming it's currently paused (expected, from Phase 2) =="
ssh "$REMOTE" "$HERMES cron list" | grep -A1 "$JOB_ID"

echo
echo "== Triggering it manually (read-only, zero cost, safe) =="
ssh "$REMOTE" "$HERMES cron run $JOB_ID"

echo
echo "== Waiting a few seconds, then pulling its last run result =="
sleep 8
ssh "$REMOTE" "$HERMES cron list" | grep -A6 "$JOB_ID"

echo
echo "== Re-pausing it (it stays paused until the real cutover) =="
ssh "$REMOTE" "$HERMES cron pause $JOB_ID" || echo "(already paused after a one-shot run — that's fine)"

echo
echo "== Phase 3 complete. =="
echo "Check the output above: did it run 'ok' and produce real stats,"
echo "or did it error (missing credentials, path issue, etc)?"
echo "Report back before Phase 4 — Phase 4 is the actual cutover."
