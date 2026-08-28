#!/usr/bin/env python3
"""Burn rolling, speech-synced subtitles onto a produced clip.

Two transcript sources, in preference order:
  1. --vtt-file: a local WebVTT file already downloaded by yt-dlp during
     sourcing (added 2026-08-28 — see below for why).
  2. --source-video-id: youtube_transcript_api, fetched live (original
     behavior, kept as fallback when no local VTT was captured).

Either source windows to the clip's [in_point, out_point) cut, de-overlaps
YouTube's rolling auto-caption segments into clean sequential subtitle cues,
and burns them in via ffmpeg's libass subtitles filter — simple line-by-line
bar style, not word-by-word karaoke.

Why --vtt-file was added: youtube_transcript_api fetches captions live from
YouTube at burn time, and for some outlets (CBS, BBC, CNBC observed) this
returns garbage or fails outright, even though yt-dlp had already downloaded
a perfectly good local .vtt file during sourcing (same auto-captions, same
source — the difference is fetching them live a second time via a different
path vs. reading the file already on disk). parse_vtt() strips the karaoke
<c>...</c> timing tags and rolling-caption line duplication YouTube's raw
VTT format uses, producing the same (start, duration, text) shape
window_and_deoverlap() already expects — that function needed zero changes,
it was already built to de-overlap exactly this rolling-caption pattern for
the API source.

Usage:
  # Preferred — local VTT already on disk from sourcing:
  python3 burn_subtitles.py --video <clip.mp4> --vtt-file <captures/x.en.vtt> \\
      --in-point 0 --out-point 40 --output <output.mp4>

  # Fallback — live API fetch (original behavior):
  python3 burn_subtitles.py --video <clip.mp4> --source-video-id <YT_ID> \\
      --in-point 0 --out-point 40 --output <output.mp4>

Style: standardized per Leo's 2026-08-27 overlay cleanup — medium size
(~6% of frame height), simple bar, positioned above the bottom safe zone
established in content-agent-prompt.md §3b (bottom ~15% is YouTube Shorts UI).
"""

import argparse
import html
import os
import re
import subprocess
import sys
import tempfile
from collections import namedtuple

# Frame is 1080x1920 (portrait, matches the pipeline's fixed export spec).
FRAME_HEIGHT = 1920
FONT_SIZE = round(FRAME_HEIGHT * 0.035)         # ~3.5% of height — the naive "6%" spec rendered
                                                  # oversized/overlapping in a real test (see
                                                  # test-batch/narrated-headline-tests/ commit history);
                                                  # this is calibrated against an actual rendered frame,
                                                  # not the abstract percentage
MARGIN_V = round(FRAME_HEIGHT * 0.17)           # sits just above the bottom ~15% safe zone
MAX_CHARS_PER_LINE = 60                          # recalibrated for the smaller font size above


# Uniform shape both transcript sources produce, so window_and_deoverlap()
# (built for youtube_transcript_api's snippet objects) works identically for
# VTT-sourced cues without any changes to that function.
Snippet = namedtuple("Snippet", ["start", "duration", "text"])

_VTT_TIMESTAMP = re.compile(r"(\d+):(\d{2}):(\d{2})\.(\d{3})")
_VTT_CUE_TIMING = re.compile(
    r"(\d+:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d+:\d{2}:\d{2}\.\d{3})"
)
_KARAOKE_TAG = re.compile(r"<\d+:\d{2}:\d{2}\.\d{3}>|</?c>")


def _vtt_ts_to_seconds(ts: str) -> float:
    m = _VTT_TIMESTAMP.match(ts)
    if not m:
        raise ValueError(f"bad VTT timestamp: {ts!r}")
    h, mi, s, ms = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 1000


def parse_vtt(path: str) -> list:
    """Parse a local WebVTT file (yt-dlp's raw auto-caption format) into
    Snippet(start, duration, text) tuples.

    YouTube's raw VTT uses two things that need stripping/handling, not
    present in a "clean" VTT file:
      - Karaoke word-timing tags inline in the text: "word<00:00:01.234><c> next</c>"
      - Rolling captions: consecutive cues repeat the prior line's text with
        one more word appended each time, rather than each cue being a
        distinct new line. This is the SAME pattern youtube_transcript_api's
        raw snippets have — deliberately not deduplicated here; cues are
        passed straight to window_and_deoverlap(), which already handles it.
    """
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    # Split on blank lines into cue blocks; each block may have a leading
    # cue-identifier line (a bare number), the timing line, then text lines.
    blocks = re.split(r"\n\s*\n", raw)
    snippets = []
    for block in blocks:
        m = _VTT_CUE_TIMING.search(block)
        if not m:
            continue  # header block ("WEBVTT", "Kind:", "Language:"), or empty
        start = _vtt_ts_to_seconds(m.group(1))
        end = _vtt_ts_to_seconds(m.group(2))
        # Text is every line after the timing line.
        lines = block.split("\n")
        timing_idx = next(i for i, l in enumerate(lines) if "-->" in l)
        text_lines = lines[timing_idx + 1:]
        text = " ".join(l for l in text_lines).strip()
        text = _KARAOKE_TAG.sub("", text)
        text = html.unescape(text)  # decode HTML entities (&gt; -> >, &lt; -> <, &amp; -> &, etc.)
        text = text.replace(">>", "")  # strip YouTube speaker-change markers (decoded from &gt;&gt;) — fixed 2026-08-28
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        duration = end - start
        if duration <= 0:
            continue  # YouTube's raw VTT includes some zero/negative-length filler cues
        snippets.append(Snippet(start=start, duration=duration, text=text))
    return snippets


