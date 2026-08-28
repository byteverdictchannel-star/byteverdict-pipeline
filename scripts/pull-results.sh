#!/usr/bin/env bash
# Pull finished (done or failed) render results back from the Alienware.
# Run manually, or via cron every few minutes for fully-automatic sync-back.
#
# For each job in queue/done/ or queue/failed/ on the Alienware that hasn't
# been pulled yet (tracked via a local marker file), this syncs the relevant
# output folders back and records the pull so it isn't re-fetched.

set -euo pipefail

WORKER_HOST="leo@192.168.0.224"
LOCAL_BASE="/home/leo/clips-channel/test-batch"
REMOTE_BASE="/home/leo/clips-channel/test-batch"
PULLED_MARKER_DIR="/home/leo/clips-channel/.pulled"

mkdir -p "$PULLED_MARKER_DIR"

for status in done failed; do
  jobs=$(ssh "$WORKER_HOST" "ls /home/leo/clips-channel/queue/$status/ 2>/dev/null" || true)
  for job in $jobs; do
    marker="$PULLED_MARKER_DIR/${status}-${job}"
    [ -f "$marker" ] && continue

    if [ "$status" = "done" ]; then
      echo "==> Pulling results for $job (succeeded)"
      for dir in exports platform-exports ready-to-post clip-log; do
        rsync -az "$WORKER_HOST:$REMOTE_BASE/$dir/" "$LOCAL_BASE/$dir/" 2>/dev/null || true
      done
    else
      echo "==> $job FAILED on the worker — see notification/logs, nothing to pull"
    fi

    touch "$marker"
  done
done
