# ByteVerdict File Organization Rules

Written 2026-08-26 after a full repo overhaul (see git log). The goal: the root directory
never again accumulates loose one-off scripts, credentials, or planning docs. These rules
are the standard an automated daily check (see bottom) evaluates the repo against.

## The rule

**Nothing new gets created directly at repo root except the 8 standing entries below.**
Everything else belongs inside one of the existing directories, or a new one you
deliberately add to this list.

## Standing root entries (the only things allowed loose at `/home/leo/clips-channel/`)

| Entry | What it is |
|---|---|
| `README.md` | repo map — keep in sync when structure changes |
| `.gitignore` | keep in sync when new secret-bearing files/dirs are added |
| `agents/` | **live cron entry points only** — the .md files Hermes cron reads directly |
| `pipeline/` | scripts the agents call to actually do things (post, refresh tokens, shared helpers) |
| `credentials/` | gitignored secrets only — nothing else ever goes here |
| `test-batch/` | the working production pipeline (sourcing → overlays → exports → ready-to-post → clip-log) |
| `sourcing/` | source-capture notes + raw capture files |
| `legal/` | privacy_policy.html / data_deletion.html — **do not rename/move without checking Meta/TikTok developer app config first**, these URLs may be registered externally |
| `docs/` | planning/business docs, this file, POST-MORTEM, anything that's reading material not code |
| `archive/` | superseded/dead code, kept for history — see rules below |

## Where new things go

- **A new posting/production script that becomes part of the live pipeline** → `pipeline/`. Update the relevant `agents/*.md` prompt to reference it by its `pipeline/` path.
- **A debug/test/one-off script** → write it directly into `archive/debug-and-tests/` or `archive/one-off-scripts/` from the start, or delete it once it's served its purpose. Never leave it at root "just in case."
- **A new credential/token/secret file** → `credentials/`, and add its filename (or `credentials/*.json` if it's covered already) to `.gitignore` in the same edit that creates it. No exceptions — a secret file existing even briefly outside `credentials/` unprotected is exactly the class of bug this cleanup fixed once already (`ig_token.json`).
- **A new business/planning doc** (cost analysis, legal research, monetization notes) → `docs/`, in a topic subdirectory if there isn't already an obvious home.
- **A per-batch, one-shot artifact** (a batch-specific overlay renderer, a specific-clip fix script) → write it directly to `archive/` when you create it, or delete it after use. These are disposable by nature — don't let them accumulate at root the way `apply_overlays_v2.py`, `apply_overlays_v3.py`, etc. did.
- **A script unrelated to ByteVerdict** (a different project that happened to get written here) → it does not belong in this repo at all. Move it out immediately, the way `alienware_dispatch.py` was.

## Naming and duplication rules

- **No version-suffixed script names** (`_v2`, `_v3`, `_pil_v2`) living at root or in `pipeline/`. If a script needs a real successor, replace it in place (git history is the version log now that this repo is under git) — don't leave both around.
- **No two scripts implementing the same thing.** If you're about to write a second version of something that already exists in `pipeline/`, either extend the existing one or explicitly move the old one to `archive/` in the same change.
- **Shared logic used by 2+ scripts belongs in a shared module**, not copy-pasted (this is exactly what `pipeline/ig_common.py` fixed for the old `ig_post.py`/`refresh_ig_token.py` duplication).

## Credential hygiene (non-negotiable)

1. Every credential file lives in `credentials/`, nothing else.
2. Every credential file (or its containing pattern) is in `.gitignore` **before** it's ever written to disk, not after.
3. No credential values — tokens, keys, secrets — ever get hardcoded directly in a `.py` file. Read them from `credentials/` or environment variables only.
4. An orphaned/unused credential file (nothing reads it) gets deleted or moved to `archive/`, not left sitting around — it's a live secret with no purpose.

## The two live agent prompts (`agents/*.md`)

These are executed autonomously by Hermes cron with no human in the loop between runs — treat edits to them with more care than regular code:

- Any file path referenced inside them must be checked against the actual repo structure before saving — a stale path silently breaks the next scheduled run.
- Any safety/approval gate in these files must not contradict `/home/leo/.hermes/skills/clips-channel-production/SKILL.md` — that skill file is the source of truth for posting safety rules; if a prompt edit would create daylight between them, fix the disagreement immediately, don't ship it.
- After editing either file, verify the corresponding Hermes cron job (`hermes cron list`) still points at the right path.

## Automated checks (two tiers)

**Daily, free, mechanical** — a `--no-agent` Hermes cron job (zero LLM cost) checks the
mechanical parts of these rules every 24h: stray files at root, credentials outside
`credentials/`, missing `.gitignore` coverage, version-suffixed filenames, `__pycache__`
buildup. Writes to `docs/organization-check-latest.md`.
Script: `/home/leo/.hermes/scripts/repo-organization-check.sh`
Cron job: "ByteVerdict Organization Check (no-agent)"

**Weekly, Claude judgment** — Mondays 9am, a Hermes cron job shells out to the real
`claude` CLI (Leo's Pro subscription) for the checks a script can't make: doc placement,
whether `agents/*.md` still agrees with itself and with SKILL.md, duplicate/one-off
scripts that should be archived, README accuracy. Writes to
`docs/organization-review-latest.md`.
Cron job: "ByteVerdict Weekly Organization Review"

Deliberately weekly, not daily — a daily automated call to Claude here would repeat the
exact Pro-quota drain pattern that caused real problems earlier (see `~/.hermes/coS/index.md`
decision log, 2026-08-26). The free daily script covers the mechanical 90% of drift; the
weekly Claude pass covers judgment calls the script can't make.
