#!/usr/bin/env bash
# Run a clips-channel render script on the Alienware worker instead of locally.
#
# Usage: scripts/remote-render.sh <script-name.py>
# Example: scripts/remote-render.sh render_tb006.py
#
# What it does:
#   1. Syncs test-batch/ (captures, exports, overlays, the scripts themselves)
#      to the same path on the Alienware, so the script runs completely
#      unmodified — no path rewriting, no behavior differences.
#   2. Runs the script there with the Alienware's ffmpeg 7.0.2-static (same
#      binary as this machine) and python3-pil 10.2.0 (same version).
#   3. Syncs the results (exports/, platform-exports/, ready-to-post/,
#      clip-log/) back here.
#
# Nothing here posts anywhere or makes any decision — it only produces files
# in the same place they'd land if you ran the script locally. The posting
# verification gate (SKILL.md section 11) still applies exactly as before.

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

echo "==> Running $SCRIPT_NAME on Alienware..."
ssh "$WORKER_HOST" "cd $REMOTE_BASE && PATH=\$HOME/.local/bin:\$PATH python3 $SCRIPT_NAME"

echo "==> Syncing results back..."
for dir in exports platform-exports ready-to-post clip-log; do
  rsync -az "$WORKER_HOST:$REMOTE_BASE/$dir/" "$LOCAL_BASE/$dir/" 2>/dev/null || true
done

echo "==> Done. Review output in $LOCAL_BASE/exports and platform-exports before posting."
echo "    (Posting verification gate still applies — watch + approve before any upload.)"