_WORD_TS = re.compile(r"<(\d+:\d{2}:\d{2}\.\d{3})><c>([^<]*)</c>")


def parse_vtt_words(path: str):
    """Extract REAL per-word (start_time, word) pairs from YouTube's raw VTT
    karaoke tags, instead of discarding them (added 2026-08-28, per Leo:
    the previous cue-level-proportional timing "flowed badly", "very
    jerky" — real speech isn't evenly paced word-to-word the way that
    approximation assumed).

    YouTube's raw VTT shows a 2-line rolling window per cue block: the
    first line is the previous block's now-"settled" line (repeated
    verbatim, no tags — already captured as real words by that PRIOR
    block), the second line is the currently-filling new line, where the
    leading word has no tag (it's brand new — never appeared in the
    previous block, so its start time is that block's own header start
    time) and every word after it carries its own explicit `<TS><c>`
    timestamp. Confirmed against a real transcript sample (2026-08-28):
    every block's leading untagged word is genuinely new, never a repeat
    of the settled first line — so no cross-block dedup logic is needed,
    just isolating the LAST whitespace token of the untagged prefix (the
    settled line's own words are joined right before it with no
    separator marking the boundary, since parse_vtt()'s line-joining
    pattern concatenates both lines of a block).

    Returns [(start_seconds, word), ...] in transcript order, plus the
    final cue's end time (needed to bound the very last word's duration,
    since it has no following word to derive an end time from).
    """
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    # Scan for cue-timing lines directly in the raw text, rather than
    # splitting on blank lines first — this file's very first cue has a
    # lone-space "align:start" filler line INSIDE the block, between the
    # timing line and the actual karaoke text, which a naive `\n\s*\n`
    # block-splitter treats as a block separator and incorrectly drops the
    # real text (confirmed via a real test: the transcript's first ~8
    # words vanished entirely). Each cue's payload is instead everything
    # between its own timing line and the NEXT timing line (or EOF) — any
    # stray blank/space-only lines inside that span are harmless noise,
    # since only actual `<c>` tag content is extracted from it.
    timing_matches = list(_VTT_CUE_TIMING.finditer(raw))
    words = []
    last_end = None
    for i, m in enumerate(timing_matches):
        block_end = timing_matches[i + 1].start() if i + 1 < len(timing_matches) else len(raw)
        payload = raw[m.end():block_end]
        if "<c>" not in payload:
            continue  # a "settled" filler cue with no new word timing
        start = _vtt_ts_to_seconds(m.group(1))
        end = _vtt_ts_to_seconds(m.group(2))
        text = " ".join(l.strip() for l in payload.split("\n")).strip()

        first_tag = text.find("<")
        leading = text[:first_tag].strip() if first_tag > 0 else ""
        leading_words = leading.split()
        if leading_words:
            w = html.unescape(leading_words[-1])
            if w and w != ">>":
                words.append((start, w))

        for ts_str, w in _WORD_TS.findall(text):
            t = _vtt_ts_to_seconds(ts_str)
            w = html.unescape(w.strip())
            if w and w != ">>":
                words.append((t, w))

        last_end = end

    return words, last_end


def fetch_transcript(video_id: str):
    from youtube_transcript_api import YouTubeTranscriptApi  # lazy — only
    # needed for the API fallback path, not the (preferred) VTT path.
    api = YouTubeTranscriptApi()
    return list(api.fetch(video_id, languages=["en"]))


