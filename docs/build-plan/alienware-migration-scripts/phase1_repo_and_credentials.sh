#!/bin/bash
# Phase 1 of the ByteVerdict Hermes -> Alienware migration.
# Run this ON THE LAPTOP (leo-NBLB-WAX9N), not on the Alienware.
#
# What it does, in order:
#   1. Renames the pre-existing render-worker directory on the Alienware
#      aside (does NOT delete anything).
#   2. Runs `hermes setup --non-interactive` on the Alienware to scaffold
#      ~/.hermes/.env and config.yaml.
#   3. Writes exactly 3 secrets into the Alienware's .env — read from
#      THIS machine's own .env, piped directly over SSH, never printed
#      to this terminal. Everything else in the laptop's .env (Anthropic
#      key, WhatsApp config, etc.) is deliberately left behind.
#   4. rsyncs the clips-channel repo (minus .git — not needed for cron
#      jobs to run) to the Alienware at the same path, including
#      credentials/ and test-batch/ (preserves in-flight clip state).
#
# Nothing here touches cron jobs. Nothing here is live/active yet.
# Safe to run — creates and copies, does not start anything.

set -euo pipefail
REMOTE="leo@100.99.62.20"

echo "== Step 1: rename aside the render-worker directory =="
ssh "$REMOTE" 'mv /home/leo/clips-channel /home/leo/clips-channel-render-worker-backup-$(date +%Y%m%d)'
ssh "$REMOTE" 'ls -d /home/leo/clips-channel*'

echo
echo "== Step 2: hermes setup --non-interactive on the Alienware =="
ssh "$REMOTE" 'cd ~/.hermes/hermes-agent && ~/.local/bin/hermes setup --non-interactive'

echo
echo "== Step 3: write OPENROUTER_API_KEY, FB_APP_ID, FB_APP_SECRET =="
OPENROUTER_KEY=$(grep '^OPENROUTER_API_KEY=' ~/.hermes/.env | head -1 | cut -d= -f2-)
FB_ID=$(grep '^FB_APP_ID=' ~/.hermes/.env | head -1 | cut -d= -f2-)
FB_SECRET=$(grep '^FB_APP_SECRET=' ~/.hermes/.env | head -1 | cut -d= -f2-)

if [ -z "$OPENROUTER_KEY" ] || [ -z "$FB_ID" ] || [ -z "$FB_SECRET" ]; then
  echo "ERROR: one or more source values were empty locally — aborting before writing anything." >&2
  exit 1
fi

ssh "$REMOTE" 'cat >> ~/.hermes/.env' <<EOF
OPENROUTER_API_KEY=$OPENROUTER_KEY
FB_APP_ID=$FB_ID
FB_APP_SECRET=$FB_SECRET
EOF
unset OPENROUTER_KEY FB_ID FB_SECRET

echo "Wrote 3 keys. Verifying presence (length/prefix only, no values):"
ssh "$REMOTE" '
for k in OPENROUTER_API_KEY FB_APP_ID FB_APP_SECRET; do
  v=$(grep "^${k}=" ~/.hermes/.env | tail -1 | cut -d= -f2-)
  echo "  $k: present, length=${#v}, prefix=${v:0:4}..."
done
'

echo
echo "== Step 4: rsync clips-channel repo (minus .git) to the Alienware =="
rsync -az --exclude='.git' /home/leo/clips-channel/ "$REMOTE:/home/leo/clips-channel/"

echo
echo "== Step 5: sync no-agent cron scripts =="
# On the laptop, ~/.hermes/scripts is a symlink to /srv/hermes/scripts (a
# system path needing sudo to recreate). Simplest equivalent on the
# Alienware: a real directory at ~/.hermes/scripts containing copies of
# the same files — no sudo needed, and --script only cares that the file
# exists under ~/.hermes/scripts/.
ssh "$REMOTE" 'mkdir -p ~/.hermes/scripts'
rsync -az /home/leo/.hermes/scripts/ "$REMOTE:/home/leo/.hermes/scripts/"
ssh "$REMOTE" 'ls -la ~/.hermes/scripts/'

echo
echo "== Phase 1 complete. Verify: =="
echo "  ssh $REMOTE 'ls /home/leo/clips-channel && ls /home/leo/clips-channel/credentials'"
echo "  ssh $REMOTE '~/.local/bin/hermes doctor'"
