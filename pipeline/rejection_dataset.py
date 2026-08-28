#!/usr/bin/env python3
"""Rejection feedback dataset — stores, categorizes, and analyzes rejections.

Every rejection is recorded with:
- clip_id, timestamp, decision
- rejection category (hook/topic/quality/attribution/other)
- free-text note from Leo
- source clip metadata (topic, outlet, format)

This dataset feeds back into the Content Agent to avoid repeating mistakes.

Usage:
    python3 rejection_dataset.py record <clip_id> <category> "<note>"
    python3 rejection_dataset.py stats
    python3 rejection_dataset.py patterns
    python3 rejection_dataset.py export
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATASET_FILE = ROOT / "test-batch" / "discovery-outputs" / ".rejection_dataset.json"

# Standard rejection categories (Leo can add free-text notes too)
CATEGORIES = [
    "weak_hook",           # opening doesn't grab attention
    "wrong_topic",         # topic doesn't fit channel / overdone
    "quality_issue",       # blurry, dark, unwatchable footage
    "attribution_unclear", # source not credible / can't verify
    "too_long",            # clip runs too long for Shorts
    "too_short",           # not enough substance
    "misleading",          # headline/claim doesn't match content
    "duplicate",           # similar clip already posted
    "timing",              # story is stale / already covered
    "other",               # catch-all
]


def load_dataset() -> dict:
    if DATASET_FILE.exists():
        try:
            return json.loads(DATASET_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"version": 1, "rejections": [], "patterns": {}}


def save_dataset(dataset: dict):
    DATASET_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATASET_FILE.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(dataset, indent=2))
    os.replace(tmp, DATASET_FILE)


def record_rejection(clip_id: str, category: str, note: str = ""):
    """Record a rejection with category and note."""
    if category not in CATEGORIES:
        print(f"Unknown category '{category}'. Valid: {', '.join(CATEGORIES)}")
        sys.exit(1)

    dataset = load_dataset()
    entry = {
        "clip_id": clip_id,
        "category": category,
        "note": note,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    dataset["rejections"].append(entry)

    # Update pattern counts
    if category not in dataset["patterns"]:
        dataset["patterns"][category] = 0
    dataset["patterns"][category] += 1

    save_dataset(dataset)
    print(f"Recorded: {clip_id} → {category}" + (f" ({note})" if note else ""))


def get_stats() -> dict:
    """Get rejection statistics."""
    dataset = load_dataset()
    total = len(dataset["rejections"])
    if total == 0:
        return {"total": 0, "message": "No rejections recorded yet."}

    # Category breakdown
    categories = Counter(r["category"] for r in dataset["rejections"])

    # Recent trend (last 7 days)
    recent = [
        r for r in dataset["rejections"]
        if (datetime.now(timezone.utc) - datetime.fromisoformat(r["timestamp"])).days < 7
    ]

    return {
        "total_rejections": total,
        "category_breakdown": dict(categories.most_common()),
        "recent_7_days": len(recent),
        "top_issue": categories.most_common(1)[0] if categories else None,
    }


def get_patterns() -> dict:
    """Analyze rejection patterns for Content Agent feedback."""
    dataset = load_dataset()
    total = len(dataset["rejections"])
    if total == 0:
        return {"message": "No data yet. Reject a few clips to build patterns."}

    # Category frequencies
    categories = Counter(r["category"] for r in dataset["rejections"])

    # Notes analysis — extract common themes from free-text notes
    notes = [r["note"] for r in dataset["rejections"] if r["note"]]

    # Recommendations for Content Agent
    recommendations = []
    if categories.get("weak_hook", 0) >= 2:
        recommendations.append("PRIORITY: Strengthen opening hooks — first 2 seconds must grab attention")
    if categories.get("wrong_topic", 0) >= 2:
        recommendations.append("PRIORITY: Review topic selection — some topics don't fit the channel")
    if categories.get("quality_issue", 0) >= 2:
        recommendations.append("PRIORITY: Improve source quality checks — reject blurry/dark footage before producing")
    if categories.get("too_long", 0) >= 2:
        recommendations.append("PRIORITY: Keep clips under 30s — shorter performs better on Shorts")
    if categories.get("attribution_unclear", 0) >= 2:
        recommendations.append("PRIORITY: Verify sources — use Tier 1/2 outlets only")

    return {
        "total_rejections": total,
        "category_frequencies": dict(categories.most_common()),
        "sample_notes": notes[:10],
        "recommendations_for_content_agent": recommendations,
    }


def export_for_agent() -> str:
    """Export patterns as a summary the Content Agent can read."""
    patterns = get_patterns()
    if "message" in patterns:
        return patterns["message"]

    lines = [
        "# Rejection Patterns — Content Agent Guidance",
        f"Total rejections analyzed: {patterns['total_rejections']}",
        "",
        "## Category Frequency:",
    ]
    for cat, count in patterns.get("category_frequencies", {}).items():
        lines.append(f"  - {cat}: {count}")

    lines.append("")
    lines.append("## Active Recommendations:")
    for rec in patterns.get("recommendations_for_agent", []):
        lines.append(f"  ⚠️ {rec}")

    if patterns.get("sample_notes"):
        lines.append("")
        lines.append("## Recent Notes from Leo:")
        for note in patterns["sample_notes"][:5]:
            lines.append(f"  - \"{note}\"")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 rejection_dataset.py [record|stats|patterns|export]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "record":
        if len(sys.argv) < 4:
            print("Usage: python3 rejection_dataset.py record <clip_id> <category> \"<note>\"")
            print(f"Categories: {', '.join(CATEGORIES)}")
            sys.exit(1)
        record_rejection(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "stats":
        print(json.dumps(get_stats(), indent=2))
    elif cmd == "patterns":
        print(json.dumps(get_patterns(), indent=2))
    elif cmd == "export":
        print(export_for_agent())
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
