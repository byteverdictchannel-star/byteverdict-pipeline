#!/usr/bin/env python3
"""Shared state management for the ByteVerdict clips pipeline.

All agents (Content, Posting, Breaking News) read/write this state so they
know what each other are doing. This enables 24/7 autonomous coordination
without agents working blindly.

State file: test-batch/discovery-outputs/.pipeline_state.json

Usage:
    from shared_state import PipelineState
    state = PipelineState()
    state.record_production("tb023_c1", "Content Agent", "produced clip")
    state.record_approval("tb023_c1", "approved")
    pending = state.get_pending_approvals()
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
STATE_FILE = ROOT / "test-batch" / "discovery-outputs" / ".pipeline_state.json"
MAX_HISTORY = 100


class PipelineState:
    """Thread-safe (atomic writes) shared state for pipeline coordination."""

    def __init__(self):
        self._state = self._load()

    def _load(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return self._default()

    def _default(self) -> dict:
        return {
            "version": 1,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "agents": {
                "content_agent": {"status": "idle", "last_run": None, "current_task": None},
                "posting_agent": {"status": "idle", "last_run": None, "current_task": None},
                "breaking_news": {"status": "idle", "last_run": None, "current_task": None},
            },
            "queue": {
                "production": [],       # clips being produced
                "approval": [],          # clips sent to Telegram, awaiting review
                "approved": [],          # clips approved, ready to post
                "posted": [],            # clips successfully posted
                "rejected": [],          # clips rejected
            },
            "stats": {
                "produced_today": 0,
                "posted_today": 0,
                "rejected_today": 0,
                "last_reset": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
            "history": [],  # rolling log of recent events
        }

    def _save(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._state["last_updated"] = datetime.now(timezone.utc).isoformat()
        tmp = STATE_FILE.with_suffix(f".tmp.{os.getpid()}")
        tmp.write_text(json.dumps(self._state, indent=2))
        os.replace(tmp, STATE_FILE)

    def _maybe_reset_daily(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._state["stats"]["last_reset"] != today:
            self._state["stats"] = {
                "produced_today": 0,
                "posted_today": 0,
                "rejected_today": 0,
                "last_reset": today,
            }

    def _log_event(self, event: str, details: dict = None):
        self._state["history"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": details or {},
        })
        self._state["history"] = self._state["history"][-MAX_HISTORY:]

    # --- Agent status ---

    def set_agent_status(self, agent: str, status: str, task: str = None):
        """Update an agent's current status."""
        if agent in self._state["agents"]:
            self._state["agents"][agent]["status"] = status
            self._state["agents"][agent]["current_task"] = task
            if status == "running":
                self._state["agents"][agent]["last_run"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def get_agent_status(self, agent: str) -> dict:
        return self._state["agents"].get(agent, {})

    # --- Queue management ---

    def record_production(self, clip_id: str, agent: str, note: str = ""):
        """Record that a clip is being produced."""
        entry = {"clip_id": clip_id, "agent": agent, "note": note, "at": datetime.now(timezone.utc).isoformat()}
        self._state["queue"]["production"].append(entry)
        self._maybe_reset_daily()
        self._state["stats"]["produced_today"] += 1
        self._log_event("production_started", entry)
        self._save()

    def record_approval_sent(self, clip_id: str, message_id: int):
        """Record that a clip was sent to Telegram for approval."""
        entry = {"clip_id": clip_id, "message_id": message_id, "at": datetime.now(timezone.utc).isoformat()}
        self._state["queue"]["approval"].append(entry)
        # Remove from production
        self._state["queue"]["production"] = [e for e in self._state["queue"]["production"] if e["clip_id"] != clip_id]
        self._log_event("approval_sent", entry)
        self._save()

    def record_approval(self, clip_id: str, decision: str):
        """Record approval/rejection decision."""
        # Find in approval queue
        entry = None
        for e in self._state["queue"]["approval"]:
            if e["clip_id"] == clip_id:
                entry = e
                break
        if entry:
            self._state["queue"]["approval"] = [e for e in self._state["queue"]["approval"] if e["clip_id"] != clip_id]
        entry["decision"] = decision
        entry["decided_at"] = datetime.now(timezone.utc).isoformat()

        if decision == "approved":
            self._state["queue"]["approved"].append(entry)
        else:
            self._state["queue"]["rejected"].append(entry)
            self._maybe_reset_daily()
            self._state["stats"]["rejected_today"] += 1

        self._log_event(f"approval_{decision}", entry)
        self._save()

    def record_posted(self, clip_id: str, platform: str, post_id: str = None):
        """Record successful post."""
        entry = {"clip_id": clip_id, "platform": platform, "post_id": post_id, "at": datetime.now(timezone.utc).isoformat()}
        self._state["queue"]["posted"].append(entry)
        # Remove from approved
        self._state["queue"]["approved"] = [e for e in self._state["queue"]["approved"] if e["clip_id"] != clip_id]
        self._maybe_reset_daily()
        self._state["stats"]["posted_today"] += 1
        self._log_event("posted", entry)
        self._save()

    # --- Queries ---

    def get_pending_approvals(self) -> list:
        """Get clips waiting for Telegram approval."""
        return self._state["queue"]["approval"]

    def get_approved_unposted(self) -> list:
        """Get clips approved but not yet posted."""
        return self._state["queue"]["approved"]

    def get_posted_today(self) -> int:
        self._maybe_reset_daily()
        return self._state["stats"]["posted_today"]

    def get_produced_today(self) -> int:
        self._maybe_reset_daily()
        return self._state["stats"]["produced_today"]

    def get_recent_history(self, n: int = 20) -> list:
        return self._state["history"][-n:]

    def get_full_state(self) -> dict:
        return self._state

    def is_clip_in_queue(self, clip_id: str) -> bool:
        """Check if a clip is already in any queue."""
        for q in self._state["queue"].values():
            if any(e.get("clip_id") == clip_id for e in q):
                return True
        return False


# CLI for quick inspection
if __name__ == "__main__":
    state = PipelineState()
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(state.get_full_state(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "pending":
        print(json.dumps(state.get_pending_approvals(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "approved":
        print(json.dumps(state.get_approved_unposted(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "history":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        print(json.dumps(state.get_recent_history(n), indent=2))
    else:
        print("Usage: python3 shared_state.py [status|pending|approved|history [n]]")
