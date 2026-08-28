# Alienware Render Worker — Setup, Architecture, and Maintenance

Dedicated compute node for the clips-channel pipeline. Runs headless, wired
into this main PC over SSH. This document covers every change made, why,
and how to maintain it.

## Hardware

- Alienware ASM100, Intel i7-4765T (4C/8T, max 3.0GHz), 7.7GB RAM
- NVIDIA GeForce GTX 860M, 2GB VRAM (NVENC-capable)
- Seagate 2TB 5400rpm HDD (`/dev/sda`, ~67,500 power-on hours) — **this is the
  system's real bottleneck**. Sequential write ~88MB/s. SMART shows 3
  pending sectors (not failed, worth re-checking periodically). No amount of
  software tuning changes the physical seek time of spinning media; if true
  low-latency lookups matter later, the fix is a ~$30-50 SATA SSD swap, not
  more tuning.
- Network: static IP `192.168.0.224` (set via NetworkManager, not DHCP
  reservation, since the router's admin UI wasn't reliably reachable)

## Network / Access

- SSH key-based auth from main PC (`~/.ssh/id_ed25519`, no passphrase —
  acceptable since this is LAN-only, both machines are physically controlled)
- `openssh-server` enabled via `systemctl enable --now ssh`
- Static IP set with:
  ```
  sudo nmcli connection modify "Wired connection 1" ipv4.addresses 192.168.0.224/24 \
    ipv4.gateway 192.168.0.1 ipv4.dns "8.8.8.8,1.1.1.1" ipv4.method manual
  sudo nmcli connection up "Wired connection 1"
  ```

## Folder Structure

Both machines mirror the same paths under `~/clips-channel/` so scripts run
unmodified on either side — no path rewriting, no per-machine config.

```
clips-channel/
├── test-batch/            # existing production pipeline (unchanged)
│   ├── captures/          # yt-dlp source downloads
│   ├── exports/           # cut/master/platform render outputs
│   ├── overlays/          # overlay PNGs
│   ├── platform-exports/  # final per-platform files + .posted markers
│   ├── ready-to-post/     # approved, awaiting posting
│   └── clip-log/          # production records
├── queue/                 # NEW — the render worker's job queue
│   ├── incoming/          # drop a render_*.py here to submit a job
│   ├── processing/        # watcher moves it here while running
│   ├── done/              # succeeded — output already in test-batch/exports
│   └── failed/            # failed — check logs/, alert already sent
├── logs/                  # NEW — watcher.log, audit.log, per-job render logs
├── scripts/               # dispatch/watcher/audit scripts (this build)
└── .ntfy_topic            # push-notification topic (Alienware side)
```

**Why a queue instead of just running scripts over SSH directly:** the
mandate asked for the Alienware to pick up work on its own rather than
needing a live SSH session each time. A folder-based queue is the simplest
mechanism that gives that — no message broker, no extra service, just files
moving between four directories.

## The Render Pipeline (end to end)

1. **On the main PC:** finish a clip's `render_*.py` script as normal
   (unchanged — no rewrite needed).
2. **Submit it:** `scripts/submit-render.sh render_tb0XX.py`
   - Syncs `test-batch/` to the Alienware (so the script's input files are
     present)
   - Drops the script into the Alienware's `queue/incoming/`
3. **On the Alienware, automatically (no login needed):** the
   `clips-render-watcher` systemd service polls `queue/incoming/` every 15s,
   picks up the job, runs it, and files the result into `queue/done/` or
   `queue/failed/` — sending a push notification either way.
4. **Back on the main PC, automatically:** a cron job
   (`scripts/pull-results.sh`, every 5 minutes) checks the Alienware's
   `queue/done/`, pulls `exports/`, `platform-exports/`, `ready-to-post/`,
   `clip-log/` back, and marks the job as pulled so it isn't re-fetched.
5. **You review and approve as always** — nothing here touches or bypasses
   the posting verification gate in `SKILL.md` section 11. The queue only
   produces files; it never posts.

**Explicit-submit design (not fully automatic):** a render only happens when
you (or Claude) deliberately run `submit-render.sh`. Nothing watches
`test-batch/` itself for new scripts — this was a deliberate choice so a
script you're still mid-editing never gets rendered by accident.

**No auto-retry on failure:** if a job fails, it gets one immediate alert and
sits in `queue/failed/`. A script bug (like the ones found during setup)
fails identically every time, so retrying just burns time; better to
surface it once and wait for a fix.

## What Was Actually Broken and Fixed Along the Way

These were pre-existing bugs in the pipeline, not artifacts of the remote
setup — confirmed by reproducing them locally before touching anything
remote:

1. **`render_tb006.py` had a trailing comma** in its ffmpeg `-vf` filter
   string (leftover from a removed filter) — fixed.
