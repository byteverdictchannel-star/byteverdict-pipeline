#!/usr/bin/env bash
# Submit a render script to the Alienware worker for automatic processing.
#
# Usage: scripts/submit-render.sh <script-name.py>
# Example: scripts/submit-render.sh render_tb012.py
#
# This is the explicit "submit" step: nothing renders until you run this.
# It syncs the current test-batch/ state (so the script's input files are
# there), then drops the script into the Alienware's queue/incoming/ —
# the render-watcher service picks it up within 15s and runs it on its own.
# Results land back here automatically via the cron-driven pull-results.sh.

set -euo pipefail

WORKER_HOST="leo@192.168.0.224"
LOCAL_BASE="/home/leo/clips-channel/test-batch"
REMOTE_BASE="/home/leo/clips-channel/test-batch"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <script-name.py>" >&2
  exit 1
fi

SCRIPT_NAME="$1"

if [ ! -f "$LOCAL_BASE/$SCRIPT_NAME" ]; then
  echo "Error: $LOCAL_BASE/$SCRIPT_NAME not found" >&2
  exit 1
fi

echo "==> Syncing test-batch to Alienware..."
ssh "$WORKER_HOST" "mkdir -p $REMOTE_BASE"
rsync -az --exclude='__pycache__' --exclude='*.pyc' \
  "$LOCAL_BASE"/ "$WORKER_HOST:$REMOTE_BASE"/

echo "==> Submitting $SCRIPT_NAME to render queue..."
scp -q "$LOCAL_BASE/$SCRIPT_NAME" "$WORKER_HOST:/home/leo/clips-channel/queue/incoming/$SCRIPT_NAME"

echo "==> Submitted. The Alienware will pick it up within ~15s and render on its own."
echo "    You'll get a push notification on success or failure."
echo "    Run scripts/pull-results.sh (or wait for the cron job) to fetch finished output."
