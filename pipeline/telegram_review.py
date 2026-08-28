#!/usr/bin/env python3
"""Clip approval via Telegram — send-for-review, and a separate poller that
picks up your Approve/Reject taps and rejection notes.

Two entry points, both no-LLM-cost, both meant to be called by cron:

  notify <clip_id> <video_path> <caption>
      Called once per finalized clip (end of content-agent-prompt.md §5).
      Sends the video with an inline Approve/Reject keyboard.

  poll
      Called every ~1-2 min via cron. Picks up new button taps and, for a
      rejection, the next plain-text reply as your note. Writes a decision
      file to test-batch/clip-log/<clip_id>.review_decision.json and, on
      reject, moves the clip's files out of ready-to-post into
      test-batch/rejected/ so a rejected clip can never accidentally post.
      Never touches the existing production/posting gates — this is a
      review layer that sits alongside them, not a replacement (2026-08-28
      decision, see conversation).

Why polling in a cron job rather than a persistent bot process: matches
this pipeline's existing "no-agent" cron pattern (pull_youtube_stats.py,
pull_trending.py, detect_breaking.py) — no new systemd service to manage,
no process to keep alive across reboots, Hermes's cron scheduler already
handles that. A 1-2 min poll interval is more than fast enough for a
human-paced approve/reject workflow.

Credentials (added by hand, see README note below):
  credentials/telegram_bot_token.txt  — from @BotFather
  credentials/telegram_chat_id.txt    — your numeric chat id

State (durable across cron runs, since each run is a fresh process):
  test-batch/discovery-outputs/.telegram_review_state.json
    {"offset": <last-seen update_id + 1>,
     "pending_reject": {"<clip_id>": <message_id>}}
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent
CREDENTIALS_DIR = ROOT / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "telegram_bot_token.txt"
CHAT_ID_FILE = CREDENTIALS_DIR / "telegram_chat_id.txt"
CLIP_LOG_DIR = ROOT / "test-batch" / "clip-log"
READY_DIR = ROOT / "test-batch" / "ready-to-post"
REJECTED_DIR = ROOT / "test-batch" / "rejected"
STATE_FILE = ROOT / "test-batch" / "discovery-outputs" / ".telegram_review_state.json"

API_BASE = "https://api.telegram.org/bot{token}"


def load_credential(path, label):
    if not path.exists():
        print(f"ERROR: {path} not found — {label}", file=sys.stderr)
        sys.exit(1)
    # Check file permissions (should be 0o600)
    st = path.stat()
    perms = oct(st.st_mode & 0o777)
    if perms != "0600":
        print(f"WARNING: {path} has insecure permissions {perms}, expected 600. Fix with: chmod 600 {path}", file=sys.stderr)
    value = path.read_text().strip()
    if not value:
        print(f"ERROR: {path} is empty — {label}", file=sys.stderr)
        sys.exit(1)
    return value


QUESTIONS_DIR = ROOT / "test-batch" / "discovery-outputs" / ".telegram_questions"
INBOX_FILE = ROOT / "test-batch" / "discovery-outputs" / ".telegram_inbox.jsonl"


def load_state():
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        state.setdefault("pending_reject", {})
        state.setdefault("pending_questions", {})  # message_id (str) -> question_id
        return state
    return {"offset": 0, "pending_reject": {}, "pending_questions": {}}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)  # atomic


HERMES_BIN = str(Path.home() / ".local" / "bin" / "hermes")
REJECTION_AUDIT_JOB_ID = "adfe3f9d5cfd"  # "ByteVerdict Rejection Pattern Audit" cron job


def trigger_rejection_audit():
    """Fire the rejection-audit agent immediately (real-time, per Leo's
    2026-08-28 request), rather than waiting for its own 30-min backstop
    schedule. Fire-and-forget — poll() shouldn't block on a full agent run
    just to finish recording one rejection. If this fails for any reason,
    the backstop cron still picks it up within 30 min, so this is a
    latency optimization, not a correctness dependency."""
    import subprocess
    try:
        subprocess.Popen(
            [HERMES_BIN, "cron", "run", REJECTION_AUDIT_JOB_ID, "--accept-hooks"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"WARNING: could not trigger rejection audit immediately ({e}) — 30-min backstop will still catch it", file=sys.stderr)


POSTING_AGENT_JOB_ID = "7a8c16fd7b21"  # "Posting Agent — clips channel auto-publish" cron job


def trigger_posting_agent():
    """Fire the Posting Agent immediately on Approve (real-time, per Leo's
    2026-08-28 'moves to be posted automatically' direction) rather than
    waiting for its own 20-min backstop schedule. Fire-and-forget, same
    pattern as trigger_rejection_audit() — the Posting Agent's own spacing
    logic (see posting-agent-prompt.md §4) decides whether to actually post
    this instant or defer to a later run, so firing immediately here is
    always safe to do."""
    import subprocess
    try:
        subprocess.Popen(
            [HERMES_BIN, "cron", "run", POSTING_AGENT_JOB_ID, "--accept-hooks"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"WARNING: could not trigger posting immediately ({e}) — 20-min backstop will still catch it", file=sys.stderr)


TELEGRAM_BRAIN_JOB_ID = "13bb45b1200d"  # "ByteVerdict Telegram Brain" cron job


def trigger_telegram_brain():
    """Fire the Telegram Brain agent immediately on a freeform message
    (real-time, per Leo's 2026-08-28 request), rather than waiting for its
    10-min backstop schedule. Fire-and-forget, same pattern as the other
    triggers."""
    import subprocess
    try:
        subprocess.Popen(
            [HERMES_BIN, "cron", "run", TELEGRAM_BRAIN_JOB_ID, "--accept-hooks"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"WARNING: could not trigger telegram brain immediately ({e}) — 10-min backstop will still catch it", file=sys.stderr)


import re
CLIP_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

def _validate_clip_id(clip_id):
    """Reject path traversal and unsafe characters in clip_id."""
    if not clip_id or not CLIP_ID_PATTERN.match(clip_id):
        raise ValueError(f"Invalid clip_id: {clip_id!r} — must match {CLIP_ID_PATTERN.pattern}")
    return clip_id

def write_decision(clip_id, decision, note=None):
    clip_id = _validate_clip_id(clip_id)
    CLIP_LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = CLIP_LOG_DIR / f"{clip_id}.review_decision.json"
    payload = {
        "clip_id": clip_id,
        "decision": decision,
        "note": note,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def move_to_rejected(clip_id):
    """Move every ready-to-post file for this clip out of the ready queue,
    so a rejected clip can never accidentally get posted. Renames rather
    than deletes — nothing is lost, just moved out of the way."""
    clip_id = _validate_clip_id(clip_id)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    moved = []
    if not READY_DIR.exists():
        return moved
    # Use exact prefix match instead of glob to prevent path traversal attacks
    # e.g. clip_id="tb01*" could match tb010, tb011 etc. if using glob
    for f in READY_DIR.iterdir():
        if f.name.startswith(clip_id + "_") or f.name.startswith(clip_id + "."):
            dest = REJECTED_DIR / f.name
            f.rename(dest)
            moved.append(str(dest))
    return moved


def notify(clip_id, video_path, caption):
    token = load_credential(TOKEN_FILE, "run @BotFather's /newbot and paste the token here")
    chat_id = load_credential(CHAT_ID_FILE, "message your new bot once, then look up the chat id via getUpdates")

    video_path = Path(video_path)
    if not video_path.exists():
        print(f"ERROR: video not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve:{clip_id}"},
            {"text": "❌ Reject", "callback_data": f"reject:{clip_id}"},
        ]]
    }

    with open(video_path, "rb") as f:
        resp = requests.post(
            API_BASE.format(token=token) + "/sendVideo",
            data={
                "chat_id": chat_id,
                "caption": caption[:1024],  # Telegram caption limit
                "reply_markup": json.dumps(keyboard),
            },
            files={"video": (video_path.name, f, "video/mp4")},
            timeout=60,
        )
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        print(f"ERROR: Telegram API: {result}", file=sys.stderr)
        sys.exit(1)
    # Sent-at marker (added 2026-08-28) — pipeline/expire_stale_clips.py
    # reads this to know how long a clip has been waiting for review, since
    # news relevance decays fast and a stale unreviewed clip should be
    # dropped rather than posted late.
    CLIP_LOG_DIR.mkdir(parents=True, exist_ok=True)
    sent_marker = CLIP_LOG_DIR / f"{clip_id}.review_sent_at.json"
    sent_marker.write_text(json.dumps({
        "clip_id": clip_id, "sent_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    print(f"Sent {clip_id} for review (message_id={result['result']['message_id']})")
    return result


def alert(text):
    """One-way notification — no reply expected. For FYI updates (e.g. an
    auto-fix that was made and verified)."""
    token = load_credential(TOKEN_FILE, "run @BotFather's /newbot and paste the token here")
    chat_id = load_credential(CHAT_ID_FILE, "message your new bot once, then look up the chat id via getUpdates")
    resp = requests.post(
        API_BASE.format(token=token) + "/sendMessage",
        data={"chat_id": chat_id, "text": text[:4096]},
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        print(f"ERROR: Telegram API: {result}", file=sys.stderr)
        sys.exit(1)
    print(f"Alert sent (message_id={result['result']['message_id']})")
    return result


CHROME_BIN = "google-chrome"


def send_report(html_path, caption="", pdf_path=None):
    """Render an HTML report to PDF via headless Chrome and send it as a
    Telegram document. Standing convention as of 2026-08-28, per Leo:
    "all reports are to be sent in that format via telegram moving
    forward" — any dashboard/diagnostic/report artifact should end here,
    not just live in chat text.

    pdf_path: where to write the PDF (defaults to a temp file, deleted
    after sending unless explicitly given a real path to keep it).
    """
    html_path = Path(html_path)
    if not html_path.exists():
        print(f"ERROR: HTML file not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    cleanup = pdf_path is None
    if pdf_path is None:
        pdf_path = Path(tempfile.mkstemp(suffix=".pdf")[1])
    else:
        pdf_path = Path(pdf_path)

    cmd = [
        CHROME_BIN, "--headless", "--disable-gpu", "--no-sandbox",
        f"--print-to-pdf={pdf_path}", "--no-pdf-header-footer",
        f"file://{html_path.resolve()}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0 or not pdf_path.exists():
        print(f"ERROR: PDF conversion failed: {result.stderr[-1000:]}", file=sys.stderr)
        sys.exit(1)

    token = load_credential(TOKEN_FILE, "run @BotFather's /newbot and paste the token here")
    chat_id = load_credential(CHAT_ID_FILE, "message your new bot once, then look up the chat id via getUpdates")

    try:
        with open(pdf_path, "rb") as f:
            resp = requests.post(
                API_BASE.format(token=token) + "/sendDocument",
                data={"chat_id": chat_id, "caption": caption[:1024]},
                files={"document": (html_path.stem + ".pdf", f, "application/pdf")},
                timeout=60,
            )
        resp.raise_for_status()
        result = resp.json()
        if not result.get("ok"):
            print(f"ERROR: Telegram API: {result}", file=sys.stderr)
            sys.exit(1)
        print(f"Report sent (message_id={result['result']['message_id']})")
        return result
    finally:
        if cleanup:
            pdf_path.unlink(missing_ok=True)


def ask(question_id, question, options=None, recommended=None):
    """Send a question that needs Leo's input — with tappable options if
    given, or an open free-text reply otherwise. Non-blocking: sends the
    question and returns immediately. The answer (if any) shows up later,
    written by `poll` to test-batch/discovery-outputs/.telegram_questions/
    <question_id>.json — check it with `check <question_id>`.

    Built 2026-08-28 in response to Leo: he wants serious/urgent questions
    reaching him via Telegram too, with tappable options where possible —
    same idea as AskUserQuestion, but for autonomous cron agents that can't
    just ask in a live chat because nobody's watching one.

    recommended (added same day, per Leo): marks one option as the
    recommended choice, same "(Recommended)" convention AskUserQuestion
    uses elsewhere this session — callers should default to putting the
    recommended option first and always state *why* it's recommended in
    the question text itself (a bare label with no reasoning isn't useful).
    Must exactly match one of `options` if given.
    """
    token = load_credential(TOKEN_FILE, "run @BotFather's /newbot and paste the token here")
    chat_id = load_credential(CHAT_ID_FILE, "message your new bot once, then look up the chat id via getUpdates")

    if recommended and options and recommended not in options:
        raise ValueError(f"recommended={recommended!r} must be one of options={options!r}")

    keyboard = None
    if options:
        def _label(opt):
            return f"{opt} (Recommended)" if opt == recommended else opt
        keyboard = {"inline_keyboard": [
            [{"text": _label(opt), "callback_data": f"ans:{question_id}:{opt}"}] for opt in options
        ]}

    data = {"chat_id": chat_id, "text": f"❓ {question}"}
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    resp = requests.post(API_BASE.format(token=token) + "/sendMessage", data=data, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        print(f"ERROR: Telegram API: {result}", file=sys.stderr)
        sys.exit(1)
    message_id = result["result"]["message_id"]

    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    q_path = QUESTIONS_DIR / f"{question_id}.json"
    q_path.write_text(json.dumps({
        "question_id": question_id, "question": question, "options": options,
        "recommended": recommended,
        "message_id": message_id, "asked_at": datetime.now(timezone.utc).isoformat(),
        "answered": False, "answer": None,
    }, indent=2))

    if not options:
        # Open question — awaiting a free-text reply, matches the
        # reject-reason reply-threading pattern (matched by message_id).
        state = load_state()
        state["pending_questions"][str(message_id)] = question_id
        save_state(state)

    print(f"Question sent (question_id={question_id}, message_id={message_id})")
    return result


def check(question_id):
    """Print the recorded answer for a question, or PENDING if not yet answered."""
    q_path = QUESTIONS_DIR / f"{question_id}.json"
    if not q_path.exists():
        print(f"ERROR: no such question: {question_id}", file=sys.stderr)
        sys.exit(1)
    q = json.loads(q_path.read_text())
    if q["answered"]:
        print(q["answer"])
    else:
        print("PENDING")


def _answer_callback(token, callback_query_id, text=None):
    requests.post(
        API_BASE.format(token=token) + "/answerCallbackQuery",
        data={"callback_query_id": callback_query_id, **({"text": text} if text else {})},
        timeout=15,
    )


def _edit_message_text(token, chat_id, message_id, text):
    requests.post(
        API_BASE.format(token=token) + "/editMessageCaption",
        data={"chat_id": chat_id, "message_id": message_id, "caption": text[:1024]},
        timeout=15,
    )


def poll():
    token = load_credential(TOKEN_FILE, "run @BotFather's /newbot and paste the token here")
    chat_id = load_credential(CHAT_ID_FILE, "message your new bot once, then look up the chat id via getUpdates")
    state = load_state()

    resp = requests.get(
        API_BASE.format(token=token) + "/getUpdates",
        params={"offset": state["offset"], "timeout": 0},
        timeout=20,
    )
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        print(f"ERROR: Telegram API: {result}", file=sys.stderr)
        sys.exit(1)

    updates = result["result"]
    if not updates:
        print("No new updates.")
        return

    for update in updates:
        state["offset"] = max(state["offset"], update["update_id"] + 1)

        cq = update.get("callback_query")
        if cq:
            # SECURITY: Verify the callback query comes from the authorized chat
            # Bug: Previously callbacks weren't checked — anyone could approve/reject
            cq_msg = cq.get("message", {})
            cq_chat = cq_msg.get("chat", {})
            if str(cq_chat.get("id")) != str(chat_id):
                print(f"Ignoring unauthorized callback from chat {cq_chat.get('id')}", file=sys.stderr)
                _answer_callback(token, cq["id"], "Unauthorized chat — not your bot.")
                continue

            data = cq.get("data", "")
            action, _, clip_id = data.partition(":")
            msg = cq["message"]
            if action == "approve":
                write_decision(clip_id, "approved")
                trigger_posting_agent()
                _edit_message_text(token, msg["chat"]["id"], msg["message_id"],
                                    f"✅ Approved — {clip_id} (posting now)")
                _answer_callback(token, cq["id"], "Approved — posting now")
                print(f"{clip_id}: approved, posting agent triggered")
            elif action == "reject":
                state["pending_reject"][clip_id] = msg["message_id"]
                _edit_message_text(token, msg["chat"]["id"], msg["message_id"],
                                    f"❌ Rejected — {clip_id}\nReply with the reason (required — this "
                                    f"is what future sourcing/production learns from).")
                _answer_callback(token, cq["id"], "Reject — reply with the reason")
                print(f"{clip_id}: rejected, awaiting reason")
            elif action == "ans":
                # data is "ans:<question_id>:<option>" — option text may itself
                # contain no colons (keyboard button text), so this is safe.
                _, question_id, option = data.split(":", 2)
                q_path = QUESTIONS_DIR / f"{question_id}.json"
                if q_path.exists():
                    q = json.loads(q_path.read_text())
                    q["answered"] = True
                    q["answer"] = option
                    q_path.write_text(json.dumps(q, indent=2))
                    _edit_message_text(token, msg["chat"]["id"], msg["message_id"],
                                        f"❓ {q['question']}\n\n→ {option}")
                    _answer_callback(token, cq["id"], f"Answered: {option}")
                    print(f"{question_id}: answered '{option}'")
                else:
                    _answer_callback(token, cq["id"], "Unknown question (already answered or expired)")
            continue

        msg = update.get("message")
        if not msg or str(msg.get("chat", {}).get("id")) != str(chat_id):
            continue
        text = msg.get("text", "")
        if not text.strip():
            continue  # empty reply, ignore

        # Match replies to a SPECIFIC pending item via Telegram's own
        # reply_to_message id first — a real test with two rejections
        # pending at once proved a bare FIFO guess wrong (2026-08-28): a
        # reply meant for the second rejection got attributed to the first.
        #
        # BUT requiring an explicit reply-to broke the common case: most
        # people just type a response in the chat without using Telegram's
        # swipe-to-reply gesture. A real rejection reason got silently
        # routed to the freeform inbox instead of being captured, because
        # it wasn't an explicit reply (2026-08-28, caught in live use).
        # Fix: when there is EXACTLY ONE pending item total (across both
        # rejects and questions combined) and the message isn't a reply to
        # something else entirely, attribute it to that one unambiguous
        # pending item. Multiple pending items still require an explicit
        # reply — genuinely ambiguous, not safe to guess.
        reply_to_id = msg.get("reply_to_message", {}).get("message_id")
        reply_id_str = str(reply_to_id) if reply_to_id is not None else None
        total_pending = len(state["pending_reject"]) + len(state["pending_questions"])

        matched_question_id = None
        if reply_id_str in state["pending_questions"]:
            matched_question_id = state["pending_questions"][reply_id_str]
        elif reply_to_id is None and total_pending == 1 and len(state["pending_questions"]) == 1:
            matched_question_id = next(iter(state["pending_questions"].values()))

        if matched_question_id is not None:
            question_id = matched_question_id
            # remove by value since the single-pending fallback doesn't know the key
            for k, v in list(state["pending_questions"].items()):
                if v == question_id:
                    del state["pending_questions"][k]
            q_path = QUESTIONS_DIR / f"{question_id}.json"
            if q_path.exists():
                q = json.loads(q_path.read_text())
                q["answered"] = True
                q["answer"] = text
                q_path.write_text(json.dumps(q, indent=2))
                print(f"{question_id}: answered (free text)")
            continue

        clip_id = None
        for cid, mid in state["pending_reject"].items():
            if mid == reply_to_id:
                clip_id = cid
                break
        if clip_id is None and reply_to_id is None and total_pending == 1 and len(state["pending_reject"]) == 1:
            clip_id = next(iter(state["pending_reject"]))

        if clip_id is None and total_pending > 1:
            # Genuinely ambiguous — more than one thing pending, and this
            # message doesn't thread to any of them. Ask rather than guess.
            requests.post(
                API_BASE.format(token=token) + "/sendMessage",
                data={"chat_id": chat_id,
                      "text": "More than one thing is awaiting your reply — "
                              "please reply directly (long-press → Reply) to the specific message."},
                timeout=15,
            )
            continue

        if clip_id is None:
            # Not a reply to any tracked pending item — a genuine freeform
            # message (added 2026-08-28, per Leo: unprompted messages route
            # to an agent that can actually act on them, not just log them).
            INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(INBOX_FILE, "a") as f:
                f.write(json.dumps({
                    "message_id": msg["message_id"], "text": text,
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "handled": False,
                }) + "\n")
            trigger_telegram_brain()
            print(f"Freeform message routed to inbox (message_id={msg['message_id']})")
            continue

        del state["pending_reject"][clip_id]
        write_decision(clip_id, "rejected", note=text)
        moved = move_to_rejected(clip_id)
        trigger_rejection_audit()
        confirm = f"Reason recorded for {clip_id}."
        if moved:
            confirm += f" Moved {len(moved)} file(s) out of ready-to-post."
        requests.post(
            API_BASE.format(token=token) + "/sendMessage",
            data={"chat_id": chat_id, "text": confirm},
            timeout=15,
        )
        print(f"{clip_id}: rejection reason recorded, {len(moved)} file(s) moved")

    save_state(state)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_notify = sub.add_parser("notify")
    p_notify.add_argument("clip_id")
    p_notify.add_argument("video_path")
    p_notify.add_argument("caption")

    sub.add_parser("poll")

    p_alert = sub.add_parser("alert")
    p_alert.add_argument("text")

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("question_id")
    p_ask.add_argument("question")
    p_ask.add_argument("--options", help="Comma-separated tappable options; omit for a free-text question")
    p_ask.add_argument("--recommended", help="Which option to mark (Recommended) — must exactly match one entry in --options")

    p_check = sub.add_parser("check")
    p_check.add_argument("question_id")

    p_report = sub.add_parser("report")
    p_report.add_argument("html_path", help="Path to the HTML report/dashboard to convert and send")
    p_report.add_argument("--caption", default="", help="Caption text for the PDF document")

    args = parser.parse_args()
    if args.cmd == "notify":
        notify(args.clip_id, args.video_path, args.caption)
    elif args.cmd == "alert":
        alert(args.text)
    elif args.cmd == "ask":
        options = [o.strip() for o in args.options.split(",")] if args.options else None
        ask(args.question_id, args.question, options, recommended=args.recommended)
    elif args.cmd == "check":
        check(args.question_id)
    elif args.cmd == "report":
        send_report(args.html_path, caption=args.caption)
    else:
        poll()
    return 0


if __name__ == "__main__":
    sys.exit(main())