2. **Unescaped commas inside `drawtext` text values** ("a dumb, stupid
   country") — ffmpeg's filter syntax treats `,` as a filter separator, so
   any literal comma/colon inside `text='...'` needs escaping as `\,` / `\:`.
   Fixed in `render_tb006.py`; **worth checking other `render_*.py` scripts
   for the same issue** if their overlay text has punctuation.
3. **The ffmpeg build in use (`~/.local/bin/ffmpeg`, johnvansickle static
   7.0.2) had no `drawtext` filter compiled in at all** — this affected the
   main PC too, not just the Alienware. Replaced on both machines with the
   BtbN GPL static build, which includes `drawtext` *and* NVENC. Same
   version/behavior on both machines now.

## System Tuning

| Change | File | Why |
|---|---|---|
| `vm.swappiness=10` | `/etc/sysctl.d/99-clips-worker.conf` | One render job at a time, 7.7GB RAM — prefer keeping ffmpeg/python resident over swapping to the slow disk |
| `vm.dirty_ratio=15`, `vm.dirty_background_ratio=8` | same | Balances write-stall latency against sequential-write throughput for large video files. **Note:** initial values (10/5) were tighter and measurably slowed a real render (~26min vs ~3min for the same clip) by forcing more frequent small flushes — loosened after catching this via a timed A/B test. If render times regress again, check this first. |
| I/O scheduler: `mq-deadline` | (kernel default, unchanged) | Already the right choice for spinning media — left as-is rather than risk a change for no gain |
| CPU governor: `performance` | new `cpu-performance.service` (systemd, enabled at boot) | Default `schedutil` was scaling idle cores down to 800MHz between bursts; a dedicated worker with no battery to save should stay pinned near max clock during jobs |
| `CPUQuota=90%` on the watcher service | `/etc/systemd/system/clips-render-watcher.service` | **This was a mistake, caught during testing:** systemd's `CPUQuota=90%` means 90% of *one* core total for the whole cgroup (including all of ffmpeg's threads) — not 90% per-core. This alone throttled a render to run ~9x slower. **Fix prepared but not yet applied** (`/tmp/fix-cpu-quota.sh` on the Alienware, changes it to `700%` = up to 7 of 8 cores, leaving one free for SSH/system responsiveness) — apply on next restart of the watcher service. |

## Automation / Headless Operation

- **`clips-render-watcher.service`** (systemd, `enabled`) — the job watcher.
  `Restart=always`, so it comes back after a crash; `enabled` means it starts
  automatically on boot with no login required.
- **`unattended-upgrades`** (systemd, `active`) — security updates apply
  automatically. Installed via `apt-get install unattended-upgrades
  apt-listchanges` + `/etc/apt/apt.conf.d/20auto-upgrades`.
- **`cpu-performance.service`** (systemd, `enabled`, oneshot) — pins CPU
  governor to `performance` at every boot.
- **Log rotation**: `/etc/logrotate.d/clips-channel` — daily, 7-day
  retention, compressed, for everything in `clips-channel/logs/*.log`.
- **Audit + retention cleanup**: `scripts/audit.sh`, cron every 4 hours
  (`0 */4 * * *`). Checks:
  - Directory traversal time (canary for filesystem degradation — alerts if
    a full tree walk exceeds 5s, which would be a real anomaly on this
    machine's current file count)
  - Naming convention (`exports/`, `overlays/`, `platform-exports/` files
    should be `tbNNN`-prefixed)
  - Jobs stuck in `queue/processing/` for over an hour (signals the watcher
    died mid-render)
  - Disk usage (alerts at 80%+)
  - Deletes `queue/done/`, `queue/failed/`, and old render logs older than
    7 days
  - **Chose a lightweight cron check over a continuous hourly daemon
    deliberately** — the drive is old and already shows wear; a full-tree
    scan every hour adds meaningful I/O for a folder this size that doesn't
    change much between checks.
- **Push notifications**: [ntfy.sh](https://ntfy.sh), topic
  `clips-worker-1ec82600c998f07c3dcc` (stored in `~/clips-channel/.ntfy_topic`
  on the Alienware). No account/credentials — it's a public topic-based
  service, so the topic name itself is the only "secret"; fine for
  non-sensitive status messages (render success/failure, disk space,
  watcher start/stop), not appropriate for anything sensitive. Subscribe via
  the ntfy app (recommended, real push) or by keeping
  `https://ntfy.sh/clips-worker-1ec82600c998f07c3dcc` open in a browser.

## Maintaining This Going Forward

- **Check SMART health periodically** (the drive has known wear):
  `ssh leo@192.168.0.224 "sudo smartctl -a /dev/sda"` — watch
  `Current_Pending_Sector` for growth.
- **New render script → run `scripts/submit-render.sh <script>.py`** from
  `~/clips-channel/` on the main PC. That's the entire workflow.
- **Something failed** → you'll get a push notification with the last few
  lines of the error; full log is in `clips-channel/logs/render-*.log` on
  the Alienware (synced back on next `pull-results.sh` run only for
  successes — for failures, SSH in to read the log directly, or run
  `rsync -az leo@192.168.0.224:/home/leo/clips-channel/logs/ ~/clips-channel/logs/`).
- **Watcher seems stuck** → `ssh leo@192.168.0.224 "systemctl status
  clips-render-watcher.service"`. It auto-restarts on crash, but if it's
  stuck rather than crashed, `sudo systemctl restart
  clips-render-watcher.service` (this will kill any in-progress render —
  that job would need resubmitting).
- **Disk fills up** → the audit script alerts at 80%; the immediate lever is
  the 7-day retention already in place, or manually clearing
  `test-batch/captures/` (source downloads) which are the biggest files and
  least needed once a clip is fully produced.

## Integration Points for Hermes / Claude

- Hermes itself still runs on the main PC — nothing was deployed to the
  Alienware beyond the render watcher. The Alienware has no judgment role;
  it only executes already-approved render scripts.
- To trigger a render from Hermes (or any automation on the main PC), the
  integration point is just: `bash ~/clips-channel/scripts/submit-render.sh
  <script>.py`. No API, no auth beyond the existing SSH key.
- To check worker health programmatically: SSH is the interface —
  `ssh leo@192.168.0.224 "systemctl is-active clips-render-watcher.service"`
  or read `~/clips-channel/logs/watcher.log`.
- The posting verification gate (SKILL.md §11) is untouched by any of this —
  the worker produces files, a human still watches and approves before
  anything posts.
