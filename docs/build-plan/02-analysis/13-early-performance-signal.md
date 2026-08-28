# Early Performance Signal (2026-08-26)

First real performance data ever pulled for this channel — via YouTube Data API v3
(`credentials/yt_data_api_key.txt`, read-only, verified working). Every prior posting-log
only recorded post IDs/status; this is the first actual view/engagement data logged
anywhere in the pipeline. Small sample (7 videos) — read as an early signal to weight
future sourcing/hook decisions, not a settled conclusion.

| Clip | Views | Likes | Comments | Topic type |
|---|---|---|---|---|
| Canada tariffs ($27.6B retaliation) | 1550 | 32 | 0 | Political/economic conflict, named figures, hard numbers |
| Wrong-way driver crash | 1073 | 20 | 3 | Raw dramatic footage, no politics |
| Israel/Iran targeting | 1155 | 15 | 1 | Geopolitical conflict |
| Canada trade tariffs (Trump) | 1190 | 24 | 4 | Political/economic conflict |
| Trump: Iran collapsing | 513 | 4 | 0 | Political statement, less concrete/visual |
| OpenAI "rogue" employee | 167 | 1 | 1 | Tech/AI industry story |
| Alibaba Wan3.0 AI video launch | 22 | 1 | 0 | Tech/AI industry story |

## Early read (low confidence, small sample)

- **Political/geopolitical conflict clips with concrete stakes (dollar figures, named
  officials, a clear "who did what to whom") clustered at the top** (1073-1550 views).
- **Tech/AI industry stories clustered at the bottom** (22-167 views) — a full 10-70x
  gap versus the political conflict clips. Two data points isn't a pattern yet, but
  it's a big enough gap to weight sourcing toward conflict/consequence stories over
  industry-announcement stories until more data says otherwise.
- Comment counts are low across the board (0-4) — the "end with an engagement question"
  rule (content-agent-prompt.md) hasn't moved comment counts much yet; may need a
  stronger/more specific question, or comments may just not be the right metric to
  chase (views/watch-time drive Shorts distribution and YPP eligibility, not comments —
  see the correction already noted in content-agent-prompt.md §2b).

## What to actually do with this

Content Agent's §2b now reads posting-log `## Performance` sections before sourcing —
this doc is the synthesized version for a quick read, but the raw per-clip numbers in
each `*-posting-log.md` are the source of truth and will accumulate real signal as more
clips get posted and Leo (or a future automated pull) logs their numbers. Revisit this
doc once there's 15-20+ data points — right now it's directional, not decisive.
