#!/usr/bin/env python3
"""Automatic backup of the pipeline's critical lightweight state — built
2026-08-28, same day test-batch/clip-log/ and test-batch/captures/ were
accidentally deleted by a separate Hermes job's git cleanup. Git's reflog
saved most of it that time, by luck (an earlier commit still had it) —
this is the actual, deliberate safety net so luck isn't the plan.

Backs up to ~/clips-channel-backups/, a location DELIBERATELY outside the
git working tree and outside test-batch/ itself — a "clean up this repo"
or "clean up test-batch" action (the exact kind of action that caused
today's incident) wouldn't touch a sibling directory.

What's backed up (lightweight text/JSON — cheap to snapshot often, this is
NOT the raw video captures, which are large and reproducible via yt-dlp
from each clip-log's recorded source URL):
  - test-batch/clip-log/           — every editorial record, decision file,
                                       posting log, review state
  - test-batch/discovery-outputs/  — trending/breaking data, telegram state
  - docs/build-plan/               — audit log, handoff docs, this session's
                                       durable decisions

Retention: keeps the last 48 hourly snapshots (2 days) plus one snapshot
per day for the last 30 days beyond that — recent granularity, longer
coverage without unbounded growth. Uses hardlinks (via `cp -al`) between
unchanged files across snapshots, so disk cost is proportional to what
actually changed, not the number of snapshots.

Usage: python3 backup_state.py
Run hourly via cron — zero LLM cost, pure file copy.
"""

import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP_ROOT = Path.home() / "clips-channel-backups"

SOURCES = [
    ROOT / "test-batch" / "clip-log",
    ROOT / "test-batch" / "discovery-outputs",
    ROOT / "docs" / "build-plan",
]

KEEP_HOURLY = 48
KEEP_DAILY = 30


def latest_snapshot():
    if not BACKUP_ROOT.exists():
        return None
    snapshots = sorted([p for p in BACKUP_ROOT.iterdir() if p.is_dir()], reverse=True)
    return snapshots[0] if snapshots else None


def make_snapshot():
    now = datetime.now(timezone.utc)
    snap_name = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    snap_dir = BACKUP_ROOT / snap_name
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    prev = latest_snapshot()

    for src in SOURCES:
        if not src.exists():
            print(f"WARNING: source missing, skipping: {src}", file=sys.stderr)
            continue
        rel = src.relative_to(ROOT)
        dest = snap_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        prev_equivalent = (prev / rel) if prev else None
        if prev_equivalent and prev_equivalent.exists():
            # Hardlink-based incremental copy — unchanged files cost ~0 extra
            # disk; only genuinely new/changed bytes take real space.
            result = subprocess.run(
                ["cp", "-al", str(prev_equivalent), str(dest)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                # Fall back to a plain copy if hardlinking fails (e.g. cross-device)
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                # cp -al gives us the PREVIOUS snapshot's content as hardlinks;
                # now sync in anything that's actually changed since.
                subprocess.run(["rsync", "-a", "--delete", f"{src}/", f"{dest}/"], check=True)
        else:
            shutil.copytree(src, dest, dirs_exist_ok=True)

    print(f"Snapshot created: {snap_dir}")
    return snap_dir


def prune_old_snapshots():
    if not BACKUP_ROOT.exists():
        return
    snapshots = sorted([p for p in BACKUP_ROOT.iterdir() if p.is_dir()], reverse=True)
    if len(snapshots) <= KEEP_HOURLY:
        return

    recent = snapshots[:KEEP_HOURLY]
    older = snapshots[KEEP_HOURLY:]

    # Among "older" snapshots, keep at most one per calendar day, for up to
    # KEEP_DAILY days; delete the rest.
    seen_days = set()
    to_delete = []
    for snap in older:
        day = snap.name[:10]  # YYYY-MM-DD prefix
        if day in seen_days or len(seen_days) >= KEEP_DAILY:
            to_delete.append(snap)
        else:
            seen_days.add(day)

    for snap in to_delete:
        shutil.rmtree(snap)
        print(f"Pruned old snapshot: {snap.name}")

    if not to_delete:
        print(f"No snapshots pruned ({len(recent)} recent + {len(seen_days)} daily kept)")


def main() -> int:
    make_snapshot()
    prune_old_snapshots()
    return 0


if __name__ == "__main__":
    sys.exit(main())
