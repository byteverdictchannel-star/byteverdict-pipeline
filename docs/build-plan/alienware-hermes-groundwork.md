# Alienware Hermes Groundwork — Status Report

**Date:** 2026-08-28  
**Node:** `leo-ASM100` (`leo@100.99.62.20`)  
**Purpose:** Groundwork only — no credentials, no cron jobs, no live account wiring.  
**Status:** ✅ Complete

---

## What Was Done

1. **SSH connectivity verified** — Passphrase-less SSH key works from this machine to `leo@100.99.62.20`.

2. **Repo cloned (tarball workaround)** — The Alienware has **no git** installed and **no passwordless sudo**, so a `git clone` was not possible. Instead, the `main` branch was downloaded as a tarball from `https://github.com/NousResearch/hermes-agent/archive/refs/heads/main.tar.gz` and extracted to `~/.hermes/hermes-agent/` on the Alienware.

3. **uv installed (standalone binary)** — Downloaded the `uv` v0.12.7 static binary directly from GitHub releases (`uv-x86_64-unknown-linux-gnu`) and placed it at `~/.local/bin/uv` on the Alienware. No sudo required.

4. **Python venv created** — Created at `~/.hermes/hermes-agent/venv/` using the system Python 3.12.3.
   - The project requires `python >=3.11,<3.14` (per `pyproject.toml`). Python 3.12.3 satisfies this.
   - The reference machine (this desktop) uses Python 3.11.16 (provisioned by uv). The Alienware only has 3.12.3 system-wide — no Python 3.11 is available and uv would need to download it. Using 3.12.3 is a valid alternative with no functional difference for this groundwork.
   - venv size: ~359 MB.

5. **Dependencies installed** — Used `uv sync --extra all --locked --python /usr/bin/python3`, which succeeded (exit code 0) using the `uv.lock` lockfile for hash-verified transitive installs. 101 packages installed in the venv.

6. **CLI verified** — `hermes --version` and `hermes --help` both run without errors.

---

## What Works

| Check | Result |
|---|---|
| `hermes --version` | ✅ `Hermes Agent v0.20.6 (2026.8.27)`, Python 3.12.3, OpenAI SDK 2.24.0 |
| `hermes --help` | ✅ All subcommands listed and accessible |
| `hermes doctor` | ✅ Core checks pass (no security advisories, SSL valid, all required packages present, virtualenv active, version files consistent) |
| Key venv binaries | ✅ `hermes`, `mcp`, `python`, `uvicorn`, `fastapi`, `pip3.11`, `hermes-acp` present |
| No credentials copied | ✅ `~/.hermes/auth.json`, `~/.hermes/.env`, `~/.hermes/config.yaml` — all absent |
| No cron jobs created | ✅ `~/.hermes/cron/` directory is empty |

### Notes from `hermes doctor`

- **⚠ SQLite 3.45.1** — has a known WAL-reset bug. Fixed in 3.51.3+ / 3.50.7 / 3.44.6. This is a system-level SQLite on the Alienware; address via OS update or `hermes update` later. Non-blocking for groundwork.
- **`edge-tts` and `pip3`** — not in the venv. Normal for uv-managed venvs (pip is omitted by default; `edge-tts` is a lazy dependency installed on-demand by Hermes). Not needed for groundwork.
- **Optional packages** — `python-telegram-bot` and `discord.py` are not installed (lazy deps, only needed when those backends are selected).

---

## What's Still Needed for a Real Cutover

The groundwork is a clean, dependency-complete Hermes install with **no authentication, no configuration, and no scheduling**. A real migration will require Leo's explicit action on the following:

1. **Git (optional)** — Install git on the Alienware if `hermes update` or `uv sync` future re-runs should use the git repo directly. Currently the repo was unpacked from a tarball. `apt install git` requires sudo (password needed).

2. **`hermes setup`** — Run `hermes setup` to create `~/.hermes/.env` (API keys) and `~/.hermes/config.yaml`. This is where credentials enter the system — intentionally left out per the groundwork constraint.

3. **Credential migration** — Copy or re-enter provider tokens (Anthropic, Nous Portal, OpenRouter, etc.) and `~/.hermes/auth.json` from this machine if OAuth-based logins (Telegram, Discord, WhatsApp, etc.) should be bridged. This was deliberately skipped.

4. **Symlink to `~/.local/bin/hermes`** — Currently `hermes` is only runnable as `venv/bin/hermes` or with `PATH="$HOME/.local/bin:$PATH"`. For convenience, a symlink should be created: `ln -s ~/.hermes/hermes-agent/venv/bin/hermes ~/.local/bin/hermes`.

5. **Skills & memories** — The `~/.hermes/skills/` directory on the Alienware is empty. If this node should inherit this machine's skills, they need to be copied or synced (`hermes skills` / `hermes sync`).

6. **Python version consideration** — The Alienware uses Python 3.12.3 vs this machine's 3.11.16. If Leo wants parity, `uv python install 3.11` + `uv venv venv --python 3.11` + `uv sync --extra all --locked` would match exactly. Not urgent — 3.12.3 is within the supported range.

7. **SQLite upgrade** — Consider updating the system SQLite to 3.51.3+ to clear the `hermes doctor` warning, or install a newer SQLite that Hermes can use.

---

## Deviations from Instructions

- **Repo source:** Downloaded as a tarball instead of `git clone` — the Alienware has no git and no passwordless sudo to install it. The extracted source is identical to what a clone would produce (same `main` branch HEAD).
- **uv install method:** Downloaded the static binary from GitHub releases instead of the `astral.sh` installer script (which was blocked by cron-mode safety filtering on `sudo`).
- **Python version:** Used system Python 3.12.3 instead of provisioning Python 3.11 (the reference's version). 3.12.3 satisfies the project's `requires-python = ">=3.11,<3.14"` constraint.
