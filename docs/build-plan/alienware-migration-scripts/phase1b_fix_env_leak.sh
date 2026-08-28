#!/bin/bash
# Phase 1b — remediation. Run this ON THE LAPTOP before proceeding to
# Phase 2. `hermes setup --non-interactive` in Phase 1 had a side effect
# nobody anticipated: it wrote real personal values into the Alienware's
# .env (WhatsApp linkage, a transcript API key, some Browserbase/FB-URL
# settings) — none of which were ever supposed to move. Confirmed via
# length-comparison against the laptop's own values (exact match on every
# field checked), not guessed.
#
# This backs up the current (contaminated) .env, then replaces it with
# a clean file containing ONLY the 3 approved keys:
#   OPENROUTER_API_KEY, FB_APP_ID, FB_APP_SECRET
# Same as Phase 1 Step 3 — values read from the laptop, piped straight
# over SSH, never printed to this terminal.

set -euo pipefail
REMOTE="leo@100.99.62.20"

echo "== Backing up the current (contaminated) .env =="
ssh "$REMOTE" 'cp ~/.hermes/.env ~/.hermes/.env.bak-contaminated-$(date +%Y%m%d-%H%M%S)'
ssh "$REMOTE" 'ls -la ~/.hermes/.env.bak-*'

echo
echo "== Rebuilding .env with ONLY the 3 approved keys =="
OPENROUTER_KEY=$(grep '^OPENROUTER_API_KEY=' ~/.hermes/.env | head -1 | cut -d= -f2-)
FB_ID=$(grep '^FB_APP_ID=' ~/.hermes/.env | head -1 | cut -d= -f2-)
FB_SECRET=$(grep '^FB_APP_SECRET=' ~/.hermes/.env | head -1 | cut -d= -f2-)

if [ -z "$OPENROUTER_KEY" ] || [ -z "$FB_ID" ] || [ -z "$FB_SECRET" ]; then
  echo "ERROR: one or more source values were empty locally — aborting before writing anything." >&2
  exit 1
fi

ssh "$REMOTE" 'cat > ~/.hermes/.env' <<EOF
OPENROUTER_API_KEY=$OPENROUTER_KEY
FB_APP_ID=$FB_ID
FB_APP_SECRET=$FB_SECRET
EOF
unset OPENROUTER_KEY FB_ID FB_SECRET

echo
echo "== Verifying the clean .env (names + lengths only) =="
ssh "$REMOTE" '
wc -l ~/.hermes/.env
for k in OPENROUTER_API_KEY FB_APP_ID FB_APP_SECRET; do
  v=$(grep "^${k}=" ~/.hermes/.env | tail -1 | cut -d= -f2-)
  echo "  $k: present, length=${#v}"
done
'

echo
echo "== Now checking WHY this happened: does config.yaml also carry your personal platform config? =="
ssh "$REMOTE" 'grep -A8 "^platforms:" ~/.hermes/config.yaml 2>&1 | head -20'

echo
echo "== Phase 1b complete. The contaminated .env is preserved at the .bak path above (not deleted) in case anything needs to be cross-checked, but Hermes will only read the clean one now. =="
