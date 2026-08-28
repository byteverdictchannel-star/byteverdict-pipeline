# watch — vendored, 2026-08-28

Lets an agent actually *watch* a video — downloads/frame-extracts + pulls a
timestamped transcript, so verification claims (outlet attribution, who's
speaking, sensitive content) are grounded in what's actually on screen
instead of a single unreliable vision check or an assumption.

**Source:** https://github.com/bradautomates/claude-video (MIT — see
`LICENSE-upstream`). Vendored here as a plain Python tool, not installed as
a Claude Code plugin, since the agents that would use it (Content/Posting
Agent) run through Hermes, not Claude Code.

**Why it's here:** two real bugs this session — tb005-c1 shipping with wrong
outlet attribution for two days, and a caption crediting the wrong minister
by name — were both things a multi-frame look at the actual footage would
plausibly have caught. `vision_analyze` (the existing Hermes tool used for
this) has also been intermittently down (401 errors across several runs per
the posting logs). This doesn't replace `vision_analyze` — it's a second,
independent way to actually look at a video when it's down, or as a deeper
check when a claim (attribution, who's on screen) matters enough to verify
properly rather than trust a single frame.

**One local patch applied:** `frames.py` used `-vsync vfr`, an ffmpeg flag
name this machine's ffmpeg build (a recent git-master snapshot) no longer
accepts — it now hard-errors instead of just warning. Changed to the modern
equivalent, `-fps_mode vfr`, in both places it appears. That's the only
change from upstream.

**Zero new dependencies.** Pure Python stdlib, calling `yt-dlp` and `ffmpeg`
— both already used elsewhere in this pipeline. The optional Whisper
transcription fallback (only used when a video has no captions) needs a
Groq or OpenAI key and was NOT configured or tested — this pipeline already
has TranscriptAPI for transcripts, so Whisper likely isn't needed here at
all. Frame extraction + a local/URL video is the useful part.

## Usage

```bash
python3 pipeline/tools/watch/scripts/watch.py <path-or-url> --detail efficient
```

Prints a markdown report with frame paths (`t=MM:SS` timestamps) and any
transcript found. Read the frame paths with the Read tool to actually see
them — same pattern as any other vision check in this pipeline.

`--detail balanced` or `--detail token-burner` for denser sampling on a
longer or more important source; `--start`/`--end` to focus a specific
window (e.g. "does the podium nameplate near 0:12 confirm who's speaking").

**Verified working** (2026-08-28) against `tb005_cut_raw.mp4` — correctly
extracted 6 deduped frames from candidates, one of which plainly shows the
"Global NEWS" watermark, matching the ground truth established by hand
earlier the same day.

## Now mandatory, with a code-level receipt (updated 2026-08-28)

Made mandatory in both `jobs.json` (Content Agent's cron prompt, step 2b)
and `posting-agent-prompt.md` (§3a step 4) on 2026-08-28. **On the first
real cron run after that change, the agent skipped it anyway and still
reported the clip as passing the quality gate** — confirmed by checking the
run's own logs, not assumed. A prompt-level "MANDATORY" is not a hard
guarantee.

So this tool now writes a **receipt** every time it genuinely extracts real
frames from a real video file — see `pipeline/watch_gate.py`. The receipt is
keyed by a SHA-256 of the video file's actual bytes, not its path, so a
stale receipt from watching an old version of a file (before a re-render)
does not satisfy the gate for a new version. `record_watch_receipt()` is
wired into `watch.py` itself; `check_watch_receipt()` is the enforcement
side, built and tested but **not yet wired into `youtube_post.py` /
`ig_post.py` / `fb_post.py`** — see the TODO at the bottom of
`watch_gate.py` for the two real scoping questions that need answering
first (which file gets checked — master or platform export — and how a
legitimate "watched it, correctly said no" case should be distinguished
from "nobody ever looked").