def window_and_deoverlap(snippets, in_point: float, out_point: float):
    """Keep snippets overlapping [in_point, out_point), shift to clip-relative
    time, and de-overlap YouTube's rolling caption style into sequential cues.

    YouTube's rolling captions repeat the prior cue's text with one more word
    appended each cue (e.g. "Hello world", "Hello world how", "Hello world how are").
    Without stripping the redundant prefix, each displayed line would be a truncated
    repeat of all prior lines — the bug this fixes (tb018_c1, 2026-08-28)."""
    windowed = [s for s in snippets if s.start < out_point and (s.start + s.duration) > in_point]
    windowed.sort(key=lambda s: s.start)

    cues = []
    prev_full_text = ""
    for i, s in enumerate(windowed):
        start = max(s.start, in_point) - in_point
        # End at the next cue's start (de-overlap), or this cue's own natural end,
        # whichever is earlier — avoids two lines ever showing at once.
        natural_end = min(s.start + s.duration, out_point) - in_point
        if i + 1 < len(windowed):
            next_start = max(windowed[i + 1].start, in_point) - in_point
            end = min(natural_end, next_start)
        else:
            end = natural_end

        # Strip redundant rolling-caption prefix: each cue repeats the prior
        # cue's text plus new words — keep only the new words
        text = s.text.strip()
        if prev_full_text and text.startswith(prev_full_text):
            text = text[len(prev_full_text):].strip()

        if end > start and text:
            cues.append((start, end, text))

        prev_full_text = s.text.strip()
    return cues


def _wrap(text: str, max_chars: int) -> str:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\\N".join(lines)  # libass line break


_SENTENCE_END = re.compile(r"[.!?]$")
_COMMA_END = re.compile(r",$")
MIN_PHRASE_WORDS = 2
MAX_PHRASE_WORDS = 4


def chunk_words_real_timing(words, last_end, in_point, out_point,
                             min_words=MIN_PHRASE_WORDS, max_words=MAX_PHRASE_WORDS):
    """Group (start_time, word) pairs — REAL per-word timestamps from
    parse_vtt_words() — into 2-4 word phrase cues, windowed to
    [in_point, out_point) and shifted to clip-relative time.

    This is the fix for "jerky"/badly-flowing timing (2026-08-28): each
    phrase starts exactly when its first word is actually spoken and ends
    exactly when the next phrase's first word starts — real speech
    rhythm (pauses, fast bursts, slow emphasis) comes through directly,
    unlike the earlier approach of evenly subdividing a whole cue's
    duration by word count, which assumed a constant words-per-second
    rate no one actually speaks at.
    """
    windowed = [(t, w) for t, w in words if in_point <= t < out_point]
    if not windowed:
        return []

    # Natural-pause-preferring chunking, same rule as the old chunk_phrases(),
    # now operating on the flat global word list instead of one cue's text.
    chunks = []
    i, n = 0, len(windowed)
    while i < n:
        remaining = n - i
        if remaining <= max_words:
            chunks.append(windowed[i:])
            i = n
            continue
        break_at = max_words
        for length in range(min_words, max_words + 1):
            if i + length - 1 < n:
                w = windowed[i + length - 1][1]
                if _SENTENCE_END.search(w) or _COMMA_END.search(w):
                    break_at = length
        chunks.append(windowed[i:i + break_at])
        i += break_at

    phrases = []
    for idx, chunk in enumerate(chunks):
        start = chunk[0][0]
        if idx + 1 < len(chunks):
            end = chunks[idx + 1][0][0]
        else:
            # last chunk in range — bound by the out_point or the last
            # known cue end, whichever is tighter, so it doesn't linger
            # forever if this is also the transcript's very last word.
            end = min(out_point, last_end) if last_end else out_point
        end = max(end, start + 0.1)  # never zero/negative duration
        text = " ".join(w for _, w in chunk)
        phrases.append((start - in_point, end - in_point, text))
    return phrases


