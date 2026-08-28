# Alienware headless conversion — handoff

**For:** whichever agent (Hermes or Claude) picks this up next.
**As of:** 2026-08-27 18:30, session ending on low token budget.

## Machine
`leo@192.168.0.224` — a 2014 **Alienware Alpha** (confirmed via `lspci`, board `ASM100`). i7-4765T, GTX 860M (2GB VRAM), 7.7GB RAM, 1.8TB HDD (`/home` eCryptfs-encrypted). Reachable over LAN, wired, ~34MB/s measured. Full hardware/thermal/NVENC audit already done — don't re-run it, ask Leo for the report if details are needed.

## Goal
Convert from Leo's daily-driver desktop into a headless render worker for the ByteVerdict pipeline (NVENC-accelerated ffmpeg, driven by `/home/leo/clips-channel/scripts/{submit,remote}-render.sh`).

## Status — HEADLESS CONVERSION COMPLETE (2026-08-27 ~18:35)
- ✅ `sudo systemctl disable lightdm` — done, autostart off.
- ✅ `sudo systemctl stop lightdm` — done (Leo ran this himself). GUI session ended, freed 424MB VRAM (458→34MB) and ~600MB RAM.
- ✅ **NVENC verified working with zero GUI/X session running** — `h264_nvenc` test encode succeeded headless. This was the one thing that could have blocked the whole approach; it didn't.
- Recovery if ever needed: `sudo systemctl enable --now lightdm` (fully reversible, no reinstall).

## Remaining items (optional, low priority, both need sudo)
   - `sudo smartctl -H /dev/sda` — disk health was never verified (this is a 2014 mechanical drive)
   - `sudo timedatectl set-local-rtc 0` — fixes a benign but confusing clock artifact (RTC-in-local-TZ causes the wall-clock boot timestamp to read wrong every boot; real uptime via `/proc/uptime` is accurate, this is cosmetic)

## Hard constraint — no passwordless sudo
`leo` is in the `sudo` group but there is **no NOPASSWD** entry. Every privileged command needs Leo to type his password interactively.
- **Never ask Leo to paste his password into chat.** Have him run the command himself in his own terminal, or set up a scoped `sudo visudo -f /etc/sudoers.d/render-worker` entry himself if he wants an agent to run these directly in the future.
- Pattern that worked well this session: hand Leo the exact command, he runs it and reports "done" (sometimes without pasting output), agent verifies independently via a **read-only** SSH check (`systemctl is-active`/`is-enabled` need no sudo). Don't trust a bare "done" — always verify.
- Watch for commands landing in the wrong terminal (happened once this session — Leo's local laptop shell vs the SSH session to the Alienware). If a change doesn't show up on verification, check both ends before re-prompting.

## What NOT to do
- Never `apt remove`/`apt purge` cinnamon or lightdm packages — `systemctl disable`/`stop` is fully reversible (`sudo systemctl enable --now lightdm` restores everything); a package removal is not.
- Don't re-run the full hardware audit — it's done, ask Leo for the report instead of repeating SSH round-trips.
- Don't touch this machine's GUI without confirming current state first — real time passes between sessions, don't assume yesterday's state holds.

## Related context (separate but relevant)
- Leo's laptop had its own unrelated GUI incident today (~17:37) that killed the WhatsApp alert bridge (`systemctl --user` service, tied to his desktop session) — already fixed, but flagging that the alert pipeline has a blind spot whenever Leo's laptop session gets disrupted. A headless Alienware doesn't fix that on its own, but was raised as a longer-term reason to get this box stable.
- ByteVerdict's two cron jobs are now pinned to paid OpenRouter (separate workstream, unrelated to this machine) — not blocked on anything here.