def chunk_phrases(text, start, end, min_words=MIN_PHRASE_WORDS, max_words=MAX_PHRASE_WORDS):
    """FALLBACK ONLY (superseded 2026-08-28 by chunk_words_real_timing() for
    the --vtt-file path, which now has REAL per-word timing). This function
    subdivides one whole (start, end, text) cue's duration proportionally
    by word count — a same-pace-per-word approximation that Leo confirmed
    "flows badly"/"jerky" against real speech. Kept only for the
    --source-video-id fallback path (youtube_transcript_api snippets have
    no per-word timing at all, so this proportional approximation is the
    best available there — real per-word timing needs the karaoke tags
    only the raw VTT file has).

    Prefers breaking at a natural pause (a word ending in , . ! or ?)
    within [min_words, max_words] over a bare word-count cutoff.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    i, n = 0, len(words)
    while i < n:
        remaining = n - i
        if remaining <= max_words:
            chunks.append(words[i:])
            i = n
            continue
        break_at = max_words
        for length in range(min_words, max_words + 1):
            if i + length - 1 < n:
                w = words[i + length - 1]
                if _SENTENCE_END.search(w) or _COMMA_END.search(w):
                    break_at = length  # keep scanning — prefer the LATEST natural break in range
        chunks.append(words[i:i + break_at])
        i += break_at

    total_words = sum(len(c) for c in chunks) or 1
    duration = end - start
    phrases = []
    t = start
    for chunk in chunks:
        frac = len(chunk) / total_words
        chunk_end = t + duration * frac
        phrases.append((t, chunk_end, " ".join(chunk)))
        t = chunk_end
    return phrases


def write_ass(phrases, path: str) -> None:
    """Write an .ass subtitle file with the standardized style baked in.

    Style matches the headline overlay (2026-08-28, per Leo: subtitle
    color/font/style "doesn't fit our other text/overlay") — yellow, bold
    DejaVu Sans, same brand as breaking_news_overlay.py's headline text.

    `phrases` is already a flat list of short (start, end, text) phrase
    cues — chunking happens before this function now (either
    chunk_words_real_timing() for real per-word sync, or chunk_phrases()
    for the API-fallback path with no per-word data), not inside it.

    Each phrase fades in/out independently via libass's \\fad(in,out) tag
    (added 2026-08-28, per Leo — the real per-word timing fixed the
    SPEED/sync of transitions, but hard cuts between phrases still read as
    "jerky"; fading softens the visual cut itself). 225ms each side,
    capped per-phrase so a fade never eats more than 40% of a very short
    phrase's own duration on each side — a phrase under ~560ms still gets
    SOME fade, just proportionally shorter, rather than never reaching
    full opacity. Independent per-phrase fades only, no crossfade overlap
    with the neighboring phrase — matches Leo's explicit choice.
    """
    FADE_MS = 225
    FADE_MS_CAP_FRACTION = 0.4  # each side gets at most this fraction of the phrase's own duration
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: {FRAME_HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,{FONT_SIZE},&H0000FFFF,&H00000000,&H90000000,-1,0,3,2,0,2,60,60,{MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def ts(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h:d}:{m:02d}:{s:05.2f}"

    lines = [header]
    for start, end, text in phrases:
        wrapped = _wrap(text, MAX_CHARS_PER_LINE)
        duration_ms = max((end - start) * 1000, 1)
        fade_ms = min(FADE_MS, int(duration_ms * FADE_MS_CAP_FRACTION))
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Default,,0,0,0,,{{\\fad({fade_ms},{fade_ms})}}{wrapped}\n")

    with open(path, "w") as f:
        f.writelines(lines)


def burn(video_path: str, ass_path: str, output_path: str) -> None:
    # subtitles filter needs an escaped path when it contains special chars
    escaped = ass_path.replace(":", "\\:").replace("'", "\\'")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"subtitles='{escaped}'",
        "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-2000:]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, help="Path to the already-cut/overlaid clip")
    parser.add_argument("--vtt-file", help="Local WebVTT file from sourcing (preferred — see module docstring)")
    parser.add_argument("--source-video-id", help="Source YouTube video ID — fallback if no --vtt-file")
    parser.add_argument("--in-point", type=float, required=True, help="Clip in-point in source, seconds")
    parser.add_argument("--out-point", type=float, required=True, help="Clip out-point in source, seconds")
    parser.add_argument("--output", required=True, help="Output path for the subtitled video")
    args = parser.parse_args()

    if not args.vtt_file and not args.source_video_id:
        parser.error("provide --vtt-file (preferred) or --source-video-id (fallback)")

    if args.vtt_file:
        # Preferred path — real per-word timing from the karaoke tags
        # (2026-08-28, fixes "jerky"/badly-flowing timing from the old
        # whole-cue proportional approximation).
        print(f"Parsing local VTT (real word timing): {args.vtt_file}...")
        words, last_end = parse_vtt_words(args.vtt_file)
        phrases = chunk_words_real_timing(words, last_end, args.in_point, args.out_point)
    else:
        print(f"Fetching transcript for {args.source_video_id}...")
        snippets = fetch_transcript(args.source_video_id)
        cues = window_and_deoverlap(snippets, args.in_point, args.out_point)
        phrases = [p for start, end, text in cues for p in chunk_phrases(text, start, end)]

    if not phrases:
        print("No transcript content found in this window — nothing to burn in.", file=sys.stderr)
        return 1
    print(f"Windowed to {len(phrases)} subtitle phrases for [{args.in_point}, {args.out_point})")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ass", delete=False) as tmp:
        ass_path = tmp.name
    write_ass(phrases, ass_path)

    try:
        burn(args.video, ass_path, args.output)
    finally:
        os.unlink(ass_path)

    print(f"Done. Subtitled video: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
